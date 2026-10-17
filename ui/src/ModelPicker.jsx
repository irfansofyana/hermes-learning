import React,{useEffect,useId,useRef,useState} from 'react';
import {loadModelOptions,modelSelectionKey} from './model-options.mjs';
export function ModelPicker({transport,profile,value,onChange,disabled=false}){
 const id=useId(),epoch=useRef(0);
 const [inventory,setInventory]=useState(null),[loading,setLoading]=useState(true),[saving,setSaving]=useState(false),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 useEffect(()=>{
  const current=++epoch.current;let alive=true;setLoading(true);setInventory(null);setError('');setSaving(false);
  loadModelOptions(transport,profile).then(result=>{if(alive&&epoch.current===current)setInventory(result);}).catch(e=>{if(alive&&epoch.current===current)setError(e.message);}).finally(()=>{if(alive&&epoch.current===current)setLoading(false);});
  return()=>{alive=false;epoch.current++;};
 },[transport,profile,retry]);
 const selected=modelSelectionKey(value),options=inventory?.options||[],known=selected==='default'||options.some(option=>modelSelectionKey(option)===selected);
 async function select(event){
  const choice=event.target.value,current=epoch.current;
  const option=choice==='default'?null:options.find(option=>modelSelectionKey(option)===choice);
  if(choice!=='default'&&!option)return;
  setSaving(true);setError('');
  try{await onChange(option?{provider:option.provider,model:option.model}:null);}
  catch(e){if(epoch.current===current)setError(e.message||'Could not save this model.');}
  finally{if(epoch.current===current)setSaving(false);}
 }
 return <div className="lw-model-picker">
  <label htmlFor={id}>Model</label>
  <select id={id} value={selected} onChange={select} disabled={disabled||loading||saving} aria-describedby={error?`${id}-error`:undefined}>
   <option value="default">Hermes default{inventory?.defaultModel?` · ${inventory.defaultModel.model}`:''}</option>
   {!known&&<option value={selected} disabled>{value?.provider} · {value?.model} (unavailable)</option>}
   {options.map(option=><option key={modelSelectionKey(option)} value={modelSelectionKey(option)}>{option.label}</option>)}
  </select>
  {loading&&<span role="status">Loading models…</span>}
  {saving&&<span role="status">Saving model…</span>}
  {error&&<span id={`${id}-error`} role="alert">{error} <button type="button" onClick={()=>setRetry(n=>n+1)} disabled={disabled||loading||saving}>Retry models</button></span>}
 </div>;
}
