'use client';

import { useState } from 'react';
import { ui } from './styles.js';
import { topHeightAt, present, phaseAt, baixLoadAt, PIS_FEET } from '../simulation/status.js';
import { PIS_COLORS, PIS_NAMES, PINYA_COLOR } from '../simulation/constants.js';

function Stat({ label, value }) {
  return (
    <div>
      <div
        style={{
          fontSize: 10.5,
          color: '#9a968d',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 17, fontWeight: 600, ...ui.num }}>{value}</div>
    </div>
  );
}

function StatusPanels({ plan, uiT, panelOpen, setPanelOpen }) {
  const [phasePanelOpen, setPhasePanelOpen] = useState(false);
  const top = topHeightAt(plan, uiT);
  const inCastell = plan.athletes.filter((a) => a.climber && present(a, uiT)).length;
  const phase = phaseAt(plan, uiT);
  const stateOf = (p) => {
    const m = plan.pis[p].members;
    if (m.some((a) => a.climber && uiT >= a.climbStart && uiT < a.arrive)) return 'sale';
    if (m.some((a) => a.climber && uiT >= a.descStart && uiT < a.descEnd)) return 'scende';
    if (m.every((a) => present(a, uiT))) return 'in posizione';
    if (m.every((a) => uiT >= a.descStart)) return 'a terra';
    return 'in attesa';
  };

  return (
    <>
      <style>
        {
          '.r57-table th,.r57-table td{border:0;background:transparent;color:inherit;box-shadow:none}.r57-table tr{border:0;background:transparent}'
        }
      </style>
      {/* scheda fase */}
      <div
        style={{
          position: 'absolute',
          top: 16,
          left: 16,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          gap: 8,
        }}
      >
        <button
          onClick={() => setPhasePanelOpen((open) => !open)}
          style={ui.chip(phasePanelOpen)}
          aria-expanded={phasePanelOpen}
          aria-controls="castell-phase-panel"
        >
          {phasePanelOpen ? 'Nascondi scheda' : 'Scheda'}
        </button>
        {phasePanelOpen && (
          <div
            id="castell-phase-panel"
            style={{
              ...ui.glass,
              padding: '14px 16px',
              width: 'min(360px, calc(100vw - 120px))',
            }}
          >
            <div style={ui.kicker}>Castell 4 de 8</div>
            <div style={{ fontSize: 20, fontWeight: 650, marginTop: 6 }}>{phase.title}</div>
            <div
              style={{
                fontSize: 13,
                lineHeight: 1.45,
                color: '#bdb8ad',
                marginTop: 4,
                minHeight: 38,
              }}
            >
              {phase.sub}
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '10px 16px',
                marginTop: 12,
              }}
            >
              <Stat label="Altezza della cima" value={`${top.toFixed(1)} m`} />
              <Stat label="Nel castell / pinya" value={`${inCastell} / 70`} />
              <Stat label="Carico su ogni baix" value={`≈ ${Math.round(baixLoadAt(plan, uiT))} kg`} />
              <Stat
                label="Piani completi"
                value={`${[1, 2, 3, 4, 5, 6, 7, 8].filter((p) => plan.pis[p].members.every((a) => present(a, uiT))).length} / 8`}
              />
            </div>
          </div>
        )}
      </div>

      {/* tabella piani */}
      <div
        style={{
          position: 'absolute',
          top: 16,
          right: 16,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          gap: 8,
        }}
      >
        <button onClick={() => setPanelOpen((o) => !o)} style={ui.chip(panelOpen)}>
          {panelOpen ? 'Nascondi piani' : 'Piani'}
        </button>
        {panelOpen && (
          <div style={{ ...ui.glass, padding: '12px 14px', width: 320 }}>
            <table
              className="r57-table"
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: 12.5,
                background: 'transparent',
                ...ui.num,
              }}
            >
              <thead>
                <tr
                  style={{
                    color: '#9a968d',
                    fontSize: 10.5,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                  }}
                >
                  <th style={{ textAlign: 'left', paddingBottom: 6 }}>Pis</th>
                  <th style={{ textAlign: 'left' }}>Ruolo</th>
                  <th style={{ textAlign: 'right' }}>N</th>
                  <th style={{ textAlign: 'right' }}>Piedi</th>
                  <th style={{ textAlign: 'right' }}>Stato</th>
                </tr>
              </thead>
              <tbody>
                {[8, 7, 6, 5, 4, 3, 2, 1].map((p) => {
                  const st = stateOf(p);
                  return (
                    <tr
                      key={p}
                      style={{ opacity: st === 'in attesa' || st === 'a terra' ? 0.5 : 1 }}
                    >
                      <td style={{ padding: '3px 0' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            width: 9,
                            height: 9,
                            borderRadius: 2,
                            background: PIS_COLORS[p - 1],
                            marginRight: 7,
                          }}
                        />
                        {p}
                      </td>
                      <td>{PIS_NAMES[p - 1]}</td>
                      <td style={{ textAlign: 'right' }}>{plan.pis[p].members.length}</td>
                      <td style={{ textAlign: 'right' }}>{PIS_FEET(p).toFixed(1)} m</td>
                      <td
                        style={{
                          textAlign: 'right',
                          color: st === 'sale' || st === 'scende' ? '#f3dca0' : undefined,
                        }}
                      >
                        {st}
                      </td>
                    </tr>
                  );
                })}
                <tr style={{ color: '#9a968d' }}>
                  <td style={{ paddingTop: 6 }}>
                    <span
                      style={{
                        display: 'inline-block',
                        width: 9,
                        height: 9,
                        borderRadius: 2,
                        background: PINYA_COLOR,
                        marginRight: 7,
                      }}
                    />
                    —
                  </td>
                  <td style={{ paddingTop: 6 }}>Pinya</td>
                  <td style={{ textAlign: 'right', paddingTop: 6 }}>66</td>
                  <td colSpan={2} style={{ textAlign: 'right', paddingTop: 6 }}>
                    a terra
                  </td>
                </tr>
              </tbody>
            </table>
            <div style={{ fontSize: 11.5, color: '#9a968d', lineHeight: 1.45, marginTop: 10 }}>
              Tronc 5 × 4 = 20 · pom de dalt 2 + 1 + 1 = 4 · pinya 66 (agulla 1, crosses 8,
              contraforts 4, mans 12, vents 12, laterals 16, darrer cordó 12, cap de colla 1).
              Carico calcolato con masse ipotizzate: segons 70 kg, terços 62, quarts 55, quints 50,
              dosos 32, aixecador 26, enxaneta 20.
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export { StatusPanels };
