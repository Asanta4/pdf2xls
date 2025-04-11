# PDF to Excel/CSV Converter Documentation

## System Architecture

The PDF to Excel/CSV Converter is a web application that allows users to upload PDF files and convert them to structured Excel or CSV files. The application consists of two main components:

1. **Frontend**: A React-based web interface that provides the user experience
2. **Backend**: A FastAPI server that handles file processing and conversion

### Architecture Diagram

```
┌─────────────┐      ┌───────────────┐      ┌────────────────┐
│   Browser   │ HTTP │  React Client  │ HTTP │  FastAPI Server │
│   (User)    │─────▶│   (Frontend)   │─────▶│    (Backend)    │
└─────────────┘      └───────────────┘      └────────────────┘
                                                     │
                                                     ▼
                                            ┌────────────────┐
                                            │  PDF Processing │
                                            │      Logic      │
                                            └────────────────┘
                                                     │
                                                     ▼
                                            ┌────────────────┐
                                            │ Table Extraction│
                                            │    & Parsing    │
                                            └────────────────┘
                                                     │
                                                     ▼
                                            ┌────────────────┐
                                            │  Excel/CSV     │
                                            │  Generation    │
                                            └────────────────┘
```

## Frontend Component

### Technologies

- **React**: Library for building user interfaces
- **Material UI**: Component library for consistent design
- **i18next**: Internationalization framework for Hebrew and English support
- **Axios**: HTTP client for API communication
- **React Dropzone**: File upload component

### Key Features

1. **Bilingual Support**: Hebrew (RTL) and English (LTR) interfaces with proper RTL support
2. **Drag and Drop**: Easy file uploading interface
3. **Conversion Controls**: Start, pause, resume, and cancel functionality
4. **Progress Tracking**: Visual progress indication with actual percentage display
5. **Preview**: Data preview before download
6. **Responsive Design**: Works on mobile and desktop
7. **Format Selection**: Choose between CSV and Excel output formats
8. **Single Download Button**: Download only the selected format when conversion completes

### Component Architecture

- **App.js**: Main application component that manages global state
- **Components/**:
  - **FileUploader.js**: Handles file selection and upload
  - **ConversionControls.js**: Manages conversion actions
  - **ProgressTracker.js**: Displays conversion progress
  - **PreviewTable.js**: Shows extracted data preview

## Backend Component

### Technologies

- **FastAPI**: Modern, fast web framework for building APIs
- **PyMuPDF**: PDF processing library
- **Tesseract OCR**: Text extraction from images
- **pandas**: Data manipulation and analysis
- **python-bidi**: Bidirectional text support for Hebrew
- **openpyxl**: Excel file generation

### Key Features

1. **PDF Processing**: Extract text from PDF files
2. **OCR Support**: Handle image-based PDFs
3. **Table Detection**: Identify tabular structures in text
4. **Data Extraction**: Convert unstructured data to structured format
5. **Session Management**: Support pause/resume operations
6. **Multiple Export Formats**: Generate both Excel and CSV outputs with improved formatting

### Module Architecture

- **main.py**: Application entry point and router configuration
- **endpoints/**:
  - **conversion.py**: API endpoints for file conversion operations
  - **status.py**: Endpoints for tracking progress and status
- **utils/**:
  - **converter.py**: Core PDF processing and conversion logic

## Communication Flow

### API Endpoints

| Method | Endpoint | Description | Parameters | Response |
|--------|----------|-------------|------------|----------|
| POST | /upload | Upload PDF file | `file`: PDF file | `session_id`, `status` |
| POST | /start/{session_id} | Start conversion | `session_id`: UUID<br>`output_format`: 'csv' or 'xlsx' | `session_id`, `status` |
| POST | /pause/{session_id} | Pause conversion | `session_id`: UUID | `session_id`, `status` |
| POST | /resume/{session_id} | Resume conversion | `session_id`: UUID | `session_id`, `status` |
| POST | /cancel/{session_id} | Cancel conversion | `session_id`: UUID | `session_id`, `status` |
| GET | /progress/{session_id} | Get progress | `session_id`: UUID | Full status object |
| GET | /preview/{session_id} | Get data preview | `session_id`: UUID | Preview data and columns |
| GET | /download/{session_id} | Download result | `session_id`: UUID | File stream |

### Authentication

The system does not require authentication for basic usage, making it simple for users to convert files without creating accounts.

### Session State

Session state is maintained through JSON files stored in the server's temporary directory. Each session has a unique UUID and includes:

- Original filename
- Conversion status
- Progress percentage
- Current and total pages
- Output format and path
- Preview data

## Data Processing Flow

### 1. Upload

1. User uploads a PDF file
2. Server validates the file (type, size)
3. A unique session ID is generated
4. The file is stored in the uploads directory

### 2. Conversion

1. User selects output format and starts conversion
2. Backend processes the PDF file page by page
3. For each page:
   - Extract text (using PyMuPDF)
   - If text extraction fails, use OCR (using Tesseract)
   - Preprocess and normalize text
   - Detect tables and tabular structures

### 3. Table Extraction

1. Identify potential table structures in text
2. Determine delimiter patterns
3. Extract rows and columns
4. Normalize data types (convert numeric strings to numbers)
5. Generate structured data (pandas DataFrame)

### 4. File Generation

1. Convert DataFrame to Excel or CSV with proper formatting
2. Store the output file
3. Provide download link for the selected format to the user

## Installation and Deployment

### Local Development

1. **Prerequisites**:
   - Python 3.8+
   - Node.js 14+
   - Tesseract OCR (for image-based PDFs)

2. **Backend Setup**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run server
   uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Frontend Setup**:
   ```bash
   cd client
   npm install
   npm start
   ```

4. **Combined Setup**:
   ```bash
   # Run both frontend and backend with one command
   ./run.sh
   ```

### Production Deployment

1. **Backend Deployment**:
   - Deploy to Render, Railway, or other Python hosting service
   - Configure environment variables
   - Set up proper CORS headers

2. **Frontend Deployment**:
   - Build the React app: `npm run build`
   - Deploy to Vercel, Netlify, or other static hosting
   - Configure the API base URL to point to your backend

## Performance Considerations

- **File Size Limits**: The default maximum file size is 10MB
- **OCR Processing**: OCR for image-based PDFs is more resource-intensive
- **Concurrent Users**: The backend can handle multiple users simultaneously
- **Temporary Storage**: Files are stored temporarily and can be purged after a certain period

## Security Considerations

- **File Validation**: All uploaded files are validated for type and size
- **Temporary Links**: Download links are based on UUIDs, not predictable paths
- **No Personal Data**: The system does not collect or store personal user data
- **File Cleanup**: Temporary files can be scheduled for deletion

## Error Handling

The application implements comprehensive error handling:

- **Client-side Validation**: File type and size validation
- **Server-side Validation**: Additional security checks
- **Process Monitoring**: Track and report conversion errors
- **User Feedback**: Clear error messages for users

## Internationalization

The application supports both Hebrew and English languages:

- **Default Language**: Hebrew (RTL)
- **Language Toggle**: Users can switch between languages
- **Translation Files**: JS-based translation files (en.js and he.js)
- **RTL Support**: Proper handling of right-to-left text and UI elements

## UI Improvements

Recent UI enhancements include:

1. **Simplified Interface**: Removed Features section and Footer for a cleaner UI
2. **Enhanced Progress Display**: Shows actual numerical percentage values
3. **Format-Specific Download**: Only the selected format (CSV or Excel) is available for download
4. **Improved RTL Support**: Better right-to-left layout for Hebrew language
5. **Streamlined Downloads**: Single download button instead of multiple options

## Troubleshooting

### Common Issues

1. **OCR Not Working**:
   - Ensure Tesseract OCR is properly installed
   - Check language packages for Hebrew support

2. **PDF Not Converting Correctly**:
   - Check if PDF is encrypted or password-protected
   - Verify PDF is text-based or has good quality images for OCR

3. **Frontend Connection Issues**:
   - Verify CORS settings in backend
   - Check API base URL configuration

4. **Icon Imports**:
   - Ensure all MUI icons are properly imported
   - Verify icon names match those available in @mui/icons-material 