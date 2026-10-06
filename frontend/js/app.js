import {createState} from './state.js';
import {createAPI} from './api.js';
import {createAuth} from './auth.js';
import {createStocks} from './stocks.js';
import {createRecords} from './records.js';
import {createConversations} from './conversations.js';
import {createChat} from './chat.js';
import {$,el,number} from './ui.js';

const state=createState();let auth,api,ctx,authenticated=false;
function notice(message,error=false){$('notice').textContent=message;$('notice').classList.toggle('error',error);}
async function perform(action){const ticket=state.ticket();try{await action();}catch(error){if(state.isCurrent(ticket))notice(error.message||'요청을 완료하지 못했습니다.',true);}}
function showTab(tab){for(const key of ['chat','records']){$(`${key}-panel`).hidden=key!==tab;$(`tab-${key}`).classList.toggle('active',key===tab);$(`tab-${key}`).setAttribute('aria-pressed',String(key===tab));}}
function setBusy(){for(const id of ['new-conversation','question','send','refresh'])$(id).disabled=!state.stock||state.busy;$('record-save').disabled=!state.stock;$('chat-loading').hidden=!state.busy;
  for(const b of document.querySelectorAll('.conversation-row button'))b.disabled=state.busy;
}
function blankSummary(){$('summary-cards').replaceChildren();$('period').textContent='종목 선택 후 표시합니다.';$('quality').textContent='최근 1년의 일별 데이터를 기준으로 분석합니다.';}
async function loadSummary(){
  if(!state.stock)return;const ticket=state.ticket();const data=await api.request(`/api/data/summary?symbol=${state.stock.symbol}`);
  if(!state.isCurrent(ticket))return;const market=data.market_data;
  $('period').textContent=`${market.start||'—'} ~ ${market.end||'—'}`;$('stock-meta').textContent=`${state.stock.symbol} · ${state.stock.exchange} · 일별 데이터 기준`;
  const trend={up:'상승',down:'하락',stable:'유지',insufficient:'판단 불가'}[market.trend.direction];
  const cards=[['최근 종가',number(market.last_close),'원',`기준일 ${market.end||'—'}`],['평균 종가',number(market.average_close),'원',`최저 ${number(market.min_close)} · 최고 ${number(market.max_close)}`],['분석 데이터',number(market.count),'개','최근 1년의 유효 데이터'],['최근 추세',trend,'',market.trend.change_percent===null?'비교 데이터가 부족합니다.':`20일 평균 대비 ${number(market.trend.change_percent)}%`]];
  $('summary-cards').replaceChildren();for(const [i,card] of cards.entries()){const item=el('div',`metric${i===3?' trend':''}`);const value=el('div','metric-value',card[1]);value.append(el('span','metric-unit',card[2]));item.append(el('span','metric-label',card[0]),value,el('div','metric-detail',card[3]));$('summary-cards').append(item);}
  $('quality').textContent=`출처 ${data.quality.source} · 평균 거래량 ${number(market.average_volume)} · 최근 거래량 ${number(market.last_volume)} · 내 기록 ${data.personal_records.count}개. ${data.quality.insufficient_sample?'100개 미만으로 분석 표본이 부족합니다. ':''}${data.quality.message||''} ${data.quality.adjustment}`;
}
async function selectStock(stock){if(state.busy)return;state.selectStock(stock);ctx.records.reset();ctx.chat.render([]);$('conversation-list').replaceChildren();$('records-list').replaceChildren();blankSummary();$('retry-chat').hidden=true;setBusy();
  $('stock-heading').textContent=stock.name;$('stock-meta').textContent=`${stock.symbol} · ${stock.exchange}`;notice('저장된 데이터를 확인하고 있습니다. 최초 조회는 시간이 걸릴 수 있습니다.');
  const ticket=state.ticket();const results=await Promise.allSettled([loadSummary(),ctx.records.load(),ctx.conversations.load(),ctx.stocks.watchlist()]);
  if(!state.isCurrent(ticket))return;const failed=results.find(r=>r.status==='rejected');notice(failed?failed.reason.message:'선택한 종목의 데이터와 기록을 불러왔습니다.',!!failed);
}
async function connect(){notice('서버에 연결하고 있습니다. 첫 연결은 시간이 걸릴 수 있습니다.');$('retry-connection').hidden=true;try{await api.request('/health');await api.request('/api/me');await ctx.stocks.watchlist();notice('서버에 연결했습니다. 관심 종목을 선택해주세요.');}catch(error){notice(error.message,true);$('retry-connection').hidden=false;}}
function clearPrivate(){ctx?.stocks?.reset();state.reset();for(const id of ['watchlist','search-results','conversation-list','records-list','messages','summary-cards'])$(id).replaceChildren();$('search-input').value='';$('question').value='';$('record-form').reset();$('stock-heading').textContent='관심 종목을 선택해주세요.';blankSummary();setBusy();}
async function onAuthChange(user){authenticated=!!user;$('workspace').hidden=!user;$('login-panel').hidden=!!user;if(!user){clearPrivate();return;}if(api)await connect();}

$('login-form').addEventListener('submit',async event=>{event.preventDefault();if(!auth)return;$('login-button').disabled=true;$('login-status').textContent='로그인하고 있습니다.';try{await auth.login($('email').value.trim(),$('password').value);$('password').value='';$('login-status').textContent='';}catch(error){$('login-status').textContent='로그인하지 못했습니다. 계정과 비밀번호를 확인해주세요.';}finally{$('login-button').disabled=false;}});
$('logout').addEventListener('click',()=>perform(()=>auth.logout()));
$('tab-chat').addEventListener('click',()=>showTab('chat'));$('tab-records').addEventListener('click',()=>showTab('records'));
$('refresh').addEventListener('click',()=>perform(async()=>{if(!state.stock)return;const ticket=state.ticket();$('refresh').disabled=true;try{notice('시장 데이터를 새로 가져오고 있습니다.');await api.request(`/api/stocks/${state.stock.symbol}/refresh`,{method:'POST'});if(!state.isCurrent(ticket))return;await loadSummary();notice('데이터 조회를 마쳤습니다. 기준일과 갱신 상태를 확인해주세요.');}finally{if(state.isCurrent(ticket))setBusy();}}));
$('retry-connection').addEventListener('click',()=>perform(connect));

try{
  const config=window.APP_CONFIG;if(!config)throw new Error('프론트 설정이 없습니다. npm run build를 먼저 실행해주세요.');
  auth=await createAuth(config.firebase,onAuthChange);api=createAPI(config.apiBaseUrl,auth);
  ctx={state,api,notice,perform,showTab,setBusy,selectStock,loadSummary};ctx.chat=createChat(ctx);ctx.records=createRecords(ctx);ctx.conversations=createConversations(ctx);ctx.stocks=createStocks(ctx);
  $('login-status').textContent='허용된 개인 계정으로 로그인해주세요.';ctx.records.reset();
  if(authenticated)await connect();
}catch(error){$('login-status').textContent=error.message;$('login-button').disabled=true;}
