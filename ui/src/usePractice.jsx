import {useEffect,useMemo,useRef,useState} from 'react';
import {PracticeSession} from './practice-session.mjs';
// Mount once in the workspace, outside selected lesson/path panels.
export function usePractice({request,transport,scope,profile,onChange}) {
 const change=useRef(onChange);change.current=onChange;
 const [state,setState]=useState({busy:false,status:'Ready',error:'',active:null,attempt:null,needsReconnect:false});
 const session=useMemo(()=>new PracticeSession({request,transport,scope,profile,onState:setState,onChange:()=>change.current?.()}),[request,transport,scope,profile]);
 useEffect(()=>{setState(session.state);return()=>session.dispose();},[session]);
 return{...state,check:input=>session.check(input),restore:input=>session.restore(input),stop:()=>session.stop(),reconnect:()=>session.reconnect()};
}
