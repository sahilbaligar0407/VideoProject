# Gaming Background Videos for Vertical Templates

This directory should contain background videos for the gaming template vertical layout.

## Required Files

Place the following MP4 files in this directory:

- `subway.mp4` - Subway Surfers gameplay background
- `templerun.mp4` - Temple Run gameplay background  
- `minecraft_parkour.mp4` - Minecraft parkour gameplay background

## Video Requirements

- **Format**: MP4
- **Resolution**: 1080x1920 (9:16 aspect ratio) preferred, but any resolution will work
- **Duration**: At least 30 seconds (will be looped to match clip duration)
- **Content**: Gameplay footage that looks good when blurred and used as background

## How It Works

When a clip is detected as gaming content, the system will:
1. Choose one of these backgrounds (rotating through them)
2. Blur the background slightly
3. Place your 16:9 gameplay clip as a rectangle on top
4. Output a perfect 1080x1920 vertical video

## Fallback

If no background files are found, the system will fall back to a blurred pillarbox layout.

## Getting Background Videos

You can:
- Record your own gameplay
- Download royalty-free gameplay footage
- Use placeholder videos for testing

## Example Commands

To create a simple test background (requires FFmpeg):
```bash
# Create a 10-second test pattern
ffmpeg -f lavfi -i "testsrc=duration=10:size=1080x1920:rate=30" -c:v libx264 -pix_fmt yuv420p subway.mp4
```
