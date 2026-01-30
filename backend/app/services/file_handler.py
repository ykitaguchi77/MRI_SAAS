"""File handling service for uploads and temporary storage"""

import os
import uuid
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import numpy as np
import nibabel as nib
from PIL import Image

from app.config import settings


class FileHandler:
    """Handle file uploads, storage, and cleanup"""

    def __init__(self, temp_dir: Path = None):
        self.temp_dir = temp_dir or settings.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        return str(uuid.uuid4())

    def get_session_dir(self, session_id: str) -> Path:
        """Get directory for a session"""
        return self.temp_dir / session_id

    def save_upload(self, content: bytes, filename: str, session_id: str) -> Path:
        """
        Save uploaded file to session directory.

        Args:
            content: File content as bytes
            filename: Original filename
            session_id: Session ID

        Returns:
            Path to saved file
        """
        session_dir = self.get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        file_path = session_dir / filename
        with open(file_path, 'wb') as f:
            f.write(content)

        return file_path

    def load_file(self, session_id: str) -> Tuple[np.ndarray, str, Dict[str, Any]]:
        """
        Load file from session directory.

        Args:
            session_id: Session ID

        Returns:
            Tuple of (data, file_type, metadata)
        """
        session_dir = self.get_session_dir(session_id)
        if not session_dir.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        # Find the uploaded file
        files = list(session_dir.glob("*"))
        upload_files = [f for f in files if not f.name.startswith("_")]

        if not upload_files:
            raise FileNotFoundError(f"No upload file found in session: {session_id}")

        file_path = upload_files[0]
        suffix = file_path.suffix.lower()

        # Handle .nii.gz
        if file_path.name.endswith('.nii.gz'):
            suffix = '.nii.gz'

        if suffix in ['.nii', '.nii.gz']:
            return self._load_nifti(file_path)
        elif suffix in ['.png', '.jpg', '.jpeg']:
            return self._load_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _load_nifti(self, file_path: Path) -> Tuple[np.ndarray, str, Dict[str, Any]]:
        """Load NIfTI file"""
        nifti = nib.load(str(file_path))
        data = nifti.get_fdata().astype(np.float32)

        metadata = {
            "dimensions": list(data.shape),
            "num_slices": data.shape[2] if len(data.shape) >= 3 else 1,
            "affine": nifti.affine.tolist(),
            "filename": file_path.name
        }

        return data, "nifti", metadata

    def _load_image(self, file_path: Path) -> Tuple[np.ndarray, str, Dict[str, Any]]:
        """Load PNG/JPEG image"""
        image = Image.open(file_path)

        # Convert to numpy array
        data = np.array(image)

        # Convert to grayscale if needed
        if len(data.shape) == 3:
            if data.shape[2] == 4:  # RGBA
                image = image.convert('L')
                data = np.array(image)
            elif data.shape[2] == 3:  # RGB
                image = image.convert('L')
                data = np.array(image)

        metadata = {
            "dimensions": list(data.shape),
            "num_slices": 1,
            "filename": file_path.name
        }

        return data.astype(np.float32), "image", metadata

    def save_results(
        self,
        session_id: str,
        predictions: np.ndarray,
        original_data: np.ndarray = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Save segmentation results to session directory.

        Args:
            session_id: Session ID
            predictions: Prediction mask
            original_data: Original image/volume data
            metadata: Additional metadata
        """
        session_dir = self.get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save predictions as numpy file
        np.save(session_dir / "_predictions.npy", predictions)

        # Save original data if provided
        if original_data is not None:
            np.save(session_dir / "_original.npy", original_data)

        # Save metadata if provided
        if metadata is not None:
            import json
            with open(session_dir / "_metadata.json", 'w') as f:
                json.dump(metadata, f)

    def load_results(self, session_id: str) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """
        Load saved results from session directory.

        Args:
            session_id: Session ID

        Returns:
            Tuple of (predictions, original_data, metadata)
        """
        session_dir = self.get_session_dir(session_id)

        predictions = np.load(session_dir / "_predictions.npy")

        original_data = None
        original_path = session_dir / "_original.npy"
        if original_path.exists():
            original_data = np.load(original_path)

        metadata = {}
        metadata_path = session_dir / "_metadata.json"
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        return predictions, original_data, metadata

    def get_nifti_for_download(self, session_id: str) -> bytes:
        """
        Get segmentation results as NIfTI file for download.

        Args:
            session_id: Session ID

        Returns:
            NIfTI file as bytes
        """
        predictions, _, metadata = self.load_results(session_id)

        # Create NIfTI image
        affine = np.eye(4)
        if metadata and "affine" in metadata:
            affine = np.array(metadata["affine"])

        nifti_img = nib.Nifti1Image(predictions.astype(np.uint8), affine)

        # Save to bytes
        import io
        buffer = io.BytesIO()
        nib.save(nifti_img, buffer)
        buffer.seek(0)

        return buffer.read()

    def cleanup_session(self, session_id: str):
        """Remove all files for a session"""
        session_dir = self.get_session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)

    def cleanup_expired(self):
        """Remove sessions older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=settings.FILE_RETENTION_HOURS)

        for session_dir in self.temp_dir.iterdir():
            if session_dir.is_dir():
                # Check modification time
                mtime = datetime.fromtimestamp(session_dir.stat().st_mtime)
                if mtime < cutoff_time:
                    shutil.rmtree(session_dir)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        return self.get_session_dir(session_id).exists()

    def has_results(self, session_id: str) -> bool:
        """Check if a session has saved results"""
        session_dir = self.get_session_dir(session_id)
        return (session_dir / "_predictions.npy").exists()


_file_handler: Optional[FileHandler] = None


def get_file_handler() -> FileHandler:
    """Get the global file handler instance"""
    global _file_handler
    if _file_handler is None:
        _file_handler = FileHandler()
    return _file_handler
