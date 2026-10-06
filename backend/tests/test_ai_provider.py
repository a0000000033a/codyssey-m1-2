import json
import httpx
import pytest
import openai
from app.core.config import Settings
from app.core.errors import ApiError
from app.providers.ai import AIProvider

CONTEXT={'instructions':'요약을 근거로 답합니다.','input':[{'role':'user','content':'개인 메모'},{'role':'assistant','content':'이전 답변'},{'role':'user','content':'추세는?'}]}


def client_stub(monkeypatch,handler):
    original=openai.OpenAI
    monkeypatch.setattr(openai,'OpenAI',lambda **kwargs: original(**kwargs,http_client=httpx.Client(transport=httpx.MockTransport(handler))))


@pytest.mark.parametrize("token_field", ["max_completion_tokens", "max_tokens"])
def test_chat_mode_uses_custom_host_and_preserves_context(monkeypatch,token_field):
    def handle(request):
        assert str(request.url)=='https://gateway.test/v1/chat/completions'
        body=json.loads(request.content)
        assert body['messages']==[{'role':'system','content':CONTEXT['instructions']}]+CONTEXT['input']
        assert body[token_field]==800 and body['model']=='gpt-5.4-mini'
        return httpx.Response(200,json={'id':'test','object':'chat.completion','created':0,'model':'gpt-5.4-mini','choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'요약 기반 답변'}}]})
    client_stub(monkeypatch,handle)
    settings=Settings(_env_file=None,openai_api_key='test-only',openai_model='gpt-5.4-mini',openai_base_url='https://gateway.test/v1',openai_api_mode='chat_completions',openai_chat_token_field=token_field)
    assert AIProvider(settings).answer(CONTEXT)=='요약 기반 답변'


@pytest.mark.parametrize('reason,content',[('length','부분 답변'),('stop',''),('content_filter',None)])
def test_chat_rejects_incomplete_or_empty_answer(monkeypatch,reason,content):
    client_stub(monkeypatch,lambda request:httpx.Response(200,json={'id':'test','object':'chat.completion','created':0,'model':'test','choices':[{'index':0,'finish_reason':reason,'message':{'role':'assistant','content':content}}]}))
    settings=Settings(_env_file=None,openai_api_key='test-only',openai_model='test',openai_base_url='https://gateway.test/v1',openai_api_mode='chat_completions')
    with pytest.raises(ApiError) as failure:AIProvider(settings).answer(CONTEXT)
    assert failure.value.code=='incomplete_answer'


def test_responses_mode_preserves_previous_contract(monkeypatch):
    def handle(request):
        assert str(request.url)=='https://api.openai.com/v1/responses'
        body=json.loads(request.content)
        assert body['instructions']==CONTEXT['instructions'] and body['input']==CONTEXT['input']
        assert body['max_output_tokens']==800 and body['store'] is False
        return httpx.Response(200,json={'id':'test','object':'response','created_at':0,'model':'test','status':'completed','output':[{'type':'message','id':'msg','role':'assistant','status':'completed','content':[{'type':'output_text','text':'답변','annotations':[]}]}]})
    client_stub(monkeypatch,handle)
    assert AIProvider(Settings(_env_file=None,openai_api_key='test-only',openai_model='test')).answer(CONTEXT)=='답변'
