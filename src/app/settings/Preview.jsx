'use client';
import { Component, useEffect, useState, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import { loadComposition } from '../scene/athlete/composition.js';

class PreviewBoundary extends Component {
  state = { error: false };
  static getDerivedStateFromError() { return { error: true }; }
  render() { return this.state.error ? <p className="preview-message" role="alert">Anteprima 3D non disponibile. Verifica che WebGL sia abilitato e ricarica la pagina.</p> : this.props.children; }
}
function Model({ source }) {
  const scene = useMemo(() => clone(source), [source]);
  useEffect(() => () => {
    const skeletons=new Set();
    scene.traverse(node=>{if(node.isSkinnedMesh)skeletons.add(node.skeleton);});
    for(const skeleton of skeletons)skeleton.dispose();
  },[scene]);
  return <primitive object={scene} dispose={null} />;
}
function View({ scene, face }) {
  return <Canvas camera={{ position: face ? [0,1.54,.65] : [0,1,3.2], fov: face ? 35 : 36, near: .01, far: 30 }} dpr={[1,1.5]}>
    <color attach="background" args={['#e7e5e1']} />
    <ambientLight intensity={1.2} />
    <hemisphereLight args={['#fffaf2','#a7a3a0',1.3]} />
    <directionalLight position={[-2,3,4]} intensity={2.5} />
    <directionalLight position={[2,2,-2]} intensity={1.5} />
    <Model source={scene} />
    {!face && <ContactShadows position={[0,-.01,0]} opacity={.25} scale={4} blur={2} far={3} />}
    <OrbitControls makeDefault target={face ? [0,1.54,0] : [0,.86,0]} minDistance={face ? .3 : 1.5} maxDistance={face ? 1.5 : 6} enablePan={false} />
  </Canvas>;
}
export default function Preview({ selection, face, onStatus }) {
  const [asset,setAsset] = useState({ scene: null, error: '', loading: true });
  const [attempt,setAttempt] = useState(0);
  useEffect(() => {
    let active=true;
    setAsset({scene:null,error:'',loading:true});onStatus('loading');
    loadComposition(selection).then(scene => {
      if(active){setAsset({scene,error:'',loading:false});onStatus('ready');}
    }).catch(error => {
      if(active){setAsset({scene:null,error:error.message,loading:false});onStatus('error');}
    });
    return () => {active=false;};
  },[selection.bodyId,selection.headId,attempt,onStatus]);
  if(asset.loading) return <div className="preview-message" role="status"><span className="preview-spinner" />Caricamento della composizione…</div>;
  if(asset.error) return <div className="preview-message" role="alert">Impossibile caricare l’anteprima.<small>{asset.error}</small><button onClick={()=>setAttempt(v=>v+1)}>Riprova</button></div>;
  return <PreviewBoundary key={`${selection.bodyId}/${selection.headId}/${attempt}`}><View key={face?'face':'body'} scene={asset.scene} face={face} /></PreviewBoundary>;
}
