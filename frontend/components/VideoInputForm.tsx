import { useState, useRef } from 'react';
import { Upload, Link, Video, FileVideo } from 'lucide-react';
import { VideoInputFormProps } from '../types';
import axios from 'axios';

const VideoInputForm: React.FC<VideoInputFormProps> = ({ onProcessingStart }) => {
  const [inputMethod, setInputMethod] = useState<'youtube' | 'file'>('youtube');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [addCaptions, setAddCaptions] = useState(true); // Default to true for gaming clips
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (inputMethod === 'youtube' && !youtubeUrl.trim()) {
      alert('Please enter a YouTube URL');
      return;
    }
    
    if (inputMethod === 'file' && !selectedFile) {
      alert('Please select a video file');
      return;
    }

    setIsProcessing(true);

    try {
      const formData = new FormData();
      
      if (inputMethod === 'youtube') {
        formData.append('youtube_url', youtubeUrl);
      } else {
        formData.append('video_file', selectedFile!);
      }
      
      // Add caption preference
      formData.append('add_captions', addCaptions.toString());

      const response = await axios.post('/api/v1/process-video', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.request_id) {
        onProcessingStart(response.data.request_id);
      }
    } catch (error) {
      console.error('Error starting processing:', error);
      alert('Failed to start video processing. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileSelect = (file: File) => {
    // Validate file type
    const validTypes = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!validTypes.includes(fileExtension)) {
      alert('Please select a valid video file format (MP4, AVI, MOV, MKV, WMV, FLV)');
      return;
    }

    // Validate file size (500MB limit)
    if (file.size > 500 * 1024 * 1024) {
      alert('File size must be less than 500MB');
      return;
    }

    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="card">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Generate Video Highlights
        </h2>
        <p className="text-gray-600">
          Choose your input method and let AI create engaging highlight clips
        </p>
      </div>

      {/* Input Method Tabs */}
      <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setInputMethod('youtube')}
          className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md transition-colors ${
            inputMethod === 'youtube'
              ? 'bg-white text-primary-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Link className="w-4 h-4 mr-2" />
          YouTube URL
        </button>
        <button
          onClick={() => setInputMethod('file')}
          className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md transition-colors ${
            inputMethod === 'file'
              ? 'bg-white text-primary-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Upload className="w-4 h-4 mr-2" />
          Upload File
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Caption Toggle */}
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="addCaptions"
              checked={addCaptions}
              onChange={(e) => setAddCaptions(e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 focus:ring-2"
            />
            <label htmlFor="addCaptions" className="text-sm font-medium text-blue-900">
              Add Captions to Clips
            </label>
          </div>
          <p className="text-sm text-blue-700 mt-1 ml-7">
            Burn captions directly into the video for better accessibility and social media sharing
          </p>
        </div>

        {inputMethod === 'youtube' ? (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              YouTube Video URL
            </label>
            <div className="flex space-x-3">
              <input
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="input-field flex-1"
                required
              />
              <button
                type="submit"
                disabled={isProcessing || !youtubeUrl.trim()}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isProcessing ? 'Processing...' : 'Process Video'}
              </button>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Enter a YouTube video URL (you must own the video or have rights to use it)
            </p>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Video File
            </label>
            
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? 'border-primary-400 bg-primary-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                className="hidden"
              />
              
              {selectedFile ? (
                <div className="space-y-3">
                  <FileVideo className="w-12 h-12 text-primary-500 mx-auto" />
                  <div>
                    <p className="font-medium text-gray-900">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedFile(null)}
                    className="text-sm text-red-600 hover:text-red-700"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                  <div>
                    <p className="font-medium text-gray-900">
                      Drop your video file here, or{' '}
                      <button
                        type="button"
                        onClick={openFileDialog}
                        className="text-primary-600 hover:text-primary-700 underline"
                      >
                        browse
                      </button>
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports MP4, AVI, MOV, MKV, WMV, FLV (max 500MB)
                    </p>
                  </div>
                </div>
              )}
            </div>

            {selectedFile && (
              <div className="mt-4 text-center">
                <button
                  type="submit"
                  disabled={isProcessing}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? 'Processing...' : 'Process Video'}
                </button>
              </div>
            )}
          </div>
        )}
      </form>

      {/* Features Preview */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
          What you'll get:
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <Video className="w-8 h-8 text-primary-500 mx-auto mb-2" />
            <h4 className="font-medium text-gray-900">AI Transcription</h4>
            <p className="text-sm text-gray-600">Accurate speech-to-text using OpenAI Whisper</p>
          </div>
          <div className="text-center">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-primary-600 text-sm font-bold">✨</span>
            </div>
            <h4 className="font-medium text-gray-900">Smart Highlights</h4>
            <p className="text-sm text-gray-600">Automatic detection of key moments</p>
          </div>
          <div className="text-center">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-primary-600 text-sm font-bold">📝</span>
            </div>
            <h4 className="font-medium text-gray-900">Auto Captions</h4>
            <p className="text-sm text-gray-600">Professional captions burned into clips</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoInputForm;
