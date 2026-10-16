import React,{useMemo,useEffect} from 'react';
import {host,useValue,ROUTES_AREA,SIDEBAR_NAV_AREA} from '@hermes/plugin-sdk';
import LearningApp from './LearningApp.jsx';
import {createTutorTransport} from './tutor-transport.mjs';
export default {id:'hermes-learning',name:'Learning',defaultEnabled:false,register(ctx){
 function ScopedWorkspace({profile,connection}) {
  const transport=useMemo(()=>createTutorTransport({...host,onEvent:(type,callback)=>host.onEvent(type,event=>{
   if(host.state.profile.get()!==profile||(host.state.connectionId&&host.state.connectionId.get()!==connection))return;
   if(event.profile&&event.profile!==profile)return;
   if(event.connectionId&&event.connectionId!==connection)return;
   callback(event);
  }),request:(method,params)=>{
   if(host.state.profile.get()!==profile||(host.state.connectionId&&host.state.connectionId.get()!==connection))throw new Error('The Hermes connection changed. Reopen Learning.');
   return host.request(method,params);
  }}),[profile,connection]);
  const request=useMemo(()=>{
   const matches=()=>host.state.profile.get()===profile&&(!host.state.connectionId||host.state.connectionId.get()===connection);
   return async(path,body)=>{
    if(!matches())throw new Error('The Hermes connection changed. Reopen Learning on the selected profile.');
    const result=await ctx.rest(path,body===undefined?{method:'GET'}:{method:'POST',body});
    if(!matches())throw new Error('The Hermes connection changed while loading Learning.');
    return result;
   };
  },[profile,connection]);
  useEffect(()=>()=>transport.dispose(),[transport]);
  return <LearningApp request={request} transport={transport} profile={profile} scope={`${connection}:${profile}`}/>;
 }
 function Workspace(){
  const profile=useValue(host.state.profile);
  const connection=host.state.connectionId?useValue(host.state.connectionId):'local';
  return <ScopedWorkspace key={`${connection}:${profile}`} profile={profile} connection={connection}/>;
 }
 ctx.register({id:'learning',area:ROUTES_AREA,data:{path:'/learning'},render:()=>React.createElement(Workspace)});
 ctx.register({id:'learning-nav',area:SIDEBAR_NAV_AREA,data:{path:'/learning',label:'Learning',codicon:'book'}});
}};
