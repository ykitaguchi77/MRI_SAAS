import { useState, useEffect, useCallback } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import type { Mesh3DResponse } from '../../types';
import { getMesh3D } from '../../services/api';
import ClassMesh from './ClassMesh';
import ClassToggle3D from './ClassToggle3D';
import LoadingSpinner from '../common/LoadingSpinner';
import './Visualization.css';

interface Viewer3DProps {
  sessionId: string;
  onClose: () => void;
}

function Viewer3D({ sessionId, onClose }: Viewer3DProps) {
  const [meshData, setMeshData] = useState<Mesh3DResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [visibility, setVisibility] = useState<Record<number, boolean>>({});

  useEffect(() => {
    let cancelled = false;

    async function loadMesh() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getMesh3D(sessionId);
        if (cancelled) return;
        setMeshData(data);

        // Initialize all classes as visible
        const vis: Record<number, boolean> = {};
        data.classes.forEach((cls) => {
          vis[cls.class_id] = true;
        });
        setVisibility(vis);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load 3D data');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadMesh();
    return () => { cancelled = true; };
  }, [sessionId]);

  const handleToggle = useCallback((classId: number) => {
    setVisibility((prev) => ({ ...prev, [classId]: !prev[classId] }));
  }, []);

  const handleShowAll = useCallback(() => {
    setVisibility((prev) => {
      const next: Record<number, boolean> = {};
      for (const key of Object.keys(prev)) next[Number(key)] = true;
      return next;
    });
  }, []);

  const handleHideAll = useCallback(() => {
    setVisibility((prev) => {
      const next: Record<number, boolean> = {};
      for (const key of Object.keys(prev)) next[Number(key)] = false;
      return next;
    });
  }, []);

  // Calculate camera distance from bounds
  const getCameraDistance = () => {
    if (!meshData || meshData.bounds.length < 6) return 200;
    const [minX, minY, minZ, maxX, maxY, maxZ] = meshData.bounds;
    const size = Math.max(maxX - minX, maxY - minY, maxZ - minZ);
    return Math.max(size * 1.8, 50);
  };

  return (
    <div className="viewer3d-container">
      <div className="viewer3d-header">
        <h3>3D Visualization</h3>
        <button className="viewer3d-close" onClick={onClose}>
          Back to 2D
        </button>
      </div>
      <div className="viewer3d-content">
        {meshData && meshData.classes.length > 0 && (
          <ClassToggle3D
            classes={meshData.classes}
            visibility={visibility}
            onToggle={handleToggle}
            onShowAll={handleShowAll}
            onHideAll={handleHideAll}
          />
        )}
        <div className="viewer3d-canvas-wrapper">
          {isLoading ? (
            <div className="viewer3d-loading">
              <LoadingSpinner />
              <p>Generating 3D meshes...</p>
            </div>
          ) : error ? (
            <div className="viewer3d-error">
              <p>{error}</p>
              <button onClick={onClose}>Go Back</button>
            </div>
          ) : meshData && meshData.classes.length > 0 ? (
            <Canvas
              camera={{
                position: [0, 0, -getCameraDistance()],
                up: [0, -1, 0],
                fov: 50,
                near: 0.1,
                far: 10000,
              }}
              style={{ background: '#1a1a2e' }}
            >
              <ambientLight intensity={0.4} />
              <directionalLight position={[10, 10, 10]} intensity={0.8} />
              <directionalLight position={[-10, -10, -5]} intensity={0.3} />
              <directionalLight position={[0, 10, -10]} intensity={0.2} />
              <OrbitControls enableDamping dampingFactor={0.1} />
              {meshData.classes.map((cls) => (
                <ClassMesh
                  key={cls.class_id}
                  vertices={cls.vertices}
                  faces={cls.faces}
                  color={cls.color}
                  visible={visibility[cls.class_id] ?? true}
                />
              ))}
            </Canvas>
          ) : (
            <div className="viewer3d-error">
              <p>No structures detected for 3D rendering</p>
              <button onClick={onClose}>Go Back</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Viewer3D;
