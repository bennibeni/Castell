'use client';

import { CAM } from '../scene/camera.js';
import { ui } from './styles.js';

function SimulationControls({ controlsRef, simulation, modelStatus }) {
  const {
    preset,
    setPreset,
    useExternalModel,
    setUseExternalModel,
    mannequin,
    setMannequin,
    colorByRole,
    setColorByRole,
    guides,
    setGuides,
    cutaway,
    setCutaway,
    inDescent,
    goPhase,
    togglePlay,
    atBreak,
    playing,
    uiT,
    END,
    restart,
    marks,
    scrub,
    DESC,
    speed,
    changeSpeed,
  } = simulation;
  return (
    <div
      ref={controlsRef}
      style={{
        position: 'absolute',
        left: '50%',
        bottom: 16,
        transform: 'translateX(-50%)',
        width: 'min(760px, calc(100vw - 32px))',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
        {Object.entries(CAM).map(([k, v]) => (
          <button key={k} style={ui.chip(preset === k)} onClick={() => setPreset(k)}>
            {v.label}
          </button>
        ))}
        <span style={{ width: 8 }} />
        <button style={ui.chip(useExternalModel)} onClick={() => setUseExternalModel((x) => !x)}>
          Modello GLB
        </button>
        <button
          style={ui.chip(mannequin)}
          onClick={() => setMannequin((x) => !x)}
          title="Figure neutre con le articolazioni evidenziate"
        >
          Manichino
        </button>
        <button style={ui.chip(colorByRole)} onClick={() => setColorByRole((x) => !x)}>
          Colori per ruolo
        </button>
        <button style={ui.chip(guides)} onClick={() => setGuides((x) => !x)}>
          Guide geometriche
        </button>
        <button style={ui.chip(cutaway)} onClick={() => setCutaway((x) => !x)}>
          Spaccato
        </button>
      </div>
      {modelStatus?.message && (
        <div
          role="status"
          style={{
            textAlign: 'center',
            fontSize: 11,
            color: modelStatus.status === 'error' ? '#f3dca0' : '#9a968d',
          }}
        >
          {mannequin && modelStatus.status === 'ready'
            ? 'Manichino standard attivo'
            : modelStatus.message}
        </div>
      )}
      <div
        style={{
          ...ui.glass,
          padding: '10px 14px',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
        }}
      >
        <div
          style={{
            display: 'flex',
            borderRadius: 8,
            overflow: 'hidden',
            border: '1px solid rgba(255,255,255,0.14)',
          }}
        >
          {[
            ['salita', 'Salita', '#d9b45c'],
            ['discesa', 'Discesa', '#7fb2e6'],
          ].map(([k, label, col]) => {
            const on = k === 'discesa' ? inDescent : !inDescent;
            return (
              <button
                key={k}
                onClick={() => goPhase(k)}
                title={
                  k === 'salita'
                    ? 'Dalla formazione al castell carregat'
                    : 'Dal castell carregat al descarregat'
                }
                style={{
                  padding: '7px 10px',
                  fontSize: 12,
                  border: 'none',
                  cursor: 'pointer',
                  background: on ? col : 'transparent',
                  color: on ? '#14110a' : '#cfcbc2',
                  fontWeight: on ? 700 : 500,
                }}
              >
                {label}
              </button>
            );
          })}
        </div>
        <button
          onClick={togglePlay}
          style={{
            width: 92,
            padding: '8px 0',
            borderRadius: 8,
            border: 'none',
            background: atBreak ? '#7fb2e6' : '#d9b45c',
            color: '#1a1408',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          {playing ? 'Pausa' : uiT >= END - 0.01 ? 'Rivedi' : atBreak ? 'Discesa ▶' : 'Avvia'}
        </button>
        <button
          onClick={restart}
          title="Ricomincia"
          style={{ ...ui.chip(false), padding: '7px 10px' }}
        >
          ↺
        </button>
        <div style={{ position: 'relative', flex: '1 1 220px', minWidth: 200, paddingTop: 14 }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 12 }}>
            {marks.map((m) => (
              <span
                key={m.label}
                style={{
                  position: 'absolute',
                  left: `${((m.t / END) * 100).toFixed(3)}%`,
                  transform: 'translateX(-50%)',
                  fontSize: 9.5,
                  color: uiT >= m.t ? '#d9b45c' : '#77736b',
                  whiteSpace: 'nowrap',
                }}
              >
                {m.label}
              </span>
            ))}
          </div>
          <input
            type="range"
            min={0}
            max={END}
            step={0.01}
            value={uiT}
            onChange={(e) => scrub(parseFloat(e.target.value))}
            style={{
              width: '100%',
              accentColor: inDescent ? '#7fb2e6' : '#d9b45c',
              cursor: 'pointer',
            }}
          />
          {/* barra delle due fasi */}
          <div
            style={{
              display: 'flex',
              height: 4,
              borderRadius: 2,
              overflow: 'hidden',
              marginTop: 2,
            }}
          >
            <div
              style={{
                width: `${((DESC / END) * 100).toFixed(3)}%`,
                background: 'rgba(217,180,92,0.55)',
              }}
            />
            <div style={{ width: 2, background: '#07070b' }} />
            <div style={{ flex: 1, background: 'rgba(127,178,230,0.55)' }} />
          </div>
        </div>
        <span
          style={{ fontSize: 12, color: '#bdb8ad', minWidth: 70, textAlign: 'right', ...ui.num }}
        >
          {uiT.toFixed(1)} / {END.toFixed(0)} s
        </span>
        <div style={{ display: 'flex', gap: 4 }}>
          {[0.5, 1, 2].map((s) => (
            <button
              key={s}
              onClick={() => changeSpeed(s)}
              style={{ ...ui.chip(speed === s), padding: '5px 8px' }}
            >
              {s}×
            </button>
          ))}
        </div>
      </div>
      <div style={{ textAlign: 'center', fontSize: 11, color: '#6f6b63' }}>
        Trascina per ruotare · rotellina per lo zoom · barra spaziatrice per pausa
      </div>
    </div>
  );
}

export { SimulationControls };
