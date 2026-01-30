import type {
  UploadResponse,
  SegmentationResponse,
  ResultsResponse,
  ClassInfo,
} from '../types';

const API_BASE = '/api/v1';

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

export async function loadSample(): Promise<UploadResponse> {
  const response = await fetch(`${API_BASE}/sample`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to load sample');
  }

  return response.json();
}

export async function runSegmentation(sessionId: string): Promise<SegmentationResponse> {
  const response = await fetch(`${API_BASE}/segment/${sessionId}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Segmentation failed');
  }

  return response.json();
}

export async function getResults(
  sessionId: string,
  sliceIndex: number = 0,
  overlayAlpha: number = 0.5
): Promise<ResultsResponse> {
  const params = new URLSearchParams({
    slice_index: sliceIndex.toString(),
    overlay_alpha: overlayAlpha.toString(),
  });

  const response = await fetch(`${API_BASE}/results/${sessionId}?${params}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get results');
  }

  return response.json();
}

export async function getClasses(): Promise<ClassInfo[]> {
  const response = await fetch(`${API_BASE}/classes`);

  if (!response.ok) {
    throw new Error('Failed to get classes');
  }

  const data = await response.json();
  return data.classes;
}

export async function downloadResults(
  sessionId: string,
  format: 'nifti' | 'png' = 'nifti'
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/results/${sessionId}/download?format=${format}`);

  if (!response.ok) {
    throw new Error('Download failed');
  }

  return response.blob();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/session/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete session');
  }
}

export async function checkHealth(): Promise<{
  status: string;
  model_loaded: boolean;
  gpu_available: boolean;
  device: string;
}> {
  const response = await fetch(`${API_BASE}/health`);

  if (!response.ok) {
    throw new Error('Health check failed');
  }

  return response.json();
}
