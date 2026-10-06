import test from 'node:test';
import assert from 'node:assert/strict';
test('expired token refreshes once and retries the unauthorized request', async () => {
  const { createAPI } = await import('../js/api.js');
  const tokens=[]; const auth={getIdToken: async force => {tokens.push(force);return force?'new':'old';}};
  const api = createAPI('http://api.test',auth,async (url,options) => options.headers.Authorization==='Bearer old' ? new Response('{}',{status:401}) : new Response('{"ok":true}'));
  assert.equal((await api.request('/api/me')).ok,true);
  assert.deepEqual(tokens,[false,true]);
});
test('network failure on a POST never automatically retries', async () => {
  const { createAPI } = await import('../js/api.js');
  let calls=0;
  const api=createAPI('http://api.test',{getIdToken:async()=> 'token'},async()=>{calls++;throw new TypeError('network');});
  await assert.rejects(api.request('/api/chat',{method:'POST',body:{message:'질문'}}));
  assert.equal(calls,1);
});
