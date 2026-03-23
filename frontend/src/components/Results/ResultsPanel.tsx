import { useState } from 'react';
import type { ClassStatistics, LRStatistics } from '../../types';
import { downloadResults } from '../../services/api';
import './Results.css';

interface ResultsPanelProps {
  sessionId: string;
  statistics: ClassStatistics[];
  processingTime: number | null;
  fileType: string;
  lrStatistics?: LRStatistics;
}

type StatsView = 'overall' | 'lr';

function ResultsPanel({
  sessionId,
  statistics,
  processingTime,
  fileType,
  lrStatistics,
}: ResultsPanelProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [statsView, setStatsView] = useState<StatsView>('overall');

  const handleDownload = async (format: 'nifti' | 'png' | 'excel') => {
    setIsDownloading(true);
    try {
      const blob = await downloadResults(sessionId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = format === 'nifti' ? 'nii.gz' : format === 'excel' ? 'xlsx' : 'png';
      const prefix = format === 'excel' ? 'analysis' : 'segmentation';
      a.download = `${prefix}_${sessionId}.${ext}`;
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

  const hasVolume = statistics.some(s => s.volume_mm3 != null);

  // Total tissue volume
  const totalVolumeMm3 = hasVolume
    ? statistics.filter(s => s.class_id !== 0).reduce((sum, s) => sum + (s.volume_mm3 || 0), 0)
    : 0;

  const formatVolume = (mm3: number) => {
    if (mm3 >= 1000) return `${(mm3 / 1000).toFixed(2)} cm³`;
    return `${mm3.toFixed(2)} mm³`;
  };

  // Build L/R comparison data
  const buildLRRows = () => {
    if (!lrStatistics) return [];
    const classIds = new Set<number>();
    lrStatistics.left.forEach(s => { if (s.class_id !== 0) classIds.add(s.class_id); });
    lrStatistics.right.forEach(s => { if (s.class_id !== 0) classIds.add(s.class_id); });

    const leftMap = new Map(lrStatistics.left.map(s => [s.class_id, s]));
    const rightMap = new Map(lrStatistics.right.map(s => [s.class_id, s]));

    return Array.from(classIds).map(id => {
      const left = leftMap.get(id);
      const right = rightMap.get(id);
      return {
        class_id: id,
        class_name: left?.class_name || right?.class_name || `Class ${id}`,
        color: left?.color || right?.color || [128, 128, 128],
        left_percentage: left?.percentage || 0,
        right_percentage: right?.percentage || 0,
        left_volume: left?.volume_mm3,
        right_volume: right?.volume_mm3,
      };
    }).sort((a, b) => (b.left_percentage + b.right_percentage) - (a.left_percentage + a.right_percentage));
  };

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

        {hasVolume && totalVolumeMm3 > 0 && (
          <div className="summary-item">
            <span className="label">Total Tissue Volume</span>
            <span className="value">{formatVolume(totalVolumeMm3)}</span>
          </div>
        )}
      </div>

      {/* Stats view toggle */}
      <div className="stats-view-toggle">
        <button
          className={statsView === 'overall' ? 'active' : ''}
          onClick={() => setStatsView('overall')}
        >
          Overall
        </button>
        <button
          className={statsView === 'lr' ? 'active' : ''}
          onClick={() => setStatsView('lr')}
          disabled={!lrStatistics}
        >
          Left / Right
        </button>
      </div>

      {statsView === 'overall' ? (
        <div className="statistics-table">
          <h4>Class Statistics</h4>
          <table>
            <thead>
              <tr>
                <th>Class</th>
                <th>Pixels</th>
                <th>%</th>
                {hasVolume && <th>Volume</th>}
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
                    {hasVolume && (
                      <td>{stat.volume_mm3 != null ? formatVolume(stat.volume_mm3) : '-'}</td>
                    )}
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="statistics-table">
          <h4>Left / Right Comparison</h4>
          <table>
            <thead>
              <tr>
                <th>Class</th>
                <th>Left %</th>
                <th>Right %</th>
                {hasVolume && <th>Left Vol</th>}
                {hasVolume && <th>Right Vol</th>}
              </tr>
            </thead>
            <tbody>
              {buildLRRows().map((row) => (
                <tr key={row.class_id}>
                  <td>
                    <span
                      className="color-indicator"
                      style={{ backgroundColor: `rgb(${row.color.join(',')})` }}
                    />
                    {row.class_name}
                  </td>
                  <td>{row.left_percentage.toFixed(2)}%</td>
                  <td>{row.right_percentage.toFixed(2)}%</td>
                  {hasVolume && (
                    <td>{row.left_volume != null ? formatVolume(row.left_volume) : '-'}</td>
                  )}
                  {hasVolume && (
                    <td>{row.right_volume != null ? formatVolume(row.right_volume) : '-'}</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          <p className="lr-note">* Left/Right is based on image orientation</p>
        </div>
      )}

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
          <button
            onClick={() => handleDownload('excel')}
            disabled={isDownloading}
            className="excel-button"
          >
            Export Excel
          </button>
        </div>
      </div>
    </div>
  );
}

export default ResultsPanel;
