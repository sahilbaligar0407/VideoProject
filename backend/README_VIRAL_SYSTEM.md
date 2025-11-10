# Viral Clip Generation System

This repository has been refined to focus on **viral clip generation** from long-form videos, with advanced ranking, face tracking, and subtitle export capabilities.

## 🎯 Core Responsibilities

### ✅ What This Repo Does:
1. **Generate viral clips** from long-form video (based on virality scoring logic)
2. **Generate full transcript** of the video using OpenAI Whisper
3. **Apply face tracking** to keep active speakers centered in vertical clips
4. **Export subtitle files** in `.ass`, `.srt`, and `.vtt` formats
5. **Rank clips** on a 0-5 scale based on viral potential

### ❌ What This Repo NO LONGER Does:
- Caption rendering/burning into video files
- Caption styling and formatting
- Caption positioning and layout

*Note: Caption rendering is now handled by a separate, dedicated captions repository.*

## 🏆 New Clip Ranking System

### Rating Scale (0-5)
- **4.5-5.0**: Exceptional viral potential
- **4.0-4.4**: High viral potential  
- **3.5-3.9**: Good viral potential
- **3.0-3.4**: Moderate viral potential
- **2.0-2.9**: Below average
- **1.0-1.9**: Poor viral potential
- **0.0-0.9**: Very poor viral potential

### Ranking Factors
1. **Viral Similarity** (25% weight) - Content matching viral patterns
2. **Content Engagement** (20% weight) - Questions, emotions, reactions
3. **Audio Analysis** (15% weight) - Energy, rhythm, dramatic pauses
4. **Story Structure** (15% weight) - Opening hooks, climax, conclusions
5. **AI Analysis** (25% weight) - ChatGPT-powered content analysis

## 👤 Face Tracking & Speaker Centering

### Features
- **Automatic face detection** using OpenCV and DNN models
- **Speaker tracking** throughout video segments
- **Dynamic cropping** to keep speakers centered in vertical frames
- **Smooth tracking** with configurable smoothing factors

### Configuration
```python
# In settings.py
face_detection_enabled: bool = True
face_detection_confidence: float = 0.7
auto_crop_enabled: bool = True
face_tracking_smoothing: float = 0.8
```

## 📝 Subtitle Export

### Supported Formats
- **WebVTT** (`.vtt`) - Web-compatible captions
- **ASS** (`.ass`) - Advanced SubStation Alpha with styling
- **SRT** (`.srt`) - SubRip text format
- **JSON** (`.json`) - Metadata with timing and text

### Features
- **Automatic timing** based on transcript segments
- **Lead-in adjustment** for Whisper timing accuracy
- **Minimum duration** enforcement for readability
- **Clean text formatting** with proper line breaks

## 🚀 Usage

### Basic Viral Clip Generation
```python
from app.services.video_processor import VideoProcessor

processor = VideoProcessor()
clips = await processor.process_video(
    video_path="your_video.mp4",
    user_topics=["podcast", "interview", "discussion"],
    vertical=True
)
```

### Get Clip Rankings
```python
# Each clip now includes ranking information
for clip in clips:
    print(f"Viral Score: {clip.ranking.viral_score:.1f}/5.0")
    print(f"Engagement: {clip.ranking.engagement_potential:.2f}")
    print(f"Shareability: {clip.ranking.shareability:.2f}")
    print(f"Trending: {clip.ranking.trending_potential:.2f}")
```

### API Endpoints
- `POST /process-video` - Generate viral clips
- `GET /status/{request_id}` - Check processing status
- `GET /clips/{request_id}/rankings` - Get detailed rankings

## 🧪 Testing

### Run Test Script
```bash
cd backend
python test_viral_system.py
```

### Test Requirements
- Test video file named `test_video.mp4`
- OpenAI API key configured
- FFmpeg installed and accessible

## ⚙️ Configuration

### Key Settings
```python
# Number of clips to generate
num_clips: int = 5  # Increased from 3 to 5

# Clip duration constraints
min_clip_duration: float = 20.0
target_clip_duration: float = 30.0
max_clip_duration: float = 40.0

# Ranking weights
ranking_weights: dict = {
    "viral_similarity": 0.25,
    "content_engagement": 0.20,
    "audio_analysis": 0.15,
    "story_structure": 0.15,
    "ai_analysis": 0.25
}
```

## 🔧 Dependencies

### Required Packages
- `opencv-python` - Face detection and tracking
- `numpy` - Numerical computations
- `librosa` - Audio analysis
- `openai` - Whisper transcription and ChatGPT analysis
- `ffmpeg-python` - Video processing

### Optional Dependencies
- DNN face detection models (for improved accuracy)
- OpenCV face cascade files (fallback detection)

## 📊 Output Structure

### Generated Clips
Each clip includes:
- **Video file** (MP4 format, vertical orientation)
- **Ranking data** (0-5 viral score with breakdown)
- **Face tracking info** (whether applied, speaker centered)
- **Subtitle files** (VTT, ASS, SRT, JSON)
- **Metadata** (timing, duration, transcript segment)

### Ranking Breakdown
- **Viral Score**: Overall 0-5 rating
- **Engagement Potential**: User interaction likelihood
- **Shareability**: Social media sharing potential
- **Trending Potential**: Viral trend likelihood
- **Factor Scores**: Individual scoring component details

## 🎬 Pipeline Flow

1. **Audio Extraction** - Extract audio for transcription
2. **Transcription** - Generate full transcript using Whisper
3. **Highlight Detection** - Identify potential viral moments
4. **Clip Ranking** - Score clips on 0-5 viral scale
5. **Face Tracking** - Apply speaker centering where possible
6. **Clip Generation** - Create optimized vertical clips
7. **Subtitle Export** - Generate multiple caption formats
8. **Output Delivery** - Return ranked clips with metadata

## 🔍 Monitoring & Debugging

### Logging
- Comprehensive logging throughout the pipeline
- Progress indicators for each processing step
- Detailed error reporting with context

### Performance Metrics
- Processing time per step
- Face detection accuracy
- Ranking score distribution
- Clip generation success rate

## 🚨 Important Notes

### Caption Rendering
- **No longer supported** in this repository
- Use dedicated captions repository for video caption burning
- This repo focuses on subtitle file export only

### Face Tracking
- Requires video files with visible faces
- Falls back to standard extraction if face tracking fails
- Performance depends on video quality and face visibility

### API Changes
- Removed `add_captions` parameter
- Simplified interface focused on viral generation
- New ranking endpoints for detailed analysis

## 🔮 Future Enhancements

### Planned Features
- **Advanced face tracking** with multiple speaker support
- **Emotion detection** for enhanced viral scoring
- **Trend analysis** integration for real-time viral prediction
- **Batch processing** for multiple video files
- **Custom ranking models** for different content types

### Performance Improvements
- **GPU acceleration** for face detection
- **Parallel processing** for multiple clips
- **Caching** for repeated analysis
- **Streaming** for large video files

---

## 📞 Support

For issues related to:
- **Viral clip generation**: This repository
- **Caption rendering**: Dedicated captions repository
- **General video processing**: Check main documentation

---

*This system is designed for high-volume viral content creation with professional-grade ranking and optimization.*

