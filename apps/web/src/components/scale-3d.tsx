"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { ContactShadows, Environment, Float } from "@react-three/drei";
import { useMemo, useRef } from "react";
import * as THREE from "three";

/* A balance scale built from primitives: no model files, no textures.
   The beam follows the pointer (tilt) and settles back, like a real balance
   finding equilibrium. Brass metal on an ink background. */

const BRASS = "#c9a44c";
const INK = "#1b2236";

function Pan({ x }: { x: number }) {
  return (
    <group position={[x, 0, 0]}>
      {[-0.42, 0.42].map((z) => (
        <mesh key={z} position={[0, -0.55, z * 0.5]} rotation={[0, 0, 0]}>
          <cylinderGeometry args={[0.012, 0.012, 1.1, 8]} />
          <meshStandardMaterial color={BRASS} metalness={0.9} roughness={0.35} />
        </mesh>
      ))}
      <mesh position={[0, -1.1, 0]}>
        <cylinderGeometry args={[0.62, 0.52, 0.08, 48]} />
        <meshStandardMaterial color={BRASS} metalness={0.85} roughness={0.3} />
      </mesh>
      <mesh position={[0, -1.06, 0]}>
        <cylinderGeometry args={[0.58, 0.58, 0.02, 48]} />
        <meshStandardMaterial color={INK} metalness={0.2} roughness={0.8} />
      </mesh>
    </group>
  );
}

function Beam() {
  const group = useRef<THREE.Group>(null);
  const { pointer } = useThree();
  const target = useRef(0);
  useFrame((state, dt) => {
    const idle = Math.sin(state.clock.elapsedTime * 0.6) * 0.035;
    target.current = THREE.MathUtils.clamp(-pointer.x * 0.22, -0.3, 0.3) + idle;
    if (group.current) {
      group.current.rotation.z = THREE.MathUtils.damp(
        group.current.rotation.z,
        target.current,
        2.2,
        dt,
      );
    }
  });
  return (
    <group ref={group} position={[0, 1.15, 0]}>
      <mesh>
        <boxGeometry args={[3.6, 0.07, 0.14]} />
        <meshStandardMaterial color={BRASS} metalness={0.9} roughness={0.3} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.11, 0.11, 0.26, 24]} />
        <meshStandardMaterial color={INK} metalness={0.4} roughness={0.5} />
      </mesh>
      <Pan x={-1.65} />
      <Pan x={1.65} />
    </group>
  );
}

function Column() {
  return (
    <group>
      <mesh position={[0, 0.2, 0]}>
        <cylinderGeometry args={[0.05, 0.07, 2.1, 24]} />
        <meshStandardMaterial color={BRASS} metalness={0.9} roughness={0.35} />
      </mesh>
      <mesh position={[0, -0.9, 0]}>
        <cylinderGeometry args={[0.9, 1.0, 0.12, 64]} />
        <meshStandardMaterial color={INK} metalness={0.3} roughness={0.6} />
      </mesh>
      <mesh position={[0, -0.82, 0]}>
        <torusGeometry args={[0.72, 0.012, 12, 96]} />
        <meshStandardMaterial color={BRASS} metalness={0.9} roughness={0.3} />
      </mesh>
    </group>
  );
}

export function Scale3D({ className }: { className?: string }) {
  const dpr = useMemo<[number, number]>(() => [1, 1.75], []);
  return (
    <div className={className} aria-hidden>
      <Canvas dpr={dpr} camera={{ position: [0, 0.8, 8.2], fov: 30 }} gl={{ antialias: true, alpha: true }}>
        <ambientLight intensity={0.35} />
        <directionalLight position={[4, 6, 5]} intensity={1.6} />
        <directionalLight position={[-5, 2, -3]} intensity={0.5} color="#b8c4ff" />
        <Float speed={1.2} rotationIntensity={0.12} floatIntensity={0.35}>
          <group position={[0, -0.25, 0]}>
            <Column />
            <Beam />
          </group>
        </Float>
        <ContactShadows position={[0, -1.25, 0]} opacity={0.5} scale={9} blur={2.6} far={3} />
        <Environment preset="city" />
      </Canvas>
    </div>
  );
}
