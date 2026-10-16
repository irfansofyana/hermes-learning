import React,{useState,useEffect,useId,useRef} from 'react';
import {Button} from './primitives.jsx';
export function Sequence({visual}) {
 const [index,setIndex]=useState(0),[available,setAvailable]=useState(650); const marker=useId().replaceAll(':',''),container=useRef(null);
 useEffect(()=>{if(!container.current||typeof ResizeObserver==='undefined')return;const observer=new ResizeObserver(entries=>setAvailable(Math.max(0,entries[0].contentRect.width)));observer.observe(container.current);return()=>observer.disconnect();},[visual?.type]);
 useEffect(()=>setIndex(0),[visual?.title]);
 if(!visual || visual.type!=='sequence' || !Array.isArray(visual.steps)||!visual.steps.length) return <p className="hl-muted">No visual has been added to this activity.</p>;
 const participants=visual.participants||[]; const steps=visual.steps;
 const current=Math.min(index,steps.length-1), shown=steps.slice(0,current+1);
 const width=Math.max(340,available,participants.length*150), height=90+shown.length*62;
 const shorten=(value,limit)=>value.length>limit?`${value.slice(0,limit-1)}…`:value;
 const x=id=>70+participants.findIndex(p=>p.id===id)*(width-140)/Math.max(1,participants.length-1);
 return <section className="hl-sequence" aria-label={visual.title||'Sequence diagram'}>
   <div className="hl-section-heading"><span>02</span><h2>{visual.title||'Follow the request'}</h2></div>
   <div className="hl-mobile-sequence"><span>{participants.find(p=>p.id===steps[current].from)?.label}</span><strong>{steps[current].label}</strong><span>→ {participants.find(p=>p.id===steps[current].to)?.label}</span></div>
   <div className="hl-diagram" ref={container} tabIndex={0} aria-label="Sequence steps. Use left and right arrow keys." onKeyDown={e=>{if(e.key==='ArrowRight'){e.preventDefault();setIndex(i=>Math.min(i+1,steps.length-1));}if(e.key==='ArrowLeft'){e.preventDefault();setIndex(i=>Math.max(i-1,0));}}}>
   <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={steps[current].label} style={{minWidth:width}}>
    <defs><marker id={marker} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="currentColor"/></marker></defs>
    {participants.map(p=><g key={p.id}><title>{p.label}</title><rect x={x(p.id)-58} y="8" width="116" height="36" rx="5" className="hl-participant"/><text x={x(p.id)} y="31" textAnchor="middle" className="hl-participant-text">{shorten(p.label,17)}</text><line x1={x(p.id)} x2={x(p.id)} y1="44" y2={height-10} className="hl-lifeline"/></g>)}
    {shown.map((s,i)=>{const y=88+i*62, self=s.from===s.to;return <g key={i} className={i===current?'hl-current-step':'hl-past-step'}>{i===current&&<rect x="16" y={y-25} width={width-32} height="55" rx="4" className="hl-step-band"/>}<path d={self?`M${x(s.from)} ${y} h-45 v20 h45`:`M${x(s.from)} ${y+12}H${x(s.to)}`} fill="none" stroke="currentColor" strokeWidth="1.8" markerEnd={`url(#${marker})`}/><text x={self?x(s.from)-55:(x(s.from)+x(s.to))/2} y={y-5} textAnchor={self?'end':'middle'}>{shorten(s.label,Math.max(20,Math.floor((width-110)/7)))}</text></g>;})}
   </svg></div>
   <div className="hl-step-controls"><Button icon="back" onClick={()=>setIndex(i=>Math.max(i-1,0))} disabled={current===0}>Previous</Button><span aria-live="polite">Step {current+1} of {steps.length}</span><Button kind="primary" onClick={()=>setIndex(i=>Math.min(i+1,steps.length-1))} disabled={current===steps.length-1}>Next step <span aria-hidden="true">→</span></Button></div>
   <p className="hl-step-explanation" aria-live="polite">{steps[current].explanation}</p>
   {visual.total_steps>steps.length&&<p className="hl-muted">The remaining sequence opens after you submit or reveal the solution.</p>}
   <details className="hl-details"><summary>Read the sequence as text</summary><ol>{steps.map((s,i)=><li key={i}><strong>{participants.find(p=>p.id===s.from)?.label} → {participants.find(p=>p.id===s.to)?.label}: {s.label}.</strong> {s.explanation}</li>)}</ol></details>
 </section>;
}
