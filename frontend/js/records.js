import {$,el,button,number} from './ui.js';

export function createRecords(ctx){
  let cursor=null,editing=null, saving=false;
  function reset(){editing=null;$('record-form').reset();$('record-date').value=new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Seoul'});$('record-date').max=$('record-date').value;$('record-save').textContent='기록 저장';$('record-cancel').hidden=true;}
  async function load(more=false){
    if(!ctx.state.stock)return;const ticket=ctx.state.ticket(),symbol=ctx.state.stock.symbol;
    const result=await ctx.api.request(`/api/data?symbol=${symbol}${more&&cursor?`&cursor=${encodeURIComponent(cursor)}`:''}`);
    if(!ctx.state.isCurrent(ticket))return;
    if(!more)$('records-list').replaceChildren();cursor=result.next_cursor;$('records-more').hidden=!cursor;
    if(!result.items.length&&!more)$('records-list').append(el('p','hint','아직 기록이 없습니다. 관심 가격과 메모를 남겨주세요.'));
    for(const record of result.items){
      const row=el('article','record'),main=el('div','record-main');
      main.append(el('div','record-head',`${record.date} · 관심 가격 ${number(record.value)}원`),el('p','record-memo',record.memo||'메모가 없습니다.'));
      const actions=el('div','record-actions');
      actions.append(button('수정',()=>{editing=record.id;$('record-date').value=record.date;$('record-value').value=record.value;$('record-memo').value=record.memo;$('record-save').textContent='수정 저장';$('record-cancel').hidden=false;$('record-value').focus();}),
        button('삭제',()=>ctx.perform(async()=>{if(!confirm('이 기록을 삭제할까요?'))return;await ctx.api.request(`/api/data/${record.id}`,{method:'DELETE'});if(!ctx.state.isCurrent(ticket))return;reset();await load();await ctx.loadSummary();ctx.notice('기록을 삭제했습니다.');})));
      row.append(main,actions);$('records-list').append(row);
    }
  }
  $('record-form').addEventListener('submit',event=>{event.preventDefault();ctx.perform(async()=>{
    if(!ctx.state.stock||saving)return;const ticket=ctx.state.ticket(),id=editing;
    saving=true;$('record-save').disabled=true;
    try{await ctx.api.request(id?`/api/data/${id}`:'/api/data',{method:id?'PUT':'POST',body:{symbol:ctx.state.stock.symbol,date:$('record-date').value,value:Number($('record-value').value),memo:$('record-memo').value}});
      if(!ctx.state.isCurrent(ticket))return;reset();await load();await ctx.loadSummary();ctx.notice(id?'기록을 수정했습니다.':'기록을 저장했습니다.');
    }finally{saving=false;if(ctx.state.isCurrent(ticket))$('record-save').disabled=!ctx.state.stock;}
  });});
  $('record-cancel').addEventListener('click',reset);$('records-more').addEventListener('click',()=>ctx.perform(()=>load(true)));
  return {load,reset};
}
