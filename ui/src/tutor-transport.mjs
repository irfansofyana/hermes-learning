// Hermes gateway notifications keep their routing metadata so callers can reject
// events from a different profile or host. Never infer a missing session ID.
function normalizeEvent(event, type) {
  const value=event?.method==='event' ? event.params : event;
  return {...value,type:value?.type||type,session_id:value?.session_id??null,payload:value?.payload??{}};
}

function eventHub() {
  const listeners=new Map();
  return {
    on(type,callback) {
      const set=listeners.get(type)||new Set();set.add(callback);listeners.set(type,set);
      return ()=>{set.delete(callback);if(!set.size)listeners.delete(type);};
    },
    emit(event) {
      for(const type of new Set([event.type,'*'])) for(const callback of [...(listeners.get(type)||[])]) {
        // A failing consumer must not break request correlation or other listeners.
        try { callback(event); } catch(error) { console.error('Tutor event listener failed',error); }
      }
    },
    clear() { listeners.clear(); },
  };
}

/** Desktop owns its gateway connection. This adapter owns only its subscriptions. */
export function createTutorTransport(host) {
  let disposed=false;
  const subscriptions=new Set();const pending=new Set();
  return {
    request(method,params={}) {
      if(disposed)return Promise.reject(new Error('Tutor transport disposed.'));
      return new Promise((resolve,reject)=>{
        const cancel=()=>reject(new Error('Tutor transport disposed.'));pending.add(cancel);
        Promise.resolve().then(()=>{
          if(disposed)throw new Error('Tutor transport disposed.');
          return host.request(method,params);
        }).then(resolve,reject).finally(()=>pending.delete(cancel));
      });
    },
    onEvent(type,callback) {
      if(disposed)return ()=>{};
      let off;
      if(type==='transport.disconnected'&&typeof host.state?.gateway?.listen==='function') {
        let previous=host.state.gateway.get();
        off=host.state.gateway.listen(state=>{
          if(!disposed&&previous==='open'&&state!=='open') {
            callback({type,session_id:null,payload:{message:'Tutor disconnected. A submitted turn may still be running; reopen the tutor to inspect history.'}});
          }
          previous=state;
        });
      } else off=host.onEvent(type,event=>{if(!disposed)callback(normalizeEvent(event,type));});
      const unsubscribe=()=>{if(subscriptions.delete(unsubscribe))off();};
      subscriptions.add(unsubscribe);return unsubscribe;
    },
    // Desktop server requests belong to the native renderer. The controller reads
    // session.activate.open_requests to display and answer them in this plugin.
    setSession() {},
    dispose() {
      if(disposed)return;disposed=true;
      for(const off of [...subscriptions])off();
      for(const cancel of pending)cancel();pending.clear();
    },
  };
}

/** An authenticated dashboard connection, with explicit reconnect support.
 * Never reconnect or replay automatically: a lost prompt response may already
 * have started a turn. Optional timing/socket dependencies permit protocol tests.
 */
export function createWebTutorTransport(SDK, options={}) {
  const Socket=options.WebSocket??globalThis.WebSocket;
  const connectTimeoutMs=options.connectTimeoutMs??15000;
  const requestTimeoutMs=options.requestTimeoutMs??120000;
  const heartbeatIntervalMs=options.heartbeatIntervalMs??15000;
  const heartbeatDeadlineMs=options.heartbeatDeadlineMs??45000;
  const events=eventHub();const pending=new Map();
  let socket=null, connection=null, terminal=null, disposed=false, nextId=0, selectedSession=null;
  let connectionGeneration=0;
  let rejectConnect=null, connectTimer=null, heartbeatTimer=null, heartbeatWaiting=false;
  let removers=[];

  function terminate(error, announce=true) {
    if(terminal)return;
    terminal=error;
    clearTimeout(connectTimer);clearInterval(heartbeatTimer);
    rejectConnect?.(error);rejectConnect=null;
    for(const entry of pending.values()){clearTimeout(entry.timer);entry.reject(error);}pending.clear();
    for(const remove of removers)remove();removers=[];
    const old=socket;socket=null;
    try{old?.close();}catch{}
    if(announce)events.emit({type:'transport.disconnected',session_id:null,payload:{message:error.message}});
  }

  function sendRequest(method,params={},timeoutMs=requestTimeoutMs) {
    if(terminal)return Promise.reject(terminal);
    if(!socket||socket.readyState!==1)return Promise.reject(new Error('Tutor gateway is not connected.'));
    const id=`learning-${++nextId}`;
    return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>terminate(new Error(`Tutor request timed out: ${method}. Its outcome may be unknown; reopen the tutor to inspect history.`)),timeoutMs);
      pending.set(id,{resolve,reject,timer});
      try{socket.send(JSON.stringify({jsonrpc:'2.0',id,method,params}));}
      catch(error){terminate(error instanceof Error?error:new Error(String(error)));}
    });
  }

  function startHeartbeat() {
    if(heartbeatTimer||heartbeatIntervalMs<=0)return;
    heartbeatTimer=setInterval(()=>{
      if(heartbeatWaiting||terminal)return;
      heartbeatWaiting=true;
      sendRequest('gateway.ping',{},heartbeatDeadlineMs).catch(()=>{}).finally(()=>{heartbeatWaiting=false;});
    },heartbeatIntervalMs);
  }

  function onMessage(event) {
    let frame;
    try{frame=JSON.parse(event.data);}catch{return;}
    if(!frame||typeof frame!=='object')return;
    if(typeof frame.method==='string'&&frame.method!=='event'&&frame.id!=null) {
      const params=frame.params||{};
      const supported=['approval','clarify'].includes(frame.method);
      if(supported&&selectedSession&&params.session_id===selectedSession) {
        events.emit({type:frame.method,session_id:params.session_id,payload:{...params,id:frame.id}});
      } else {
        // Decline requests for other sessions; never answer on their behalf.
        const code=supported?4404:-32601;
        socket?.send(JSON.stringify({jsonrpc:'2.0',id:frame.id,error:{code,message:supported?'This tutor is not showing the session.':`Tutor cannot handle ${frame.method}.`}}));
      }
      return;
    }
    if(frame.id!=null) {
      const entry=pending.get(frame.id);if(!entry)return;
      pending.delete(frame.id);clearTimeout(entry.timer);
      if(frame.error) {
        const error=new Error(frame.error.message||'Hermes request failed.');
        error.code=frame.error.code;error.data=frame.error.data;entry.reject(error);
      } else entry.resolve(frame.result);
      return;
    }
    if(frame.method==='event'&&typeof frame.params?.type==='string') {
      if(frame.params.type==='gateway.ready'&&frame.params.payload?.heartbeat)startHeartbeat();
      events.emit(normalizeEvent(frame));
    }
  }

  function connect() {
    if(terminal)return Promise.reject(terminal);
    if(connection)return connection;
    const generation=++connectionGeneration;
    connection=new Promise((resolve,reject)=>{
      rejectConnect=reject;
      connectTimer=setTimeout(()=>terminate(new Error('Tutor connection timed out. Reopen the tutor to connect again.')),connectTimeoutMs);
      Promise.resolve().then(()=>SDK.buildWsUrl('/api/ws')).then(url=>{
        if(terminal||generation!==connectionGeneration)return;
        socket=new Socket(url);
        const listen=(type,fn)=>{const current=socket;current.addEventListener(type,fn);removers.push(()=>current.removeEventListener(type,fn));};
        listen('message',onMessage);
        listen('close',event=>terminate(new Error(`Tutor disconnected (${event.code??'closed'}). A submitted turn may still be running; reopen the tutor to inspect history.`)));
        listen('error',()=>terminate(new Error('Tutor disconnected: WebSocket connection failed. Reopen the tutor to inspect history.')));
        listen('open',()=>{
          // The gateway otherwise refuses interactive tools as unsupported.
          sendRequest('client.capabilities',{server_requests:true}).then(()=>{
            if(terminal||generation!==connectionGeneration)return;
            clearTimeout(connectTimer);rejectConnect=null;resolve();
          }).catch(error=>{if(generation===connectionGeneration)terminate(error);});
        });
      }).catch(error=>{if(generation===connectionGeneration)terminate(error instanceof Error?error:new Error(String(error)));});
    });
    return connection;
  }

  return {
    async request(method,params={}) {await connect();return sendRequest(method,params);},
    async reconnect() {
      if(disposed)throw new Error('Tutor transport disposed.');
      terminate(new Error('Tutor disconnected for an explicit reconnect. Previous request outcomes may be unknown.'),false);
      terminal=null;connection=null;selectedSession=null;heartbeatTimer=null;heartbeatWaiting=false;
      await connect();
    },
    onEvent(type,callback) {return disposed?()=>{}:events.on(type,callback);},
    setSession(sessionId) {selectedSession=typeof sessionId==='string'?sessionId:null;},
    dispose() {
      if(disposed)return;disposed=true;
      terminate(new Error('Tutor transport disposed.'),false);events.clear();
    },
  };
}
