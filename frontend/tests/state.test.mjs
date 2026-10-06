import test from 'node:test';
import assert from 'node:assert/strict';
test('switching stocks rejects responses from the previous stock', async () => {
  const { createState } = await import('../js/state.js');
  const state = createState();
  state.selectStock({symbol:'005930'});
  const old = state.ticket();
  state.selectStock({symbol:'000660'});
  assert.equal(state.isCurrent(old), false);
  assert.equal(state.conversationId, null);
  assert.equal(state.stock.symbol, '000660');
});
test('logging out invalidates pending requests and clears private state', async () => {
  const { createState } = await import('../js/state.js');
  const state = createState();
  state.selectStock({symbol:'005930'}); state.conversationId = 'private';
  const old = state.ticket(); state.reset();
  assert.equal(state.isCurrent(old), false);
  assert.equal(state.stock, null); assert.equal(state.conversationId, null);
});
