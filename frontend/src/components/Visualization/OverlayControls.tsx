import './Visualization.css';

interface OverlayControlsProps {
  viewMode: 'original' | 'mask' | 'overlay';
  onViewModeChange: (mode: 'original' | 'mask' | 'overlay') => void;
  overlayAlpha: number;
  onAlphaChange: (alpha: number) => void;
}

function OverlayControls({
  viewMode,
  onViewModeChange,
  overlayAlpha,
  onAlphaChange,
}: OverlayControlsProps) {
  return (
    <div className="overlay-controls">
      <h3>View Mode</h3>

      <div className="view-mode-buttons">
        <button
          className={viewMode === 'original' ? 'active' : ''}
          onClick={() => onViewModeChange('original')}
        >
          Original
        </button>
        <button
          className={viewMode === 'mask' ? 'active' : ''}
          onClick={() => onViewModeChange('mask')}
        >
          Mask
        </button>
        <button
          className={viewMode === 'overlay' ? 'active' : ''}
          onClick={() => onViewModeChange('overlay')}
        >
          Overlay
        </button>
      </div>

      {viewMode === 'overlay' && (
        <div className="alpha-control">
          <label>
            Opacity: {Math.round(overlayAlpha * 100)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={overlayAlpha}
            onChange={(e) => onAlphaChange(Number(e.target.value))}
          />
        </div>
      )}
    </div>
  );
}

export default OverlayControls;
