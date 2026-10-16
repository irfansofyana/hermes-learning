export const example = {
  title:'Reliable distributed systems',
  interest:'Understand how retries behave when a client cannot tell whether a write succeeded.',
  brief:'Follow one request across a client and a server. Separate what happened from what the client knows, then reason about a safe retry.',
  objectives:['Distinguish a timeout from a failed write.','Explain why a retry can repeat an effect.','Describe what an idempotency key must guarantee.'],
  source:{title:'Retry and idempotency',kind:'notes',url:'',locator:'Authored example · Scenario 1',sharing:'selected-excerpts',verification:'unverified',excerpt:'A client sends a request to create a payment. The server commits the write, but its response is lost. The client times out and retries. A timeout describes what the client observed; it does not prove that the server rolled back its work.\n\nThis is an original demonstration written for Hermes Learning. It is not an excerpt from a published book or paper.'},
  activity:{title:'When a retry becomes two writes',kind:'prediction',description:'Predict what happens when a response never arrives.',prompt:'What could happen when the client retries? Explain what the timeout does—and does not—tell us.',criteria:['Distinguish the client’s observation from the server’s completed write.','Explain why an unprotected retry can repeat an effect.','Explain how an idempotency mechanism recognizes the same operation.'],solution:'The first write may already have committed. Retrying can create a second payment unless the server recognizes the repeated operation. An idempotency key must be stored atomically with the effect and consistently reused by the client; retries alone cannot guarantee this.',hints:['Separate what the client knows from what happened on the server.','Trace the first write before tracing the retry. Was the write rolled back merely because the response was lost?','If the first request already created a payment, a retry needs a durable identity that tells the server it is the same operation.'],visual:{schema_version:1,type:'sequence',title:'Follow the request',visible_steps:3,participants:[{id:'client',label:'Client'},{id:'server',label:'Server'}],steps:[{from:'client',to:'server',label:'Create payment',explanation:'The client sends a request. A response has not arrived yet.'},{from:'server',to:'server',label:'Commit write',explanation:'The server records the payment. This event happens independently of whether the response reaches the client.'},{from:'server',to:'client',label:'Response lost',explanation:'The response is lost. From the client’s perspective the request has timed out.'},{from:'client',to:'server',label:'Retry the request',explanation:'Without a durable idempotency mechanism, this request can repeat the effect.'}]}}
};

// These are teaching fixtures, never a learner's prior evidence.
example.activity.purpose = 'diagnostic';
example.activity.competency = 'conceptual';
example.activity.objective_indexes = [0, 1, 2];
example.followups = [
 {
  title: 'Apply the idea to email delivery', kind: 'explanation', purpose: 'transfer', competency: 'conceptual', objective_indexes: [0, 1, 2],
  description: 'Use the same reasoning in a different system.',
  prompt: 'An email provider accepts a message, but your worker loses the response. Explain the choices for retrying. What additional contract would let you avoid sending the same email twice?',
  criteria: ['Explain why a timeout leaves acceptance uncertain.', 'Distinguish the risk of omission from the risk of duplicate delivery.', 'State that safe deduplication requires a durable identity and a provider contract, not just a local retry loop.'],
  solution: 'The email might already have been accepted. Never retrying risks omission; retrying without deduplication risks duplicate delivery. A stable operation identity helps only when the receiving system durably deduplicates it under a stated contract. A local flag cannot atomically cover an unrelated remote side effect.',
  hints: ['Separate what the worker observed from what the provider accepted.', 'Can the worker atomically update its database and the remote provider?'],
  visual: {schema_version: 1, type: 'state-machine', title: 'What the worker knows', initial: 'ready', visible_steps: 2,
   states: [{id: 'ready', label: 'Ready to send'}, {id: 'waiting', label: 'Waiting for response'}, {id: 'uncertain', label: 'Outcome unknown'}, {id: 'confirmed', label: 'Acceptance confirmed'}],
   steps: [{from: 'ready', to: 'waiting', label: 'Send message', explanation: 'The worker starts the remote operation.'}, {from: 'waiting', to: 'uncertain', label: 'Timeout', explanation: 'The observation does not tell us whether the provider accepted the message.'}, {from: 'uncertain', to: 'confirmed', label: 'Resolve by operation identity', explanation: 'If the provider supports durable deduplication or lookup, the worker can resolve the same operation without starting a new one.'}]}
 },
 {
  title: 'Build and test a retry boundary', kind: 'build', purpose: 'practice', competency: 'practical', objective_indexes: [2],
  description: 'Implement a small local experiment in your own project. This workspace stores your report; it does not execute code.',
  prompt: 'Implement an operation with a stable request key and a saved result. Test the same request twice, a changed payload with the same key, and two simultaneous requests. Submit your code or artifact reference and the observed results. Explain what transaction boundary your implementation relies on.',
  criteria: ['Show that identical retries return the saved result without repeating the effect.', 'Reject a changed payload under the same key.', 'Show a concurrent test and explain how the key, result, and effect are committed atomically.'],
  solution: 'Within one transaction, claim a unique operation key, check a fingerprint of the payload, apply the effect, and save its result. An identical retry returns the saved result; a conflicting payload is rejected. A uniqueness constraint and transaction serialize competing claims. A remote effect outside that transaction needs an additional protocol; these local tests do not establish exactly-once delivery across services.',
  hints: ['Put the key lookup and write under the same transaction boundary.', 'A check followed by an unguarded insert can race. Use a uniqueness constraint.'],
  visual: {schema_version: 1, type: 'code-trace', title: 'Inspect the transaction boundary', language: 'pseudocode', visible_steps: 2,
   code: 'begin transaction\nclaim unique operation key\ncompare request fingerprint\napply local effect\nsave result with key\ncommit transaction\nreturn saved result',
   steps: [{line: 1, label: 'Begin', explanation: 'All local writes belong to one transaction.', variables: [{name: 'key', value: 'request-42'}, {name: 'transaction', value: 'open'}]}, {line: 2, label: 'Claim the key', explanation: 'A uniqueness constraint prevents two committed claims for this key.', variables: [{name: 'key', value: 'request-42'}, {name: 'claim', value: 'pending commit'}]}, {line: 6, label: 'Commit together', explanation: 'The local effect and saved result become durable together. This is an authored trace, not executed code.', variables: [{name: 'transaction', value: 'committed'}]}]}
 }
];
