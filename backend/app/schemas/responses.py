"""Pydantic response models"""

from typing import List, Optional
from pydantic import BaseModel


class FileInfo(BaseModel):
    """Information about an uploaded file"""
    filename: str
    file_type: str  # "nifti" or "image"
    dimensions: List[int]
    num_slices: int


class UploadResponse(BaseModel):
    """Response for file upload"""
    session_id: str
    file_info: FileInfo
    message: str


class ClassStatistics(BaseModel):
    """Statistics for a single class"""
    class_id: int
    class_name: str
    pixel_count: int
    percentage: float
    color: List[int]
    volume_mm3: Optional[float] = None
    volume_cm3: Optional[float] = None


class LRStatistics(BaseModel):
    """Left/Right split statistics"""
    left: List[ClassStatistics]
    right: List[ClassStatistics]


class SegmentationResponse(BaseModel):
    """Response for segmentation request"""
    session_id: str
    num_slices_processed: int
    statistics: List[ClassStatistics]
    processing_time_ms: float
    lr_statistics: Optional[LRStatistics] = None


class SliceData(BaseModel):
    """Data for a single slice"""
    original_image: str      # Base64 encoded PNG
    segmentation_mask: str   # Base64 encoded PNG (colored)
    overlay_image: str       # Base64 encoded PNG
    slice_index: int
    statistics: List[ClassStatistics]
    lr_statistics: Optional[LRStatistics] = None


class ResultsResponse(BaseModel):
    """Response for results request"""
    session_id: str
    slice_data: SliceData
    total_slices: int
    file_type: str


class HealthResponse(BaseModel):
    """Response for health check"""
    status: str
    model_loaded: bool
    gpu_available: bool
    device: str


class MeshClassData(BaseModel):
    """Mesh data for a single segmentation class"""
    class_id: int
    class_name: str
    color: str  # hex color "#ff0000"
    vertices: List[float]  # flat [x,y,z,...]
    faces: List[int]  # flat [i,j,k,...]
    vertex_count: int
    face_count: int


class Mesh3DResponse(BaseModel):
    """Response for 3D mesh generation"""
    session_id: str
    classes: List[MeshClassData]
    bounds: List[float]  # [minX, minY, minZ, maxX, maxY, maxZ]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
