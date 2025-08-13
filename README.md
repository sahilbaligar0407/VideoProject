# ClipGenius

A web application that automatically generates highlight clips from videos with AI-powered transcription and caption generation.

## Features

- **Video Input**: Support for YouTube URLs and direct file uploads
- **AI Transcription**: Uses OpenAI Whisper API for accurate speech-to-text
- **Highlight Detection**: Automatically identifies key moments using audio analysis, transcript analysis, and **Viral Similarity Engine**
- **Viral Similarity Engine**: AI-powered content scoring using OpenAI embeddings and cosine similarity for viral content detection
- **Auto-Generated Clips**: Creates 2-3 highlight clips (20-40 seconds each) using ffmpeg
- **Burned-in Captions**: Automatically adds captions to each clip

## Tech Stack

- **Frontend**: Next.js with Tailwind CSS
- **Backend**: Python FastAPI
- **AI Services**: OpenAI Whisper API for transcription, OpenAI Embeddings API for viral similarity
- **Viral Engine**: OpenAI text-embedding-3-small for semantic analysis, cosine similarity scoring
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
   EMBEDDING_MODEL=text-embedding-3-small
   VIRAL_WINDOW_SEC=16
   VIRAL_WINDOW_HOP=8
   VIRAL_MIN_SCORE=0.30
   VIRAL_TOP_K=12
   VIRAL_MAX_TERMS=256
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
│   │   ├── viral/    # Viral Similarity Engine
│   │   │   ├── embeddings.py      # OpenAI embeddings with caching
│   │   │   ├── viral_terms.py     # Viral terms management
│   │   │   ├── viral_vector.py    # Viral vector computation
│   │   │   ├── similarity.py      # Cosine similarity and windowing
│   │   │   └── persist.py         # SQLite persistence
│   │   ├── routers/  # API endpoints
│   │   ├── services/ # Business logic
│   │   └── models.py # Data models
│   ├── requirements.txt
│   └── main.py
├── frontend/          # Next.js frontend
│   ├── components/   # React components
│   ├── pages/        # Next.js pages
│   └── package.json
└── README.md
```

## Viral Similarity Engine

The Viral Similarity Engine is an AI-powered system that automatically detects viral content potential in videos using semantic analysis.

### How It Works

1. **Viral Vocabulary**: Maintains a curated list of viral terms/phrases (e.g., "wow", "insane", "no way", "watch till the end")
2. **Semantic Embeddings**: Converts viral terms and video captions to high-dimensional vectors using OpenAI's text-embedding-3-small
3. **Similarity Scoring**: Uses cosine similarity to score how "viral" each caption window is
4. **Highlight Generation**: Integrates viral scores into the highlight detection pipeline for better content selection

### API Endpoints

- `POST /api/v1/viral/terms` - Add/update viral terms
- `GET /api/v1/viral/terms` - List all viral terms
- `POST /api/v1/viral/rebuild` - Rebuild viral vector from terms
- `POST /api/v1/viral/videos/{video_id}/score-viral` - Score video captions
- `GET /api/v1/viral/videos/{video_id}/viral-top` - Get top viral scores
- `GET /api/v1/viral/stats` - Database statistics
- `POST /api/v1/viral/test` - Test viral engine

### Configuration

Environment variables for fine-tuning:
- `EMBEDDING_MODEL`: OpenAI embedding model (default: text-embedding-3-small)
- `VIRAL_WINDOW_SEC`: Caption window length in seconds (default: 16)
- `VIRAL_WINDOW_HOP`: Window stride in seconds (default: 8)
- `VIRAL_MIN_SCORE`: Minimum similarity score threshold (default: 0.30)
- `VIRAL_TOP_K`: Maximum number of viral segments to keep (default: 12)
- `VIRAL_MAX_TERMS`: Maximum number of viral terms (default: 256)

### Usage Example

```bash
# Seed viral terms
curl -X POST "http://localhost:8000/api/v1/viral/terms" \
  -H "Content-Type: application/json" \
  -d '{"term": "epic fail", "weight": 1.3}'

# Rebuild viral vector
curl -X POST "http://localhost:8000/api/v1/viral/rebuild"

# Score a video
curl -X POST "http://localhost:8000/api/v1/viral/videos/123/score-viral" \
  -H "Content-Type: application/json" \
  -d '{"captions": [{"start": 0, "end": 10, "text": "wow that was insane!"}], "video_duration": 300}'
```

## Future Enhancements

- User authentication and user management
- Payment processing for premium features
- Cloud storage integration
- Advanced highlight detection algorithms
- Social sharing capabilities
- Viral trend analysis and reporting
