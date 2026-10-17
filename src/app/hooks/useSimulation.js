'use client';

import { useMemo, useRef, useState, useCallback, useEffect } from 'react';
import { buildPlan } from '../simulation/plan.js';

function useSimulation() {
  const plan = useMemo(() => buildPlan(), []);
  const END = plan.T.end;
  const tRef = useRef(0);
  const playingRef = useRef(true);
  const speedRef = useRef(1);
  const [uiT, setUiT] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [colorByRole, setColorByRole] = useState(false);
  const [useExternalModel, setUseExternalModel] = useState(true);
  const [mannequin, setMannequin] = useState(false);
  const [cutaway, setCutaway] = useState(false);
  const [guides, setGuides] = useState(false);
  const [preset, setPreset] = useState('video');
  const [panelOpen, setPanelOpen] = useState(true);
  const onTick = useCallback((t) => setUiT(t), []);
  const onEnd = useCallback(() => {
    playingRef.current = false;
    setPlaying(false);
  }, []);
  const onUserCamera = useCallback(() => setPreset('libera'), []);

  const togglePlay = useCallback(() => {
    const next = !playingRef.current;
    if (next && tRef.current >= END - 0.01) tRef.current = 0;
    playingRef.current = next;
    setPlaying(next);
  }, [END]);
  const restart = () => {
    tRef.current = 0;
    setUiT(0);
    playingRef.current = true;
    setPlaying(true);
  };
  const DESC = plan.T.descent;
  const goPhase = (which) => {
    const t0 = which === 'discesa' ? DESC : 0;
    tRef.current = t0;
    setUiT(t0);
    playingRef.current = true;
    setPlaying(true);
  };
  const inDescent = uiT > DESC + 0.01;
  const atBreak = !playing && Math.abs(uiT - DESC) < 0.02;
  const scrub = (v) => {
    tRef.current = v;
    setUiT(v);
    playingRef.current = false;
    setPlaying(false);
  };
  const changeSpeed = (s) => {
    speedRef.current = s;
    setSpeed(s);
  };

  useEffect(() => {
    const onKey = (e) => {
      if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {
        e.preventDefault();
        togglePlay();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [togglePlay]);

  const marks = [
    { t: plan.T.tPinya, label: 'pinya' },
    { t: plan.pis[6].start, label: 'pom' },
    { t: plan.T.aletaStart, label: 'aleta' },
    { t: plan.pis[5].descStart, label: 'tronc giù' },
  ];
  return {
    plan,
    END,
    DESC,
    tRef,
    playingRef,
    speedRef,
    uiT,
    playing,
    speed,
    colorByRole,
    setColorByRole,
    mannequin,
    setMannequin,
    useExternalModel,
    setUseExternalModel,
    cutaway,
    setCutaway,
    guides,
    setGuides,
    preset,
    setPreset,
    panelOpen,
    setPanelOpen,
    onTick,
    onEnd,
    onUserCamera,
    togglePlay,
    restart,
    goPhase,
    inDescent,
    atBreak,
    scrub,
    changeSpeed,
    marks,
  };
}

export { useSimulation };
