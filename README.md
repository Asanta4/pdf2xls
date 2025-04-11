# PDF to CSV/Excel Converter

A modern, bilingual web application that converts PDF files to structured CSV or Excel files with support for both English and Hebrew.

## Features

- **Bilingual Interface**: Full support for both English and Hebrew with proper RTL handling
- **Simple Conversion Process**: Upload PDF → Select Format → Convert → Download
- **Format Options**: Choose between CSV and Excel output formats
- **Progress Tracking**: Real-time conversion progress with status indicators
- **Data Preview**: View extracted data before downloading
- **Responsive Design**: Works on both desktop and mobile devices

## Installation

### Prerequisites

- Node.js 14+ for frontend
- Python 3.8+ for backend
- Tesseract OCR (for image-based PDFs)

### Setup and Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd pdf-to-csv
```

2. **Quick Start (using the provided script)**

```bash
chmod +x run.sh
./run.sh
```

This script will:
- Create a Python virtual environment
- Install all backend dependencies
- Start the backend server
- Install frontend dependencies
- Start the frontend development server

3. **Manual Setup**

Backend:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd client
npm install
npm start
```

## Usage

1. Select your language preference (English/Hebrew)
2. Drag & drop or click to upload your PDF file
3. Choose your preferred output format (CSV or Excel)
4. Click "Start Conversion"
5. Monitor the conversion progress
6. Preview the extracted data
7. Download the converted file

## Deployment

This application consists of two parts that need to be deployed separately: a React frontend and a FastAPI backend.

### Backend Deployment

#### Option 1: Deploy to Render

1. Sign up for a [Render](https://render.com/) account
2. Create a new Web Service
3. Connect your GitHub repository
4. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables:
     - Set `CORS_ORIGINS` to your frontend URL
     - Set `PORT` to the port provided by Render (usually auto-configured)

#### Option 2: Deploy to Railway

1. Sign up for a [Railway](https://railway.app/) account
2. Create a new project and select "Deploy from GitHub repo"
3. Configure the project:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables in the Railway dashboard

#### Option 3: Deploy to Heroku

1. Sign up for a [Heroku](https://heroku.com/) account
2. Install the Heroku CLI: `npm install -g heroku`
3. Create a `Procfile` in your project root with:
   ```
   web: uvicorn server.main:app --host=0.0.0.0 --port=$PORT
   ```
4. Deploy with these commands:
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```
5. Set environment variables in the Heroku dashboard

### Frontend Deployment

#### Option 1: Deploy to Netlify

1. Sign up for a [Netlify](https://netlify.com/) account
2. In your project, create a `.env.production` file in the `client` directory with:
   ```
   REACT_APP_API_URL=https://your-backend-url.com
   ```
3. Build the frontend:
   ```bash
   cd client
   npm install
   npm run build
   ```
4. Deploy using Netlify CLI or drag and drop the `build` folder to Netlify dashboard

#### Option 2: Deploy to Vercel

1. Sign up for a [Vercel](https://vercel.com/) account
2. Install the Vercel CLI: `npm install -g vercel`
3. Create a `vercel.json` file in the `client` directory:
   ```json
   {
     "env": {
       "REACT_APP_API_URL": "https://your-backend-url.com"
     },
     "buildCommand": "npm run build",
     "outputDirectory": "build",
     "rewrites": [
       { "source": "/(.*)", "destination": "/index.html" }
     ]
   }
   ```
4. Deploy from the `client` directory:
   ```bash
   cd client
   vercel
   ```

### Important Deployment Notes

1. **CORS Configuration**: Ensure your backend allows requests from your frontend domain by setting the appropriate CORS headers. Update your `.env` file with:
   ```
   CORS_ORIGINS=https://your-frontend-domain.com
   ```

2. **File Storage**: For production, consider using cloud storage services like AWS S3 or Google Cloud Storage for temporary files instead of local storage.

3. **Environment Variables**: Update all environment variables to match your production setup.

4. **API Base URL**: Make sure your frontend is configured to point to your deployed backend API URL.

5. **SSL**: Ensure both frontend and backend use HTTPS for secure communication.

## Project Structure

```
pdf-to-csv/
├── client/                 # React frontend
│   ├── public/             # Static assets
│   └── src/
│       ├── components/     # React components
│       ├── services/       # API client services
│       ├── translations/   # i18n translation files
│       ├── App.js          # Main application component
│       └── i18n.js         # Internationalization setup
├── server/                 # FastAPI backend
│   ├── endpoints/          # API endpoints
│   ├── utils/              # Utility functions
│   └── main.py             # Server entry point
├── uploads/                # Uploaded PDF files
├── venv/                   # Python virtual environment
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── run.sh                  # Setup and run script
```

## Technologies Used

### Frontend
- React
- Material UI
- i18next (internationalization)
- Axios (HTTP client)

### Backend
- FastAPI
- PyMuPDF (PDF processing)
- Pandas (data manipulation)
- Tesseract OCR
- OpenPyXL (Excel generation)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Material UI for the component library
- PyMuPDF for PDF processing
- Tesseract OCR for text extraction from images 