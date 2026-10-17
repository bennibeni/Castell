'use client';

import { useAthleteAsset } from './hooks/useAthleteAsset.js';
import { useSimulation } from './hooks/useSimulation.js';
import { useSimulationLayout } from './hooks/useSimulationLayout.js';
import { ui } from './ui/styles.js';
import { Canvas } from '@react-three/fiber';
import { FOV } from './simulation/constants.js';
import { Scene } from './scene/Scene.jsx';
import { StatusPanels } from './ui/StatusPanels.jsx';
import { SimulationControls } from './ui/SimulationControls.jsx';

function AcrobatSimulation() {
  const simulation = useSimulation();
  const athleteAsset = useAthleteAsset(simulation.useExternalModel);
  const {
    plan,
    tRef,
    playingRef,
    speedRef,
    onTick,
    onEnd,
    onUserCamera,
    colorByRole,
    mannequin,
    cutaway,
    guides,
    preset,
    uiT,
    panelOpen,
    setPanelOpen,
  } = simulation;
  const { controlsRef, controlsHeight, topPx } = useSimulationLayout(setPanelOpen);
  return (
    <div style={{ ...ui.root, top: topPx, height: `calc(100dvh - ${topPx}px)` }}>
      <Canvas
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: `calc(100% - ${controlsHeight}px)`,
        }}
        dpr={[1, 2]}
        camera={{ position: [13.4, 2.0, 13.4], fov: FOV, near: 0.1, far: 200 }}
        gl={{ antialias: true }}
      >
        <Scene
          athleteScene={athleteAsset.scene}
          plan={plan}
          tRef={tRef}
          playingRef={playingRef}
          speedRef={speedRef}
          onTick={onTick}
          onEnd={onEnd}
          onUserCamera={onUserCamera}
          colorByRole={colorByRole}
          mannequin={mannequin}
          cutaway={cutaway}
          guides={guides}
          preset={preset}
        />
      </Canvas>
      <StatusPanels plan={plan} uiT={uiT} panelOpen={panelOpen} setPanelOpen={setPanelOpen} />
      <SimulationControls
        controlsRef={controlsRef}
        simulation={simulation}
        modelStatus={athleteAsset}
      />
    </div>
  );
}

export default AcrobatSimulation;
