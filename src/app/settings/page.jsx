'use client';
import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { BODIES, HEADS, DEFAULT_COMPOSITION, COMPOSITION_EVENT, compatible, normalizeComposition } from '../scene/athlete/catalog.js';
import { getSessionComposition, setSessionComposition } from '../scene/athlete/session.js';
import './settings.css';
const Preview=dynamic(()=>import('./Preview.jsx'),{ssr:false,loading:()=> <p className="preview-message">Avvio anteprima 3D…</p>});

export default function SettingsPage(){
  const [draft,setSelection]=useState({...DEFAULT_COMPOSITION});
  const [stored,setSaved]=useState({...DEFAULT_COMPOSITION});
  const selection=normalizeComposition(draft);
  const saved=normalizeComposition(stored);
  const [face,setFace]=useState(false);
  const [status,setStatus]=useState('loading');
  const [notice,setNotice]=useState('');
  const [hydrated,setHydrated]=useState(false);
  const onStatus=useCallback(value=>setStatus(value),[]);
  useEffect(()=>{
    const value=getSessionComposition();setSelection(value);setSaved(value);
    setHydrated(true);
  },[]);
  const dirty=selection.bodyId!==saved.bodyId||selection.headId!==saved.headId;
  const body=BODIES.find(item=>item.id===selection.bodyId);
  const head=HEADS.find(item=>item.id===selection.headId);
  function chooseBody(id){
    if(id===selection.bodyId)return;
    const valid=compatible(id,selection.headId);
    setSelection(normalizeComposition({bodyId:id,headId:selection.headId}));
    setStatus('loading');
    setNotice(valid?'':'Selezionata una testa disponibile per questo corpo.');
  }
  function save(){
    if(status!=='ready'||!compatible(selection.bodyId,selection.headId))return;
    const applied=setSessionComposition(selection);
    window.dispatchEvent(new Event(COMPOSITION_EVENT));
    setSaved(applied);setNotice('Composizione applicata alle 90 atlete per questa sessione. Al prossimo avvio si riparte dal manichino originale.');
  }
  return <main className="settings-page">
    <header className="settings-header"><Link href="/" className="settings-brand">CASTELL<span>STUDIO</span></Link><Link href="/" className="settings-back">← Torna alla simulazione</Link></header>
    <div className="settings-intro"><span className="eyebrow">SETTINGS / PERSONAGGI</span><h1>La tua atleta.</h1><p>Scegli un corpo, abbina una testa e guarda il risultato prima di portarlo nella torre.</p></div>
    <div className="settings-layout">
      <section className="catalog-panel" aria-label="Catalogo delle parti">
        <div className="catalog-heading"><span className="step-number">01</span><div><h2>Il corpo</h2><p>La base della tua composizione</p></div></div>
        <div className="body-options">{BODIES.map(item=><button key={item.id} disabled={!hydrated} className={`asset-card body-card ${selection.bodyId===item.id?'selected':''}`} aria-pressed={selection.bodyId===item.id} onClick={()=>chooseBody(item.id)}><div className="asset-image"><img src={item.image} alt=""/><span className="selection-dot"/></div><div className="asset-description"><strong>{item.label}</strong><small>{item.description}</small></div></button>)}</div>
        <div className="catalog-heading head-heading"><span className="step-number">02</span><div><h2>La testa</h2><p>Viso, sguardo e capelli</p></div></div>
        <div className="head-options">{HEADS.map(item=>{
          const allowed=compatible(selection.bodyId,item.id);
          return <button key={item.id} disabled={!hydrated||!allowed} className={`asset-card head-card ${selection.headId===item.id?'selected':''}`} aria-pressed={selection.headId===item.id} onClick={()=>{if(item.id===selection.headId)return;setSelection({...selection,headId:item.id});setStatus('loading');setNotice('');}}><div className="asset-image"><img src={item.image} alt=""/><span className="selection-dot"/></div><div className="asset-description"><strong>{item.label}</strong><small>{allowed?item.description:'Disponibile con il manichino con divisa'}</small></div></button>;
        })}</div>
        <p className="catalog-note">La testa originale è geometrica e leggera. Realistic girl conserva il modello dettagliato precedente ed è disponibile con il manichino con divisa.</p>
      </section>
      <section className="composition-panel" aria-label="Anteprima della composizione">
        <div className="preview-topline"><span>ANTEPRIMA 3D</span><div className="view-switch" aria-label="Inquadratura"><button aria-pressed={!face} onClick={()=>setFace(false)}>Figura intera</button><button aria-pressed={face} onClick={()=>setFace(true)}>Viso</button></div></div>
        <div className="composition-preview">{hydrated&&<Preview selection={selection} face={face} onStatus={onStatus}/>}</div>
        <p className="preview-hint">Trascina per ruotare · Usa la rotellina per avvicinarti</p>
        <div className="composition-summary"><div><span>LA TUA COMPOSIZIONE</span><strong>{body.label}</strong><p>+ {head.label}</p></div><span className={`save-state ${dirty?'unsaved':''}`}>{dirty?'Da salvare':'Salvata'}</span></div>
        <div className="save-actions"><button className="save-composition" onClick={save} disabled={!hydrated||status!=='ready'||!dirty}>Salva e applica alle atlete <span>↗</span></button><button className="reset-composition" onClick={()=>{if(selection.bodyId!==DEFAULT_COMPOSITION.bodyId||selection.headId!==DEFAULT_COMPOSITION.headId){setSelection({...DEFAULT_COMPOSITION});setStatus('loading');}setNotice('Composizione iniziale ripristinata in anteprima. Salva per applicarla.');}}>Ripristina composizione iniziale</button></div>
        <p className="settings-notice" role="status" aria-live="polite">{notice||'Le scelte valgono per questa sessione. All’avvio: Manichino Castell + Testa del manichino originale.'}</p>
      </section>
    </div>
  </main>;
}
