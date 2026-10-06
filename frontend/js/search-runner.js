export function createSearchRunner({request,apply,status,error,delay=300,setTimer=setTimeout,clearTimer=clearTimeout}){
 let generation=0,timer=null,controller=null;
 function cancel(){generation++;clearTimer(timer);timer=null;controller?.abort();controller=null;status(false);}
 async function run(query,more=false){
  cancel();if(!query.trim())return;const current=generation;controller=new AbortController();status(true);
  try{const result=await request(query,more,controller.signal);if(current===generation)apply(result,more);}
  catch(reason){if(current===generation)error(reason);}
  finally{if(current===generation){controller=null;status(false);}}
 }
 function schedule(query){cancel();if(!query.trim())return;timer=setTimer(()=>{timer=null;void run(query);},delay);}
 return {run,schedule,cancel};
}
