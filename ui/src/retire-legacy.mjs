// Discard only state owned by the retired activity UI, including old unsubmitted answers.
export function clearLegacyStorage(storage) {
 try {
  if (!storage) return;
  const keys=Array.from({length:storage.length},(_,index)=>storage.key(index));
  for (const key of keys) {
   if (key==='hermes-learning:context'||key==='hermes-learning:tutor-request'||key?.startsWith('hermes-learning:draft:v1:')||key?.startsWith('hermes-learning:location:')) storage.removeItem(key);
  }
 } catch { /* Restricted storage must not prevent opening lessons. */ }
}
