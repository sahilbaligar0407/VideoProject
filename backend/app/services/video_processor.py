import os
import tempfile
import subprocess
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import asyncio
import aiofiles
from openai import OpenAI
import numpy as np
import librosa
from scipy.signal import find_peaks
from app.settings import settings
from app.models import GeneratedClip, HighlightSegment, TranscriptionResult
from app.viral import (
    window_captions, score_windows_against_viral_vector, 
    filter_windows_by_score, create_highlight_segments_from_windows
)

# New modules for enhanced functionality
from app.highlight.snapping import (
    snap_to_transcript_boundary, snap_to_audio_pause, 
    choose_clip_window, duration_preference
)
from app.topic.search import topic_windows, topic_windows_embedding
from app.video.vertical import extract_vertical_clip, get_vertical_dimensions
from app.highlight.ranking import ClipRanker
from app.prepass.faces import FaceTracker

class VideoProcessor:
    def __init__(self, 
                 temp_dir: str = "temp",
                 output_dir: str = "outputs"):
        # OpenAI client will be initialized when needed
        self.temp_dir = temp_dir
        self.output_dir = output_dir
        
        # Initialize new components
        self.clip_ranker = ClipRanker()
        self.face_tracker = FaceTracker()
    
    async def process_video(
        self,
        video_path: str,
        input_type: str = "file",
        user_topics: Optional[List[str]] = None,
        vertical: bool = True
    ) -> List[GeneratedClip]:
        """Main processing pipeline for viral clip generation"""
        try:
            print(f"🎬 Starting viral clip generation for: {video_path}")
            print(f"📁 Input type: {input_type}")
            print(f"🎯 User topics: {user_topics}")
            print(f"📱 Vertical output: {vertical}")
            print(f"📁 File exists: {os.path.exists(video_path)}")
            if os.path.exists(video_path):
                print(f"📏 File size: {os.path.getsize(video_path)} bytes")
            
            # Step 1: Extract audio for transcription
            print("🎵 Step 1: Extracting audio...")
            audio_path = await self._extract_audio(video_path)
            
            # Step 2: Transcribe audio using OpenAI Whisper
            print("🗣️ Step 2: Transcribing audio...")
            transcription = await self._transcribe_audio(audio_path)
            
            # Step 3: Detect highlight segments
            print("✨ Step 3: Detecting highlights...")
            highlights = await self._detect_highlights(video_path, transcription, audio_path, user_topics)
            
            # Step 3.5: Rank clips using the new ranking system
            print("🏆 Step 3.5: Ranking clips for virality...")
            highlights = self.clip_ranker.rank_clips(highlights, transcription, video_path)
            
            # Print ranking report
            self.clip_ranker.print_ranking_report(highlights)
            
            # Step 4: Generate clips from highlights
            print("🎬 Step 4: Generating clips...")
            clips = await self._generate_clips(video_path, highlights, transcription, vertical)
            
            # Cleanup temporary files
            await self._cleanup_temp_files([audio_path])
            
            print(f"✅ Viral clip generation completed! Generated {len(clips)} clips")
            return clips
            
        except Exception as e:
            raise Exception(f"Viral clip generation failed: {str(e)}")
    
    async def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video file using ffmpeg"""
        audio_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.wav")
        
        print(f"🎵 Extracting audio from: {video_path}")
        print(f"🎵 Output audio path: {audio_path}")
        print(f"🎵 Temp directory exists: {os.path.exists(self.temp_dir)}")
        
        # Try different FFmpeg locations
        ffmpeg_paths = [
            "ffmpeg",  # Default PATH
            "C:\\ffmpeg\\bin\\ffmpeg.exe",  # Common Windows install location
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",  # Program Files location
            "C:\\Users\\%USERNAME%\\AppData\\Local\\ffmpeg\\bin\\ffmpeg.exe"  # User AppData
        ]
        
        ffmpeg_path = None
        for path in ffmpeg_paths:
            if os.path.exists(path) or path == "ffmpeg":
                ffmpeg_path = path
                break
        
        if not ffmpeg_path:
            raise Exception("FFmpeg not found. Please install FFmpeg and add it to your PATH.")
        
        cmd = [
            ffmpeg_path, "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            "-y", audio_path
        ]
        
        print(f"🔧 Running FFmpeg command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
            print(f"🔧 FFmpeg completed with return code: {result.returncode}")
            
            if result.returncode != 0:
                print(f"❌ FFmpeg stderr: {result.stderr}")
                print(f"❌ FFmpeg stdout: {result.stdout}")
                raise Exception(f"Audio extraction failed: {result.stderr}")
            
            # Verify audio file was created
            if os.path.exists(audio_path):
                audio_size = os.path.getsize(audio_path)
                print(f"✅ Audio extraction successful: {audio_size} bytes")
            else:
                raise Exception("Audio file was not created")
            
            return audio_path
            
        except subprocess.TimeoutExpired:
            print("❌ Audio extraction timed out after 5 minutes")
            raise Exception("Audio extraction timed out")
        except Exception as e:
            print(f"❌ Audio extraction failed: {e}")
            raise
    
    async def _transcribe_audio(self, audio_path: str) -> TranscriptionResult:
        """Transcribe audio using OpenAI Whisper API with chunked approach"""
        try:
            # Validate API key
            if not settings.openai_api_key or settings.openai_api_key.strip() == "":
                raise Exception("OpenAI API key is missing. Please check your .env file.")
            
            print(f"🔑 Using OpenAI API key: {settings.openai_api_key[:10]}...")
            
            # Initialize OpenAI client
            client = OpenAI(api_key=settings.openai_api_key)
            
            print(f"🎤 Starting chunked transcription with model: {settings.whisper_model}")
            print(f"🎵 Audio file size: {os.path.getsize(audio_path)} bytes")
            
            # Use chunked transcription for large files
            if os.path.getsize(audio_path) > 10 * 1024 * 1024:  # 10MB threshold
                print(f"📦 Audio file is large, using chunked transcription approach")
                return await self._transcribe_audio_chunked(client, audio_path)
            else:
                print(f"📦 Audio file is small, using direct transcription")
                return await self._transcribe_audio_direct(client, audio_path)
            
        except Exception as e:
            print(f"❌ Transcription error details: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Transcription failed: {str(e)}")
    
    async def _transcribe_audio_direct(self, client, audio_path: str) -> TranscriptionResult:
        """Direct transcription for small audio files"""
        try:
            print(f"🎤 Starting direct transcription...")
            
            async def transcribe_with_timeout():
                with open(audio_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model=settings.whisper_model,
                        file=audio_file,
                        response_format="verbose_json"
                    )
                return response
            
            # Set timeout to 2 minutes for direct transcription
            response = await asyncio.wait_for(transcribe_with_timeout(), timeout=120.0)
            
            print(f"✅ Direct transcription completed successfully!")
            print(f"📝 Transcribed text length: {len(response.text)} characters")
            
            # Parse the response
            segments = response.segments if hasattr(response, 'segments') else []
            text = response.text
            
            return TranscriptionResult(
                text=text,
                segments=segments,
                language=response.language if hasattr(response, 'language') else "en",
                duration=response.duration if hasattr(response, 'duration') else 0.0
            )
            
        except asyncio.TimeoutError:
            print(f"❌ Direct transcription timed out")
            raise Exception("Direct transcription timed out")
        except Exception as e:
            print(f"❌ Direct transcription failed: {e}")
            raise
    
    async def _transcribe_audio_chunked(self, client, audio_path: str) -> TranscriptionResult:
        """Chunked transcription for large audio files"""
        try:
            print(f"📦 Starting chunked transcription...")
            
            # Get audio duration using librosa
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            total_duration = len(y) / sr
            print(f"⏱️ Total audio duration: {total_duration:.2f} seconds")
            
            # Split into 30-second chunks
            chunk_duration = 30.0  # seconds
            chunks = []
            
            for i in range(0, int(total_duration), int(chunk_duration)):
                start_time = i
                end_time = min(i + chunk_duration, total_duration)
                chunks.append((start_time, end_time))
            
            print(f"📦 Split audio into {len(chunks)} chunks of ~{chunk_duration} seconds each")
            
            # Transcribe each chunk
            all_segments = []
            all_text = []
            
            for i, (start_time, end_time) in enumerate(chunks):
                print(f"🎤 Transcribing chunk {i+1}/{len(chunks)} ({start_time:.1f}s - {end_time:.1f}s)")
                
                # Extract chunk using FFmpeg
                chunk_path = os.path.join(self.temp_dir, f"chunk_{i}_{uuid.uuid4()}.wav")
                
                cmd = [
                    "ffmpeg", "-i", audio_path,
                    "-ss", str(start_time), "-t", str(end_time - start_time),
                    "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                    "-y", chunk_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    print(f"❌ Failed to extract chunk {i+1}: {result.stderr}")
                    continue
                
                try:
                    # Transcribe chunk with timeout
                    async def transcribe_chunk():
                        with open(chunk_path, "rb") as chunk_file:
                            response = client.audio.transcriptions.create(
                                model=settings.whisper_model,
                                file=chunk_file,
                                response_format="verbose_json"
                            )
                        return response
                    
                    response = await asyncio.wait_for(transcribe_chunk(), timeout=60.0)
                    
                    # Adjust segment timestamps
                    if hasattr(response, 'segments') and response.segments:
                        for segment in response.segments:
                            if 'start' in segment and 'end' in segment:
                                segment['start'] += start_time
                                segment['end'] += start_time
                        all_segments.extend(response.segments)
                    
                    all_text.append(response.text)
                    print(f"✅ Chunk {i+1} transcribed: {len(response.text)} characters")
                    
                except Exception as e:
                    print(f"❌ Chunk {i+1} transcription failed: {e}")
                finally:
                    # Cleanup chunk file
                    try:
                        os.remove(chunk_path)
                    except:
                        pass
            
            # Combine results
            combined_text = " ".join(all_text)
            print(f"✅ Chunked transcription completed!")
            print(f"📝 Total transcribed text length: {len(combined_text)} characters")
            print(f"📊 Total segments: {len(all_segments)}")
            
            return TranscriptionResult(
                text=combined_text,
                segments=all_segments,
                language="en",  # Default for chunked approach
                duration=total_duration
            )
            
        except Exception as e:
            print(f"❌ Chunked transcription failed: {e}")
            raise
    
    async def _detect_highlights(self, video_path: str, transcription: TranscriptionResult, audio_path: str = None, user_topics: Optional[List[str]] = None) -> List[HighlightSegment]:
        """Detect highlight segments optimized for short-form content (TikTok, Reels, Shorts)"""
        print(f"🎬 Starting enhanced highlight detection for short-form content...")
        
        highlights = []
        
        # Method 1: Enhanced audio analysis (reuse audio if provided) - 30% weight
        if audio_path and os.path.exists(audio_path):
            print(f"🎵 Reusing existing audio file for enhanced analysis: {audio_path}")
            audio_highlights = await self._detect_enhanced_audio_highlights(audio_path)
        else:
            print(f"🎵 Extracting new audio for enhanced analysis")
            audio_highlights = await self._detect_enhanced_audio_highlights_from_video(video_path)
        
        # Apply audio weight
        for highlight in audio_highlights:
            highlight.confidence_score *= 0.3
        print(f"🎵 Audio analysis found {len(audio_highlights)} segments (30% weight)")
        
        # Method 2: Content engagement analysis - 25% weight
        print(f"📱 Analyzing content for engagement potential...")
        engagement_highlights = await self._analyze_content_engagement(transcription)
        for highlight in engagement_highlights:
            highlight.confidence_score *= 0.25
        print(f"📱 Content engagement found {len(engagement_highlights)} segments (25% weight)")
        
        # Method 3: Viral moment detection - 20% weight
        print(f"🔥 Detecting potential viral moments...")
        viral_highlights = await self._detect_viral_moments(transcription, audio_path)
        for highlight in viral_highlights:
            highlight.confidence_score *= 0.20
        print(f"🔥 Viral moments found {len(viral_highlights)} segments (20% weight)")
        
        # Method 4: Story arc detection - 15% weight
        print(f"📖 Analyzing story structure...")
        story_highlights = await self._detect_story_arcs(transcription)
        for highlight in story_highlights:
            highlight.confidence_score *= 0.15
        print(f"📖 Story arcs found {len(story_highlights)} segments (15% weight)")
        
        # Method 5: ChatGPT-powered content analysis - 30% weight (INCREASED!)
        print(f"🤖 Using ChatGPT to analyze content quality and engagement...")
        try:
            ai_highlights = await self._analyze_content_with_chatgpt(transcription)
            for highlight in ai_highlights:
                highlight.confidence_score *= 0.30  # Increased from 10% to 30%
            print(f"🤖 AI analysis found {len(ai_highlights)} segments (30% weight)")
        except Exception as e:
            print(f"⚠️ ChatGPT analysis failed, continuing without AI analysis: {e}")
            ai_highlights = []
            print(f"🤖 AI analysis found 0 segments (skipped due to error)")
        
        # Method 6: Viral Similarity Engine - 25% weight
        print(f"🚀 Using Viral Similarity Engine for viral content detection...")
        try:
            viral_similarity_highlights = await self._score_viral(transcription, video_path)
            for highlight in viral_similarity_highlights:
                highlight.confidence_score *= 0.25
            print(f"🚀 Viral similarity found {len(viral_similarity_highlights)} segments (25% weight)")
        except Exception as e:
            print(f"⚠️ Viral similarity analysis failed, continuing without it: {e}")
            viral_similarity_highlights = []
            print(f"🚀 Viral similarity found 0 segments (skipped due to error)")
        
        # Method 7: Topic Search - 25% weight (NEW!)
        topic_highlights = []
        if user_topics:
            print(f"🎯 Searching for user-specified topics: {user_topics}")
            try:
                for topic in user_topics:
                    topic_results = await topic_windows_embedding(transcription, topic)
                    topic_highlights.extend(topic_results)
                    print(f"🎯 Topic '{topic}' found {len(topic_results)} segments")
                
                # Apply topic weight
                for highlight in topic_highlights:
                    highlight.confidence_score *= 0.25
                print(f"🎯 Topic search found {len(topic_highlights)} total segments (25% weight)")
            except Exception as e:
                print(f"⚠️ Topic search failed, continuing without it: {e}")
                topic_highlights = []
                print(f"🎯 Topic search found 0 segments (skipped due to error)")
        else:
            print(f"🎯 No user topics specified, skipping topic search")
        
        # Combine all detection methods
        all_segments = audio_highlights + engagement_highlights + viral_highlights + story_highlights + ai_highlights + viral_similarity_highlights + topic_highlights
        print(f"📊 Found {len(all_segments)} potential highlight segments with weighted scoring")
        
        # CRITICAL FIX: Limit segments before expensive ranking (was causing hang)
        if len(all_segments) > 100:
            print(f"⚠️ Too many segments ({len(all_segments)}), limiting to top 100 before ranking...")
            # Sort by confidence and take top 100
            all_segments.sort(key=lambda x: x.confidence_score, reverse=True)
            all_segments = all_segments[:100]
            print(f"📊 Limited to top {len(all_segments)} segments for ranking")
        
        # Ensure we have at least some segments to work with
        if not all_segments:
            print("⚠️ No highlight segments found, creating fallback segments...")
            # Create fallback segments from the beginning, middle, and end of the video
            fallback_segments = []
            try:
                # Get video duration
                cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", video_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    video_duration = float(result.stdout.strip())
                    
                    # Create 3 fallback segments
                    segment_duration = 30  # 30 seconds each
                    positions = [0, video_duration/2 - 15, video_duration - 30]
                    
                    for i, start_time in enumerate(positions):
                        if start_time >= 0 and start_time + segment_duration <= video_duration:
                                                fallback_segments.append(HighlightSegment(
                        start_time=start_time,
                        end_time=start_time + segment_duration,
                        duration=segment_duration,
                        confidence_score=0.5,  # Lower confidence for fallbacks
                        keywords=["fallback", "default_segment"],
                        transcript_segment="Fallback highlight segment",
                        detection_method="fallback"
                    ))
                    
                    print(f"📊 Created {len(fallback_segments)} fallback segments")
                    all_segments = fallback_segments
            except:
                print("⚠️ Failed to create fallback segments")
                return []
        
        # Advanced ranking and filtering for short-form optimization
        print(f"🏆 Starting advanced ranking with {len(all_segments)} segments...")
        try:
            # Add timeout to ranking to prevent hanging
            highlights = await asyncio.wait_for(
                self._rank_for_shorts_advanced(all_segments, transcription, video_path), 
                timeout=60.0  # 1 minute timeout
            )
        except asyncio.TimeoutError:
            print("⚠️ Advanced ranking timed out, using simple ranking instead...")
            # Fallback to simple ranking
            all_segments.sort(key=lambda x: x.confidence_score, reverse=True)
            highlights = all_segments[:settings.num_clips]
            print(f"📊 Simple ranking selected {len(highlights)} segments")
        except Exception as e:
            print(f"⚠️ Advanced ranking failed: {e}, using simple ranking...")
            # Fallback to simple ranking
            all_segments.sort(key=lambda x: x.confidence_score, reverse=True)
            highlights = all_segments[:settings.num_clips]
            print(f"📊 Simple ranking selected {len(highlights)} segments")
        
        # Ensure we get the BEST segments, not just the first ones
        highlights = sorted(highlights, key=lambda x: x.confidence_score, reverse=True)
        highlights = highlights[:settings.num_clips]
        
        print(f"🎯 Selected {len(highlights)} BEST highlights after advanced ranking and scoring")
        return highlights
    
    async def _detect_audio_peaks(self, video_path: str) -> List[HighlightSegment]:
        """Detect audio peaks for highlight detection by extracting audio from video"""
        try:
            # Extract audio data for analysis using the same method as transcription
            audio_path = await self._extract_audio(video_path)
            
            # Use the extracted audio file for analysis
            highlights = await self._detect_audio_peaks_from_file(audio_path)
            
            # Cleanup the temporary audio file
            try:
                os.remove(audio_path)
            except:
                pass
                
            return highlights
            
        except Exception as e:
            print(f"Audio peak detection failed: {e}")
            return []
    
    async def _detect_audio_peaks_from_file(self, audio_path: str) -> List[HighlightSegment]:
        """Detect audio peaks from an audio file"""
        try:
            print(f"🎵 Analyzing audio peaks from: {audio_path}")
            
            # Load the WAV file for analysis
            y, sr = librosa.load(audio_path, sr=22050)
            duration = len(y) / sr
            
            highlights = []
            
            # Energy-based peak detection
            energy = librosa.feature.rms(y=y)[0]
            energy_peaks, _ = find_peaks(energy, height=np.mean(energy) * 1.5, distance=sr*3)
            
            for peak in energy_peaks:
                start_time = max(0, peak / sr - 5)
                end_time = min(duration, peak / sr + 5)
                
                if end_time - start_time >= 10:  # Minimum 10 seconds
                    highlights.append(HighlightSegment(
                        start_time=start_time,
                        end_time=end_time,
                        duration=end_time - start_time,
                        confidence_score=0.7,
                        keywords=["audio_peak", "energy_peak"],
                        transcript_segment="Audio peak detected",
                        detection_method="audio_peak"
                    ))
            
            print(f"🎵 Found {len(highlights)} audio peaks")
            return highlights
            
        except Exception as e:
            print(f"❌ Audio peak detection from file failed: {e}")
            return []
    
    async def _detect_enhanced_audio_highlights(self, audio_path: str) -> List[HighlightSegment]:
        """Enhanced audio analysis for short-form content optimization"""
        try:
            print(f"🎵 Starting enhanced audio analysis: {audio_path}")
            
            # Load the WAV file for analysis
            y, sr = librosa.load(audio_path, sr=22050)
            duration = len(y) / sr
            
            highlights = []
            
            # 1. Volume/Energy Analysis with enhanced detection
            print(f"🔊 Analyzing volume and energy patterns...")
            energy = librosa.feature.rms(y=y)[0]
            
            # More sensitive peak detection for gaming content
            energy_peaks, _ = find_peaks(energy, height=np.mean(energy) * 1.2, distance=sr*2)
            
            for peak in energy_peaks:
                start_time = max(0, peak / sr - 10)
                end_time = min(duration, peak / sr + 15)
                
                if end_time - start_time >= 5.0:  # Minimum 5 seconds for better context
                    # Enhanced scoring based on energy intensity and duration
                    intensity = energy[peak] / np.mean(energy)
                    
                    # Calculate energy variance in the segment for more dynamic scoring
                    segment_start = int(start_time * sr / 512)  # Convert to frame index
                    segment_end = int(end_time * sr / 512)
                    segment_energy = energy[segment_start:segment_end]
                    
                    if len(segment_energy) > 0:
                        energy_variance = np.var(segment_energy)
                        energy_mean = np.mean(segment_energy)
                        
                        # Score based on intensity, variance, and duration
                        base_score = min(0.95, 0.5 + (intensity - 1.2) * 0.3)
                        variance_bonus = min(0.2, energy_variance / (energy_mean * 2))  # Bonus for dynamic energy
                        duration_bonus = min(0.1, (end_time - start_time - 5) / 20)  # Bonus for longer segments
                        
                        confidence = base_score + variance_bonus + duration_bonus
                        
                        highlight = HighlightSegment(
                            start_time=start_time,
                            end_time=end_time,
                            duration=end_time - start_time,
                            confidence_score=confidence,
                            keywords=["high_energy", "dynamic_audio", "gaming_moment"],
                            transcript_segment="",
                            detection_method="enhanced_audio"
                        )
                        highlights.append(highlight)
            
            # 2. Rhythm/Beat Detection
            print(f"🥁 Analyzing rhythm and beat patterns...")
            try:
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
                beat_times = librosa.frames_to_time(beats, sr=sr)
                
                # Find segments with strong rhythmic patterns
                for i in range(len(beat_times) - 1):
                    start_time = beat_times[i]
                    end_time = min(duration, start_time + 15)  # 15-second rhythmic segments
                    
                    if end_time - start_time >= 5.0:
                        highlight = HighlightSegment(
                            start_time=start_time,
                            end_time=end_time,
                            duration=end_time - start_time,
                            confidence_score=0.75,
                            keywords=["rhythm", "beat", "music"],
                            transcript_segment="",
                            detection_method="enhanced_audio"
                        )
                        highlights.append(highlight)
            except:
                print(f"⚠️ Rhythm detection failed, continuing...")
            
            # 3. Sudden Audio Changes Detection (reactions, explosions, etc.)
            print(f"💥 Analyzing sudden audio changes and reactions...")
            try:
                # Calculate spectral contrast for detecting sudden changes
                spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
                contrast_mean = np.mean(spectral_contrast, axis=0)
                
                # Find sudden changes in spectral contrast
                contrast_diff = np.diff(contrast_mean)
                change_threshold = np.std(contrast_diff) * 2
                change_points = np.where(np.abs(contrast_diff) > change_threshold)[0]
                
                for change_point in change_points:
                    if change_point < len(contrast_diff) - 1:  # Ensure we have enough data
                        start_time = max(0, change_point * 512 / sr - 5)
                        end_time = min(duration, change_point * 512 / sr + 10)
                        
                        if end_time - start_time >= 8.0:  # Minimum 8 seconds for reaction context
                            change_intensity = np.abs(contrast_diff[change_point]) / change_threshold
                            confidence = min(0.9, 0.6 + change_intensity * 0.2)
                            
                            highlight = HighlightSegment(
                                start_time=start_time,
                                end_time=end_time,
                                duration=end_time - start_time,
                                confidence_score=confidence,
                                keywords=["sudden_change", "reaction", "surprise"],
                                transcript_segment="",
                                detection_method="enhanced_audio"
                            )
                            highlights.append(highlight)
            except Exception as e:
                print(f"⚠️ Sudden change detection failed: {e}")
            
            # 4. Silence Detection (for dramatic pauses)
            print(f"🤫 Analyzing silence and dramatic pauses...")
            silence_threshold = 0.01
            silence_frames = np.where(energy < silence_threshold)[0]
            
            if len(silence_frames) > 0:
                # Group consecutive silence frames
                silence_groups = []
                current_group = [silence_frames[0]]
                
                for frame in silence_frames[1:]:
                    if frame - current_group[-1] <= sr:  # Within 1 second
                        current_group.append(frame)
                    else:
                        if len(current_group) >= sr * 2:  # At least 2 seconds of silence
                            silence_groups.append(current_group)
                        current_group = [frame]
                
                # Add the last group
                if len(current_group) >= sr * 2:
                    silence_groups.append(current_group)
                
                for group in silence_groups:
                    start_time = max(0, group[0] / sr - 3)
                    end_time = min(duration, group[-1] / sr + 3)
                    
                    if end_time - start_time >= 5.0:
                        highlight = HighlightSegment(
                            start_time=start_time,
                            end_time=end_time,
                            duration=end_time - start_time,
                            confidence_score=0.8,
                            keywords=["dramatic_pause", "silence", "tension"],
                            transcript_segment="",
                            detection_method="enhanced_audio"
                        )
                        highlights.append(highlight)
            
            print(f"🎵 Enhanced audio analysis found {len(highlights)} highlights")
            return highlights
            
        except Exception as e:
            print(f"❌ Enhanced audio analysis failed: {e}")
            return []
    
    async def _detect_enhanced_audio_highlights_from_video(self, video_path: str) -> List[HighlightSegment]:
        """Extract audio and run enhanced analysis"""
        try:
            audio_path = await self._extract_audio(video_path)
            highlights = await self._detect_enhanced_audio_highlights(audio_path)
            
            # Cleanup
            try:
                os.remove(audio_path)
            except:
                pass
            
            return highlights
        except Exception as e:
            print(f"❌ Audio extraction for enhanced analysis failed: {e}")
            return []
    
    async def _analyze_content_engagement(self, transcription: TranscriptionResult) -> List[HighlightSegment]:
        """Analyze content for engagement potential (questions, emotions, reactions)"""
        print(f"📱 Analyzing content engagement patterns...")
        
        highlights = []
        text = transcription.text.lower()
        
        # 1. Question Detection (high engagement)
        question_indicators = ["?", "what", "how", "why", "when", "where", "who", "which"]
        question_score = 0.9
        
        for indicator in question_indicators:
            if indicator in text:
                # Find question positions
                positions = [i for i, char in enumerate(text) if char == "?"]
                for pos in positions:
                    # Estimate time position
                    estimated_time = (pos / len(text)) * transcription.duration
                    start_time = max(0, estimated_time - 10)
                    end_time = min(transcription.duration, estimated_time + 10)
                    
                    highlight = HighlightSegment(
                        start_time=start_time,
                        end_time=end_time,
                        duration=end_time - start_time,
                        confidence_score=question_score,
                        keywords=["question", "engagement"],
                        transcript_segment="",
                        detection_method="content_engagement"
                    )
                    highlights.append(highlight)
        
        # 2. Emotional/Reactive Content
        emotional_keywords = [
            "amazing", "incredible", "wow", "unbelievable", "omg", "holy",
            "best", "worst", "love", "hate", "crazy", "insane", "mind-blowing"
        ]
        
        for keyword in emotional_keywords:
            if keyword in text:
                keyword_pos = text.find(keyword)
                estimated_time = (keyword_pos / len(text)) * transcription.duration
                start_time = max(0, estimated_time - 12)
                end_time = min(transcription.duration, estimated_time + 12)
                
                highlight = HighlightSegment(
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    confidence_score=0.85,
                    keywords=["emotional", "reaction", keyword],
                    transcript_segment="",
                    detection_method="content_engagement"
                )
                highlights.append(highlight)
        
        # 3. Important/Key Information
        important_indicators = [
            "important", "key", "critical", "essential", "main", "primary",
            "breakthrough", "discovery", "secret", "reveal", "announcement"
        ]
        
        for indicator in important_indicators:
            if indicator in text:
                indicator_pos = text.find(indicator)
                estimated_time = (indicator_pos / len(text)) * transcription.duration
                start_time = max(0, estimated_time - 15)
                end_time = min(transcription.duration, estimated_time + 15)
                
                highlight = HighlightSegment(
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    confidence_score=0.8,
                    keywords=["important", "key_info", indicator],
                    transcript_segment="",
                    detection_method="content_engagement"
                )
                highlights.append(highlight)
        
        print(f"📱 Content engagement analysis found {len(highlights)} highlights")
        return highlights
    
    async def _detect_viral_moments(self, transcription: TranscriptionResult, audio_path: str = None) -> List[HighlightSegment]:
        """Detect potential viral moments based on social media patterns"""
        print(f"🔥 Analyzing for viral potential...")
        
        highlights = []
        text = transcription.text.lower()
        
        # 1. Controversial/Provocative Content
        viral_keywords = [
            "controversial", "shocking", "revealing", "exposed", "truth", "lie",
            "scandal", "drama", "beef", "fight", "argument", "confrontation"
        ]
        
        for keyword in viral_keywords:
            if keyword in text:
                keyword_pos = text.find(keyword)
                estimated_time = (keyword_pos / len(text)) * transcription.duration
                start_time = max(0, estimated_time - 15)
                end_time = min(transcription.duration, estimated_time + 15)
                
                highlight = HighlightSegment(
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    confidence_score=0.9,
                    keywords=["viral", "controversial", keyword],
                    transcript_segment="",
                    detection_method="viral_moments"
                )
                highlights.append(highlight)
        
        # 2. Call-to-Action Moments
        cta_indicators = [
            "subscribe", "follow", "like", "share", "comment", "save",
            "check out", "visit", "download", "join", "sign up"
        ]
        
        for indicator in cta_indicators:
            if indicator in text:
                indicator_pos = text.find(indicator)
                estimated_time = (indicator_pos / len(text)) * transcription.duration
                start_time = max(0, estimated_time - 8)
                end_time = min(transcription.duration, estimated_time + 8)
                
                highlight = HighlightSegment(
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    confidence_score=0.8,
                    keywords=["cta", "engagement", indicator],
                    transcript_segment="",
                    detection_method="viral_moments"
                )
                highlights.append(highlight)
        
        # 3. Trending Topics/References
        trending_indicators = [
            "trending", "viral", "popular", "famous", "celebrity", "influencer",
            "tiktok", "instagram", "youtube", "social media", "viral trend"
        ]
        
        for indicator in trending_indicators:
            if indicator in text:
                indicator_pos = text.find(indicator)
                estimated_time = (indicator_pos / len(text)) * transcription.duration
                start_time = max(0, estimated_time - 12)
                end_time = min(transcription.duration, estimated_time + 12)
                
                highlight = HighlightSegment(
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    confidence_score=0.85,
                    keywords=["trending", "viral", indicator],
                    transcript_segment="",
                    detection_method="viral_moments"
                )
                highlights.append(highlight)
        
        print(f"🔥 Viral moment detection found {len(highlights)} highlights")
        return highlights
    
    async def _detect_story_arcs(self, transcription: TranscriptionResult) -> List[HighlightSegment]:
        """Detect story structure and narrative arcs"""
        print(f"📖 Analyzing story structure...")
        
        highlights = []
        
        if hasattr(transcription, 'segments') and transcription.segments:
            segments = transcription.segments
            
            # 1. Opening Hook (first 30 seconds)
            if segments:
                first_segment = segments[0]
                if 'start' in first_segment and 'end' in first_segment:
                    start_time = first_segment['start']
                    end_time = min(transcription.duration, start_time + 30)
                    
                    highlight = HighlightSegment(
                        start_time=start_time,
                        end_time=end_time,
                        duration=end_time - start_time,
                        confidence_score=0.8,
                        keywords=["opening", "hook", "introduction"],
                        transcript_segment="",
                        detection_method="story_arcs"
                    )
                    highlights.append(highlight)
            
            # 2. Middle Climax (around 50% mark)
            mid_point = transcription.duration * 0.5
            for segment in segments:
                if 'start' in segment and 'end' in segment:
                    if abs(segment['start'] - mid_point) < 30:  # Within 30 seconds of midpoint
                        start_time = max(0, segment['start'] - 15)
                        end_time = min(transcription.duration, segment['end'] + 15)
                        
                        highlight = HighlightSegment(
                            start_time=start_time,
                            end_time=end_time,
                            duration=end_time - start_time,
                            confidence_score=0.75,
                            keywords=["climax", "middle", "peak"],
                            transcript_segment="",
                            detection_method="story_arcs"
                        )
                        highlights.append(highlight)
                        break
            
            # 3. Conclusion/Summary (last 30 seconds)
            if segments:
                last_segment = segments[-1]
                if 'start' in last_segment and 'end' in last_segment:
                    start_time = max(0, transcription.duration - 30)
                    end_time = transcription.duration
                    
                    highlight = HighlightSegment(
                        start_time=start_time,
                        end_time=end_time,
                        duration=end_time - start_time,
                        confidence_score=0.8,
                        keywords=["conclusion", "summary", "ending"],
                        transcript_segment="",
                        detection_method="story_arcs"
                    )
                    highlights.append(highlight)
        
        print(f"📖 Story arc detection found {len(highlights)} highlights")
        return highlights
    
    async def _rank_for_shorts(self, segments: List[HighlightSegment], transcription: TranscriptionResult) -> List[HighlightSegment]:
        """Advanced ranking system optimized for short-form content (TikTok, Reels, Shorts)"""
        print(f"🎯 Ranking segments for short-form optimization...")
        
        if not segments:
            return []
        
        # Enhanced scoring system for shorts
        for segment in segments:
            # Base score from detection methods
            base_score = segment.confidence_score
            
            # Duration optimization (15-60 seconds is ideal for shorts)
            duration = segment.duration
            if 15 <= duration <= 60:
                duration_score = 1.0
            elif 10 <= duration < 15 or 60 < duration <= 90:
                duration_score = 0.8
            else:
                duration_score = 0.6
            
            # Position optimization (beginning and end are better for retention)
            video_duration = transcription.duration
            segment_center = (segment.start_time + segment.end_time) / 2
            position_ratio = segment_center / video_duration
            
            if position_ratio < 0.2:  # First 20%
                position_score = 1.0
            elif position_ratio > 0.8:  # Last 20%
                position_score = 0.9
            elif 0.3 < position_ratio < 0.7:  # Middle (good for climax)
                position_score = 0.85
            else:
                position_score = 0.7
            
            # Content type scoring
            content_score = 1.0
            keywords = segment.keywords
            
            # High engagement content types
            if any(word in keywords for word in ["question", "emotional", "viral", "controversial"]):
                content_score = 1.0
            elif any(word in keywords for word in ["rhythm", "beat", "music"]):
                content_score = 0.9
            elif any(word in keywords for word in ["opening", "hook", "climax"]):
                content_score = 0.85
            elif any(word in keywords for word in ["dramatic_pause", "silence"]):
                content_score = 0.8
            
            # Calculate final score
            final_score = (base_score * 0.4 + duration_score * 0.3 + 
                          position_score * 0.2 + content_score * 0.1)
            
            segment.confidence_score = min(0.95, final_score)
        
        # Sort by enhanced confidence score
        segments.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Remove overlapping segments (keep higher scoring ones)
        merged = []
        for segment in segments:
            overlapping = False
            for existing in merged:
                if (segment.start_time < existing.end_time + 5 and  # 5 second buffer
                    segment.end_time + 5 > existing.start_time):
                    overlapping = True
                    break
            
            if not overlapping:
                merged.append(segment)
        
        # Ensure optimal duration distribution
        final_highlights = []
        total_duration = 0
        max_total_duration = 180  # 3 minutes total
        
        for segment in merged:
            if total_duration + segment.duration <= max_total_duration:
                final_highlights.append(segment)
                total_duration += segment.duration
            else:
                break
        
        print(f"🎯 Short-form optimization complete:")
        print(f"   📊 Enhanced scoring applied")
        print(f"   ⏱️ Duration optimization: {len([s for s in final_highlights if 15 <= s.duration <= 60])}/{len(final_highlights)} optimal")
        print(f"   📍 Position optimization: {len([s for s in final_highlights if s.confidence_score > 0.8])}/{len(final_highlights)} high-scoring")
        print(f"   🎬 Total duration: {total_duration:.1f}s")
        
        return final_highlights
    
    async def _generate_clips(self, video_path: str, highlights: List[HighlightSegment], 
                             transcription: TranscriptionResult, vertical: bool = True) -> List[GeneratedClip]:
        """Generate video clips from highlight segments with smart clipping and vertical rendering"""
        clips = []
        
        print(f"🎬 Generating clips from {len(highlights)} highlights")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📱 Vertical output: {vertical}")
        
        # Get video duration for clipping
        video_duration = 0
        try:
            cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", video_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                video_duration = float(result.stdout.strip())
                print(f"⏱️ Video duration: {video_duration:.2f} seconds")
        except Exception as e:
            print(f"⚠️ Could not determine video duration: {e}")
            video_duration = 300  # Default fallback
        
        # Extract audio for pause detection if needed
        audio_path = None
        if any(highlight.detection_method in ["audio_pause", "enhanced_audio"] for highlight in highlights):
            print(f"🎵 Extracting audio for pause detection...")
            audio_path = await self._extract_audio(video_path)
        
        for i, highlight in enumerate(highlights):
            try:
                print(f"\n--- Processing highlight {i+1} ---")
                
                # Use smart clip window selection
                center_time = (highlight.start_time + highlight.end_time) / 2
                duration_policy = {
                    'min': settings.min_clip_duration,
                    'target': settings.target_clip_duration,
                    'max': settings.max_clip_duration
                }
                
                start_time, end_time = choose_clip_window(center_time, duration_policy, video_duration)
                duration = end_time - start_time
                
                print(f"🎯 Smart clip window: {start_time:.2f}s to {end_time:.2f}s (duration: {duration:.2f}s)")
                
                # Apply smart snapping for clean endings
                print(f"🔍 Applying smart snapping for clean endings...")
                
                # First try transcript boundary snapping
                new_start, new_end, snap_reason = snap_to_transcript_boundary(
                    start_time, end_time, transcription.segments, 
                    settings.snap_max_overhang, settings.snap_punctuations
                )
                
                if new_end != end_time:
                    print(f"📝 Transcript boundary snap: {end_time:.2f}s → {new_end:.2f}s ({snap_reason})")
                    start_time, end_time = new_start, new_end
                    duration = end_time - start_time
                
                # If transcript snapping didn't help much, try audio pause snapping
                if audio_path and abs(new_end - end_time) < 1.0:  # Only if transcript snap didn't move much
                    print(f"🔊 Trying audio pause snapping...")
                    new_start, new_end, snap_reason = snap_to_audio_pause(
                        audio_path, start_time, end_time,
                        settings.snap_silence_thresh_db, settings.snap_min_pause, 
                        settings.snap_max_overhang
                    )
                    
                    if new_end != end_time:
                        print(f"🔊 Audio pause snap: {end_time:.2f}s → {new_end:.2f}s ({snap_reason})")
                        start_time, end_time = new_start, new_end
                        duration = end_time - start_time
                
                # Ensure final duration is within bounds
                if duration < settings.min_clip_duration:
                    print(f"⚠️ Duration too short after snapping, adjusting...")
                    end_time = start_time + settings.min_clip_duration
                    duration = settings.min_clip_duration
                elif duration > settings.max_clip_duration:
                    print(f"⚠️ Duration too long after snapping, adjusting...")
                    end_time = start_time + settings.max_clip_duration
                    duration = settings.max_clip_duration
                
                print(f"✅ Final clip timing: {start_time:.2f}s to {end_time:.2f}s (duration: {duration:.2f}s)")
                
                # Generate clip filename
                clip_id = str(uuid.uuid4())
                clip_filename = f"clip_{i+1}_{clip_id}.mp4"
                # Ensure output_dir is absolute
                output_dir_abs = os.path.abspath(self.output_dir)
                clip_path = os.path.join(output_dir_abs, clip_filename)
                
                print(f"🎬 Clip {i+1} ID: {clip_id}")
                print(f"🎬 Clip {i+1} path: {clip_path}")
                
                # Extract clip using vertical rendering if requested
                if vertical:
                    # Decide vertical layout per highlight
                    layout_mode = "cover"
                    gaming_theme = None

                    kw = set((highlight.keywords or []))
                    text_snippet = (highlight.transcript_segment or "").lower()

                    if any(k in kw for k in ["podcast", "interview", "guest"]) or "podcast" in text_snippet:
                        layout_mode = "podcast_face"
                    elif any(k in kw for k in ["gaming", "gameplay", "roblox", "minecraft", "valorant", "fortnite"]) or "game" in text_snippet:
                        layout_mode = "gaming_template"
                        # pick a theme
                        themes = ["subway", "templerun", "minecraft"]
                        gaming_theme = themes[(i) % len(themes)]

                    bg_assets = getattr(settings, "gaming_backgrounds", {
                        "subway": "assets/backgrounds/subway.mp4",
                        "templerun": "assets/backgrounds/templerun.mp4",
                        "minecraft": "assets/backgrounds/minecraft_parkour.mp4",
                    })

                    print(f"📱 Extracting vertical clip mode={layout_mode} theme={gaming_theme}")
                    
                    # Try face tracking first for speaker centering
                    face_tracking_success = False
                    if settings.face_detection_enabled and settings.auto_crop_enabled:
                        print(f"👤 Attempting face tracking for speaker centering...")
                        face_tracking_success = self.face_tracker.apply_face_tracking_to_clip(
                            video_path, clip_path, start_time, end_time
                        )
                    
                    if not face_tracking_success:
                        # Fall back to standard vertical extraction
                        print(f"📱 Using standard vertical extraction...")
                        success = extract_vertical_clip(
                            video_path, clip_path, start_time, duration,
                            mode=layout_mode, theme=gaming_theme, bg_roots=bg_assets
                        )
                    else:
                        success = True
                        print(f"✅ Face tracking applied successfully")
                    
                    if not success:
                        print(f"❌ Vertical extraction failed - NOT falling back to standard")
                        print(f"❌ Clip {i+1} generation failed due to vertical extraction failure")
                        continue
                else:
                    print(f"📺 Extracting standard clip...")
                    success = await self._extract_video_clip(video_path, clip_path, start_time, duration)
                    if not success:
                        print(f"❌ Standard extraction failed for clip {i+1}")
                        continue
                
                # Verify the clip was created
                if os.path.exists(clip_path) and os.path.getsize(clip_path) > 1024:
                    print(f"✅ Clip {i+1} created successfully: {os.path.getsize(clip_path)} bytes")
                else:
                    print(f"❌ Clip {i+1} was not created or is too small!")
                    continue
                
                # Ensure clip_path is absolute
                clip_path_abs = os.path.abspath(clip_path)
                if not os.path.exists(clip_path_abs):
                    print(f"❌ Clip path does not exist: {clip_path_abs}")
                    continue
                
                # Generate caption text for metadata
                caption_text = await self._generate_caption_text(transcription, start_time, end_time)
                
                # Export transcript files (.ass, .srt, .vtt, .json) for the clip
                base_noext = os.path.splitext(clip_path_abs)[0]
                await self._export_sidecar_captions(base_noext, transcription, start_time, end_time)
                
                # Use the absolute clip path
                file_path_to_publish = clip_path_abs
                
                print(f"✅ Clip {i+1} completed: {os.path.basename(file_path_to_publish)}")
                print(f"📁 Clip path (absolute): {file_path_to_publish}")
                print(f"📁 Clip size: {os.path.getsize(file_path_to_publish)} bytes")
                print(f"📁 Clip ID: {clip_id}")
                
                # Create clip object with absolute path
                clip = GeneratedClip(
                    clip_id=clip_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    file_path=file_path_to_publish,  # Store absolute path
                    caption_text=caption_text,
                    download_url=f"/api/v1/download/{clip_id}",
                    ranking=getattr(highlight, 'ranking', None),  # Include ranking information if available
                    face_tracking_applied=face_tracking_success,  # Whether face tracking was used
                    speaker_centered=face_tracking_success  # Whether speaker was kept centered
                )
                
                clips.append(clip)
                print(f"✅ Clip {i+1} added to results")
                
            except Exception as e:
                print(f"❌ Failed to generate clip {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Cleanup audio file if we created one
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                print(f"🧹 Cleaned up temporary audio file")
            except:
                pass
        
        print(f"\n=== Generated {len(clips)} clips successfully ===")
        return clips
    
    async def _extract_video_clip(self, video_path: str, output_path: str, start_time: float, duration: float) -> bool:
        """Extract a video clip using FFmpeg with Windows-compatible settings"""
        try:
            print(f"🎬 Extracting clip: {start_time:.2f}s to {start_time + duration:.2f}s")
            
            # Ensure minimum duration
            duration = max(duration, 2.0)
            
            # Use Windows-compatible FFmpeg settings
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-ss", str(start_time),
                "-t", str(duration),
                "-avoid_negative_ts", "make_zero",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "veryfast",
                "-crf", "23",
                "-r", "30",
                "-vsync", "cfr",
                "-profile:v", "baseline",
                "-level:v", "3.0",
                "-tag:v", "avc1",
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "48000",
                "-ac", "2",
                "-movflags", "+faststart",
                "-y",
                output_path
            ]
            
            print(f"🔧 FFmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ FFmpeg failed: {result.stderr}")
                return False
            
            # Verify the output file
            if await self._verify_video_file(output_path):
                print(f"✅ Clip extracted successfully: {os.path.getsize(output_path)} bytes")
                return True
            else:
                print(f"❌ Clip verification failed")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ FFmpeg timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"❌ Clip extraction failed: {e}")
            return False
    
    async def _generate_caption_text(self, transcription: TranscriptionResult, 
                                    start_time: float, end_time: float) -> str:
        """Generate caption text for a specific time segment with better speaker handling"""
        if not hasattr(transcription, 'segments') or not transcription.segments:
            return "Generated clip"
        
        # Find transcript segments within the time range
        relevant_segments = []
        for segment in transcription.segments:
            if 'start' in segment and 'end' in segment:
                # Check if segment overlaps with our time range
                segment_start = segment['start']
                segment_end = segment['end']
                
                # Calculate overlap
                overlap_start = max(start_time, segment_start)
                overlap_end = min(end_time, segment_end)
                
                if overlap_end > overlap_start:  # There's an overlap
                    # Calculate how much of this segment is within our range
                    overlap_duration = overlap_end - overlap_start
                    segment_duration = segment_end - segment_start
                    
                    if overlap_duration / segment_duration > 0.3:  # At least 30% overlap
                        relevant_segments.append({
                            'text': segment.get('text', ''),
                            'start': segment_start,
                            'end': segment_end,
                            'overlap_ratio': overlap_duration / segment_duration
                        })
        
        if relevant_segments:
            # Sort by overlap ratio and take the most relevant
            relevant_segments.sort(key=lambda x: x['overlap_ratio'], reverse=True)
            
            # Combine text with better formatting
            combined_text = ""
            for i, seg in enumerate(relevant_segments[:3]):  # Take top 3 most relevant
                if i > 0:
                    combined_text += " | "  # Separate speakers/segments
                combined_text += seg['text'].strip()
            
            # Clean up and limit length
            combined_text = combined_text.replace("  ", " ").strip()
            if len(combined_text) > 120:
                combined_text = combined_text[:120] + "..."
            
            return combined_text
        else:
            return "Generated highlight clip"
    
    # Caption burning removed - now handled by external caption repository
    
    async def _cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Failed to cleanup {file_path}: {e}")
    
    async def _verify_video_file(self, path: str) -> bool:
        """Check if video file is valid"""
        try:
            if not os.path.exists(path):
                print(f"❌ Output file not created: {path}")
                return False
            
            if os.path.getsize(path) < 1024:  # 1KB minimum
                print(f"❌ Output file too small: {os.path.getsize(path)} bytes")
                return False
            
            # Quick sanity check with ffprobe
            cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"❌ Video validation failed: {result.stderr}")
                return False
            
            print(f"✅ Video file verified successfully: {path}")
            return True
            
        except subprocess.TimeoutExpired:
            print(f"❌ Video validation timed out")
            return False
        except Exception as e:
            print(f"❌ Video validation error: {e}")
            return False

    async def _analyze_content_with_chatgpt(self, transcription: TranscriptionResult) -> List[HighlightSegment]:
        """Use ChatGPT to analyze content quality and identify the best moments"""
        try:
            from openai import OpenAI
            
            if not settings.openai_api_key:
                print("⚠️ OpenAI API key not available, skipping ChatGPT analysis")
                return []
            
            print("🤖 Starting ChatGPT content analysis...")
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Add timeout wrapper for the entire analysis (reduced from 2 minutes to 30 seconds)
            return await asyncio.wait_for(self._perform_chatgpt_analysis(client, transcription), timeout=30.0)
            
        except asyncio.TimeoutError:
            print("⚠️ ChatGPT analysis timed out after 2 minutes, continuing without AI analysis...")
            return []
        except Exception as e:
            print(f"⚠️ ChatGPT analysis failed: {e}")
            print(f"⚠️ Continuing without AI analysis...")
            return []

    async def _perform_chatgpt_analysis(self, client, transcription: TranscriptionResult) -> List[HighlightSegment]:
        """Perform the actual ChatGPT analysis"""
        # Prepare transcript for analysis
        full_text = ""
        if hasattr(transcription, 'segments') and transcription.segments:
            for segment in transcription.segments:
                if 'text' in segment:
                    full_text += segment['text'] + " "
        
        if not full_text.strip():
            print("⚠️ No transcript text available for ChatGPT analysis")
            return []
        
        # Create optimized prompt for faster analysis
        prompt = f"""
        Find the 3 MOST VIRAL moments in this gaming transcript for TikTok/Reels. Look for:
        - Funny reactions or surprises
        - Intense gameplay wins/losses
        - Memorable quotes
        - Moments people would share
        
        IMPORTANT: Each clip should be {settings.target_clip_duration} seconds (±{settings.snap_max_overhang}s) and end on natural boundaries:
        - Prefer endings at sentence end or audio pause
        - May extend up to {settings.snap_max_overhang} seconds beyond target to land cleanly
        - Ensure minimum duration of {settings.min_clip_duration}s and maximum of {settings.max_clip_duration}s
        
        Transcript: {full_text[:2000]}...
        
        Return ONLY JSON with start_time, end_time, reason, confidence (0.8-1.0):
        [
            {{"start_time": float, "end_time": float, "reason": "string", "confidence": float}}
        ]
        """
        
        # Call ChatGPT (synchronous call wrapped in asyncio)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,  # Reduced for faster response
                temperature=0.3   # Lower temperature for more focused output
            )
        )
        
        # Parse response
        try:
            content = response.choices[0].message.content
            # Extract JSON from response
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                import json
                ai_analysis = json.loads(json_str)
                
                # Convert to HighlightSegment objects
                highlights = []
                for item in ai_analysis:
                    if 'start_time' in item and 'end_time' in item:
                        highlight = HighlightSegment(
                            start_time=float(item['start_time']),
                            end_time=float(item['end_time']),
                            duration=float(item['end_time']) - float(item['start_time']),
                            confidence_score=float(item.get('confidence', 0.8)),
                            keywords=["ai_analyzed", "viral_potential"],
                            transcript_segment=item.get('reason', 'AI-identified engaging moment'),
                            detection_method="chatgpt_analysis"
                        )
                        highlights.append(highlight)
                
                print(f"🤖 ChatGPT identified {len(highlights)} high-quality moments")
                return highlights
                
        except Exception as e:
            print(f"⚠️ Failed to parse ChatGPT response: {e}")
            return []

    async def _score_viral(self, transcription: TranscriptionResult, video_path: str) -> List[HighlightSegment]:
        """Score video content against viral vector using the Viral Similarity Engine."""
        try:
            print("🚀 Starting viral similarity scoring...")
            
            # Get video duration
            video_duration = transcription.duration
            
            # Create caption windows
            windows = window_captions(
                segments=transcription.segments,
                start=0,
                end=video_duration,
                window_sec=settings.viral_window_sec,
                hop_sec=settings.viral_window_hop
            )
            
            if not windows:
                print("🚀 No caption windows created for viral scoring")
                return []
            
            print(f"🚀 Created {len(windows)} caption windows for viral scoring")
            
            # Score windows against viral vector
            scored_windows = await score_windows_against_viral_vector(windows)
            
            if not scored_windows:
                print("🚀 No scored windows from viral similarity")
                return []
            
            # Filter by minimum score and keep top K
            top_windows = filter_windows_by_score(
                scored_windows, 
                settings.viral_min_score, 
                settings.viral_top_k
            )
            
            print(f"🚀 Viral similarity found {len(top_windows)} high-scoring windows")
            
            # Convert to HighlightSegment objects
            viral_highlights = create_highlight_segments_from_windows(
                top_windows, 
                video_duration,
                padding=2.0  # Add 2 seconds padding
            )
            
            # Convert to HighlightSegment objects
            highlights = []
            for segment_data in viral_highlights:
                highlight = HighlightSegment(
                    start_time=segment_data["start_time"],
                    end_time=segment_data["end_time"],
                    duration=segment_data["end_time"] - segment_data["start_time"],
                    confidence_score=segment_data["confidence_score"],
                    keywords=segment_data["keywords"],
                    transcript_segment=segment_data["text"],
                    detection_method="viral_similarity"
                )
                highlights.append(highlight)
            
            print(f"🚀 Viral similarity engine generated {len(highlights)} highlight segments")
            return highlights
            
        except Exception as e:
            print(f"⚠️ Viral similarity scoring failed: {e}")
            return []

    async def _rank_for_shorts_advanced(self, segments: List[HighlightSegment], 
                                       transcription: TranscriptionResult, 
                                       video_path: str) -> List[HighlightSegment]:
        """Advanced ranking system for short-form content optimization"""
        print("🏆 Starting advanced ranking for short-form content...")
        
        if not segments:
            return []
        
        # Enhanced scoring system
        total_segments = len(segments)
        print(f"📊 Processing {total_segments} segments for ranking...")
        
        for i, segment in enumerate(segments):
            if i % 50 == 0:  # Progress update every 50 segments
                print(f"📊 Ranking progress: {i}/{total_segments} segments processed...")
            
            base_score = segment.confidence_score
            
            # 1. Duration optimization using new duration preference function
            duration_score = duration_preference(
                segment.duration, 
                settings.target_clip_duration, 
                settings.min_clip_duration, 
                settings.max_clip_duration
            )
            
            # 2. Position scoring (middle content often better than beginning/end)
            video_duration = 0
            try:
                # Get video duration using ffprobe
                cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", video_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    video_duration = float(result.stdout.strip())
            except:
                video_duration = 300  # Default 5 minutes
            
            if video_duration > 0:
                segment_center = (segment.start_time + segment.end_time) / 2
                video_center = video_duration / 2
                position_diff = abs(segment_center - video_center) / video_center
                position_score = 1.0 - (position_diff * 0.3)  # Middle content gets bonus
            else:
                position_score = 1.0
            
            # 3. Content diversity (avoid overlapping segments)
            diversity_score = 1.0
            for other_segment in segments:
                if other_segment != segment:
                    overlap = min(segment.end_time, other_segment.end_time) - max(segment.start_time, other_segment.start_time)
                    if overlap > 0:
                        diversity_score *= 0.8  # Penalty for overlap
            
            # 4. Transcript quality (more text = better)
            transcript_score = 1.0
            if hasattr(transcription, 'segments'):
                relevant_text = ""
                for seg in transcription.segments:
                    if 'start' in seg and 'end' in seg:
                        if (seg['start'] >= segment.start_time and seg['end'] <= segment.end_time):
                            relevant_text += seg.get('text', '')
                
                if len(relevant_text.strip()) > 50:
                    transcript_score = 1.2  # Good amount of dialogue
                elif len(relevant_text.strip()) > 20:
                    transcript_score = 1.0  # Moderate dialogue
                else:
                    transcript_score = 0.7  # Little dialogue
            
            # 5. Viral similarity boost
            viral_boost = 1.0
            if hasattr(segment, 'keywords') and "viral_similarity" in segment.keywords:
                viral_boost = 1.15  # 15% boost for viral similarity segments
                print(f"🚀 Viral similarity boost applied to segment {segment.start_time:.1f}s-{segment.end_time:.1f}s")
            
            # Calculate final weighted score
            final_score = base_score * duration_score * position_score * diversity_score * transcript_score * viral_boost
            segment.confidence_score = final_score
            
            print(f"📊 Segment {segment.start_time:.1f}s-{segment.end_time:.1f}s: "
                  f"base={base_score:.2f}, duration={duration_score:.2f}, "
                  f"position={position_score:.2f}, diversity={diversity_score:.2f}, "
                  f"transcript={transcript_score:.2f}, final={final_score:.2f}")
        
        # Sort by final score and remove overlaps
        segments.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Smart overlap removal
        final_segments = []
        for segment in segments:
            overlap_found = False
            for existing in final_segments:
                overlap = min(segment.end_time, existing.end_time) - max(segment.start_time, existing.start_time)
                if overlap > 5:  # 5 second overlap threshold
                    overlap_found = True
                    break
            
            if not overlap_found:
                final_segments.append(segment)
                if len(final_segments) >= settings.num_clips:
                    break
        
        print(f"🏆 Advanced ranking complete: {len(final_segments)} segments selected")
        return final_segments

    def _sec_to_vtt(self, t: float) -> str:
        """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)"""
        from datetime import timedelta
        td = timedelta(seconds=float(t))
        s = str(td)
        if "." not in s:
            s += ".000"
        return s.replace(",", ".")  # VTT needs dot millis
    
    def _sec_to_srt(self, t: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
        hours = int(t // 3600)
        minutes = int((t % 3600) // 60)
        seconds = int(t % 60)
        milliseconds = int((t % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def _sec_to_ass(self, t: float) -> str:
        """Convert seconds to ASS timestamp format (H:MM:SS.cc)"""
        hh = int(t // 3600)
        mm = int((t % 3600) // 60)
        ss = int(t % 60)
        cc = int((t % 1) * 100)
        return f"{hh}:{mm:02d}:{ss:02d}.{cc:02d}"

    async def _export_sidecar_captions(
        self, 
        base_path: str, 
        transcription: TranscriptionResult, 
        start: float, 
        end: float
    ) -> dict:
        """
        Exports sidecar transcript files:
          - WebVTT: base_path + ".vtt"
          - ASS:    base_path + ".ass" (styled subtitles)
          - SRT:    base_path + ".srt" (standard subtitles)
          - JSON:   base_path + ".json" (metadata)
        Pulls segments overlapping [start,end] and adjusts timing to be clip-relative.
        """
        import re
        try:
            # Apply caption lead-in timing (fixes Whisper's natural lag ~120-220ms)
            lead = getattr(settings, "caption_lead_sec", 0.18)
            min_dur = getattr(settings, "min_caption_dur", 0.12)
            
            segs = []
            for seg in getattr(transcription, "segments", []) or []:
                s, e = seg.get("start"), seg.get("end")
                if s is None or e is None: 
                    continue
                if e <= start or s >= end:
                    continue
                # Apply lead-in and ensure clip-relative timing
                start_relative = max(0.0, (s - start) - lead)
                end_relative = max(0.01, (e - start) - lead)
                
                segs.append({
                    "start": start_relative,
                    "end": end_relative,
                    "text": (seg.get("text") or "").strip()
                })
            
            # Enforce minimum on-screen time & monotonicity
            for sg in segs:
                if sg["end"] - sg["start"] < min_dur:
                    sg["end"] = min(sg["start"] + min_dur, (end - start))
            
            # Ensure segments are in chronological order
            segs.sort(key=lambda x: x["start"])
            
            # WebVTT format
            vtt_path = base_path + ".vtt"
            vtt_lines = ["WEBVTT\n"]
            for i, sg in enumerate(segs, 1):
                vtt_lines.append(str(i))
                vtt_lines.append(f"{self._sec_to_vtt(sg['start'])} --> {self._sec_to_vtt(sg['end'])}")
                vtt_lines.append(re.sub(r"\s+", " ", sg["text"]))
                vtt_lines.append("")
            
            async with aiofiles.open(vtt_path, "w", encoding="utf-8") as f:
                await f.write("\n".join(vtt_lines))

            # SRT format
            srt_path = base_path + ".srt"
            srt_lines = []
            for i, sg in enumerate(segs, 1):
                srt_lines.append(str(i))
                srt_lines.append(f"{self._sec_to_srt(sg['start'])} --> {self._sec_to_srt(sg['end'])}")
                srt_lines.append(re.sub(r"\s+", " ", sg["text"]))
                srt_lines.append("")
            
            async with aiofiles.open(srt_path, "w", encoding="utf-8") as f:
                await f.write("\n".join(srt_lines))

            # ASS format (styled subtitles)
            ass_path = base_path + ".ass"
            # Default ASS style configuration
            font_name = getattr(settings, "caption_font", "Arial")
            font_size = getattr(settings, "caption_fontsize_vertical", 44)
            outline = getattr(settings, "caption_outline", 3)
            shadow = getattr(settings, "caption_shadow", 1)
            safe_bottom = getattr(settings, "vertical_safe_bottom", 260)
            
            style = (
                "[Script Info]\n"
                "ScriptType: v4.00+\n"
                "PlayResX: 1080\n"
                "PlayResY: 1920\n"
                "\n[V4+ Styles]\n"
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
                "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                "Alignment, MarginL, MarginR, MarginV, Encoding\n"
                f"Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
                f"1,0,0,0,100,100,0,0,1,{outline},{shadow},"
                f"2,40,40,{safe_bottom},1\n"
                "\n[Events]\n"
                "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            )
            ass_lines = [style]
            for sg in segs:
                ass_lines.append(
                    f"Dialogue: 0,{self._sec_to_ass(sg['start'])},{self._sec_to_ass(sg['end'])},Default,,0,0,{safe_bottom},,"
                    + re.sub(r"\s+", " ", sg["text"])
                )
            
            # Add trailing newline for proper file formatting
            ass_lines.append("")
            
            async with aiofiles.open(ass_path, "w", encoding="utf-8") as f:
                await f.write("\n".join(ass_lines))

            # JSON metadata
            meta = {
                "clip_start": start,
                "clip_end": end,
                "duration": end - start,
                "segments": segs,
                "keywords": [],
                "transcript_files": {
                    "vtt": os.path.basename(vtt_path),
                    "srt": os.path.basename(srt_path),
                    "ass": os.path.basename(ass_path),
                    "json": os.path.basename(base_path + ".json")
                }
            }
            json_path = base_path + ".json"
            async with aiofiles.open(json_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(meta, ensure_ascii=False, indent=2))
            
            print(f"📝 Transcript files exported: VTT, SRT, ASS, JSON")
            return {"vtt": vtt_path, "srt": srt_path, "ass": ass_path, "json": json_path}
            
        except Exception as e:
            print(f"⚠️ Transcript file export failed: {e}")
            import traceback
            traceback.print_exc()
            return {}





    # Caption rendering methods removed - now handled by external caption repository


