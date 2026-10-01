from ..core.errors import ApiError


class AIProvider:
    def __init__(self, settings):
        self.settings = settings

    def answer(self, context):
        if not self.settings.openai_api_key.get_secret_value() or not self.settings.openai_model:
            raise ApiError(503, "configuration_required", "OpenAI 키와 모델 설정이 필요합니다.")
        from openai import OpenAI
        with OpenAI(api_key=self.settings.openai_api_key.get_secret_value(), timeout=self.settings.openai_timeout_seconds, max_retries=0) as client:
            response = client.responses.create(model=self.settings.openai_model,
                instructions=context["instructions"], input=context["input"],
                max_output_tokens=self.settings.openai_max_output_tokens, store=False)
        if response.status != "completed" or not response.output_text.strip():
            raise ApiError(502, "incomplete_answer", "답변이 완성되지 않았습니다. 질문을 줄여 다시 요청해주세요.")
        return response.output_text
