"""Image preprocessing for segmentation"""

import numpy as np
import cv2
from typing import Tuple

from app.config import settings


def preprocess_image(
    image: np.ndarray,
    target_size: Tuple[int, int] = None
) -> np.ndarray:
    """
    Preprocess a single 2D image for inference.

    Args:
        image: Input image (grayscale or RGB)
        target_size: Target size (H, W). Defaults to settings.INPUT_SIZE

    Returns:
        Preprocessed image as float32 array
    """
    if target_size is None:
        target_size = (settings.INPUT_SIZE, settings.INPUT_SIZE)

    # Convert to grayscale if RGB
    if len(image.shape) == 3:
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        else:
            image = image[:, :, 0]

    # Convert to float32
    image = image.astype(np.float32)

    # Resize if needed
    if image.shape[:2] != target_size:
        image = cv2.resize(image, target_size[::-1], interpolation=cv2.INTER_LINEAR)

    # Normalize (min-max normalization)
    if image.max() > image.min():
        image = (image - image.min()) / (image.max() - image.min())

    return image


def preprocess_volume(
    volume_data: np.ndarray,
    target_size: Tuple[int, int] = None
) -> np.ndarray:
    """
    Preprocess 3D NIfTI volume for inference.

    Args:
        volume_data: 3D volume array (H, W, D)
        target_size: Target size for each slice (H, W)

    Returns:
        Preprocessed volume as (D, H, W) array
    """
    if target_size is None:
        target_size = (settings.INPUT_SIZE, settings.INPUT_SIZE)

    # Rotate 90 degrees right to correct orientation (NIfTI is rotated left)
    volume_data = np.rot90(volume_data, k=-1, axes=(0, 1))

    # Process each slice
    processed_slices = []
    for i in range(volume_data.shape[2]):
        slice_data = volume_data[:, :, i].astype(np.float32)

        # Resize if needed
        if slice_data.shape[:2] != target_size:
            slice_data = cv2.resize(
                slice_data,
                target_size[::-1],
                interpolation=cv2.INTER_LINEAR
            )

        # Normalize
        if slice_data.max() > slice_data.min():
            slice_data = (slice_data - slice_data.min()) / (slice_data.max() - slice_data.min())

        processed_slices.append(slice_data)

    return np.stack(processed_slices, axis=0)


def postprocess_predictions(
    predictions: np.ndarray,
    original_shape: Tuple[int, int, int]
) -> np.ndarray:
    """
    Postprocess predictions (now at display size from logits upscaling).

    Args:
        predictions: Predictions array (D, H, W) at display size (512x512)
        original_shape: Original volume shape (H, W, D) - not used, kept for API compatibility

    Returns:
        Postprocessed predictions (H, W, D) at display size
    """
    # Transpose to (H, W, D) format for storage
    # predictions is (D, display_size, display_size) -> (display_size, display_size, D)
    predictions = np.transpose(predictions, (1, 2, 0))

    return predictions.astype(np.uint8)
