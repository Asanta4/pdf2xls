# Deployment Guide for PDF to CSV/Excel Converter

This guide provides detailed steps to deploy your PDF to CSV/Excel Converter application to the web.

## Prerequisites

- GitHub account (for code hosting)
- Accounts on your chosen hosting platforms (e.g., Render/Railway for backend, Netlify/Vercel for frontend)

## 1. Prepare Your Code for Deployment

### Backend Preparation

1. Update your `.env` file to use environment variables suitable for production:

```
# Server configuration
PORT=${PORT}  # Will be provided by the hosting platform
HOST=0.0.0.0
DEBUG=False  # Set to False in production

# Upload configuration
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=pdf

# File storage
UPLOAD_FOLDER=uploads
TEMP_FOLDER=server/temp_files

# OCR configuration
TESSERACT_CMD=tesseract
TESSERACT_LANGS=eng+heb

# Security
CORS_ORIGINS=${FRONTEND_URL}  # Will be set during deployment
```

2. Update `server/main.py` to correctly handle CORS in production:

```python
# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use the origins from environment variables
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. Create a `Procfile` for Heroku deployment (if using Heroku):

```
web: uvicorn server.main:app --host=0.0.0.0 --port=$PORT
```

### Frontend Preparation

1. Create an `.env.production` file in the `client` directory:

```
REACT_APP_API_URL=https://your-backend-url.com
```

2. Update API base URL in `client/src/services/api.js` to use environment variables:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8003';
```

## 2. Deploy the Backend

### Option A: Deploy to Render

1. Push your code to GitHub
2. Log in to [Render](https://render.com/)
3. Click "New" and select "Web Service"
4. Connect your GitHub repository
5. Configure the service:
   - Name: `pdf-to-csv-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables:
   - `CORS_ORIGINS` = your frontend URL (once deployed)
   - `DEBUG` = False
   - `TESSERACT_CMD` = tesseract
   - `TESSERACT_LANGS` = eng+heb
7. Click "Create Web Service"

### Option B: Deploy to Railway

1. Push your code to GitHub
2. Log in to [Railway](https://railway.app/)
3. Click "New Project" and select "Deploy from GitHub repo"
4. Find and select your repository
5. Click "Deploy"
6. Add environment variables in the Railway dashboard (same as Render)
7. Once deployed, note the URL provided by Railway

## 3. Deploy the Frontend

### Option A: Deploy to Netlify

1. In your client directory, build the frontend with the backend URL:

```bash
cd client
REACT_APP_API_URL=https://your-backend-url npm run build
```

2. Log in to [Netlify](https://www.netlify.com/)
3. Click "New site from Git"
4. Choose GitHub and select your repository
5. Configure build settings:
   - Base directory: `client`
   - Build command: `npm run build`
   - Publish directory: `client/build`
6. Add environment variables:
   - `REACT_APP_API_URL` = your backend URL
7. Click "Deploy site"

### Option B: Deploy to Vercel

1. Log in to [Vercel](https://vercel.com/)
2. Click "Import Project" and select your repository
3. Configure project:
   - Framework Preset: `Create React App`
   - Root Directory: `client`
4. Add environment variables:
   - `REACT_APP_API_URL` = your backend URL
5. Click "Deploy"

## 4. Connect Frontend and Backend

1. After deploying the frontend, get the frontend URL
2. Update the backend's CORS settings with the frontend URL:
   - Go to your backend hosting platform
   - Add/update the environment variable `CORS_ORIGINS` with your frontend URL
3. Redeploy the backend if needed

## 5. Verify the Deployment

1. Visit your frontend URL
2. Test uploading a PDF and converting it
3. Verify that all features are working correctly

## 6. Additional Production Considerations

### File Storage

For production environments, consider using cloud storage instead of local storage:

1. Set up an AWS S3 bucket or similar cloud storage
2. Update your backend code to use the cloud storage
3. Add the relevant environment variables for cloud storage credentials

### Security

1. Ensure all communications use HTTPS
2. Set up proper file validation and sanitization
3. Implement rate limiting if needed

### Monitoring

1. Set up logging
2. Configure monitoring for your services
3. Set up alerts for critical errors

## Troubleshooting

### CORS Issues

If you encounter CORS errors:

1. Verify that the backend's `CORS_ORIGINS` includes the exact frontend URL (including https://)
2. Check browser console for specific CORS error messages
3. Temporarily enable CORS debugging by adding logging to your backend

### File Upload Issues

If file uploads fail:

1. Check the maximum file size settings on both frontend and backend
2. Verify that the upload directory is writable
3. Check server logs for specific error messages

### Connection Issues

If the frontend cannot connect to the backend:

1. Verify that the `REACT_APP_API_URL` is correct
2. Check if the backend is running and accessible
3. Test the backend endpoints directly using a tool like Postman 