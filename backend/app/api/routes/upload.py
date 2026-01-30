"""File upload endpoint"""

from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException

from app.config import settings
from app.services.file_handler import get_file_handler
from app.schemas import UploadResponse, FileInfo

router = APIRouter()

# Sample file path (resolve to get absolute path)
SAMPLE_FILE = (Path(__file__).parent.parent.parent.parent / "samples" / "sample.nii.gz").resolve()


def validate_file(filename: str, size: int) -> None:
    """Validate uploaded file"""
    # Check extension
    ext = filename.lower()
    if ext.endswith('.nii.gz'):
        ext = '.nii.gz'
    else:
        ext = '.' + filename.rsplit('.', 1)[-1].lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )

    # Check size
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
        )


@router.post("/sample", response_model=UploadResponse)
async def load_sample():
    """
    Load the sample NIfTI file for users without test data.

    Returns session_id for subsequent operations.
    """
    if not SAMPLE_FILE.exists():
        raise HTTPException(status_code=404, detail="Sample file not found")

    # Read sample file
    content = SAMPLE_FILE.read_bytes()

    # Save file
    file_handler = get_file_handler()
    session_id = file_handler.generate_session_id()
    file_handler.save_upload(content, "sample.nii.gz", session_id)

    # Load to get file info
    try:
        data, file_type, metadata = file_handler.load_file(session_id)
    except Exception as e:
        file_handler.cleanup_session(session_id)
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    file_info = FileInfo(
        filename="sample.nii.gz",
        file_type=file_type,
        dimensions=metadata["dimensions"],
        num_slices=metadata["num_slices"]
    )

    return UploadResponse(
        session_id=session_id,
        file_info=file_info,
        message="Sample file loaded successfully"
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload NIfTI or PNG/JPEG file for segmentation.

    Returns session_id for subsequent operations.
    """
    # Read file content
    content = await file.read()

    # Validate
    validate_file(file.filename, len(content))

    # Save file
    file_handler = get_file_handler()
    session_id = file_handler.generate_session_id()
    file_handler.save_upload(content, file.filename, session_id)

    # Load to get file info
    try:
        data, file_type, metadata = file_handler.load_file(session_id)
    except Exception as e:
        file_handler.cleanup_session(session_id)
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    file_info = FileInfo(
        filename=file.filename,
        file_type=file_type,
        dimensions=metadata["dimensions"],
        num_slices=metadata["num_slices"]
    )

    return UploadResponse(
        session_id=session_id,
        file_info=file_info,
        message="File uploaded successfully"
    )
