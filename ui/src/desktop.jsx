import React from 'react';
import {host,useValue,ROUTES_AREA,SIDEBAR_NAV_AREA} from '@hermes/plugin-sdk';
import App from './App.jsx';
import {openTutorChat} from './handoff.mjs';
export default {id:'hermes-learning',name:'Learning',defaultEnabled:false,register(ctx){
 const request=(path,body)=>ctx.rest(path,body===undefined?{method:'GET'}:{method:'POST',body});
 const onTutorHandoff=typeof host.newChat==='function'&&typeof host.composer?.insertText==='function'&&typeof host.composer?.getDraft==='function'?(command,request)=>openTutorChat(host,command,sessionStorage,request):undefined;
 function Workspace(){const profile=useValue(host.state.profile),gateway=useValue(host.state.gateway);return <App key={`${profile}:${gateway}`} request={request} onTutorHandoff={onTutorHandoff}/>;}
 ctx.register({id:'learning',area:ROUTES_AREA,data:{path:'/learning'},render:()=>React.createElement(Workspace)});
 ctx.register({id:'learning-nav',area:SIDEBAR_NAV_AREA,data:{path:'/learning',label:'Learning',codicon:'book'}});
}};
