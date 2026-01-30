import type { ClassStatistics } from '../../types';
import './Visualization.css';

const CLASS_FULL_NAMES: Record<number, string> = {
  0: 'Background',
  1: 'Superior Rectus',
  2: 'Lateral Rectus',
  3: 'Medial Rectus',
  4: 'Inferior Rectus',
  5: 'Optic Nerve',
  6: 'Orbital Fat',
  7: 'Lacrimal Gland',
  8: 'Superior Oblique',
  9: 'Eyeball',
};

interface ColorLegendProps {
  statistics: ClassStatistics[];
}

function ColorLegend({ statistics }: ColorLegendProps) {
  // Filter out background for display
  const visibleStats = statistics.filter(s => s.class_id !== 0);

  return (
    <div className="color-legend">
      <h3>Classes</h3>

      <div className="legend-items">
        {visibleStats.map((stat) => (
          <div key={stat.class_id} className="legend-item">
            <span
              className="color-box"
              style={{
                backgroundColor: `rgb(${stat.color.join(',')})`,
              }}
            />
            <span className="class-name">
              {stat.class_name}
              <span className="full-name">
                {CLASS_FULL_NAMES[stat.class_id]}
              </span>
            </span>
            <span className="percentage">{stat.percentage.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ColorLegend;
