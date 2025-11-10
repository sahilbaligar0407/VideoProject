import { useState, useRef } from 'react';
import { Upload, Youtube, Play, Download, FileVideo } from 'lucide-react';

interface VideoInputFormProps {
  onProcessingStart: (requestId: string) => void;
}

const VideoInputForm: React.FC<VideoInputFormProps> = ({ onProcessingStart }) => {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<'youtube' | 'upload'>('youtube');
  const [addCaptions, setAddCaptions] = useState(true);
  const [userTopics, setUserTopics] = useState('');
  const [vertical, setVertical] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setSelectedFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (activeTab === 'youtube' && !youtubeUrl.trim()) {
      alert('Please enter a YouTube URL');
      return;
    }
    
    if (activeTab === 'upload' && !selectedFile) {
      alert('Please select a video file');
      return;
    }

    setIsProcessing(true);

    try {
      const formData = new FormData();
      
      if (activeTab === 'youtube') {
        formData.append('youtube_url', youtubeUrl.trim());
      } else {
        formData.append('video_file', selectedFile!);
      }
      
      formData.append('add_captions', addCaptions.toString());
      if (userTopics.trim()) {
        formData.append('user_topics', userTopics.trim());
      }
      formData.append('vertical', vertical.toString());

      const response = await fetch('/api/v1/process-video', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Processing started:', data);
      
      onProcessingStart(data.request_id);
      
      // Reset form
      setYoutubeUrl('');
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
    } catch (error) {
      console.error('Error starting processing:', error);
      alert('Failed to start video processing. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTabChange = (tab: 'youtube' | 'upload') => {
    setActiveTab(tab);
    // Reset form when switching tabs
    setYoutubeUrl('');
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">🎬 ClipGenius</h2>
        <p className="text-gray-600">Transform your videos into engaging short-form content</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
        <button
          type="button"
          onClick={() => handleTabChange('youtube')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'youtube'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Youtube className="w-4 h-4 inline mr-2" />
          YouTube URL
        </button>
        <button
          type="button"
          onClick={() => handleTabChange('upload')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'upload'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Upload className="w-4 h-4 inline mr-2" />
          Upload File
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* YouTube URL Input */}
        {activeTab === 'youtube' && (
          <div className="space-y-2">
            <label htmlFor="youtubeUrl" className="block text-sm font-medium text-gray-700">
              YouTube Video URL
            </label>
            <input
              type="url"
              id="youtubeUrl"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="input-field"
              required
            />
          </div>
        )}

        {/* File Upload Input */}
        {activeTab === 'upload' && (
          <div className="space-y-2">
            <label htmlFor="videoFile" className="block text-sm font-medium text-gray-700">
              Video File
            </label>
            <input
              ref={fileInputRef}
              type="file"
              id="videoFile"
              accept="video/*"
              onChange={handleFileSelect}
              className="input-field"
              required
            />
            <p className="text-sm text-gray-500">
              Supported formats: MP4, MOV, AVI, MKV (Max 500MB)
            </p>
          </div>
        )}

        {/* Caption Toggle */}
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="addCaptions"
              checked={addCaptions}
              onChange={(e) => setAddCaptions(e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
            />
            <label htmlFor="addCaptions" className="text-sm font-medium text-blue-900">
              📝 Add Captions to Clips
            </label>
          </div>
          <p className="text-sm text-blue-700 mt-1 ml-7">
            Automatically generate and burn in captions from the video transcript
          </p>
          
        </div>

        {/* User Topics Input */}
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <label htmlFor="userTopics" className="block text-sm font-medium text-green-900 mb-2">
            🎯 Find Clips About (Optional)
          </label>
          <input
            type="text"
            id="userTopics"
            value={userTopics}
            onChange={(e) => setUserTopics(e.target.value)}
            placeholder="e.g., pricing, onboarding, features (comma-separated)"
            className="input-field w-full"
          />
          <p className="text-sm text-green-700 mt-1">
            Leave empty to use AI highlight detection, or specify topics to find specific content
          </p>
        </div>

        {/* Vertical Output Toggle */}
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="vertical"
              checked={vertical}
              onChange={(e) => setVertical(e.target.checked)}
              className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 focus:ring-2"
            />
            <label htmlFor="vertical" className="text-sm font-medium text-purple-900">
              📱 Vertical Output (9:16)
            </label>
          </div>
          <p className="text-sm text-purple-700 mt-1 ml-7">
            Generate clips in vertical format optimized for TikTok, Instagram Reels, and YouTube Shorts
          </p>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isProcessing}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isProcessing ? (
            <span className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Processing...
            </span>
          ) : (
            <span className="flex items-center justify-center">
              <Play className="w-5 h-5 mr-2" />
              Generate Clips
            </span>
          )}
        </button>
      </form>

      {/* Features Preview */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">✨ What You'll Get</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-green-600 text-sm font-bold">🎯</span>
            </div>
            <h4 className="font-medium text-gray-900">Topic Search</h4>
            <p className="text-sm text-gray-600">Find clips about specific topics or keywords</p>
          </div>
          <div className="text-center">
            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-purple-600 text-sm font-bold">📱</span>
            </div>
            <h4 className="font-medium text-gray-900">Vertical Format</h4>
            <p className="text-sm text-gray-600">9:16 aspect ratio for social media</p>
          </div>
          <div className="text-center">
            <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-orange-600 text-sm font-bold">🔍</span>
            </div>
            <h4 className="font-medium text-gray-900">Smart Endings</h4>
            <p className="text-sm text-gray-600">Clean cuts at natural boundaries</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoInputForm;
