import React,{useEffect,useRef,useState} from 'react';
import {ArrowDown,ArrowLeft,ArrowRight,ArrowUp,RotateCcw,ZoomIn,ZoomOut} from 'lucide-react';
import {Button} from './ui/button';
import {Skeleton} from './ui/skeleton';

// The canvas keeps the DOM bounded while the original, authenticated source pixels pan inside it.
export const SourceDetailViewer=({src,alt})=>{
 const canvas=useRef(null),frame=useRef(null),drag=useRef(null),metrics=useRef(null);
 const [image,setImage]=useState(null),[zoom,setZoom]=useState(()=>window.matchMedia('(max-width:640px)').matches?2:1),[pan,setPan]=useState({x:0,y:0}),[size,setSize]=useState({w:1,h:1}),[error,setError]=useState(false),[reload,setReload]=useState(0);
 useEffect(()=>{let active=true;setImage(null);setError(false);const img=new Image();img.onload=()=>active&&setImage(img);img.onerror=()=>active&&setError(true);img.src=src;return()=>{active=false}},[src,reload]);
 useEffect(()=>{const observer=new ResizeObserver(entries=>{const r=entries[0].contentRect;setSize({w:r.width,h:r.height})});if(frame.current)observer.observe(frame.current);return()=>observer.disconnect()},[]);
 useEffect(()=>{
  if(!image||!canvas.current)return;
  const c=canvas.current,dpr=Math.min(window.devicePixelRatio||1,2),ctx=c.getContext('2d');
  c.width=Math.round(size.w*dpr);c.height=Math.round(size.h*dpr);ctx.scale(dpr,dpr);ctx.clearRect(0,0,size.w,size.h);
  const ratio=Math.min(size.w/image.naturalWidth,size.h/image.naturalHeight)*zoom;
  const w=image.naturalWidth*ratio,h=image.naturalHeight*ratio,minX=Math.min(0,size.w-w),minY=Math.min(0,size.h-h);
  metrics.current={minX,minY};const x=Math.max(minX,Math.min(0,pan.x)),y=Math.max(minY,Math.min(0,pan.y));
  ctx.drawImage(image,x,y,w,h);
 },[image,zoom,pan,size]);
 function move(x,y){const m=metrics.current||{minX:0,minY:0};setPan(p=>({x:Math.max(m.minX,Math.min(0,p.x+x)),y:Math.max(m.minY,Math.min(0,p.y+y))}))}
 function changeZoom(next){setZoom(Math.max(1,Math.min(5,next)));setPan({x:0,y:0})}
 function keys(e){const action={ArrowLeft:()=>move(60,0),ArrowRight:()=>move(-60,0),ArrowUp:()=>move(0,60),ArrowDown:()=>move(0,-60),'+':()=>changeZoom(zoom+.5),'-':()=>changeZoom(zoom-.5)}[e.key];if(action){e.preventDefault();action()}}
 return <div className="source-detail-viewer" data-testid="source-detail-viewer">
  <div className="source-zoom-controls"><Button variant="outline" size="icon" onClick={()=>changeZoom(zoom-.5)} disabled={zoom<=1||!image} aria-label="Zoom out" data-testid="source-zoom-out"><ZoomOut size={18}/></Button><span role="status" data-testid="source-zoom-level">{Math.round(zoom*100)}%</span><Button variant="outline" size="icon" onClick={()=>changeZoom(zoom+.5)} disabled={zoom>=5||!image} aria-label="Zoom in" data-testid="source-zoom-in"><ZoomIn size={18}/></Button><Button variant="outline" onClick={()=>changeZoom(1)} disabled={!image} data-testid="source-zoom-reset"><RotateCcw size={15}/>Fit</Button></div>
  <div ref={frame} className="source-canvas-frame">
   {!image&&!error&&<Skeleton className="source-canvas-loading" data-testid="source-zoom-loading"/>}
   <canvas ref={canvas} className="source-pan-canvas" tabIndex={0} role="img" aria-label={alt+' Use arrow keys to pan and plus or minus to zoom.'} data-testid="source-zoom-canvas" onKeyDown={keys}
    onPointerDown={e=>{drag.current={x:e.clientX,y:e.clientY};e.currentTarget.setPointerCapture(e.pointerId)}}
    onPointerMove={e=>{if(!drag.current)return;move(e.clientX-drag.current.x,e.clientY-drag.current.y);drag.current={x:e.clientX,y:e.clientY}}}
    onPointerUp={()=>{drag.current=null}} onPointerCancel={()=>{drag.current=null}}/>
  </div>
  {error&&<p role="alert" data-testid="source-zoom-error">The original image could not load. <Button variant="outline" onClick={()=>setReload(v=>v+1)} data-testid="source-zoom-retry">Retry</Button></p>}
  <div className="source-pan-controls" aria-label="Pan original image">{[[ArrowLeft,60,0,'left'],[ArrowRight,-60,0,'right'],[ArrowUp,0,60,'up'],[ArrowDown,0,-60,'down']].map(([Icon,x,y,label])=><Button key={label} variant="outline" size="icon" disabled={!image||zoom<=1} aria-label={'Pan '+label} onClick={()=>move(x,y)} data-testid={'source-pan-'+label}><Icon size={17}/></Button>)}</div>
  <p className="import-fineprint" data-testid="source-zoom-help">Drag the image to read across it. Use +/− to enlarge; arrow buttons or keyboard arrows move around the original.</p>
 </div>;
};
