"""Visualization utilities for segmentation results"""

import base64
import io
import numpy as np
from PIL import Image
from typing import List, Dict


# Class definitions for eye MRI segmentation
CLASS_NAMES = {
    0: "Background",
    1: "SR",   # Superior Rectus
    2: "LR",   # Lateral Rectus
    3: "MR",   # Medial Rectus
    4: "IR",   # Inferior Rectus
    5: "ON",   # Optic Nerve
    6: "FAT",  # Orbital Fat
    7: "LG",   # Lacrimal Gland
    8: "SO",   # Superior Oblique
    9: "EB"    # Eyeball
}

CLASS_FULL_NAMES = {
    0: "Background",
    1: "Superior Rectus",
    2: "Lateral Rectus",
    3: "Medial Rectus",
    4: "Inferior Rectus",
    5: "Optic Nerve",
    6: "Orbital Fat",
    7: "Lacrimal Gland",
    8: "Superior Oblique",
    9: "Eyeball"
}

CLASS_COLORS = {
    0: [0, 0, 0],        # Background - Black
    1: [255, 0, 0],      # SR - Red
    2: [0, 255, 0],      # LR - Green
    3: [0, 0, 255],      # MR - Blue
    4: [255, 255, 0],    # IR - Yellow
    5: [255, 0, 255],    # ON - Magenta
    6: [0, 255, 255],    # FAT - Cyan
    7: [255, 128, 0],    # LG - Orange
    8: [128, 0, 255],    # SO - Purple
    9: [128, 128, 128]   # EB - Gray
}


def create_colored_mask(mask: np.ndarray) -> np.ndarray:
    """
    Convert class indices to RGB colored mask.

    Note: Upscaling is now done via logits interpolation in inference.py
    for smooth boundaries.

    Args:
        mask: 2D array with class indices (already at display size)

    Returns:
        RGB image array (H, W, 3)
    """
    h, w = mask.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    for class_id, color in CLASS_COLORS.items():
        colored[mask == class_id] = color

    return colored


def create_overlay(
    image: np.ndarray,
    mask: np.ndarray,
    alpha: float = 0.5
) -> np.ndarray:
    """
    Create overlay visualization with segmentation mask on original image.

    Note: Both image and mask should already be at display size (512x512).
    Upscaling is done via logits interpolation in inference.py.

    Args:
        image: Original grayscale image (already at display size)
        mask: Segmentation mask with class indices (already at display size)
        alpha: Transparency for the mask overlay (0-1)

    Returns:
        RGB overlay image
    """
    # Normalize image to 0-255
    if image.max() > image.min():
        image_norm = ((image - image.min()) / (image.max() - image.min()) * 255).astype(np.uint8)
    else:
        image_norm = np.zeros_like(image, dtype=np.uint8)

    # Convert grayscale to RGB
    img_rgb = np.stack([image_norm, image_norm, image_norm], axis=-1).astype(np.float32)

    # Create colored mask
    mask_rgb = create_colored_mask(mask).astype(np.float32)

    # Create overlay (only blend where mask is not background)
    overlay = img_rgb.copy()
    mask_pixels = mask > 0
    overlay[mask_pixels] = (1 - alpha) * img_rgb[mask_pixels] + alpha * mask_rgb[mask_pixels]

    return overlay.astype(np.uint8)


def normalize_image_for_display(image: np.ndarray) -> np.ndarray:
    """
    Normalize image to 0-255 range for display.

    Note: Image should already be at display size (512x512).
    Upscaling is done in segmentation.py.

    Args:
        image: Input image (already at display size)

    Returns:
        Normalized uint8 image
    """
    if image.max() > image.min():
        normalized = ((image - image.min()) / (image.max() - image.min()) * 255)
    else:
        normalized = np.zeros_like(image)

    return normalized.astype(np.uint8)


def encode_image_base64(image: np.ndarray, format: str = "PNG") -> str:
    """
    Encode numpy array as base64 string.

    Args:
        image: Image array (grayscale or RGB)
        format: Image format (PNG, JPEG)

    Returns:
        Base64 encoded string
    """
    # Handle grayscale vs RGB
    if len(image.shape) == 2:
        pil_image = Image.fromarray(image, mode='L')
    else:
        pil_image = Image.fromarray(image, mode='RGB')

    # Save to buffer
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format)
    buffer.seek(0)

    # Encode to base64
    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/{format.lower()};base64,{encoded}"


def get_class_info() -> List[Dict]:
    """Get class information for frontend display"""
    return [
        {
            "id": class_id,
            "name": CLASS_NAMES[class_id],
            "full_name": CLASS_FULL_NAMES[class_id],
            "color": CLASS_COLORS[class_id],
            "hex_color": "#{:02x}{:02x}{:02x}".format(*CLASS_COLORS[class_id])
        }
        for class_id in range(10)
    ]
