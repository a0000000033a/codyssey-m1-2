import {$,el,button} from './ui.js';
import {createSearchRunner} from './search-runner.js';

export function createStocks(ctx){
  let searchCursor=null,searchQuery='',searchTicket=null;
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
  const runner=createSearchRunner({
    async request(query,more,signal){
      const ticket=ctx.state.ticket();searchTicket=ticket;
      if(!more){searchQuery=query;searchCursor=null;$('search-results').replaceChildren();$('search-more').hidden=true;}
      const result=await ctx.api.request(`/api/stocks?q=${encodeURIComponent(searchQuery)}${more&&searchCursor?`&cursor=${encodeURIComponent(searchCursor)}`:''}`,{signal});
      return {result,ticket};
    },
    status(busy){$('search-status').textContent=busy?'종목을 검색하고 있습니다.':'';$('search-results').setAttribute('aria-busy',String(busy));$('search-more').disabled=busy;},
    error(reason){if(ctx.state.isCurrent(searchTicket))ctx.notice(reason.message||'검색하지 못했습니다. 다시 검색해주세요.',true);},
    apply({result,ticket},more){
    if(!ctx.state.isCurrent(ticket))return;
    searchCursor=result.next_cursor;$('search-more').hidden=!searchCursor;
    if(!result.items.length&&!more)$('search-results').append(el('p','hint','검색 결과가 없습니다. 종목명 또는 코드를 확인해주세요.'));
    for(const stock of result.items){
      const row=el('div','search-result');row.append(el('span','',`${stock.name} · ${stock.symbol}`));
      const add=button('등록',()=>ctx.perform(async()=>{add.disabled=true;try{await ctx.api.request('/api/watchlist',{method:'POST',body:{symbol:stock.symbol}});if(!ctx.state.isCurrent(ticket))return;await watchlist();ctx.notice(`${stock.name}을 등록했습니다.`);}finally{add.disabled=false;}}),'button compact');
      row.append(add);$('search-results').append(row);
    }
    }
  });
  function search(more=false){return runner.run($('search-input').value.trim(),more);}
  $('search-input').addEventListener('input',()=>{searchCursor=null;$('search-results').replaceChildren();$('search-more').hidden=true;runner.schedule($('search-input').value.trim());});
  $('search-form').addEventListener('submit',event=>{event.preventDefault();void search();});
  $('search-more').addEventListener('click',()=>{void search(true);});
  return {watchlist,search,reset:()=>runner.cancel()};
}
