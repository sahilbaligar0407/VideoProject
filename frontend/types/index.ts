export interface VideoProcessingResponse {
  request_id: string;
  status: string;
  message: string;
  clips?: GeneratedClip[];
  error?: string;
}

export interface ProcessingStatus {
  status: string;
  progress: number;
  message: string;
  current_step: string;
  estimated_time?: number;
  clips?: GeneratedClip[];
  error?: string;
}

export interface GeneratedClip {
  clip_id: string;
  start_time: number;
  end_time: number;
  duration: number;
  file_path: string;
  thumbnail_path?: string;
  caption_text: string;
  download_url: string;
}

export interface VideoInputFormProps {
  onProcessingStart: (requestId: string) => void;
}

export interface ProcessingStatusProps {
  requestId: string;
  onStatusUpdate: (status: ProcessingStatus) => void;
  onComplete: (clips: GeneratedClip[]) => void;
}

export interface GeneratedClipsProps {
  clips: GeneratedClip[];
}
