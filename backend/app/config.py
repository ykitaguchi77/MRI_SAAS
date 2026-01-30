"""Application configuration"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Model settings
    MODEL_PATH: Path = Path(__file__).parent.parent / "checkpoints" / "final_model.pth"
    NUM_CLASSES: int = 10
    INPUT_SIZE: int = 256

    # File handling
    TEMP_DIR: Path = Path(__file__).parent.parent / "temp"
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: set = {".nii", ".nii.gz", ".png", ".jpg", ".jpeg"}
    FILE_RETENTION_HOURS: int = 1

    # Processing
    DEVICE: str = "cuda"
    BATCH_SIZE: int = 8

    # API
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_prefix = "MRI_SAAS_"


settings = Settings()
