import { createRoot } from 'react-dom/client'
import { Canvas, createPortal, useFrame, useThree } from '@react-three/fiber'
import { Physics, CuboidCollider, RigidBody } from '@react-three/rapier'
import { useMemo, useRef, useState, useSyncExternalStore } from 'react'
import type { Object3D } from 'three'
import { Vector3 } from 'three'
import { Character } from 'als-ue5-r3f/app/Character'
import { AlsCamera } from 'als-ue5-r3f/app/AlsCamera'
import { createWorldTimeState } from 'als-ue5-r3f/engine/timeDilation'
import { AlsFootstepAudioRuntime } from '../vendor/als-web/src/engine/alsAudioBridge'
import { Operator, createOperator } from '@blacksite/operator'
import type { OperatorState } from '@blacksite/operator'
import { ALS_WEAPONS, createWeaponRuntime } from '@blacksite/arsenal'
import './style.css'

const noHits = { castRay: () => null, sweepSphere: () => null }

function BodyVisibility({ scene, controller }: { scene: Object3D; controller: OperatorState }) {
  useFrame(() => { scene.visible = controller.view === 'third-person' })
  return null
}

function Arms({ controller }: { controller: OperatorState }) {
  const { camera } = useThree()
  const color = controller.weapon === 'pistol' ? '#b9b8a4' : '#586871'
  if (controller.view !== 'first-person') return null
  return createPortal(<group position={[0.27, -0.29, -0.48]} rotation={[0, -0.13, 0]}>
    <mesh position={[-0.2, -0.1, 0.06]} rotation-z={-0.38}><capsuleGeometry args={[0.055, 0.31, 4, 8]} /><meshStandardMaterial color="#b99a79" /></mesh>
    <mesh position={[0.12, -0.12, 0.03]} rotation-z={0.28}><capsuleGeometry args={[0.055, 0.29, 4, 8]} /><meshStandardMaterial color="#b99a79" /></mesh>
    <mesh position={[0, 0, -0.17]} rotation-x={Math.PI / 2}><cylinderGeometry args={[0.045, 0.06, 0.64, 10]} /><meshStandardMaterial color={color} metalness={0.6} roughness={0.4} /></mesh>
    <mesh position={[0, -0.045, 0.06]}><boxGeometry args={[0.16, 0.13, 0.22]} /><meshStandardMaterial color="#23333c" /></mesh>
  </group>, camera)
}

function WeaponDriver({ controller, onShot }: { controller: OperatorState; onShot: () => void }) {
  const runtime = useMemo(() => createWeaponRuntime({ ownerId: 'local', seed: 1, definitions: ALS_WEAPONS }), [])
  const lastReload = useRef(0)
  const accumulated = useRef(0)
  useFrame((_, delta) => {
    const frame = controller.frame
    if (!frame.ready) return
    accumulated.current = Math.min(accumulated.current + delta, 0.1)
    while (accumulated.current >= 1 / 60) {
    accumulated.current -= 1 / 60
    const origin = frame.aimOrigin
    const direction = frame.aimDirection
    const muzzle = frame.muzzlePosition
    const reload = controller.input.reloadSequence !== lastReload.current
    lastReload.current = controller.input.reloadSequence
    const events = runtime.step({
      tick: runtime.snapshot().nextTick,
      trigger: controller.input.fire,
      reload,
      selectWeaponId: controller.weapon,
      aim: { origin: { x: origin.x, y: origin.y, z: origin.z }, direction: { x: direction.x, y: direction.y, z: direction.z } },
      muzzle: { x: muzzle.x, y: muzzle.y, z: muzzle.z },
    }, noHits)
    for (const event of events) if (event.type === 'shot') { controller.addRecoil(event.recoil.pitch * 180 / Math.PI); onShot() }
    }
  }, 0.5)
  return null
}

function Scene({ controller, onShot }: { controller: OperatorState; onShot: () => void }) {
  const time = useMemo(createWorldTimeState, [])
  const audio = useMemo(() => new AlsFootstepAudioRuntime({ AutoInstallUserGestureUnlock: true }), [])
  const inputSource = () => {
    const command = controller.player.command
    const yaw = command.yaw * Math.PI / 180
    const x = command.forward * Math.cos(yaw) - command.right * Math.sin(yaw)
    const z = command.forward * Math.sin(yaw) + command.right * Math.cos(yaw)
    return { movementDirection: { x: command.active ? x : 0, z: command.active ? z : 0 }, desiredGait: command.sprint ? 'Sprinting' as const : 'Running' as const, desiredStance: command.crouch ? 'Crouching' as const : 'Standing' as const, viewYawAngle: command.yaw, viewPitchAngle: command.pitch, aiming: command.aim, overlayMode: command.overlay }
  }
  return <>
    <ambientLight intensity={1.5} />
    <directionalLight position={[5, 12, 4]} intensity={2.5} castShadow />
    <Physics gravity={[0, -9.8, 0]} timeStep={1 / 60}>
      <Character onSizeChange={() => {}} poseSample={controller.player.pose} worldTime={time} onOverlayModeBridgeChange={() => {}} footstepSoundSink={audio} inputSource={inputSource} inputEnabled={false} initialPosition={controller.player.spawn} renderOverlayObject={(scene) => <BodyVisibility scene={scene} controller={controller} />} />
      {controller.view === 'third-person' && <AlsCamera poseSample={controller.player.pose} worldTime={time} footstepAudioRuntime={audio} toggleViewModeKey={null} gamepadEnabled={false} />}
      <Operator controller={controller} />
      <WeaponDriver controller={controller} onShot={onShot} />
      <RigidBody type="fixed" colliders={false}><CuboidCollider args={[30, 0.1, 30]} position={[0, -0.1, 0]} /></RigidBody>
    </Physics>
    <Arms controller={controller} />
    <mesh rotation-x={-Math.PI / 2} position-y={-0.01} receiveShadow><planeGeometry args={[60, 60]} /><meshStandardMaterial color="#293743" /></mesh>
    <gridHelper args={[60, 30, '#506d77', '#394c58']} />
  </>
}

function App() {
  const controller = useMemo(() => createOperator(), [])
  const snapshot = useSyncExternalStore(controller.subscribe, controller.getSnapshot)
  const [shots, setShots] = useState(0)
  return <>
    <Canvas shadows camera={{ position: [0, 1.63, 0], fov: 75 }}><Scene controller={controller} onShot={() => setShots(value => value + 1)} /></Canvas>
    <div className="hud"><strong>First person · {snapshot.weapon}</strong><span>Click scene · WASD move · Mouse look · V switch view · 1–3 weapon · R reload · Left click fire</span><span>Shots: {shots}</span></div>
    {snapshot.view === 'first-person' && <div className="reticle">+</div>}
  </>
}

createRoot(document.getElementById('root')!).render(<App />)
