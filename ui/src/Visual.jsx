import React,{useState,useEffect} from 'react';
import {Sequence} from './Sequence.jsx';
import {Button} from './primitives.jsx';
import {visibleSteps} from './learning.mjs';

export function Visual({visual}) {
 if(!visual||visual.type==='sequence')return <Sequence visual={visual}/>;
 if(!['state-machine','code-trace'].includes(visual.type))return <p className="hl-muted">This visual needs a newer workspace version.</p>;
 return <StructuredVisual visual={visual}/>;
}
function StructuredVisual({visual}) {
 const [index,setIndex]=useState(0);
 useEffect(()=>setIndex(0),[visual.title,visual.steps]);
 const steps=visibleSteps(visual),current=Math.min(index,steps.length-1),step=steps[current];
 const label=id=>visual.states?.find(state=>state.id===id)?.label||id;
 if(!step)return <p className="hl-muted">This visual opens after you submit or reveal the solution.</p>;
 const move=amount=>setIndex(i=>Math.max(0,Math.min(i+amount,steps.length-1)));
 return <section className="hl-sequence hl-structured-visual" aria-label={visual.title||'Step-through visual'}>
  <div className="hl-section-heading"><span>02</span><h2>{visual.title||'Follow the steps'}</h2></div>
  <div className="hl-visual-stage" tabIndex={0} aria-label="Visual steps. Use left and right arrow keys." onKeyDown={e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();move(e.key==='ArrowRight'?1:-1);}}}>
   {visual.type==='state-machine'?<><p className="hl-overline">Starts at {label(visual.initial)}</p><div className="hl-state-transition"><div><span>From</span><strong>{label(step.from)}</strong></div><span aria-hidden="true">→</span><div className="hl-state-current"><span>To</span><strong>{label(step.to)}</strong></div></div><p className="hl-state-label">{step.label}</p><p className="hl-muted">Transition {current+1}{step.from===step.to?' · state remains the same':''}</p></>:<><p className="hl-overline">{visual.language||'Code'} · line {step.line}</p><pre className="hl-trace-code" aria-label="Code listing">{(visual.code||'').split('\n').map((line,i)=><span key={i} className={i+1===step.line?'is-current':''} aria-current={i+1===step.line?'step':undefined}><span className="hl-line-number" aria-hidden="true">{i+1}</span><code>{line||' '}</code></span>)}</pre><h3>{step.label}</h3>{step.variables?.length>0&&<dl className="hl-variables">{step.variables.map((variable,i)=><div key={i}><dt>{variable.name}</dt><dd>{variable.value}</dd></div>)}</dl>}</>}
  </div>
  <div className="hl-step-controls"><Button icon="back" onClick={()=>move(-1)} disabled={current===0}>Previous</Button><span aria-live="polite">Step {current+1} of {steps.length}</span><Button kind="primary" onClick={()=>move(1)} disabled={current===steps.length-1}>Next step →</Button></div>
  <p className="hl-step-explanation" aria-live="polite">{step.explanation}</p>
  {(visual.total_steps||visual.steps.length)>steps.length&&<p className="hl-muted">The remaining steps open after you submit or reveal the solution.</p>}
  <details className="hl-details"><summary>Read the visual as text</summary><ol>{steps.map((item,i)=><li key={i}><strong>{visual.type==='state-machine'?`${label(item.from)} → ${label(item.to)}`:`Line ${item.line}`}: {item.label}.</strong> {item.explanation}{item.variables?.length>0&&<p>{item.variables.map(v=>`${v.name} = ${v.value}`).join('; ')}</p>}</li>)}</ol></details>
 </section>;
}
