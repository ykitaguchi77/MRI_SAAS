"""Inference functions for segmentation with logits-based upscaling"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Tuple

from app.config import settings


# Display size for upscaling
DISPLAY_SIZE = 512


def predict_single(
    model: torch.nn.Module,
    image: np.ndarray,
    device: str,
    upscale_size: int = DISPLAY_SIZE
) -> np.ndarray:
    """
    Run inference on a single preprocessed image with logits upscaling.

    Args:
        model: The segmentation model
        image: Preprocessed image (H, W)
        device: Device to run inference on
        upscale_size: Target size for upscaling (default 512)

    Returns:
        Prediction mask (upscale_size, upscale_size) with class indices
    """
    # Add batch and channel dimensions: (H, W) -> (1, 1, H, W)
    tensor = torch.from_numpy(image).unsqueeze(0).unsqueeze(0).float().to(device)

    with torch.no_grad():
        # Get raw logits
        logits = model(tensor)  # [1, num_classes, H, W]

        # Upscale logits BEFORE argmax for smooth boundaries
        if upscale_size and (logits.shape[2] != upscale_size or logits.shape[3] != upscale_size):
            logits = F.interpolate(
                logits,
                size=(upscale_size, upscale_size),
                mode='bilinear',
                align_corners=False
            )

        # Now apply argmax on upscaled logits
        prediction = torch.argmax(logits, dim=1)

    return prediction.squeeze().cpu().numpy().astype(np.uint8)


def predict_volume(
    model: torch.nn.Module,
    volume: np.ndarray,
    device: str,
    batch_size: int = None,
    upscale_size: int = DISPLAY_SIZE
) -> np.ndarray:
    """
    Run inference on a 3D volume with logits upscaling.

    Args:
        model: The segmentation model
        volume: Preprocessed volume (D, H, W)
        device: Device to run inference on
        batch_size: Batch size for inference
        upscale_size: Target size for upscaling (default 512)

    Returns:
        Predictions array (D, upscale_size, upscale_size) with class indices
    """
    if batch_size is None:
        batch_size = settings.BATCH_SIZE

    num_slices = volume.shape[0]
    predictions = []

    # Process in batches
    for i in range(0, num_slices, batch_size):
        batch_slices = volume[i:min(i + batch_size, num_slices)]

        # Add channel dimension and convert to tensor
        batch_tensor = torch.from_numpy(batch_slices).unsqueeze(1).float().to(device)

        with torch.no_grad():
            # Get raw logits
            logits = model(batch_tensor)  # [B, num_classes, H, W]

            # Upscale logits BEFORE argmax for smooth boundaries
            if upscale_size and (logits.shape[2] != upscale_size or logits.shape[3] != upscale_size):
                logits = F.interpolate(
                    logits,
                    size=(upscale_size, upscale_size),
                    mode='bilinear',
                    align_corners=False
                )

            # Now apply argmax on upscaled logits
            batch_pred = torch.argmax(logits, dim=1)

        predictions.append(batch_pred.cpu().numpy())

    # Concatenate predictions
    predictions = np.concatenate(predictions, axis=0)

    return predictions.astype(np.uint8)


def extract_voxel_dims(metadata: dict) -> tuple:
    """
    Extract voxel dimensions (mm) from NIfTI affine matrix.

    Args:
        metadata: Metadata dict containing 'affine' key

    Returns:
        Tuple of (voxel_x, voxel_y, voxel_z) in mm, or None
    """
    if metadata and "affine" in metadata:
        affine = np.array(metadata["affine"])
        voxel_dims = np.sqrt(np.sum(affine[:3, :3] ** 2, axis=0))
        return tuple(voxel_dims)
    return None


def get_prediction_statistics(
    mask: np.ndarray,
    voxel_dims: tuple = None,
    scale_factors: tuple = None
) -> dict:
    """
    Calculate statistics for a prediction mask.

    Args:
        mask: Prediction mask with class indices
        voxel_dims: Voxel dimensions in mm (x, y, z) from affine matrix
        scale_factors: Scale factors (sy, sx) = (original_H/display_H, original_W/display_W)
                       to correct for display upscaling

    Returns:
        Dictionary with statistics per class
    """
    from app.services.visualization import CLASS_NAMES, CLASS_COLORS

    unique_labels, counts = np.unique(mask, return_counts=True)
    total_pixels = mask.size

    # Calculate voxel volume if dimensions are available
    voxel_volume = None
    if voxel_dims is not None:
        voxel_volume = float(voxel_dims[0] * voxel_dims[1] * voxel_dims[2])
        if scale_factors is not None:
            voxel_volume *= scale_factors[0] * scale_factors[1]

    statistics = []
    for label, count in zip(unique_labels, counts):
        label = int(label)
        stat = {
            "class_id": label,
            "class_name": CLASS_NAMES.get(label, f"Unknown({label})"),
            "pixel_count": int(count),
            "percentage": round((count / total_pixels) * 100, 2),
            "color": CLASS_COLORS.get(label, [128, 128, 128])
        }
        if voxel_volume is not None:
            stat["volume_mm3"] = round(int(count) * voxel_volume, 2)
            stat["volume_cm3"] = round(int(count) * voxel_volume / 1000.0, 4)
        statistics.append(stat)

    return statistics


def get_lr_statistics(
    mask: np.ndarray,
    voxel_dims: tuple = None,
    scale_factors: tuple = None
) -> dict:
    """
    Calculate left/right statistics by splitting the mask at the horizontal midline.

    Args:
        mask: Prediction mask (H, W) or (H, W, D)
        voxel_dims: Voxel dimensions in mm
        scale_factors: Scale factors for display upscaling correction

    Returns:
        Dict with 'left' and 'right' statistics lists
    """
    mid = mask.shape[1] // 2
    if len(mask.shape) == 3:
        left_mask = mask[:, :mid, :]
        right_mask = mask[:, mid:, :]
    else:
        left_mask = mask[:, :mid]
        right_mask = mask[:, mid:]

    return {
        "left": get_prediction_statistics(left_mask, voxel_dims, scale_factors),
        "right": get_prediction_statistics(right_mask, voxel_dims, scale_factors)
    }
