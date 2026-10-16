import React,{useMemo,useEffect} from 'react';
import LearningApp from './LearningApp.jsx';
import {createWebTutorTransport} from './tutor-transport.mjs';
const SDK=window.__HERMES_PLUGIN_SDK__;
const request=(path,body)=>SDK.fetchJSON(`/api/plugins/hermes-learning${path}`,body===undefined?{method:'GET'}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
function LearningWorkspace(){
 const transport=useMemo(()=>createWebTutorTransport(SDK),[]);
 useEffect(()=>()=>transport.dispose(),[transport]);
 return <LearningApp request={request} transport={transport} scope="dashboard"/>;
}
window.__HERMES_PLUGINS__.register('hermes-learning',LearningWorkspace);
