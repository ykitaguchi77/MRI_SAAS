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
  volume_mm3?: number;
  volume_cm3?: number;
}

export interface LRStatistics {
  left: ClassStatistics[];
  right: ClassStatistics[];
}

export interface SegmentationResponse {
  session_id: string;
  num_slices_processed: number;
  statistics: ClassStatistics[];
  processing_time_ms: number;
  lr_statistics?: LRStatistics;
}

export interface SliceData {
  original_image: string;
  segmentation_mask: string;
  overlay_image: string;
  slice_index: number;
  statistics: ClassStatistics[];
  lr_statistics?: LRStatistics;
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

export interface MeshClassData {
  class_id: number;
  class_name: string;
  color: string;
  vertices: number[];
  faces: number[];
  vertex_count: number;
  face_count: number;
}

export interface Mesh3DResponse {
  session_id: string;
  classes: MeshClassData[];
  bounds: number[];
}

export type ViewMode = 'original' | 'mask' | 'overlay' | 'side-by-side';
