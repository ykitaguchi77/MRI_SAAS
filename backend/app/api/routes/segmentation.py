"""Segmentation endpoints"""

import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
import numpy as np

from app.config import settings
from app.core.model_loader import get_model_manager
from app.core.preprocessing import preprocess_image, preprocess_volume, postprocess_predictions
from app.core.inference import predict_single, predict_volume, get_prediction_statistics
from app.services.file_handler import get_file_handler
from app.services.visualization import (
    create_colored_mask,
    create_overlay,
    encode_image_base64,
    normalize_image_for_display,
    get_class_info,
)
from app.schemas import (
    SegmentationResponse,
    ResultsResponse,
    SliceData,
    ClassStatistics,
)

router = APIRouter()


@router.post("/segment/{session_id}", response_model=SegmentationResponse)
async def run_segmentation(session_id: str):
    """
    Run segmentation on uploaded file.

    Args:
        session_id: Session ID from upload
    """
    file_handler = get_file_handler()

    # Check session exists
    if not file_handler.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Load file
    try:
        data, file_type, metadata = file_handler.load_file(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load file: {str(e)}")

    # Get model
    model_manager = get_model_manager()
    try:
        model = model_manager.get_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

    device = model_manager.get_device()

    start_time = time.time()

    # Display size (predictions will be upscaled via logits)
    display_size = 512

    # Process based on file type
    if file_type == "nifti":
        # Process 3D volume
        original_shape = data.shape
        processed = preprocess_volume(data)  # (D, 256, 256)
        # Predictions are now 512x512 (logits upscaled before argmax)
        predictions = predict_volume(model, processed, device, upscale_size=display_size)  # (D, 512, 512)
        predictions = postprocess_predictions(predictions, original_shape)  # (512, 512, D)
        num_slices = predictions.shape[2]

        # Upscale preprocessed volume to match predictions size
        # Transpose from (D, 256, 256) to (256, 256, D) then upscale each slice
        processed_transposed = np.transpose(processed, (1, 2, 0))
        import cv2
        data = np.zeros((display_size, display_size, processed_transposed.shape[2]), dtype=np.float32)
        for i in range(processed_transposed.shape[2]):
            data[:, :, i] = cv2.resize(
                processed_transposed[:, :, i],
                (display_size, display_size),
                interpolation=cv2.INTER_CUBIC
            )
    else:
        # Process 2D image
        original_shape = data.shape
        processed = preprocess_image(data)  # (256, 256)
        # Predictions are now 512x512 (logits upscaled before argmax)
        predictions = predict_single(model, processed, device, upscale_size=display_size)  # (512, 512)

        # Upscale preprocessed image to match predictions size
        import cv2
        data = cv2.resize(processed, (display_size, display_size), interpolation=cv2.INTER_CUBIC)

        num_slices = 1

    processing_time = (time.time() - start_time) * 1000

    # Save results
    file_handler.save_results(session_id, predictions, data, metadata)

    # Calculate statistics
    statistics = get_prediction_statistics(predictions)

    return SegmentationResponse(
        session_id=session_id,
        num_slices_processed=num_slices,
        statistics=[ClassStatistics(**s) for s in statistics],
        processing_time_ms=round(processing_time, 2)
    )


@router.get("/results/{session_id}", response_model=ResultsResponse)
async def get_results(
    session_id: str,
    slice_index: int = Query(0, ge=0),
    overlay_alpha: float = Query(0.5, ge=0.0, le=1.0)
):
    """
    Get visualization data for a specific slice.

    Args:
        session_id: Session ID
        slice_index: Slice index (0 for 2D images)
        overlay_alpha: Overlay transparency (0-1)
    """
    file_handler = get_file_handler()

    # Check results exist
    if not file_handler.has_results(session_id):
        raise HTTPException(status_code=404, detail="Results not found. Run segmentation first.")

    # Load results
    try:
        predictions, original_data, metadata = file_handler.load_results(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load results: {str(e)}")

    # Determine file type
    file_type = "nifti" if len(predictions.shape) == 3 else "image"
    total_slices = predictions.shape[2] if file_type == "nifti" else 1

    # Validate slice index
    if slice_index >= total_slices:
        raise HTTPException(status_code=400, detail=f"Slice index out of range. Max: {total_slices - 1}")

    # Get slice data
    if file_type == "nifti":
        pred_slice = predictions[:, :, slice_index]
        orig_slice = original_data[:, :, slice_index] if original_data is not None else None
    else:
        pred_slice = predictions
        orig_slice = original_data

    # Create visualizations
    if orig_slice is not None:
        orig_display = normalize_image_for_display(orig_slice)
        original_b64 = encode_image_base64(orig_display)
        overlay = create_overlay(orig_slice, pred_slice, overlay_alpha)
        overlay_b64 = encode_image_base64(overlay)
    else:
        original_b64 = ""
        overlay_b64 = ""

    colored_mask = create_colored_mask(pred_slice)
    mask_b64 = encode_image_base64(colored_mask)

    # Calculate slice statistics
    statistics = get_prediction_statistics(pred_slice)

    slice_data = SliceData(
        original_image=original_b64,
        segmentation_mask=mask_b64,
        overlay_image=overlay_b64,
        slice_index=slice_index,
        statistics=[ClassStatistics(**s) for s in statistics]
    )

    return ResultsResponse(
        session_id=session_id,
        slice_data=slice_data,
        total_slices=total_slices,
        file_type=file_type
    )


@router.get("/results/{session_id}/download")
async def download_results(
    session_id: str,
    format: str = Query("nifti", pattern="^(nifti|png)$")
):
    """
    Download segmentation results.

    Args:
        session_id: Session ID
        format: Download format (nifti or png)
    """
    file_handler = get_file_handler()

    if not file_handler.has_results(session_id):
        raise HTTPException(status_code=404, detail="Results not found")

    try:
        predictions, _, metadata = file_handler.load_results(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load results: {str(e)}")

    if format == "nifti":
        # Return NIfTI file
        import nibabel as nib
        import io

        affine = np.eye(4)
        if metadata and "affine" in metadata:
            affine = np.array(metadata["affine"])

        nifti_img = nib.Nifti1Image(predictions.astype(np.uint8), affine)

        buffer = io.BytesIO()
        file_map = nifti_img.to_file_map()
        file_map['image'].fileobj = buffer
        nifti_img.to_file_map(file_map)
        buffer.seek(0)

        return Response(
            content=buffer.read(),
            media_type="application/gzip",
            headers={"Content-Disposition": f"attachment; filename=segmentation_{session_id}.nii.gz"}
        )

    else:  # png
        # Return colored PNG (only for 2D or middle slice)
        if len(predictions.shape) == 3:
            pred_slice = predictions[:, :, predictions.shape[2] // 2]
        else:
            pred_slice = predictions

        colored = create_colored_mask(pred_slice)

        from PIL import Image
        import io

        img = Image.fromarray(colored)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return Response(
            content=buffer.read(),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=segmentation_{session_id}.png"}
        )


@router.get("/classes")
async def get_classes():
    """Get class information (names, colors)"""
    return {"classes": get_class_info()}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its files"""
    file_handler = get_file_handler()

    if not file_handler.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    file_handler.cleanup_session(session_id)

    return {"message": "Session deleted successfully"}
