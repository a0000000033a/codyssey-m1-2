from ..core.errors import ApiError


class AIProvider:
    def __init__(self, settings):
        self.settings = settings

    def answer(self, context):
        settings = self.settings
        if not settings.openai_api_key.get_secret_value() or not settings.openai_model:
            raise ApiError(503, "configuration_required", "AI API 키와 모델 설정이 필요합니다.")
        from openai import OpenAI
        with OpenAI(api_key=settings.openai_api_key.get_secret_value(),
                    base_url=str(settings.openai_base_url),
                    timeout=settings.openai_timeout_seconds, max_retries=0) as client:
            if settings.openai_api_mode == "chat_completions":
                response = client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[{"role": "system", "content": context["instructions"]}] + context["input"],
                    **{settings.openai_chat_token_field: settings.openai_max_output_tokens})
                choice = response.choices[0] if response.choices else None
                answer = choice.message.content if choice and choice.finish_reason == "stop" else None
            else:
                response = client.responses.create(model=settings.openai_model,
                    instructions=context["instructions"], input=context["input"],
                    max_output_tokens=settings.openai_max_output_tokens, store=False)
                answer = response.output_text if response.status == "completed" else None
        if not answer or not answer.strip():
            raise ApiError(502, "incomplete_answer", "답변이 완성되지 않았습니다. 질문을 줄여 다시 요청해주세요.")
        return answer
