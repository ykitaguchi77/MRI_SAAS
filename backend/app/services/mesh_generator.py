"""3D mesh generation from segmentation predictions using marching cubes"""

import json
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
from scipy.ndimage import zoom, gaussian_filter
from skimage.measure import marching_cubes

from app.services.visualization import CLASS_NAMES, CLASS_FULL_NAMES, CLASS_COLORS
from app.core.inference import extract_voxel_dims

logger = logging.getLogger(__name__)


# Override colors for better 3D visibility
_3D_COLOR_OVERRIDES = {
    9: [192, 192, 210],  # Eyeball - brighter silver-blue instead of dark gray
}


def _rgb_to_hex(rgb: list) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def generate_meshes(
    predictions: np.ndarray,
    metadata: dict,
    downsample_xy: int = 2,
    max_faces_per_class: int = 80000,
    smooth_sigma: float = 1.0,
) -> dict:
    """
    Generate 3D meshes from segmentation predictions using marching cubes.

    Args:
        predictions: Segmentation mask (H, W, D) with class indices
        metadata: File metadata containing affine matrix
        downsample_xy: Downsample factor for in-plane resolution
        max_faces_per_class: Maximum faces per class mesh
        smooth_sigma: Gaussian smoothing sigma for smoother surfaces

    Returns:
        Dict with 'classes' list and 'bounds'
    """
    if len(predictions.shape) != 3:
        raise ValueError("3D mesh generation requires a 3D volume")

    # Undo preprocessing rotation and flip to correct 3D orientation
    predictions = np.rot90(predictions, k=1, axes=(0, 1))
    predictions = np.flipud(predictions)

    # Get voxel dimensions from affine
    voxel_dims = extract_voxel_dims(metadata)
    if voxel_dims is not None:
        vx, vy, vz = voxel_dims
    else:
        # Default to isotropic 1mm voxels
        vx, vy, vz = 1.0, 1.0, 1.0

    # In-plane resolution after downsampling
    # Original predictions are at display size (512), map back to physical
    orig_dims = metadata.get("dimensions", [])
    if len(orig_dims) >= 2:
        scale_x = orig_dims[0] / predictions.shape[0]
        scale_y = orig_dims[1] / predictions.shape[1]
        in_plane_res_x = vx * scale_x * downsample_xy
        in_plane_res_y = vy * scale_y * downsample_xy
    else:
        in_plane_res_x = vx * downsample_xy
        in_plane_res_y = vy * downsample_xy

    # Z zoom factor to make voxels more isotropic
    avg_in_plane = (in_plane_res_x + in_plane_res_y) / 2.0
    z_zoom = vz / avg_in_plane if avg_in_plane > 0 else 1.0
    z_zoom = max(1.0, min(z_zoom, 5.0))  # Clamp between 1 and 5

    all_vertices = []
    mesh_classes = []

    for class_id in range(1, 10):  # Skip background (0)
        # Extract binary mask
        mask = (predictions == class_id).astype(np.float32)

        # Check if class has any voxels
        if mask.sum() == 0:
            continue

        # Downsample in-plane
        downsampled = mask[::downsample_xy, ::downsample_xy, :]

        # Interpolate Z-axis for smoother 3D
        if z_zoom > 1.01:
            try:
                downsampled = zoom(downsampled, [1, 1, z_zoom], order=1)
            except Exception as e:
                logger.warning(f"Z-axis zoom failed for class {class_id}: {e}")

        # Gaussian smoothing for smoother surfaces
        smoothed = gaussian_filter(downsampled, sigma=smooth_sigma)

        # Marching cubes
        try:
            step_size = 1
            verts, faces, _, _ = marching_cubes(smoothed, level=0.5, step_size=step_size)

            # If too many faces, increase step size
            if len(faces) > max_faces_per_class:
                step_size = 2
                verts, faces, _, _ = marching_cubes(smoothed, level=0.5, step_size=step_size)

            # Still too many? Subsample faces
            if len(faces) > max_faces_per_class:
                indices = np.linspace(0, len(faces) - 1, max_faces_per_class, dtype=int)
                faces = faces[indices]
        except Exception as e:
            logger.warning(f"Marching cubes failed for class {class_id}: {e}")
            continue

        if len(verts) == 0 or len(faces) == 0:
            continue

        # Scale vertices to physical coordinates
        verts_physical = verts.copy().astype(np.float32)
        verts_physical[:, 0] *= in_plane_res_x  # X
        verts_physical[:, 1] *= in_plane_res_y  # Y
        verts_physical[:, 2] *= avg_in_plane     # Z (was zoomed to be isotropic)

        all_vertices.append(verts_physical)

        mesh_classes.append({
            "class_id": class_id,
            "class_name": CLASS_FULL_NAMES.get(class_id, CLASS_NAMES.get(class_id, f"Class {class_id}")),
            "color": _rgb_to_hex(_3D_COLOR_OVERRIDES.get(class_id, CLASS_COLORS.get(class_id, [128, 128, 128]))),
            "vertices": verts_physical.flatten().tolist(),
            "faces": faces.flatten().tolist(),
            "vertex_count": len(verts_physical),
            "face_count": len(faces),
        })

    # Compute global bounds and center all meshes
    if all_vertices:
        all_verts_combined = np.concatenate(all_vertices, axis=0)
        center = all_verts_combined.mean(axis=0)
        min_bounds = all_verts_combined.min(axis=0) - center
        max_bounds = all_verts_combined.max(axis=0) - center

        # Center each mesh
        for i, mc in enumerate(mesh_classes):
            verts_arr = np.array(mc["vertices"]).reshape(-1, 3)
            verts_arr -= center
            mesh_classes[i]["vertices"] = verts_arr.flatten().tolist()

        bounds = [
            float(min_bounds[0]), float(min_bounds[1]), float(min_bounds[2]),
            float(max_bounds[0]), float(max_bounds[1]), float(max_bounds[2]),
        ]
    else:
        bounds = [0, 0, 0, 0, 0, 0]

    return {
        "classes": mesh_classes,
        "bounds": bounds,
    }


def get_cached_meshes(session_dir: Path) -> Optional[dict]:
    """Load cached mesh data if available."""
    cache_path = session_dir / "_meshes.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            return json.load(f)
    return None


def save_mesh_cache(session_dir: Path, mesh_data: dict):
    """Save mesh data to cache."""
    cache_path = session_dir / "_meshes.json"
    with open(cache_path, "w") as f:
        json.dump(mesh_data, f)
