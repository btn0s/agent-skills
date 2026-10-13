import { createRoot } from 'react-dom/client'
import { Canvas } from '@react-three/fiber'
import { Physics, RigidBody } from '@react-three/rapier'
import './style.css'

function Scene() {
  return <>
    <ambientLight intensity={1.4} />
    <directionalLight position={[4, 8, 5]} intensity={2} />
    <Physics gravity={[0, -9.8, 0]}>
      <RigidBody position={[0, 2, 0]}><mesh castShadow><boxGeometry /><meshStandardMaterial color="#edb25d" /></mesh></RigidBody>
      <RigidBody type="fixed"><mesh position-y={-0.2} receiveShadow><boxGeometry args={[20, 0.4, 20]} /><meshStandardMaterial color="#314d55" /></mesh></RigidBody>
    </Physics>
  </>
}
createRoot(document.getElementById('root')!).render(<><Canvas camera={{ position: [4, 3, 6] }}><Scene /></Canvas><div className="hud">Blank game scene</div></>)
