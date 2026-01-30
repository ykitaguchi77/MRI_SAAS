"""Model loading and caching"""

import torch
from pathlib import Path
from typing import Optional

from app.models.vanilla_unet import VanillaUNet
from app.config import settings


class ModelManager:
    """Singleton model manager for loading and caching the segmentation model"""

    _instance: Optional["ModelManager"] = None
    _model: Optional[VanillaUNet] = None
    _device: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self) -> VanillaUNet:
        """Get the loaded model, loading it if necessary"""
        if self._model is None:
            self._load_model()
        return self._model

    def get_device(self) -> str:
        """Get the device being used"""
        if self._device is None:
            self._setup_device()
        return self._device

    def _setup_device(self):
        """Setup the computation device"""
        if settings.DEVICE == "cuda" and torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"

    def _load_model(self):
        """Load the model from checkpoint"""
        if self._device is None:
            self._setup_device()

        self._model = VanillaUNet(
            in_channels=1,
            n_classes=settings.NUM_CLASSES,
            features=[64, 128, 256, 512, 1024],
            bilinear=True
        )

        checkpoint_path = settings.MODEL_PATH
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_path}")

        checkpoint = torch.load(checkpoint_path, map_location=self._device, weights_only=False)
        self._model.load_state_dict(checkpoint['model_state_dict'])
        self._model.to(self._device)
        self._model.eval()

    def is_loaded(self) -> bool:
        """Check if the model is loaded"""
        return self._model is not None

    def is_gpu_available(self) -> bool:
        """Check if GPU is available"""
        return torch.cuda.is_available()


_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
