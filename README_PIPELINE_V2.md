# ClipGenius Pipeline v2 - Advanced AI Video Processing

## 🚀 Overview

ClipGenius Pipeline v2 is a revolutionary upgrade that transforms video processing with AI-powered face tracking, dynamic layouts, enhanced captions, and viral optimization. This advanced system automatically detects faces, tracks them throughout videos, and creates intelligent layouts that adapt to content type.

## ✨ New Features

### 🎯 **Prepass Detection System**
- **Face Tracking**: MediaPipe-powered face detection with BYTE tracking
- **Speech Analysis**: Advanced speech segmentation with language detection
- **Scene Change Detection**: HSV-based scene change detection to avoid hard cuts

### 🎬 **Dynamic Layout State Machine**
- **BG_BLUR_RECT**: Blurred background with foreground rectangle overlay
- **VERT_FOCUS**: Face-centered auto-reframe with smooth transitions
- **Smart Transitions**: 0.3-0.5s smooth transitions between states
- **Content-Aware Layouts**: Automatically chooses optimal layout per clip

### 🎨 **Enhanced Caption System**
- **Multiple Modes**: Burn, Sidecar (VTT/ASS/JSON), or Off
- **Language Support**: Auto-detection + translation to English
- **Styling Options**: Boxed, Outline, Karaoke, and custom themes
- **Safe Positioning**: Mobile-optimized placement with configurable margins

### 🎮 **Background Templates**
- **Blur Background**: Self-video blurred background
- **Gameplay Backgrounds**: Subway Surfers, Temple Run, Minecraft parkour
- **Custom Themes**: Easily extensible background system

### 🤖 **AI Content Generation**
- **Auto Titles**: GPT-powered engaging titles (≤60 chars)
- **Hook Lines**: Attention-grabbing opening lines (≤8 words)
- **Smart CTAs**: Context-aware call-to-action suggestions
- **Viral Analysis**: Content viral potential scoring

### 📊 **Enhanced Scoring System**
- **Speaking-Face Bonus**: +0.1-0.2 when face overlaps with speech
- **Hook Heuristics**: +0.05-0.15 for early interrogatives/claims
- **Scene Change Penalty**: Avoids disruptive transitions
- **Multi-Signal Fusion**: Combines 7+ detection methods

## 🏗️ Architecture

### Core Modules

```
app/
├── prepass/           # Prepass detection system
│   ├── faces.py      # Face tracking with MediaPipe
│   ├── speech.py     # Speech segmentation & analysis
│   └── shots.py      # Scene change detection
├── layout/            # Layout management
│   ├── state_machine.py  # Layout state transitions
│   └── crop_path.py      # Face-tracking crop paths
├── render/            # Video rendering
│   ├── blur_bg.py    # Blur background renderer
│   ├── game_bg.py    # Gameplay background renderer
│   └── auto_reframe.py   # Face-tracking auto-reframe
├── captions/          # Enhanced caption system
│   ├── stt.py        # Speech-to-text with Whisper
│   ├── translate.py  # Multi-language translation
│   └── styles.py     # Caption styling & positioning
├── ai_text/           # AI content generation
│   └── titles_cta.py # Titles, hooks, and CTAs
└── config/            # Feature configuration
    └── features.py    # Pipeline configuration schema
```

### Data Flow

```
Video Input → Prepass Detection → Layout State Machine → Enhanced Scoring → Clip Generation → AI Content → Output
     ↓              ↓                    ↓                    ↓                ↓              ↓
  Face Boxes   Speech Segments    Layout States      Enhanced Scores    Video Clips   Titles/CTAs
     ↓              ↓                    ↓                    ↓                ↓              ↓
  Tracking      Language Det.     State Transitions   Viral Potential   Layout Modes   SEO Metadata
```

## 🎛️ Configuration

### Pipeline Configuration Schema

```typescript
interface PipelineConfig {
  captions: {
    mode: 'burn' | 'sidecar' | 'off';
    language: string;
    style: 'boxed' | 'outline' | 'karaoke' | 'default';
    safe_bottom: number;
    max_lines: number;
    word_by_word: boolean;
  };
  background: {
    mode: 'blur' | 'gameplay' | 'none';
    game?: 'subway' | 'templerun' | 'minecraft';
    mute: boolean;
    blur_strength: number;
  };
  face_tracking: {
    enabled: boolean;
    min_confidence: number;
    smoothing_window: number;
    transition_duration: number;
  };
  ai: {
    auto_titles: boolean;
    cta: 'auto' | 'subscribe' | 'follow' | 'comment' | 'like' | 'share';
    model: string;
    temperature: number;
  };
  video: {
    duration_target: number;
    fps: number;
    resolution: string;
    quality: 'high' | 'medium' | 'low';
  };
}
```

### Preset Configurations

```python
# Podcast preset
config = get_podcast_preset()
# - Sidecar captions with auto-language
# - Face tracking enabled
# - Blur background
# - 30s target duration

# Gaming preset  
config = get_gaming_preset()
# - Burn-in captions with outline style
# - Face tracking disabled
# - Gameplay background (Subway Surfers)
# - 25s target duration

# Educational preset
config = get_educational_preset()
# - Sidecar captions with word-by-word
# - Face tracking enabled
# - Blur background
# - 35s target duration
```

## 🚀 Usage

### Backend API

#### Generate Enhanced Clips

```bash
POST /api/v1/clips/generate
Content-Type: multipart/form-data

video_file: <video_file>
config_json: '{"captions":{"mode":"sidecar"},"face_tracking":{"enabled":true}}'
topics: "gaming, tutorial, comedy"
```

#### Check Processing Status

```bash
GET /api/v1/clips/status/{request_id}
```

#### Download Generated Clips

```bash
GET /api/v1/clips/download/{request_id}/{clip_index}
```

### Frontend Component

```tsx
import EnhancedVideoInput from './components/EnhancedVideoInput';

function App() {
  return (
    <div className="App">
      <EnhancedVideoInput />
    </div>
  );
}
```

### Python Integration

```python
from app.config.features import get_default_config
from app.prepass import track_faces, detect_speech_segments
from app.layout import compute_layout_states
from app.highlight.scoring import apply_enhanced_scoring

# Initialize configuration
config = get_default_config()
config.face_tracking.enabled = True
config.captions.mode = "sidecar"

# Run prepass detection
face_boxes = track_faces("video.mp4")
speech_segments = detect_speech_segments(transcription_data)

# Compute layout states
layout_states = compute_layout_states(face_boxes)

# Apply enhanced scoring
enhanced_highlights = apply_enhanced_scoring(
    highlights, face_boxes, speech_segments
)
```

## 🔧 Installation

### Dependencies

```bash
pip install -r requirements.txt
```

New dependencies for Pipeline v2:
- `mediapipe==0.10.7` - Face detection and tracking
- Enhanced `opencv-python` - Computer vision operations
- `openai>=1.3.7` - AI content generation

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Enhanced Pipeline Settings
ENABLE_FACE_TRACKING=true
ENABLE_SCENE_DETECTION=true
ENABLE_AI_CONTENT=true

# Caption Settings
CAPTION_MODE=sidecar
CAPTION_LANGUAGE=auto
CAPTION_SAFE_BOTTOM=160

# Face Tracking Settings
FACE_TRACKING_CONFIDENCE=0.5
FACE_TRACKING_SMOOTHING=5
TRANSITION_DURATION=0.4
```

## 📊 Performance

### Processing Times

- **Face Tracking**: ~2-5s per minute of video (10fps sampling)
- **Scene Detection**: ~1-3s per minute of video (5fps sampling)
- **Layout Computation**: ~0.1s per video
- **AI Content Generation**: ~2-5s per clip
- **Total Pipeline**: ~10-20s per minute of video

### Resource Requirements

- **CPU**: 4+ cores recommended for real-time processing
- **RAM**: 8GB+ for large video files
- **GPU**: Optional, CPU-only processing supported
- **Storage**: 2-5x input video size for temporary files

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific module tests
python -m pytest tests/test_face_tracking.py
python -m pytest tests/test_layout_state_machine.py
python -m pytest tests/test_enhanced_scoring.py
```

### Integration Tests

```bash
# Test end-to-end pipeline
python -m pytest tests/test_pipeline_v2.py

# Test with sample videos
python -m pytest tests/test_integration.py
```

### Sample Test Data

```python
# Test face tracking
def test_face_tracking():
    face_boxes = track_faces("test_video.mp4")
    assert len(face_boxes) > 0
    assert all(hasattr(box, 'confidence') for box in face_boxes)

# Test layout state machine
def test_layout_states():
    states = compute_layout_states(face_boxes)
    assert len(states) > 0
    assert all(hasattr(state, 'state') for state in states)
```

## 🔍 Troubleshooting

### Common Issues

#### Face Tracking Not Working
```bash
# Check MediaPipe installation
python -c "import mediapipe; print('MediaPipe OK')"

# Verify video format
ffprobe -v error -select_streams v:0 input.mp4

# Check confidence threshold
# Lower from 0.5 to 0.3 in config
```

#### Layout State Machine Issues
```bash
# Check face detection output
python -c "from app.prepass.faces import track_faces; print(track_faces('test.mp4'))"

# Verify state transitions
python -c "from app.layout.state_machine import compute_layout_states; print(compute_layout_states(...))"
```

#### AI Content Generation Fails
```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# Verify API quota
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Check model availability
# Ensure gpt-4o or gpt-3.5-turbo is available
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable verbose FFmpeg output
from app.render.ffmpeg import run_ffmpeg_command
# FFmpeg commands will show detailed output
```

## 🚀 Future Enhancements

### Planned Features

- **Multi-Person Tracking**: Support for multiple faces with speaker identification
- **Advanced Scene Detection**: AI-powered scene understanding
- **Custom Background Templates**: User-uploadable background videos
- **Real-time Processing**: Live video stream processing
- **Batch Processing**: Multiple video processing queue
- **Cloud Deployment**: AWS/GCP deployment scripts

### Extensibility

```python
# Custom face tracking
class CustomFaceTracker:
    def track_faces(self, video_path):
        # Implement custom tracking logic
        pass

# Custom layout renderer
class CustomLayoutRenderer:
    def render(self, video_path, layout_state):
        # Implement custom rendering logic
        pass

# Custom AI content generator
class CustomAIGenerator:
    def generate_content(self, transcript):
        # Implement custom AI logic
        pass
```

## 📚 API Reference

### Core Functions

```python
# Face tracking
track_faces(video_path: str, sample_rate: int = 10) -> List[FrameBox]

# Layout management
compute_layout_states(face_boxes: List[FrameBox], fps: int = 30) -> List[LayoutState]

# Enhanced scoring
apply_enhanced_scoring(segments: List[HighlightSegment], face_boxes: List[FrameBox], 
                      speech_segments: List[SpeechSegment]) -> List[HighlightSegment]

# AI content generation
generate_titles_cta(transcript_text: str, viral_terms: List[str] = None) -> Dict[str, Any]
```

### Data Models

```python
@dataclass
class FrameBox:
    t: float          # timestamp
    x: int            # center x
    y: int            # center y
    w: int            # width
    h: int            # height
    conf: float       # confidence

@dataclass
class LayoutState:
    timestamp: float
    state: State      # BG_BLUR_RECT or VERT_FOCUS
    transition_in: Optional[float]
    transition_out: Optional[float]
```

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/clipgenius.git
cd clipgenius

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

### Code Style

- **Python**: Black, isort, flake8
- **TypeScript**: ESLint, Prettier
- **Documentation**: Google-style docstrings
- **Testing**: pytest with 90%+ coverage

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/pipeline-v2`
3. Make changes and add tests
4. Run test suite: `python -m pytest tests/`
5. Submit pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MediaPipe**: Face detection and tracking
- **OpenAI**: Whisper transcription and GPT content generation
- **FFmpeg**: Video processing and rendering
- **OpenCV**: Computer vision operations

## 📞 Support

- **Documentation**: [docs.clipgenius.com](https://docs.clipgenius.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/clipgenius/issues)
- **Discord**: [Join our community](https://discord.gg/clipgenius)
- **Email**: support@clipgenius.com

---

**ClipGenius Pipeline v2** - Transforming video content creation with AI-powered intelligence. 🚀
