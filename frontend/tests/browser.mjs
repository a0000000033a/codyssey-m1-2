// Real DOM + HTTP against test-only backend. Firebase/GPT/Firestore are substituted.
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('**/config.js',r=>r.fulfill({contentType:'application/javascript',body:'window.APP_CONFIG={apiBaseUrl:"http://127.0.0.1:8001",firebase:{apiKey:"test",authDomain:"test",projectId:"test"}};'}));
await page.route('**/js/auth.js',r=>r.fulfill({contentType:'application/javascript',body:'export async function createAuth(c,onChange){setTimeout(()=>onChange(null),0);return {login:async()=>onChange({uid:"browser-test"}),logout:async()=>onChange(null),getIdToken:async()=>"browser-test"};}'}));
try{
  for(const path of ['data','conversations']){
    const response=await page.request.get(`http://127.0.0.1:8001/api/${path}?symbol=005930&limit=100`,{headers:{Authorization:'Bearer browser-test'}});
    for(const row of (await response.json()).items)await page.request.delete(`http://127.0.0.1:8001/api/${path}/${row.id}`,{headers:{Authorization:'Bearer browser-test'}});
  }
  await page.goto('http://127.0.0.1:5500');
  await page.fill('#email','test@example.test');await page.fill('#password','test-password');
  await page.click('#login-button');await page.waitForSelector('#workspace:visible',{timeout:5000});
  await page.fill('#search-input','삼성');await page.click('#search-form button');
  await page.getByRole('button',{name:'등록',exact:true}).first().click();
  await page.locator('.watch-select').first().click();
  await page.waitForSelector('.metric');
  await page.click('#tab-records');await page.fill('#record-date','2026-09-01');await page.fill('#record-value','60000');
  await page.fill('#record-memo','<img src=x onerror=alert(1)>');await page.click('#record-save');
  await page.waitForSelector('.record');assert.ok((await page.locator('.record-memo').textContent()).includes('<img'));
  assert.equal(await page.locator('.record-memo img').count(),0);
  await page.getByRole('button',{name:'수정',exact:true}).click();await page.fill('#record-value','61000');await page.click('#record-save');
  await page.waitForFunction(()=>document.querySelector('.record-head')?.textContent.includes('61,000'));
  await page.click('#tab-chat');await page.click('#new-conversation');
  await page.fill('#question','첫 번째 대화 질문');await page.click('#send');await page.waitForSelector('.message.assistant');
  await page.click('#new-conversation');await page.fill('#question','두 번째 대화 질문');await page.click('#send');
  await page.waitForFunction(()=>document.querySelectorAll('.conversation-open').length>=2);
  await page.locator('.conversation-open').filter({hasText:'첫 번째 대화 질문'}).click();
  await page.waitForFunction(()=>document.querySelector('.message.user .message-body')?.textContent==='첫 번째 대화 질문');
  assert.equal(await page.locator('.message.user').count(),1);
  await page.evaluate(()=>{const note=document.createElement('div');note.textContent='개발 검증 화면 · 인증/저장소/GPT는 테스트 대체 객체를 사용합니다.';note.style.cssText='background:#ffe8bc;padding:8px;text-align:center;font-size:12px';document.body.prepend(note);});
  await mkdir('docs/screenshots/development',{recursive:true});
  await page.screenshot({path:'docs/screenshots/development/chat.png',fullPage:true});
  await page.click('#tab-records');await page.screenshot({path:'docs/screenshots/development/records.png',fullPage:true});
  page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'삭제',exact:true}).click();
  await page.waitForFunction(()=>document.querySelectorAll('.record').length===0);
  await page.setViewportSize({width:390,height:844});await page.click('#tab-chat');
  await page.screenshot({path:'docs/screenshots/development/mobile.png',fullPage:true});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
  await page.click('#logout');await page.waitForSelector('#login-panel:visible');
  assert.deepEqual(errors,[]);console.log('PASS browser: login, stock, record CRUD/XSS, two conversations, restore, mobile, logout (test-only external adapters).');
}finally{await browser.close();}
