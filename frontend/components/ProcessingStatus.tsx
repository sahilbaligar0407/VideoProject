import { useState, useEffect } from 'react';
import { ProcessingStatusProps, ProcessingStatus as ProcessingStatusType } from '../types';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ 
  requestId, 
  onStatusUpdate, 
  onComplete 
}) => {
  const [status, setStatus] = useState<ProcessingStatusType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pollStatus = async () => {
      try {
        console.log(`🔄 Polling status for request: ${requestId}`);
        const response = await axios.get(`/api/v1/status/${requestId}`);
        const statusData = response.data;
        
        console.log(`📊 Status update:`, statusData);
        
        setStatus(statusData);
        onStatusUpdate(statusData);
        
        // Check if processing is complete
        if (statusData.status === 'completed' && statusData.clips) {
          console.log(`✅ Processing completed! Clips:`, statusData.clips);
          onComplete(statusData.clips);
        } else if (statusData.status === 'failed') {
          console.log(`❌ Processing failed:`, statusData.error);
          setError(statusData.error || 'Processing failed');
        }
        
        // Continue polling if still processing
        if (statusData.status === 'processing') {
          console.log(`⏳ Still processing... Current step: ${statusData.current_step}`);
          setTimeout(pollStatus, 2000); // Poll every 2 seconds
        }
      } catch (err) {
        console.error('❌ Error polling status:', err);
        setError('Failed to get processing status');
      }
    };

    // Start polling immediately
    pollStatus();
  }, [requestId, onStatusUpdate, onComplete]);

  if (error) {
    return (
      <div className="card bg-red-50 border-red-200">
        <div className="flex items-center space-x-3">
          <AlertCircle className="w-6 h-6 text-red-600" />
          <div>
            <h3 className="font-semibold text-red-800">Error</h3>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
          <span className="ml-3 text-gray-600">Loading status...</span>
        </div>
      </div>
    );
  }

  const getStepIcon = (step: string) => {
    const currentStep = status.current_step;
    const stepOrder = [
      'initializing',
      'downloading_youtube',
      'saving_file',
      'processing_video',
      'transcribing',
      'detecting_highlights',
      'generating_clips',
      'adding_captions',
      'completed'
    ];
    
    const stepIndex = stepOrder.indexOf(step);
    const currentIndex = stepOrder.indexOf(currentStep);
    
    if (stepIndex < currentIndex) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (stepIndex === currentIndex) {
      return <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />;
    } else {
      return <div className="w-5 h-5 border-2 border-gray-300 rounded-full" />;
    }
  };

  const getStepLabel = (step: string) => {
    const stepLabels: Record<string, string> = {
      'initializing': 'Initializing',
      'downloading_youtube': 'Downloading YouTube Video',
      'saving_file': 'Saving Uploaded File',
      'processing_video': 'Processing Video',
      'transcribing': 'Transcribing Audio',
      'detecting_highlights': 'Detecting Highlights',
      'generating_clips': 'Generating Clips',
      'adding_captions': 'Adding Captions',
      'completed': 'Completed'
    };
    return stepLabels[step] || step;
  };

  const steps = [
    'initializing',
    'transcribing',
    'detecting_highlights',
    'generating_clips',
    'adding_captions'
  ];

  return (
    <div className="card">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Processing Your Video
        </h2>
        <p className="text-gray-600">
          {status.message}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span>{status.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-primary-600 h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${status.progress}%` }}
          />
        </div>
      </div>

      {/* Processing Steps */}
      <div className="space-y-4">
        {steps.map((step) => (
          <div key={step} className="flex items-center space-x-4">
            {getStepIcon(step)}
            <div className="flex-1">
              <p className="font-medium text-gray-900">
                {getStepLabel(step)}
              </p>
              {step === status.current_step && (
                <p className="text-sm text-gray-600">
                  {status.message}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Current Status */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center space-x-3">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
          <div>
            <p className="font-medium text-blue-900">Current Step</p>
            <p className="text-sm text-blue-700">
              {getStepLabel(status.current_step)}
            </p>
          </div>
        </div>
      </div>

      {/* Estimated Time (if available) */}
      {status.estimated_time && (
        <div className="mt-4 text-center text-sm text-gray-600">
          Estimated time remaining: {Math.ceil(status.estimated_time / 60)} minutes
        </div>
      )}
    </div>
  );
};

export default ProcessingStatus;
