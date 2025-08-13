import { useState } from 'react';
import { GeneratedClipsProps } from '../types';
import { Download, Play, Clock, FileVideo } from 'lucide-react';

const GeneratedClips: React.FC<GeneratedClipsProps> = ({ clips }) => {
  const [downloadingClips, setDownloadingClips] = useState<Set<string>>(new Set());

  // Debug logging when clips are received
  console.log('🔍 GeneratedClips received:', clips);
  clips.forEach((clip, index) => {
    console.log(`📹 Clip ${index + 1}:`, {
      id: clip.clip_id,
      file_path: clip.file_path,
      download_url: clip.download_url,
      duration: clip.duration,
      start_time: clip.start_time,
      end_time: clip.end_time
    });
  });

  const handleDownload = async (clip: any) => {
    if (downloadingClips.has(clip.clip_id)) return;
    
    console.log(`🚀 Starting download for clip: ${clip.clip_id}`);
    console.log(`📁 Download URL: ${clip.download_url}`);
    console.log(`📂 File path: ${clip.file_path}`);
    
    setDownloadingClips(prev => new Set(prev).add(clip.clip_id));
    
    try {
      // Construct the full download URL
      const downloadUrl = `http://localhost:8000${clip.download_url}`;
      console.log(`🌐 Fetching from full URL: ${downloadUrl}`);
      
      const response = await fetch(downloadUrl, {
        method: 'GET',
        mode: 'cors',
      });
      
      console.log(`📡 Response status: ${response.status}`);
      console.log(`📡 Response headers:`, Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      console.log(`📦 Blob received: ${blob.size} bytes, type: ${blob.type}`);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `clip_${clip.clip_id}.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log(`✅ Download completed successfully for clip: ${clip.clip_id}`);
    } catch (error) {
      console.error('❌ Download failed:', error);
      console.error('❌ Error details:', {
        message: error.message,
        stack: error.stack,
        clip_id: clip.clip_id,
        download_url: clip.download_url
      });
      alert('Download failed. Please try again.');
    } finally {
      setDownloadingClips(prev => {
        const newSet = new Set(prev);
        newSet.delete(clip.clip_id);
        return newSet;
      });
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTimestamp = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="card">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Your Highlight Clips Are Ready! 🎉
        </h2>
        <p className="text-gray-600">
          We've generated {clips.length} highlight clips from your video. 
          Each clip includes burned-in captions and is ready for download.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clips.map((clip, index) => (
          <div key={clip.clip_id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            {/* Clip Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <FileVideo className="w-5 h-5 text-primary-600" />
                <span className="font-semibold text-gray-900">
                  Clip {index + 1}
                </span>
              </div>
              <div className="flex items-center space-x-1 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                <span>{formatTime(clip.duration)}</span>
              </div>
            </div>

            {/* Video Preview Placeholder */}
            <div className="bg-gray-200 rounded-lg h-32 mb-4 flex items-center justify-center">
              <div className="text-center">
                <Play className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">Video Preview</p>
              </div>
            </div>

            {/* Clip Details */}
            <div className="space-y-3 mb-4">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Timeline</p>
                <p className="text-sm text-gray-600">
                  {formatTimestamp(clip.start_time)} → {formatTimestamp(clip.end_time)}
                </p>
              </div>
              
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Captions</p>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {clip.caption_text || 'Generated highlight clip'}
                </p>
              </div>
            </div>

            {/* Download Button */}
            <button
              onClick={() => handleDownload(clip)}
              disabled={downloadingClips.has(clip.clip_id)}
              className="w-full btn-primary flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {downloadingClips.has(clip.clip_id) ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Downloading...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download Clip</span>
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-primary-600">{clips.length}</p>
            <p className="text-sm text-gray-600">Total Clips</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-primary-600">
              {formatTime(clips.reduce((total, clip) => total + clip.duration, 0))}
            </p>
            <p className="text-sm text-gray-600">Total Duration</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-primary-600">
              {Math.round(clips.reduce((total, clip) => total + clip.duration, 0) / clips.length)}
            </p>
            <p className="text-sm text-gray-600">Avg. Clip Length (sec)</p>
          </div>
        </div>
      </div>

      {/* Tips */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">💡 Tips for Best Results</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Each clip is optimized for social media sharing</li>
          <li>• Captions are automatically burned in for accessibility</li>
          <li>• Clips are generated in MP4 format for maximum compatibility</li>
          <li>• Use these highlights for social media, presentations, or marketing</li>
        </ul>
      </div>
    </div>
  );
};

export default GeneratedClips;
