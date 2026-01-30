import './Visualization.css';

interface ImageViewerProps {
  originalImage: string;
  segmentationMask: string;
  overlayImage: string;
  viewMode: 'original' | 'mask' | 'overlay';
  isLoading: boolean;
}

function ImageViewer({
  originalImage,
  segmentationMask,
  overlayImage,
  viewMode,
  isLoading,
}: ImageViewerProps) {
  const getDisplayImage = () => {
    switch (viewMode) {
      case 'original':
        return originalImage;
      case 'mask':
        return segmentationMask;
      case 'overlay':
      default:
        return overlayImage;
    }
  };

  const getViewLabel = () => {
    switch (viewMode) {
      case 'original':
        return 'Original Image';
      case 'mask':
        return 'Segmentation Mask';
      case 'overlay':
      default:
        return 'Overlay';
    }
  };

  return (
    <div className="image-viewer">
      <div className="view-label">{getViewLabel()}</div>

      <div className="image-container">
        {isLoading ? (
          <div className="loading-overlay">
            <div className="spinner"></div>
          </div>
        ) : (
          <img
            src={getDisplayImage()}
            alt={getViewLabel()}
            className="display-image"
          />
        )}
      </div>
    </div>
  );
}

export default ImageViewer;
