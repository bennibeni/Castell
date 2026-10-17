'use client';

import { useState, useEffect, useRef, useLayoutEffect } from 'react';

/**
 * Bordo superiore della simulazione = fondo dell'intestazione del sito (<header>), misurato:
 * la simulazione resta fissa a tutta larghezza ma non finisce sotto il menu, qualunque altezza
 * abbia. Si aggiorna con la finestra e con l'intestazione. Il setState avviene solo nei callback.
 * Su schermi stretti il pannello dei piani parte chiuso.
 */
function useLayout(setPanelOpen) {
  const [top, setTop] = useState(0);
  useEffect(() => {
    const header = document.querySelector('header');
    const measure = () =>
      setTop(header ? Math.max(0, Math.round(header.getBoundingClientRect().bottom)) : 0);
    const raf = requestAnimationFrame(() => {
      measure();
      if (window.innerWidth < 900) setPanelOpen(false);
    });
    window.addEventListener('resize', measure);
    window.addEventListener('scroll', measure, { passive: true });
    const ro = header ? new ResizeObserver(() => requestAnimationFrame(measure)) : null;
    if (ro) ro.observe(header);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', measure);
      window.removeEventListener('scroll', measure);
      if (ro) ro.disconnect();
    };
  }, [setPanelOpen]);
  return top;
}

function useSimulationLayout(setPanelOpen) {
  const controlsRef = useRef(null);
  const [controlsHeight, setControlsHeight] = useState(180);

  // Il canvas usa solo lo spazio sopra i comandi, anche quando vanno a capo.
  useLayoutEffect(() => {
    const element = controlsRef.current;
    if (!element) return;
    const measure = () => setControlsHeight(Math.ceil(element.getBoundingClientRect().height) + 32);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const topPx = useLayout(setPanelOpen);

  return { controlsRef, controlsHeight, topPx };
}

export { useSimulationLayout };
