# ClipGenius Setup Guide

This guide will help you set up and run the ClipGenius application on your local machine.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 16+** - [Download Node.js](https://nodejs.org/)
- **FFmpeg** - [Download FFmpeg](https://ffmpeg.org/download.html)
- **Git** - [Download Git](https://git-scm.com/downloads)

### FFmpeg Installation

#### Windows:
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract the downloaded archive
3. Add the `bin` folder to your system PATH environment variable
4. Verify installation by running `ffmpeg -version` in Command Prompt

#### macOS:
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

## Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd ClipGenius
```

### 2. Set Up the Backend

#### Navigate to the backend directory:
```bash
cd backend
```

#### Create a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Install Python dependencies:
```bash
pip install -r requirements.txt
```

#### Set up environment variables:
1. Copy the example environment file:
   ```bash
   # Windows
   copy env.example .env
   
   # macOS/Linux
   cp env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

#### Start the backend server:
```bash
# Option 1: Use the run script
python run.py

# Option 2: Use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

### 3. Set Up the Frontend

#### Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

#### Install Node.js dependencies:
```bash
npm install
```

#### Start the frontend development server:
```bash
npm run dev
```

The frontend will be available at: http://localhost:3000

## Project Structure

```
ClipGenius/
├── backend/                    # Python FastAPI backend
│   ├── app/                   # Application code
│   │   ├── config.py         # Configuration settings
│   │   ├── models.py         # Pydantic data models
│   │   ├── routers/          # API route handlers
│   │   │   └── video_processing.py
│   │   └── services/         # Business logic
│   │       └── video_processor.py
│   ├── requirements.txt       # Python dependencies
│   ├── main.py               # FastAPI application entry point
│   ├── run.py                # Server startup script
│   └── env.example           # Environment variables template
├── frontend/                  # Next.js frontend
│   ├── components/           # React components
│   │   ├── VideoInputForm.tsx
│   │   ├── ProcessingStatus.tsx
│   │   └── GeneratedClips.tsx
│   ├── pages/                # Next.js pages
│   │   └── index.tsx
│   ├── styles/               # CSS and Tailwind styles
│   │   └── globals.css
│   ├── types/                # TypeScript type definitions
│   │   └── index.ts
│   ├── package.json          # Node.js dependencies
│   ├── tailwind.config.js    # Tailwind CSS configuration
│   ├── next.config.js        # Next.js configuration
│   └── run.bat               # Windows startup script
├── README.md                  # Project overview
└── SETUP.md                  # This setup guide
```

## Configuration

### Backend Configuration

The backend configuration is managed in `backend/app/config.py`. Key settings include:

- **File size limits**: Maximum 500MB per video
- **Supported formats**: MP4, AVI, MOV, MKV, WMV, FLV
- **Clip settings**: 20-40 seconds per clip, 2-3 clips per video
- **OpenAI Whisper**: Uses the "whisper-1" model for transcription

### Frontend Configuration

The frontend is configured in `frontend/next.config.js` with:

- API proxy to backend (localhost:8000)
- Tailwind CSS for styling
- TypeScript support

## Usage

### 1. Start Both Services

Make sure both backend and frontend are running:

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000

### 2. Process a Video

1. Open http://localhost:3000 in your browser
2. Choose input method:
   - **YouTube URL**: Paste a YouTube video URL
   - **File Upload**: Drag & drop or browse for a video file
3. Click "Process Video"
4. Monitor progress in real-time
5. Download generated highlight clips

### 3. API Endpoints

- `POST /api/v1/process-video` - Start video processing
- `GET /api/v1/status/{request_id}` - Get processing status
- `GET /api/v1/download/{clip_id}` - Download generated clip

## Troubleshooting

### Common Issues

#### FFmpeg not found
- Ensure FFmpeg is installed and added to PATH
- Test with `ffmpeg -version` in terminal

#### OpenAI API errors
- Verify your API key is correct in `.env`
- Check API quota and billing status
- Ensure the API key has access to Whisper models

#### Port conflicts
- Backend: Change port in `run.py` or `main.py`
- Frontend: Change port in `package.json` scripts

#### File upload errors
- Check file size (max 500MB)
- Verify file format is supported
- Ensure backend has write permissions to upload/output directories

### Debug Mode

#### Backend debugging:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run.py
```

#### Frontend debugging:
```bash
# Enable Next.js debug mode
DEBUG=* npm run dev
```

## Development

### Adding New Features

1. **Backend**: Add new routes in `app/routers/`
2. **Frontend**: Create new components in `components/`
3. **Models**: Update data models in `app/models.py`
4. **Services**: Add business logic in `app/services/`

### Testing

#### Backend tests:
```bash
cd backend
python -m pytest
```

#### Frontend tests:
```bash
cd frontend
npm test
```

## Production Deployment

### Backend Deployment
- Use Gunicorn or uWSGI with FastAPI
- Set up reverse proxy (Nginx/Apache)
- Configure environment variables
- Set up logging and monitoring

### Frontend Deployment
- Build production version: `npm run build`
- Deploy to Vercel, Netlify, or static hosting
- Configure API endpoint URLs
- Set up CDN for static assets

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the API documentation at http://localhost:8000/docs
3. Check console logs in browser and terminal
4. Verify all prerequisites are installed correctly

## Next Steps

After successful setup, consider:

- Adding user authentication
- Implementing payment processing
- Setting up cloud storage
- Adding more video processing options
- Implementing advanced highlight detection algorithms
