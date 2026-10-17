import {useEffect,useMemo,useRef,useState} from 'react';
import {TutorSession} from './tutor-session.mjs';
export function useTutor({request,transport,scope,profile,onChange}) {
 const change=useRef(onChange);change.current=onChange;
 const [state,setState]=useState({messages:[],busy:false,status:'Ready',error:'',pending:null,plan:null});
 const session=useMemo(()=>new TutorSession({request,transport,scope,profile,onState:setState,onChange:()=>change.current?.()}),[request,transport,scope,profile]);
 useEffect(()=>{setState(session.state);return()=>session.dispose();},[session]);
 return {...state,needsReconnect:session.uncertain,send:(text,context)=>session.send(text,context),restore:(binding,context)=>session.restore(binding,context),stop:()=>session.stop(),respond:value=>session.respond(value),clear:()=>session.clear()};
}
