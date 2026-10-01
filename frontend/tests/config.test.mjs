import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, readFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
test('build emits only public settings and safely escapes values', async () => {
  const dir=await mkdtemp(join(tmpdir(),'stock-config-'));
  try {
    execFileSync(process.execPath,['frontend/scripts/build-config.mjs',join(dir,'config.js')],{env:{...process.env,API_BASE_URL:'https://api.test',FIREBASE_API_KEY:'public"key',OPENAI_API_KEY:'supersecret',FIREBASE_SERVICE_ACCOUNT_JSON:'private'}});
    const output=await readFile(join(dir,'config.js'),'utf8');
    assert.ok(!output.includes('supersecret'));assert.ok(!output.includes('private'));
    const config=JSON.parse(output.replace('window.APP_CONFIG = ','').replace(/;\s*$/,''));
    assert.equal(config.firebase.apiKey,'public"key');assert.equal(config.apiBaseUrl,'https://api.test');
  } finally {await rm(dir,{recursive:true,force:true});}
});
