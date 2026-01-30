export interface FileInfo {
  filename: string;
  file_type: 'nifti' | 'image';
  dimensions: number[];
  num_slices: number;
}

export interface UploadResponse {
  session_id: string;
  file_info: FileInfo;
  message: string;
}

export interface ClassStatistics {
  class_id: number;
  class_name: string;
  pixel_count: number;
  percentage: number;
  color: number[];
}

export interface SegmentationResponse {
  session_id: string;
  num_slices_processed: number;
  statistics: ClassStatistics[];
  processing_time_ms: number;
}

export interface SliceData {
  original_image: string;
  segmentation_mask: string;
  overlay_image: string;
  slice_index: number;
  statistics: ClassStatistics[];
}

export interface ResultsResponse {
  session_id: string;
  slice_data: SliceData;
  total_slices: number;
  file_type: string;
}

export interface ClassInfo {
  id: number;
  name: string;
  full_name: string;
  color: number[];
  hex_color: string;
}

export type ViewMode = 'original' | 'mask' | 'overlay' | 'side-by-side';
