import os
import time
import json
import pandas as pd
import fitz  # PyMuPDF
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
import logging
import re
import concurrent.futures
from PIL import Image
import pytesseract
from bidi.algorithm import get_display
import numpy as np
from collections import defaultdict
import pdfplumber
import arabic_reshaper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants from environment variables
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
TEMP_FOLDER = os.getenv("TEMP_FOLDER", "server/temp_files")
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
TESSERACT_LANGS = os.getenv("TESSERACT_LANGS", "eng+heb")

# Configure tesseract
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Status constants
class ConversionStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    ANALYSIS = "analysis"  # New state for PDF analysis

# Helper functions
def get_session_file_path(session_id: str) -> str:
    """Get the path to the session status file"""
    return os.path.join(TEMP_FOLDER, f"{session_id}.json")

def save_session_status(session_id: str, status: dict) -> None:
    """Save session status to a JSON file"""
    with open(get_session_file_path(session_id), "w") as f:
        json.dump(status, f)

def get_session_status(session_id: str) -> dict:
    """Get session status from a JSON file"""
    with open(get_session_file_path(session_id), "r") as f:
        return json.load(f)

def update_progress(session_id: str, current_page: int, total_pages: int) -> None:
    """Update conversion progress"""
    status = get_session_status(session_id)
    
    # Check if paused
    if status["status"] == ConversionStatus.PAUSED:
        return status
    
    progress = int((current_page / total_pages) * 100) if total_pages > 0 else 0
    
    status["progress"] = progress
    status["current_page"] = current_page
    status["total_pages"] = total_pages
    
    save_session_status(session_id, status)
    return status

def is_rtl_text(text: str) -> bool:
    """Check if text contains RTL characters (mainly Hebrew)"""
    # Hebrew Unicode range: 0x0590-0x05FF
    hebrew_pattern = re.compile(r'[\u0590-\u05FF]')
    return bool(hebrew_pattern.search(text))

def fix_rtl_text(text: str) -> str:
    """
    Properly fix RTL text (Hebrew) for correct display and output
    
    This handles the bidirectional text properly and ensures Hebrew
    characters are displayed in the correct order
    """
    if not text or not is_rtl_text(text):
        return text
    
    try:
        # Reshape Arabic and Hebrew text (handles connecting characters properly)
        reshaped_text = arabic_reshaper.reshape(text)
        # Apply bidirectional algorithm
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception as e:
        logger.error(f"Error fixing RTL text: {str(e)}")
        return text

def preprocess_text(text: str) -> str:
    """Preprocess extracted text"""
    # Handle RTL text using the improved method
    if is_rtl_text(text):
        text = fix_rtl_text(text)
    
    # Remove excessive whitespace while preserving some structure
    text = re.sub(r'\s{3,}', '  ', text).strip()
    
    return text

def is_number(text: str) -> bool:
    """Check if a string represents a number"""
    # Remove common number formatting
    cleaned = text.replace(',', '').replace(' ', '')
    
    # Try to convert to float
    try:
        float(cleaned)
        return True
    except ValueError:
        return False

def extract_text_from_page(page) -> str:
    """Extract text from a PyMuPDF page"""
    return page.get_text()

def extract_text_from_image(image_bytes) -> str:
    """Extract text from an image using OCR"""
    try:
        # Convert bytes to PIL Image
        image = Image.open(tempfile.NamedTemporaryFile(suffix='.png', delete=False))
        image.save(image.filename)
        
        # Use Tesseract OCR to extract text
        text = pytesseract.image_to_string(image, lang=TESSERACT_LANGS)
        
        # Clean up
        os.unlink(image.filename)
        
        return text
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return ""

def analyze_text_layout(page) -> List[Dict]:
    """
    Enhanced analysis of the text layout on a page using PyMuPDF's text extraction
    
    Returns a list of blocks with their positions and text
    """
    # Extract text blocks with their positions
    blocks = page.get_text("dict")["blocks"]
    text_blocks = []
    
    for block in blocks:
        if block.get("type") == 0:  # Type 0 is text
            for line in block.get("lines", []):
                line_text = ""
                line_bbox = line.get("bbox", [0, 0, 0, 0])
                
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                
                if line_text.strip():
                    # Store the original text without RTL handling at this stage
                    text_blocks.append({
                        "text": line_text.strip(),
                        "bbox": line_bbox,
                        "x0": line_bbox[0],
                        "y0": line_bbox[1],
                        "x1": line_bbox[2],
                        "y1": line_bbox[3]
                    })
    
    # Sort blocks by y-coordinate (top to bottom)
    text_blocks.sort(key=lambda b: b["y0"])
    
    return text_blocks

def identify_columns(text_blocks: List[Dict]) -> List[float]:
    """
    Identify column positions based on the alignment of text blocks
    
    Returns a list of x-coordinates that likely represent column boundaries
    """
    # Collect all starting x-coordinates
    x_positions = [block["x0"] for block in text_blocks]
    
    # Group similar x-positions (allowing for small differences)
    x_clusters = []
    tolerance = 10  # Increased tolerance for RTL text alignment variations
    
    for pos in sorted(x_positions):
        # Check if this position belongs to an existing cluster
        found_cluster = False
        for i, cluster in enumerate(x_clusters):
            if abs(cluster["center"] - pos) <= tolerance:
                cluster["positions"].append(pos)
                # Update center as average
                cluster["center"] = sum(cluster["positions"]) / len(cluster["positions"])
                found_cluster = True
                break
        
        # If not found, create a new cluster
        if not found_cluster:
            x_clusters.append({"center": pos, "positions": [pos]})
    
    # Filter clusters with enough occurrences to be considered columns
    min_occurrences = max(2, len(text_blocks) // 10)  # At least 2 occurrences or 10% of blocks
    column_positions = [cluster["center"] for cluster in x_clusters 
                       if len(cluster["positions"]) >= min_occurrences]
    
    return sorted(column_positions)

def group_blocks_into_rows(text_blocks: List[Dict]) -> List[List[Dict]]:
    """
    Group text blocks into rows based on their vertical positions
    
    Returns a list of rows, where each row is a list of text blocks
    """
    rows = []
    current_row = []
    
    # Sort blocks by y-coordinate
    sorted_blocks = sorted(text_blocks, key=lambda b: b["y0"])
    
    if not sorted_blocks:
        return rows
    
    # Start with the first block
    current_row = [sorted_blocks[0]]
    current_y = sorted_blocks[0]["y1"]
    
    # Group blocks with similar y-coordinates
    for block in sorted_blocks[1:]:
        # If the block is near the current row, add it
        if abs(block["y0"] - current_y) < 10:  # Increased tolerance for row detection
            current_row.append(block)
            # Update current_y to the maximum bottom coordinate
            current_y = max(current_y, block["y1"])
        else:
            # Sort blocks in row by x-coordinate
            current_row.sort(key=lambda b: b["x0"])
            rows.append(current_row)
            current_row = [block]
            current_y = block["y1"]
    
    # Add the last row
    if current_row:
        current_row.sort(key=lambda b: b["x0"])
        rows.append(current_row)
    
    return rows

def assign_blocks_to_columns(rows: List[List[Dict]], column_positions: List[float]) -> List[List[List[Dict]]]:
    """
    Assign text blocks to their respective columns
    
    Returns a list of rows, where each row is a list of columns, 
    and each column contains blocks belonging to that column
    """
    structured_rows = []
    
    for row in rows:
        # Initialize empty columns (add one extra for the rightmost column)
        columns = [[] for _ in range(len(column_positions) + 1)]
        
        for block in row:
            # Find which column this block belongs to
            col_index = 0
            for i, col_pos in enumerate(column_positions):
                if block["x0"] >= col_pos - 10:  # Increased tolerance
                    col_index = i
            
            columns[col_index].append(block)
        
        structured_rows.append(columns)
    
    return structured_rows

def detect_tables_in_text(text: str) -> List[Dict[str, Any]]:
    """
    Detect table structures in extracted text
    
    This is a simplified implementation that looks for patterns in text
    that might indicate table structures.
    
    Returns a list of dictionaries representing potential tables
    """
    # Split text into lines
    lines = text.split('\n')
    tables = []
    current_table = []
    
    # Simple table detection: look for lines with consistent delimiters
    # or consistent spacing patterns
    for line in lines:
        line = line.strip()
        if not line:
            # Empty line might indicate end of table
            if current_table:
                tables.append(current_table)
                current_table = []
            continue
        
        # Check if line has tabular structure (spaces, tabs, or consistent delimiters)
        if '\t' in line or '  ' in line or '|' in line or ';' in line or ',' in line:
            current_table.append(line)
    
    # Add the last table if any
    if current_table:
        tables.append(current_table)
    
    # Convert raw tables to structured data
    structured_tables = []
    for table_lines in tables:
        # Try to determine the delimiter
        sample_line = table_lines[0]
        delimiter = None
        
        if '|' in sample_line:
            delimiter = '|'
        elif ';' in sample_line:
            delimiter = ';'
        elif ',' in sample_line:
            delimiter = ','
        
        # If no clear delimiter, try to split by whitespace
        rows = []
        for line in table_lines:
            if delimiter:
                # Split by delimiter
                cells = [cell.strip() for cell in line.split(delimiter)]
            else:
                # Split by whitespace (keeping consecutive whitespace as a single delimiter)
                cells = re.split(r'\s{2,}', line)
            
            # Remove empty cells
            cells = [cell for cell in cells if cell]
            
            if cells:
                rows.append(cells)
        
        # Check if we have consistent number of columns
        if rows:
            # Get number of columns in first row
            num_cols = len(rows[0])
            
            # Check if all rows have the same number of columns
            is_consistent = all(len(row) == num_cols for row in rows)
            
            if is_consistent and num_cols > 1:
                # This looks like a valid table
                structured_tables.append({
                    "rows": rows,
                    "num_columns": num_cols
                })
    
    return structured_tables

def extract_structured_table(page) -> Optional[List[List[str]]]:
    """
    Extract a structured table from a PDF page using layout analysis
    
    Returns a list of rows, where each row is a list of cell values
    """
    try:
        # Get text blocks with their positions
        text_blocks = analyze_text_layout(page)
        
        if not text_blocks:
            return None
        
        # Identify column positions
        column_positions = identify_columns(text_blocks)
        
        # Group blocks into rows
        rows = group_blocks_into_rows(text_blocks)
        
        # Assign blocks to columns
        structured_rows = assign_blocks_to_columns(rows, column_positions)
        
        # Convert to text rows
        table_rows = []
        for row in structured_rows:
            text_row = []
            for column in row:
                if column:
                    # Combine all blocks in this column
                    combined_text = " ".join(block["text"] for block in column)
                    # Handle RTL at the cell level
                    if is_rtl_text(combined_text):
                        combined_text = get_display(combined_text)
                    text_row.append(combined_text)
                else:
                    text_row.append("")
            
            # Skip empty rows
            if any(cell.strip() for cell in text_row):
                table_rows.append(text_row)
        
        # Ensure we have at least a few rows with multiple cells for it to be a valid table
        if table_rows and len(table_rows) > 1 and any(len(row) > 1 for row in table_rows):
            return table_rows
        
        return None
        
    except Exception as e:
        logger.error(f"Error in structured table extraction: {str(e)}")
        return None

def normalize_table_data(tables: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert detected tables to a pandas DataFrame
    
    This function tries to normalize the table data and identify headers
    """
    if not tables:
        return pd.DataFrame()
    
    # Start with the first table
    table = tables[0]
    rows = table["rows"]
    
    # Try to identify headers
    header_row = rows[0] if len(rows) > 0 else []
    
    # Analyze if the first row looks like a header
    is_header = False
    if header_row:
        # Check if first row differs from others (e.g., formatting, bold, etc.)
        # For simplicity, we'll assume the first row is a header if it's different in some way
        is_header = True
    
    # Convert to DataFrame
    if len(rows) > 1:
        # Get max columns across all rows
        max_cols = max(len(row) for row in rows)
        
        # Only proceed if we have multiple columns
        if max_cols <= 1:
            logger.warning("Table with only one column detected in text-based extraction")
            return pd.DataFrame()
        
        # Ensure all rows have same number of columns
        padded_rows = []
        for i, row in enumerate(rows):
            # Skip header row if it's identified as a header
            if i == 0 and is_header:
                continue
                
            if len(row) < max_cols:
                padded_rows.append(row + [''] * (max_cols - len(row)))
            else:
                padded_rows.append(row[:max_cols])  # Trim if too long
        
        # Make sure all cells are properly converted to strings
        clean_rows = []
        for row in padded_rows:
            clean_row = [str(cell) if cell is not None else '' for cell in row]
            clean_rows.append(clean_row)
        
        try:
            # Create DataFrame
            df = pd.DataFrame(clean_rows)
            
            # Set column headers if we have a header row
            if is_header:
                # Make sure header has the right length
                if len(header_row) < max_cols:
                    header_row = header_row + [f'Column {i+1}' for i in range(len(header_row), max_cols)]
                elif len(header_row) > max_cols:
                    header_row = header_row[:max_cols]
                
                df.columns = header_row
        except Exception as e:
            logger.error(f"Error creating DataFrame in normalize_table_data: {str(e)}")
            return pd.DataFrame()
    else:
        # Only header row exists, create empty DataFrame with those headers
        df = pd.DataFrame(columns=header_row)
    
    # Try to convert numeric columns
    for col in df.columns:
        try:
            # Check if at least 50% of non-empty values in column look like numbers
            non_empty = df[col][df[col].astype(str).str.strip() != '']
            if len(non_empty) > 0:
                num_count = sum(is_number(str(x)) for x in non_empty)
                if num_count / len(non_empty) >= 0.5:
                    # Convert to numeric, coerce errors to NaN
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
        except Exception as e:
            logger.warning(f"Error converting column {col} to numeric: {str(e)}")
    
    return df

def merge_multiline_entries(rows):
    """
    Merge rows that appear to be continuations of previous rows
    """
    if not rows:
        return rows
    
    merged_rows = [rows[0]]
    
    for i in range(1, len(rows)):
        current_row = rows[i]
        
        # Check if this row looks like a continuation of the previous row
        is_continuation = False
        
        # If the row starts with many empty cells, it might be a continuation
        empty_cells_at_start = 0
        for cell in current_row:
            if not cell.strip():
                empty_cells_at_start += 1
            else:
                break
        
        # If more than half of beginning cells are empty, consider it a continuation
        if empty_cells_at_start > len(current_row) / 2:
            is_continuation = True
        
        if is_continuation and merged_rows:
            # Merge with the previous row
            prev_row = merged_rows[-1]
            for j in range(len(current_row)):
                if j < len(prev_row):
                    if current_row[j].strip() and not prev_row[j].strip():
                        # Fill empty cell in previous row
                        prev_row[j] = current_row[j]
                    elif current_row[j].strip() and prev_row[j].strip():
                        # Append to non-empty cell
                        prev_row[j] += " " + current_row[j]
        else:
            # Add as a new row
            merged_rows.append(current_row)
    
    return merged_rows

def extract_tables_with_pdfplumber(pdf_path: str, page_num: int) -> List[pd.DataFrame]:
    """
    Extract tables from a PDF page using pdfplumber with enhanced table detection
    and data type preservation, especially for numerical values.
    
    Args:
        pdf_path: Path to the PDF file
        page_num: Page number to extract tables from (0-based)
    
    Returns:
        List of pandas DataFrames, each representing a table
    """
    try:
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                
                # Try different table extraction strategies
                # 1. First try with default settings
                extracted_tables = page.extract_tables()
                
                # 2. Try with text-based strategy if no tables found
                if not extracted_tables:
                    extracted_tables = page.extract_tables(
                        table_settings={
                            "vertical_strategy": "text", 
                            "horizontal_strategy": "text",
                            "intersection_tolerance": 5,
                            "join_tolerance": 15,
                            "edge_min_length": 3,
                            "min_words_vertical": 1,
                            "min_words_horizontal": 1
                        }
                    )
                
                # 3. Try with line-based strategy if still no tables
                if not extracted_tables:
                    extracted_tables = page.extract_tables(
                        table_settings={
                            "vertical_strategy": "lines", 
                            "horizontal_strategy": "lines",
                            "intersection_tolerance": 10,
                            "join_tolerance": 20,
                            "edge_min_length": 5
                        }
                    )
                
                # Convert each table to DataFrame
                for table in extracted_tables:
                    if table and len(table) > 0:
                        # Get header (first row)
                        header = table[0]
                        data = table[1:] if len(table) > 1 else []
                        
                        # Skip tables with only one column
                        if len(header) <= 1:
                            continue
                        
                        # Clean data and header - properly handle RTL text
                        clean_header = []
                        for i, cell in enumerate(header):
                            if cell is None:
                                clean_header.append(f"Column {i+1}")
                            else:
                                cell_text = str(cell).strip()
                                if is_rtl_text(cell_text):
                                    clean_header.append(fix_rtl_text(cell_text))
                                else:
                                    clean_header.append(cell_text)
                        
                        # Clean column names to be valid for Excel
                        clean_header = [sanitize_column_name(col) for col in clean_header]
                        
                        clean_data = []
                        for row in data:
                            clean_row = []
                            for cell in row:
                                if cell is None:
                                    clean_row.append("")
                                else:
                                    cell_text = str(cell).strip()
                                    # Preserve numeric values as numbers
                                    if is_numeric(cell_text):
                                        try:
                                            # Try to convert to float or int
                                            if '.' in cell_text:
                                                clean_row.append(float(cell_text.replace(',', '')))
                                            else:
                                                clean_row.append(int(cell_text.replace(',', '')))
                                        except ValueError:
                                            # If conversion fails, keep as string
                                            clean_row.append(cell_text)
                                    elif is_rtl_text(cell_text):
                                        clean_row.append(fix_rtl_text(cell_text))
                                    else:
                                        clean_row.append(cell_text)
                            clean_data.append(clean_row)
                        
                        # Create DataFrame
                        if clean_data:
                            df = pd.DataFrame(clean_data, columns=clean_header)
                            
                            # Convert numeric columns to appropriate types
                            for col in df.columns:
                                if df[col].dtype == 'object':  # Only process string columns
                                    # Check if at least 70% of non-empty values are numeric
                                    non_empty = df[col].astype(str).str.strip() != ''
                                    if non_empty.sum() > 0:
                                        numeric_values = df[col][non_empty].apply(lambda x: is_numeric(str(x)))
                                        if numeric_values.sum() / len(numeric_values) >= 0.7:
                                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            
                            tables.append(df)
        
        return tables
    except Exception as e:
        logger.error(f"Error extracting tables with pdfplumber: {str(e)}")
        return []

def sanitize_column_name(name: str) -> str:
    """
    Sanitize column names to be valid in Excel
    
    Args:
        name: Original column name
    
    Returns:
        Sanitized column name
    """
    # Replace characters that might cause issues in Excel
    if not name:
        return "Column"
        
    # Remove or replace problematic characters
    sanitized = re.sub(r'[\[\]\\\/\*\?\:\']', '', name)
    sanitized = sanitized.strip()
    
    # Ensure column name isn't empty after sanitization
    if not sanitized:
        return "Column"
    
    return sanitized

def is_numeric(text: str) -> bool:
    """
    Check if a string represents a number
    
    Args:
        text: String to check
    
    Returns:
        True if the string represents a number, False otherwise
    """
    # Remove common number formatting characters
    cleaned_text = text.replace(',', '').replace(' ', '').strip()
    
    # Check if it's a number (integer or float)
    try:
        float(cleaned_text)
        return True
    except ValueError:
        return False

def analyze_pdf_structure(pdf_path: str) -> Dict[str, Any]:
    """
    Analyze the structure of a PDF to determine the best extraction strategy
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary containing analysis results
    """
    results = {
        "page_count": 0,
        "has_tables": False,
        "has_images": False,
        "has_rtl_text": False,
        "suggested_strategy": "text"
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            results["page_count"] = len(pdf.pages)
            
            # Sample a few pages to determine content type
            pages_to_check = min(3, len(pdf.pages))
            
            for i in range(pages_to_check):
                page = pdf.pages[i]
                
                # Check for tables
                tables = page.extract_tables()
                if tables:
                    results["has_tables"] = True
                
                # Check for images
                if page.images:
                    results["has_images"] = True
                
                # Check for RTL text
                text = page.extract_text()
                if text and is_rtl_text(text):
                    results["has_rtl_text"] = True
            
            # Determine best strategy
            if results["has_tables"]:
                results["suggested_strategy"] = "plumber"
            elif results["has_rtl_text"]:
                results["suggested_strategy"] = "rtl_optimized"
            elif results["has_images"]:
                results["suggested_strategy"] = "ocr"
            else:
                results["suggested_strategy"] = "text"
    
    except Exception as e:
        logger.error(f"Error analyzing PDF structure: {str(e)}")
    
    return results

def process_pdf(session_id: str, output_format: str, start_page: int = 0) -> None:
    """
    Process a PDF file and extract tables
    
    Args:
        session_id: UUID of the conversion session
        output_format: Output format ('csv' or 'xlsx')
        start_page: Page number to start processing from (for resume functionality)
    """
    try:
        # Get status
        status = get_session_status(session_id)
        
        # Get file path
        pdf_path = os.path.join(UPLOAD_FOLDER, f"{session_id}.pdf")
        
        # Open the PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Update status with total pages
        status["total_pages"] = total_pages
        status["status"] = ConversionStatus.ANALYSIS
        save_session_status(session_id, status)
        
        # Analyze PDF structure to determine best strategy
        analysis_results = analyze_pdf_structure(pdf_path)
        logger.info(f"PDF analysis results: {analysis_results}")
        
        # Update status with analysis results
        status["analysis"] = analysis_results
        status["status"] = ConversionStatus.PROCESSING
        save_session_status(session_id, status)
        
        # Initialize result data
        all_tables = []
        structured_table_data = []
        dataframes = []
        
        # Choose processing strategy based on analysis
        extraction_strategy = analysis_results["suggested_strategy"]
        rtl_mode = analysis_results["has_rtl_text"]
        
        # Process each page
        for page_num in range(start_page, total_pages):
            # Check if paused
            status = get_session_status(session_id)
            if status["status"] != ConversionStatus.PROCESSING:
                return
            
            # Get the page
            page = doc[page_num]
            
            # Use the best strategy based on analysis
            if extraction_strategy == "plumber" or extraction_strategy == "rtl_optimized":
                # PDFPlumber is best for tables and RTL content
                plumber_tables = extract_tables_with_pdfplumber(pdf_path, page_num)
                if plumber_tables:
                    logger.info(f"Found {len(plumber_tables)} tables using pdfplumber on page {page_num+1}")
                    dataframes.extend(plumber_tables)
                    # Skip other extraction methods if pdfplumber found tables
                    update_progress(session_id, page_num + 1, total_pages)
                    time.sleep(0.1)
                    continue
            
            # If PDFPlumber didn't find tables or wasn't the chosen strategy, try structured table extraction
            structured_table = extract_structured_table(page)
            
            if structured_table and len(structured_table) > 1:
                # We found a structured table using layout analysis
                logger.info(f"Found structured table on page {page_num+1} with {len(structured_table)} rows")
                
                # Merge multiline entries if needed
                merged_table = merge_multiline_entries(structured_table)
                structured_table_data.extend(merged_table)
            else:
                # Fall back to text-based extraction
                # Extract text from page
                text = extract_text_from_page(page)
                
                # If text is very short or empty, try OCR
                if len(text.strip()) < 50 or extraction_strategy == "ocr":
                    # Check if page has images
                    image_list = page.get_images(full=True)
                    
                    if image_list:
                        for img_index, img_info in enumerate(image_list):
                            xref = img_info[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            # Extract text from image using OCR
                            ocr_text = extract_text_from_image(image_bytes)
                            text += "\n" + ocr_text
                
                # Preprocess text with proper RTL handling
                text = preprocess_text(text)
                
                # Detect tables
                tables = detect_tables_in_text(text)
                all_tables.extend(tables)
            
            # Update progress
            update_progress(session_id, page_num + 1, total_pages)
            
            # Add a small sleep to allow for pause functionality
            time.sleep(0.1)
        
        # Process all detected data
        df = None
        
        # First try to use the dataframes from pdfplumber
        if dataframes:
            # Combine all dataframes
            if len(dataframes) == 1:
                df = dataframes[0]
            else:
                # Find the DataFrame with the most columns and rows as the main one
                main_df = max(dataframes, key=lambda x: x.shape[0] * x.shape[1])
                df = main_df
                
                # Try to append other dataframes if they have compatible structure
                for other_df in dataframes:
                    if other_df is not main_df and other_df.shape[1] == main_df.shape[1]:
                        df = pd.concat([df, other_df], ignore_index=True)
        
        # If no dataframes from pdfplumber, try structured tables
        elif structured_table_data:
            try:
                # If we found structured tables, use them
                # First row as header
                if len(structured_table_data) > 1:
                    header = structured_table_data[0]
                    data_rows = structured_table_data[1:]
                    
                    # Ensure all rows have consistent columns
                    # Find the maximum number of columns across all rows
                    max_cols = max(len(row) for row in structured_table_data)
                    
                    # Only create DataFrame if we have multiple columns
                    if max_cols > 1:
                        # Ensure header has enough columns and is properly formatted
                        if len(header) < max_cols:
                            header = header + [f'Column {i+1}' for i in range(len(header), max_cols)]
                        else:
                            header = header[:max_cols]
                        
                        # Sanitize column names
                        header = [sanitize_column_name(col) for col in header]
                        
                        # Ensure data rows have consistent columns
                        padded_data_rows = []
                        for row in data_rows:
                            if len(row) < max_cols:
                                padded_data_rows.append(row + [''] * (max_cols - len(row)))
                            else:
                                padded_data_rows.append(row[:max_cols])
                        
                        # Create DataFrame with explicit column specification
                        try:
                            # Check that we have reasonable data
                            if padded_data_rows and all(isinstance(row, list) for row in padded_data_rows):
                                # Convert entries with appropriate data types
                                clean_data_rows = []
                                for row in padded_data_rows:
                                    clean_row = []
                                    for cell in row:
                                        if cell is None:
                                            clean_row.append('')
                                        else:
                                            cell_str = str(cell)
                                            if is_numeric(cell_str):
                                                try:
                                                    # Try to convert to float or int
                                                    if '.' in cell_str:
                                                        clean_row.append(float(cell_str.replace(',', '')))
                                                    else:
                                                        clean_row.append(int(cell_str.replace(',', '')))
                                                except ValueError:
                                                    # If conversion fails, keep as string with RTL handling
                                                    if is_rtl_text(cell_str):
                                                        clean_row.append(fix_rtl_text(cell_str))
                                                    else:
                                                        clean_row.append(cell_str)
                                            elif is_rtl_text(cell_str):
                                                clean_row.append(fix_rtl_text(cell_str))
                                            else:
                                                clean_row.append(cell_str)
                                    clean_data_rows.append(clean_row)
                                
                                # Create the DataFrame with proper column specification
                                df = pd.DataFrame(clean_data_rows, columns=header)
                                
                                # Convert numeric columns to appropriate types
                                for col in df.columns:
                                    if df[col].dtype == 'object':  # Only process string columns
                                        # Check if at least 70% of non-empty values are numeric
                                        non_empty = df[col].astype(str).str.strip() != ''
                                        if non_empty.sum() > 0:
                                            numeric_values = df[col][non_empty].apply(lambda x: is_numeric(str(x)))
                                            if numeric_values.sum() / len(numeric_values) >= 0.7:
                                                df[col] = pd.to_numeric(df[col], errors='coerce')
                            else:
                                logger.warning("Invalid data format in structured_table_data")
                                df = pd.DataFrame()
                        except Exception as e:
                            logger.error(f"Error creating DataFrame: {str(e)}")
                            df = pd.DataFrame()
                    else:
                        # Only one column - likely not a proper table
                        logger.warning("Table with only one column detected - may not be a proper table")
                        df = pd.DataFrame()
                else:
                    # Not enough rows for header + data
                    df = pd.DataFrame()
            except Exception as e:
                logger.error(f"Error creating DataFrame from structured table: {str(e)}")
                # Fall back to text-based tables
                df = normalize_table_data(all_tables)
        else:
            # Fall back to text-based tables
            df = normalize_table_data(all_tables)
        
        # If no data found, create an empty DataFrame
        if df is None or df.empty:
            df = pd.DataFrame()
            logger.warning("No table data found in the PDF")
        
        # Clean the DataFrame
        # Remove rows that are entirely empty
        df = df.dropna(how='all')
        
        # Handle RTL text in column names
        if rtl_mode:
            new_columns = []
            for col in df.columns:
                if is_rtl_text(str(col)):
                    new_columns.append(fix_rtl_text(str(col)))
                else:
                    new_columns.append(str(col))
            df.columns = new_columns
        
        # Generate preview
        preview_data = df.head(10).to_dict(orient='records') if not df.empty else []
        columns = df.columns.tolist()
        
        # Save output file
        output_filename = f"{session_id}.{output_format}"
        output_path = os.path.join(TEMP_FOLDER, output_filename)
        
        if output_format == 'csv':
            # Enhanced CSV output with better handling of data types and encoding
            
            # 1. Determine the best CSV dialect based on data
            csv_dialect = 'excel'  # Default dialect
            csv_quoting = 1  # Default csv.QUOTE_ALL
            
            # Use tab delimiter if content might contain commas
            if df.astype(str).apply(lambda x: x.str.contains(',', na=False)).any().any():
                csv_delimiter = '\t'
            else:
                csv_delimiter = ','
            
            # 2. Ensure numbers remain as numbers
            # Create a copy to avoid modifying the original DataFrame during processing
            df_csv = df.copy()
            
            # 3. Handle complex cell contents (e.g., cells with newlines, quotes)
            for col in df_csv.columns:
                # If it's a string column and contains newlines, quotes, etc., handle specially
                if df_csv[col].dtype == 'object':
                    # Replace newlines with spaces in string columns
                    df_csv[col] = df_csv[col].astype(str).apply(
                        lambda x: x.replace('\n', ' ').replace('\r', ' ') if pd.notna(x) else x
                    )
            
            # 4. Write the CSV with enhanced settings
            try:
                df_csv.to_csv(
                    output_path, 
                    index=False, 
                    sep=csv_delimiter,
                    encoding='utf-8-sig',  # UTF-8 with BOM for Excel
                    quoting=csv_quoting,
                    quotechar='"',
                    date_format='%Y-%m-%d',  # ISO format for dates
                    doublequote=True,        # Handle quotes properly
                    line_terminator='\r\n'   # Windows line endings for better Excel compatibility
                )
                
                # Verify the CSV file was saved correctly
                if not os.path.exists(output_path) or os.path.getsize(output_path) < 1:
                    logger.error(f"CSV file not properly saved: {output_path}")
                    # Fallback to basic CSV export if enhanced export fails
                    df.to_csv(output_path, index=False, encoding='utf-8-sig')
                
            except Exception as e:
                logger.error(f"Error saving enhanced CSV: {str(e)}")
                # Fallback to basic CSV export
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                
        else:  # xlsx
            # For Excel, use openpyxl engine with additional formatting
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
                
                # Access workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Data']
                
                # Apply formatting to make it more readable
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    # Add some padding
                    adjusted_width = (max_length + 2) * 1.2
                    worksheet.column_dimensions[column_letter].width = min(adjusted_width, 50)
                
                # Add borders and formatting to header
                from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
                
                header_font = Font(bold=True, size=12)
                header_fill = PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")
                border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
                
                # Apply styles to header row
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.border = border
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Apply borders to all cells with data
                data_rows = list(worksheet.rows)[1:]  # Skip header
                for row in data_rows:
                    for cell in row:
                        cell.border = Border(
                            left=Side(style='thin'),
                            right=Side(style='thin'),
                            top=Side(style='thin'),
                            bottom=Side(style='thin')
                        )
                        # Center numeric values
                        if isinstance(cell.value, (int, float)):
                            cell.alignment = Alignment(horizontal='right')
        
        # Update status
        status = get_session_status(session_id)
        status["status"] = ConversionStatus.COMPLETED
        status["progress"] = 100
        status["output_path"] = output_path
        status["preview"] = preview_data
        status["columns"] = columns
        save_session_status(session_id, status)
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        
        # Update status with error
        status = get_session_status(session_id)
        status["status"] = ConversionStatus.ERROR
        status["error"] = str(e)
        save_session_status(session_id, status)

def reset_preview(session_id: str) -> None:
    """Clear the preview data for a session"""
    try:
        status = get_session_status(session_id)
        status["preview"] = []
        save_session_status(session_id, status)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error resetting preview: {str(e)}")
        return {"success": False, "error": str(e)}

def start_conversion_task(session_id: str, output_format: str) -> None:
    """Start the conversion process"""
    # Process the PDF from the beginning
    process_pdf(session_id, output_format, start_page=0)

def resume_conversion_task(session_id: str, output_format: str) -> None:
    """Resume the conversion process from the last page"""
    # Get current page from status
    status = get_session_status(session_id)
    current_page = status.get("current_page", 0)
    
    # Process the PDF from the current page
    process_pdf(session_id, output_format, start_page=current_page) 