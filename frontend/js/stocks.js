import {$,el,button} from './ui.js';

export function createStocks(ctx){
  let searchCursor=null,searchQuery='',searchGeneration=0;
  async function watchlist(){
    const ticket=ctx.state.ticket();const result=await ctx.api.request('/api/watchlist');
    if(!ctx.state.isCurrent(ticket))return;
    $('watchlist').replaceChildren();
    if(!result.items.length)$('watchlist').append(el('p','hint','검색한 종목을 관심 목록에 등록해주세요.'));
    for(const stock of result.items){
      const row=el('div','watch-row'+(ctx.state.stock?.symbol===stock.symbol?' active':''));
      const select=button('',()=>ctx.perform(()=>ctx.selectStock(stock)),'watch-select');
      select.append(el('strong','',stock.name),el('small','',`${stock.symbol} · ${stock.exchange}`));
      const remove=button('×',()=>ctx.perform(async()=>{if(!confirm(`${stock.name}을 관심 목록에서 제거할까요? 기록과 대화는 보존됩니다.`))return;await ctx.api.request(`/api/watchlist/${stock.id}`,{method:'DELETE'});await watchlist();}),'button subtle remove');
      remove.setAttribute('aria-label',`${stock.name} 관심 목록에서 제거`);row.append(select,remove);$('watchlist').append(row);
    }
  }
  async function search(more=false){
    const generation=++searchGeneration;const ticket=ctx.state.ticket();
    if(!more){searchQuery=$('search-input').value.trim();searchCursor=null;$('search-results').replaceChildren();}
    const result=await ctx.api.request(`/api/stocks?q=${encodeURIComponent(searchQuery)}${more&&searchCursor?`&cursor=${encodeURIComponent(searchCursor)}`:''}`);
    if(generation!==searchGeneration||!ctx.state.isCurrent(ticket))return;
    searchCursor=result.next_cursor;$('search-more').hidden=!searchCursor;
    if(!result.items.length&&!more)$('search-results').append(el('p','hint','검색 결과가 없습니다. 종목명 또는 코드를 확인해주세요.'));
    for(const stock of result.items){
      const row=el('div','search-result');row.append(el('span','',`${stock.name} · ${stock.symbol}`));
      const add=button('등록',()=>ctx.perform(async()=>{add.disabled=true;try{await ctx.api.request('/api/watchlist',{method:'POST',body:{symbol:stock.symbol}});if(!ctx.state.isCurrent(ticket))return;await watchlist();ctx.notice(`${stock.name}을 등록했습니다.`);}finally{add.disabled=false;}}),'button compact');
      row.append(add);$('search-results').append(row);
    }
  }
  $('search-form').addEventListener('submit',event=>{event.preventDefault();ctx.perform(()=>search());});
  $('search-more').addEventListener('click',()=>ctx.perform(()=>search(true)));
  return {watchlist,search};
}
