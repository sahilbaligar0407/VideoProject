# ClipGenius

A web application that automatically generates highlight clips from videos with AI-powered transcription and caption generation.

## Features

- **Video Input**: Support for YouTube URLs and direct file uploads
- **AI Transcription**: Uses OpenAI Whisper API for accurate speech-to-text
- **Highlight Detection**: Automatically identifies key moments using audio analysis and transcript analysis
- **Auto-Generated Clips**: Creates 2-3 highlight clips (20-40 seconds each) using ffmpeg
- **Burned-in Captions**: Automatically adds captions to each clip

## Tech Stack

- **Frontend**: Next.js with Tailwind CSS
- **Backend**: Python FastAPI
- **AI Services**: OpenAI Whisper API for transcription
- **Video Processing**: FFmpeg for video clipping and caption burning
- **Architecture**: Designed for easy integration of user authentication and payment processing

## Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- FFmpeg installed locally
- OpenAI API key

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. Run the backend:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Usage

1. Choose input method: YouTube URL or file upload
2. Wait for processing (transcription, highlight detection, clip generation)
3. Download generated highlight clips with burned-in captions

## Project Structure

```
ClipGenius/
├── backend/           # FastAPI backend
│   ├── app/          # Application logic
│   ├── requirements.txt
│   └── main.py
├── frontend/          # Next.js frontend
│   ├── components/   # React components
│   ├── pages/        # Next.js pages
│   └── package.json
└── README.md
```

## Future Enhancements

- User authentication and user management
- Payment processing for premium features
- Cloud storage integration
- Advanced highlight detection algorithms
- Social sharing capabilities
