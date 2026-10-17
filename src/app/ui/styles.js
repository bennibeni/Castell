const ui = {
  // Contenitore fisso; useSimulationLayout misura intestazione e comandi.
  root: {
    position: 'fixed',
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 30,
    background: '#07070b',
    color: '#ece9e1',
    fontFamily: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif',
    overflow: 'hidden',
  },
  glass: {
    background: 'rgba(14,14,20,0.82)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 12,
    backdropFilter: 'blur(10px)',
    boxShadow: '0 10px 30px rgba(0,0,0,0.45)',
  },
  kicker: {
    fontSize: 11,
    letterSpacing: '0.14em',
    textTransform: 'uppercase',
    color: '#d9b45c',
    fontWeight: 600,
  },
  num: { fontVariantNumeric: 'tabular-nums' },
  chip: (on) => ({
    padding: '6px 10px',
    borderRadius: 999,
    fontSize: 12,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    border: `1px solid ${on ? '#d9b45c' : 'rgba(255,255,255,0.14)'}`,
    background: on ? 'rgba(217,180,92,0.18)' : 'rgba(255,255,255,0.03)',
    color: on ? '#f3dca0' : '#cfcbc2',
  }),
};

export { ui };
