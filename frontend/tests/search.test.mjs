import test from 'node:test';
import assert from 'node:assert/strict';
import {createSearchRunner} from '../js/search-runner.js';
test('typing invalidates an in-flight result before the next search starts',async()=>{
 let resolve,signal;const results=[];
 const runner=createSearchRunner({request:(q,m,s)=>{signal=s;return new Promise(r=>resolve=r);},apply:r=>results.push(r),status:()=>{},error:()=>{}});
 const pending=runner.run('삼');runner.cancel();assert.equal(signal.aborted,true);resolve({items:['old']});await pending;
 assert.deepEqual(results,[]);
});
test('superseded errors do not replace the latest search status',async()=>{
 let reject;const errors=[];
 const runner=createSearchRunner({request:()=>new Promise((r,j)=>reject=j),apply:()=>{},status:()=>{},error:e=>errors.push(e)});
 const pending=runner.run('삼');runner.cancel();reject(new Error('old'));await pending;
 assert.deepEqual(errors,[]);
});
test('rapid input schedules only the latest query',async()=>{
 let callback,cleared=0,signal;const queries=[];
 const runner=createSearchRunner({request:async(q,m,s)=>{queries.push(q);signal=s;return {};},apply:()=>{},status:()=>{},error:()=>{},setTimer:fn=>{callback=fn;return 1;},clearTimer:()=>{cleared++;}});
 runner.schedule('삼');runner.schedule('삼성');assert.deepEqual(queries,[]);
 callback();await Promise.resolve();assert.deepEqual(queries,['삼성']);assert.ok(cleared>=2);
 runner.cancel();
});
