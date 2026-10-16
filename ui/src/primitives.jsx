import React,{useEffect,useRef} from 'react';
import {Icon} from './icons.jsx';
export function Button({children,icon,kind='',className='',...props}) {return <button className={`hl-btn ${kind} ${className}`} {...props}>{icon&&<Icon name={icon}/>}<span>{children}</span></button>;}
export function Empty({title,children,action}) {return <div className="hl-empty"><Icon name="book" size={32}/><h2>{title}</h2><p>{children}</p>{action}</div>;}
export function Field({label,children,hint}) {return <label className="hl-field"><span>{label}</span>{children}{hint&&<small>{hint}</small>}</label>;}
export function Modal({title,children,onClose}) {
 const ref=useRef(null);
 useEffect(()=>{const previous=document.activeElement; const dialog=ref.current; dialog?.focus(); const handler=e=>{if(e.key==='Escape'){e.preventDefault();onClose();} if(e.key==='Tab'){const items=[...dialog.querySelectorAll('button:not(:disabled),input,select,textarea,[tabindex="0"]')]; if(!items.length)return; const first=items[0],last=items.at(-1); if(e.shiftKey&&(document.activeElement===first||document.activeElement===dialog)){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}};dialog?.addEventListener('keydown',handler);return()=>{dialog?.removeEventListener('keydown',handler);previous?.focus?.();};},[onClose]);
 return <div className="hl-modal-backdrop"><section className="hl-modal" role="dialog" aria-modal="true" aria-label={title} tabIndex={-1} ref={ref}><header><h2>{title}</h2><button className="hl-icon-btn" aria-label="Close dialog" onClick={onClose}><Icon name="close"/></button></header>{children}</section></div>;
}
export function DateLabel({value}) {return <time dateTime={value}>{value?new Date(value).toLocaleDateString(undefined,{month:'short',day:'numeric'}):'Not scheduled'}</time>;}
export const human=value=>String(value||'').replaceAll('_',' ').replaceAll('-',' ');
