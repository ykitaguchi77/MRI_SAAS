import './Visualization.css';

interface ClassToggle3DProps {
  classes: Array<{ class_id: number; class_name: string; color: string }>;
  visibility: Record<number, boolean>;
  onToggle: (classId: number) => void;
  onShowAll: () => void;
  onHideAll: () => void;
}

function ClassToggle3D({
  classes,
  visibility,
  onToggle,
  onShowAll,
  onHideAll,
}: ClassToggle3DProps) {
  return (
    <div className="class-toggle-3d">
      <h4>Structures</h4>
      <div className="toggle-buttons-row">
        <button className="toggle-btn" onClick={onShowAll}>Show All</button>
        <button className="toggle-btn" onClick={onHideAll}>Hide All</button>
      </div>
      <div className="toggle-list">
        {classes.map((cls) => (
          <label key={cls.class_id} className="toggle-item">
            <input
              type="checkbox"
              checked={visibility[cls.class_id] ?? true}
              onChange={() => onToggle(cls.class_id)}
            />
            <span
              className="toggle-color"
              style={{ backgroundColor: cls.color }}
            />
            <span className="toggle-name">{cls.class_name}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

export default ClassToggle3D;
