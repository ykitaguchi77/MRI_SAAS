import { useState } from 'react';
import type { ClassStatistics } from '../../types';
import { downloadResults } from '../../services/api';
import './Results.css';

interface ResultsPanelProps {
  sessionId: string;
  statistics: ClassStatistics[];
  processingTime: number | null;
  fileType: string;
}

function ResultsPanel({
  sessionId,
  statistics,
  processingTime,
  fileType,
}: ResultsPanelProps) {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async (format: 'nifti' | 'png') => {
    setIsDownloading(true);
    try {
      const blob = await downloadResults(sessionId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `segmentation_${sessionId}.${format === 'nifti' ? 'nii.gz' : 'png'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  // Calculate total non-background pixels
  const totalPixels = statistics.reduce((sum, s) => sum + s.pixel_count, 0);
  const nonBgPixels = statistics
    .filter(s => s.class_id !== 0)
    .reduce((sum, s) => sum + s.pixel_count, 0);
  const segmentedPercent = totalPixels > 0 ? (nonBgPixels / totalPixels * 100).toFixed(1) : '0';

  return (
    <div className="results-panel">
      <h3>Results</h3>

      <div className="results-summary">
        {processingTime && (
          <div className="summary-item">
            <span className="label">Processing Time</span>
            <span className="value">{(processingTime / 1000).toFixed(2)}s</span>
          </div>
        )}

        <div className="summary-item">
          <span className="label">Segmented Area</span>
          <span className="value">{segmentedPercent}%</span>
        </div>

        <div className="summary-item">
          <span className="label">Classes Detected</span>
          <span className="value">
            {statistics.filter(s => s.class_id !== 0 && s.pixel_count > 0).length}
          </span>
        </div>
      </div>

      <div className="statistics-table">
        <h4>Class Statistics</h4>
        <table>
          <thead>
            <tr>
              <th>Class</th>
              <th>Pixels</th>
              <th>%</th>
            </tr>
          </thead>
          <tbody>
            {statistics
              .filter(s => s.class_id !== 0 && s.pixel_count > 0)
              .sort((a, b) => b.pixel_count - a.pixel_count)
              .map((stat) => (
                <tr key={stat.class_id}>
                  <td>
                    <span
                      className="color-indicator"
                      style={{ backgroundColor: `rgb(${stat.color.join(',')})` }}
                    />
                    {stat.class_name}
                  </td>
                  <td>{stat.pixel_count.toLocaleString()}</td>
                  <td>{stat.percentage.toFixed(2)}%</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <div className="download-section">
        <h4>Download Results</h4>
        <div className="download-buttons">
          {fileType === 'nifti' && (
            <button
              onClick={() => handleDownload('nifti')}
              disabled={isDownloading}
            >
              Download NIfTI
            </button>
          )}
          <button
            onClick={() => handleDownload('png')}
            disabled={isDownloading}
          >
            Download PNG
          </button>
        </div>
      </div>
    </div>
  );
}

export default ResultsPanel;
