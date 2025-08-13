import { useState } from 'react';
import Head from 'next/head';
import VideoInputForm from '../components/VideoInputForm';
import ProcessingStatus from '../components/ProcessingStatus';
import GeneratedClips from '../components/GeneratedClips';
import { VideoProcessingResponse } from '../types';

export default function Home() {
  const [processingRequest, setProcessingRequest] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<any>(null);
  const [generatedClips, setGeneratedClips] = useState<any[]>([]);

  const handleProcessingComplete = (clips: any[]) => {
    console.log('🎉 Processing completed! Received clips:', clips);
    console.log('📊 Clips details:', clips.map((clip, index) => ({
      index: index + 1,
      id: clip.clip_id,
      file_path: clip.file_path,
      download_url: clip.download_url,
      duration: clip.duration
    })));
    
    setGeneratedClips(clips);
    setProcessingStatus({ status: 'completed', progress: 100 });
  };

  return (
    <>
      <Head>
        <title>ClipGenius - AI Video Highlight Generator</title>
        <meta name="description" content="Generate AI-powered video highlights with automatic transcription and captions" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              ClipGenius
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Transform your videos into engaging highlights with AI-powered transcription, 
              automatic highlight detection, and professional captions.
            </p>
          </div>

          {/* Main Content */}
          <div className="max-w-4xl mx-auto">
            {!processingRequest ? (
              <VideoInputForm 
                onProcessingStart={(requestId) => {
                  setProcessingRequest(requestId);
                  setProcessingStatus({ status: 'processing', progress: 0 });
                }}
              />
            ) : (
              <div className="space-y-8">
                <ProcessingStatus 
                  requestId={processingRequest}
                  onStatusUpdate={setProcessingStatus}
                  onComplete={handleProcessingComplete}
                />
                
                {processingStatus?.status === 'completed' && generatedClips.length > 0 && (
                  <GeneratedClips clips={generatedClips} />
                )}
                
                {processingStatus?.status === 'failed' && (
                  <div className="card bg-red-50 border-red-200">
                    <div className="text-red-800">
                      <h3 className="font-semibold mb-2">Processing Failed</h3>
                      <p>{processingStatus.error || 'An error occurred during processing.'}</p>
                    </div>
                  </div>
                )}
                
                <div className="text-center">
                  <button
                    onClick={() => {
                      setProcessingRequest(null);
                      setProcessingStatus(null);
                      setGeneratedClips([]);
                    }}
                    className="btn-secondary"
                  >
                    Process Another Video
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
