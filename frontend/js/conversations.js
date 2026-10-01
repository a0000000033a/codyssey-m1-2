import {$,el,button,dateTime} from './ui.js';

export function createConversations(ctx){
  let cursor=null;
  async function load(more=false){
    if(!ctx.state.stock)return;const ticket=ctx.state.ticket(),symbol=ctx.state.stock.symbol;
    const result=await ctx.api.request(`/api/conversations?symbol=${symbol}${more&&cursor?`&cursor=${encodeURIComponent(cursor)}`:''}`);
    if(!ctx.state.isCurrent(ticket))return;
    if(!more)$('conversation-list').replaceChildren();cursor=result.next_cursor;$('conversation-more').hidden=!cursor;
    if(!result.items.length&&!more)$('conversation-list').append(el('p','hint','이 종목의 첫 대화를 시작해주세요.'));
    for(const conversation of result.items){
      const row=el('div','conversation-row'+(ctx.state.conversationId===conversation.id?' active':''));
      const open=button('',()=>ctx.perform(()=>restore(conversation.id)),'conversation-open');
      open.append(el('span','',conversation.title),el('small','',dateTime(conversation.updated_at)));
      open.disabled=ctx.state.busy||conversation.status!=='active';
      const remove=button('×',()=>ctx.perform(async()=>{if(!confirm('대화와 메시지를 삭제할까요?'))return;await ctx.api.request(`/api/conversations/${conversation.id}`,{method:'DELETE'});if(!ctx.state.isCurrent(ticket))return;if(ctx.state.conversationId===conversation.id){ctx.state.conversationId=null;ctx.state.pending=null;ctx.chat.render([]);}$('retry-chat').hidden=true;await load();ctx.notice('대화를 삭제했습니다.');}),'button subtle remove');
      remove.setAttribute('aria-label',`${conversation.title} 대화 삭제`);remove.disabled=ctx.state.busy;
      row.append(open,remove);$('conversation-list').append(row);
    }
  }
  async function restore(id){
    if(ctx.state.busy)return;const ticket=ctx.state.ticket();
    const detail=await ctx.api.request(`/api/conversations/${id}`);
    if(!ctx.state.isCurrent(ticket))return;
    if(ctx.state.stock?.symbol!==detail.symbol){await ctx.selectStock({symbol:detail.symbol,name:detail.stock_name,exchange:'국내 주식'});}
    ctx.state.conversationId=id;ctx.state.pending=null;$('retry-chat').hidden=true;
    ctx.chat.render(detail.messages,detail.title);ctx.showTab('chat');await load();
    ctx.notice('대화를 불러왔습니다. 이어서 질문할 수 있습니다.');
  }
  async function create(){
    if(!ctx.state.stock||ctx.state.busy)return;const ticket=ctx.state.ticket();
    const detail=await ctx.api.request('/api/conversations',{method:'POST',body:{symbol:ctx.state.stock.symbol,messages:[]}});
    if(!ctx.state.isCurrent(ticket))return;
    ctx.state.conversationId=detail.id;ctx.state.pending=null;ctx.chat.render([],'새 대화');$('retry-chat').hidden=true;
    await load();ctx.showTab('chat');$('question').focus();ctx.notice('새 대화를 만들었습니다.');
  }
  $('new-conversation').addEventListener('click',()=>ctx.perform(create));$('conversation-more').addEventListener('click',()=>ctx.perform(()=>load(true)));
  return {load,restore,create};
}
