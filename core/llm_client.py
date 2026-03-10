"""LLM 호출 추상화 모듈 (Ollama 기본, GPT 전환 대비)."""

import ollama


class LLMClient:
    """Ollama 기반 LLM 클라이언트."""

    def __init__(self, model: str = "qwen3.5:27b"):
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """시스템/사용자 프롬프트로 텍스트 생성."""
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response["message"]["content"]

    def list_models(self) -> list[str]:
        """사용 가능한 Ollama 모델 목록 반환."""
        models = ollama.list()
        return [m.model for m in models.models]
