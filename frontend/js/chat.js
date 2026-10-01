import {$,el} from './ui.js';

export function createChat(ctx){
  function render(messages,title='새로운 관찰을 시작합니다.'){
    $('messages').replaceChildren();$('conversation-heading').textContent=title;
    if(!messages.length){const empty=el('div','empty-state');empty.append(el('span','empty-symbol','✦'),el('h3','',ctx.state.stock?`${ctx.state.stock.name}, 무엇이 궁금하신가요?`:'이 종목, 무엇이 궁금하신가요?'),el('p','',ctx.state.stock?'주가 흐름, 거래량, 내 기록에 대해 질문할 수 있습니다.':'먼저 왼쪽에서 관심 종목을 선택해주세요.'));$('messages').append(empty);}
    for(const message of messages){const item=el('article',`message ${message.role}`);item.append(el('div','message-label',message.role==='user'?'나의 질문':'AI 분석 비서'),el('div','message-body',message.content));
      const snapshot=message.context_snapshot;
      if(snapshot)item.append(el('div','message-context',`답변 근거 · ${snapshot.stock.name} · ${snapshot.market_data.start||'—'} ~ ${snapshot.market_data.end||'—'} · ${snapshot.market_data.count}개 데이터`));
      $('messages').append(item);}
    $('messages').scrollTop=$('messages').scrollHeight;
  }
  async function send(retry=false){
    if(!ctx.state.stock||ctx.state.busy)return;
    if(!retry){const message=$('question').value.trim();if(!message)return;
      ctx.state.pending={symbol:ctx.state.stock.symbol,conversation_id:ctx.state.conversationId,message,request_id:crypto.randomUUID()};}
    if(!ctx.state.pending)return;const ticket=ctx.state.ticket(),body={...ctx.state.pending};ctx.state.busy=true;ctx.setBusy();$('retry-chat').hidden=true;
    try{const result=await ctx.api.request('/api/chat',{method:'POST',body});if(!ctx.state.isCurrent(ticket))return;
      ctx.state.conversationId=result.conversation_id;
      const detail=await ctx.api.request(`/api/conversations/${result.conversation_id}`);if(!ctx.state.isCurrent(ticket))return;
      ctx.state.pending=null;$('question').value='';render(detail.messages,detail.title);ctx.notice('답변과 대화를 저장했습니다.');
    }catch(error){if(ctx.state.isCurrent(ticket)){$('retry-chat').hidden=false;ctx.notice(error.message,true);}return;
    }finally{if(ctx.state.isCurrent(ticket)){ctx.state.busy=false;ctx.setBusy();await ctx.conversations.load();}}
  }
  $('chat-form').addEventListener('submit',e=>{e.preventDefault();ctx.perform(()=>send());});
  $('retry-chat').addEventListener('click',()=>ctx.perform(()=>send(true)));
  for(const suggestion of document.querySelectorAll('.suggestion'))suggestion.addEventListener('click',()=>{$('question').value=suggestion.dataset.question;$('question').focus();});
  return {render,send};
}
