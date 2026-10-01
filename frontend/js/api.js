export function createAPI(baseUrl,auth,fetcher=globalThis.fetch){
  return {async request(path,{method='GET',body,signal}={}){
    const controller=new AbortController();
    const timeout=path==='/health'?60000:path==='/api/chat'?90000:30000;
    const timer=setTimeout(()=>controller.abort(),timeout);
    const abort=()=>controller.abort();signal?.addEventListener('abort',abort,{once:true});
    if(signal?.aborted)controller.abort();
    try{
      const execute=async(force)=>{
        const headers={'Content-Type':'application/json'};
        if(path!=='/health')headers.Authorization=`Bearer ${await auth.getIdToken(force)}`;
        return fetcher(`${baseUrl.replace(/\/$/,'')}${path}`,{method,headers,body:body===undefined?undefined:JSON.stringify(body),signal:controller.signal});
      };
      let response=await execute(false);
      if(response.status===401&&path!=='/health')response=await execute(true);
      if(response.status===204)return null;
      const value=await response.json().catch(()=>({}));
      if(!response.ok){const error=new Error(value.message|| (response.status===422?'입력 값을 확인해주세요.':'요청을 완료하지 못했습니다.'));error.code=value.code;error.status=response.status;throw error;}
      return value;
    }catch(error){if(error.name==='AbortError')throw new Error('연결이 지연되고 있습니다. 서버 준비에 시간이 걸릴 수 있습니다. 잠시 후 재시도해주세요.');throw error;}
    finally{clearTimeout(timer);signal?.removeEventListener('abort',abort);}
  }};
}
