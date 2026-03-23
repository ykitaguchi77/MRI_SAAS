import { useMemo } from 'react';
import * as THREE from 'three';

interface ClassMeshProps {
  vertices: number[];
  faces: number[];
  color: string;
  visible: boolean;
  opacity?: number;
}

function ClassMesh({ vertices, faces, color, visible, opacity = 0.85 }: ClassMeshProps) {
  const geometry = useMemo(() => {
    const geom = new THREE.BufferGeometry();

    const positionArray = new Float32Array(vertices);
    geom.setAttribute('position', new THREE.BufferAttribute(positionArray, 3));

    const indexArray = new Uint32Array(faces);
    geom.setIndex(new THREE.BufferAttribute(indexArray, 1));

    geom.computeVertexNormals();

    return geom;
  }, [vertices, faces]);

  return (
    <mesh geometry={geometry} visible={visible}>
      <meshStandardMaterial
        color={color}
        transparent={opacity < 1}
        opacity={opacity}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}

export default ClassMesh;
