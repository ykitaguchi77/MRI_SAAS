import './Visualization.css';

interface SliceSliderProps {
  currentSlice: number;
  totalSlices: number;
  onChange: (slice: number) => void;
}

function SliceSlider({ currentSlice, totalSlices, onChange }: SliceSliderProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft' && currentSlice > 0) {
      onChange(currentSlice - 1);
    } else if (e.key === 'ArrowRight' && currentSlice < totalSlices - 1) {
      onChange(currentSlice + 1);
    }
  };

  return (
    <div className="slice-slider" onKeyDown={handleKeyDown} tabIndex={0}>
      <div className="slice-controls">
        <button
          className="slice-btn"
          onClick={() => onChange(Math.max(0, currentSlice - 1))}
          disabled={currentSlice === 0}
        >
          &lt;
        </button>

        <input
          type="range"
          min="0"
          max={totalSlices - 1}
          value={currentSlice}
          onChange={(e) => onChange(Number(e.target.value))}
          className="slice-range"
        />

        <button
          className="slice-btn"
          onClick={() => onChange(Math.min(totalSlices - 1, currentSlice + 1))}
          disabled={currentSlice === totalSlices - 1}
        >
          &gt;
        </button>
      </div>

      <div className="slice-info">
        <span>Slice</span>
        <input
          type="number"
          min="0"
          max={totalSlices - 1}
          value={currentSlice}
          onChange={(e) => {
            const val = Number(e.target.value);
            if (val >= 0 && val < totalSlices) {
              onChange(val);
            }
          }}
          className="slice-input"
        />
        <span>/ {totalSlices - 1}</span>
      </div>
    </div>
  );
}

export default SliceSlider;
