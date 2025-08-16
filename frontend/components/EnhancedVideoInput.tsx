import React, { useState } from 'react';
import { Upload, Video, Settings, Play, Eye, Brain, Captions, Palette } from 'lucide-react';

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

const EnhancedVideoInput: React.FC = () => {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [topics, setTopics] = useState('');
  const [activeTab, setActiveTab] = useState<'upload' | 'youtube'>('upload');
  
  // Pipeline configuration
  const [config, setConfig] = useState<PipelineConfig>({
    captions: {
      mode: 'sidecar',
      language: 'auto',
      style: 'default',
      safe_bottom: 160,
      max_lines: 2,
      word_by_word: false
    },
    background: {
      mode: 'blur',
      mute: true,
      blur_strength: 40
    },
    face_tracking: {
      enabled: true,
      min_confidence: 0.5,
      smoothing_window: 5,
      transition_duration: 0.4
    },
    ai: {
      auto_titles: true,
      cta: 'auto',
      model: 'gpt-4o',
      temperature: 0.7
    },
    video: {
      duration_target: 28.0,
      fps: 30,
      resolution: '1080x1920',
      quality: 'high'
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setVideoFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!videoFile && !youtubeUrl) {
      alert('Please select a video file or enter a YouTube URL');
      return;
    }

    setIsProcessing(true);
    
    try {
      const formData = new FormData();
      
      if (videoFile) {
        formData.append('video_file', videoFile);
      } else {
        // For YouTube URLs, we'd need to handle differently
        // For now, just show an alert
        alert('YouTube URL processing not yet implemented in enhanced pipeline');
        setIsProcessing(false);
        return;
      }
      
      formData.append('config_json', JSON.stringify(config));
      if (topics.trim()) {
        formData.append('topics', topics.trim());
      }

      const response = await fetch('/api/v1/clips/generate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setRequestId(result.request_id);
      
      // Start polling for status
      pollStatus(result.request_id);
      
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to start processing');
      setIsProcessing(false);
    }
  };

  const pollStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/clips/status/${id}`);
        const status = await response.json();
        
        if (status.status === 'completed') {
          setIsProcessing(false);
          clearInterval(interval);
          alert(`Processing complete! Generated ${status.clips?.length || 0} clips.`);
        } else if (status.status === 'failed') {
          setIsProcessing(false);
          clearInterval(interval);
          alert(`Processing failed: ${status.message}`);
        }
      } catch (error) {
        console.error('Status polling error:', error);
      }
    }, 2000);
  };

  const updateConfig = (section: keyof PipelineConfig, key: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          ClipGenius Pipeline v2
        </h1>
        <p className="text-gray-600">
          Advanced AI-powered video clip generation with face tracking, dynamic layouts, and viral optimization
        </p>
      </div>

      {/* Input Tabs */}
      <div className="flex mb-6 border-b">
        <button
          className={`px-4 py-2 font-medium ${
            activeTab === 'upload'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setActiveTab('upload')}
        >
          <Upload className="inline w-4 h-4 mr-2" />
          Upload Video
        </button>
        <button
          className={`px-4 py-2 font-medium ${
            activeTab === 'youtube'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setActiveTab('youtube')}
        >
          <Video className="inline w-4 h-4 mr-2" />
          YouTube URL
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Video Input */}
        {activeTab === 'upload' ? (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <input
              type="file"
              accept="video/*"
              onChange={handleFileChange}
              className="hidden"
              id="video-upload"
            />
            <label htmlFor="video-upload" className="cursor-pointer">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-600">
                {videoFile ? videoFile.name : 'Click to upload video file'}
              </p>
            </label>
          </div>
        ) : (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              YouTube URL
            </label>
            <input
              type="url"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        {/* Topics */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Content Topics (optional)
          </label>
          <input
            type="text"
            value={topics}
            onChange={(e) => setTopics(e.target.value)}
            placeholder="gaming, tutorial, comedy, etc."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Configuration Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Captions Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
              <Captions className="w-5 h-5 mr-2" />
              Captions
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Mode</label>
                <select
                  value={config.captions.mode}
                  onChange={(e) => updateConfig('captions', 'mode', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="sidecar">Sidecar (VTT/ASS/JSON)</option>
                  <option value="burn">Burn In</option>
                  <option value="off">No Captions</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Language</label>
                <select
                  value={config.captions.language}
                  onChange={(e) => updateConfig('captions', 'language', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="auto">Auto-detect</option>
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Style</label>
                <select
                  value={config.captions.style}
                  onChange={(e) => updateConfig('captions', 'style', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="default">Default</option>
                  <option value="boxed">Boxed</option>
                  <option value="outline">Outline</option>
                  <option value="karaoke">Karaoke</option>
                </select>
              </div>
            </div>
          </div>

          {/* Background Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
              <Palette className="w-5 h-5 mr-2" />
              Background
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Mode</label>
                <select
                  value={config.background.mode}
                  onChange={(e) => updateConfig('background', 'mode', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="blur">Blur Background</option>
                  <option value="gameplay">Gameplay Background</option>
                  <option value="none">No Background</option>
                </select>
              </div>

              {config.background.mode === 'gameplay' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Theme</label>
                  <select
                    value={config.background.game || 'subway'}
                    onChange={(e) => updateConfig('background', 'game', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="subway">Subway Surfers</option>
                    <option value="templerun">Temple Run</option>
                    <option value="minecraft">Minecraft Parkour</option>
                  </select>
                </div>
              )}

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="mute-bg"
                  checked={config.background.mute}
                  onChange={(e) => updateConfig('background', 'mute', e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="mute-bg" className="text-sm text-gray-700">
                  Mute background audio
                </label>
              </div>
            </div>
          </div>

          {/* Face Tracking Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
              <Eye className="w-5 h-5 mr-2" />
              Face Tracking
            </h3>
            <div className="space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="face-tracking"
                  checked={config.face_tracking.enabled}
                  onChange={(e) => updateConfig('face_tracking', 'enabled', e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="face-tracking" className="text-sm text-gray-700">
                  Enable face tracking
                </label>
              </div>

              {config.face_tracking.enabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Confidence Threshold: {config.face_tracking.min_confidence}
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="0.9"
                      step="0.1"
                      value={config.face_tracking.min_confidence}
                      onChange={(e) => updateConfig('face_tracking', 'min_confidence', parseFloat(e.target.value))}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Transition Duration: {config.face_tracking.transition_duration}s
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="1.0"
                      step="0.1"
                      value={config.face_tracking.transition_duration}
                      onChange={(e) => updateConfig('face_tracking', 'transition_duration', parseFloat(e.target.value))}
                      className="w-full"
                    />
                  </div>
                </>
              )}
            </div>
          </div>

          {/* AI Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
              <Brain className="w-5 h-5 mr-2" />
              AI Features
            </h3>
            <div className="space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto-titles"
                  checked={config.ai.auto_titles}
                  onChange={(e) => updateConfig('ai', 'auto_titles', e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="auto-titles" className="text-sm text-gray-700">
                  Generate titles & CTAs
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Call-to-Action</label>
                <select
                  value={config.ai.cta}
                  onChange={(e) => updateConfig('ai', 'cta', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="auto">Auto</option>
                  <option value="subscribe">Subscribe</option>
                  <option value="follow">Follow</option>
                  <option value="comment">Comment</option>
                  <option value="like">Like</option>
                  <option value="share">Share</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">AI Model</label>
                <select
                  value={config.ai.model}
                  onChange={(e) => updateConfig('ai', 'model', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Video Output Configuration */}
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-lg font-medium text-blue-900 mb-3 flex items-center">
            <Play className="w-5 h-5 mr-2" />
            Video Output
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-blue-800">Duration Target</label>
              <input
                type="number"
                min="10"
                max="60"
                step="1"
                value={config.video.duration_target}
                onChange={(e) => updateConfig('video', 'duration_target', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-blue-300 rounded-md text-sm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-blue-800">FPS</label>
              <select
                value={config.video.fps}
                onChange={(e) => updateConfig('video', 'fps', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-blue-300 rounded-md text-sm"
              >
                <option value="24">24</option>
                <option value="25">25</option>
                <option value="30">30</option>
                <option value="50">50</option>
                <option value="60">60</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-blue-800">Quality</label>
              <select
                value={config.video.quality}
                onChange={(e) => updateConfig('video', 'quality', e.target.value)}
                className="w-full px-3 py-2 border border-blue-300 rounded-md text-sm"
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-blue-800">Resolution</label>
              <div className="text-sm text-blue-700 font-medium">
                {config.video.resolution}
              </div>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="text-center">
          <button
            type="submit"
            disabled={isProcessing || (!videoFile && !youtubeUrl)}
            className={`px-8 py-3 rounded-lg font-medium text-white ${
              isProcessing || (!videoFile && !youtubeUrl)
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isProcessing ? (
              <>
                <Play className="inline w-5 h-5 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Play className="inline w-5 h-5 mr-2" />
                Generate Enhanced Clips
              </>
            )}
          </button>
        </div>
      </form>

      {/* Processing Status */}
      {requestId && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-lg font-medium text-green-900 mb-2">
            Processing Started
          </h3>
          <p className="text-green-700">
            Request ID: {requestId}
          </p>
          <p className="text-green-600 text-sm">
            Check the status endpoint for progress updates
          </p>
        </div>
      )}
    </div>
  );
};

export default EnhancedVideoInput;
