"""LLM 호출 추상화 모듈 (Ollama 기본, GPT 전환 대비)."""

from collections.abc import Generator

import ollama
from ollama import ResponseError

from core.logger import get_logger

logger = get_logger(__name__)


class OllamaConnectionError(Exception):
    """Ollama 서버 연결 실패 시 발생."""


class LLMClient:
    """Ollama 기반 LLM 클라이언트."""

    def __init__(self, model: str = "qwen3.5:27b"):
        self.model = model
        logger.info("LLMClient 초기화: model=%s", model)

    def check_connection(self) -> bool:
        """Ollama 서버 연결 상태 확인."""
        try:
            ollama.list()
            return True
        except Exception as e:
            logger.error("Ollama 서버 연결 실패: %s", e)
            return False

    def ensure_connected(self) -> None:
        """Ollama 연결을 확인하고, 실패 시 예외 발생."""
        if not self.check_connection():
            raise OllamaConnectionError(
                "Ollama 서버에 연결할 수 없습니다. "
                "'ollama serve' 명령으로 Ollama를 실행해 주세요."
            )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """시스템/사용자 프롬프트로 텍스트 생성."""
        self.ensure_connected()
        logger.debug("generate 호출: model=%s, prompt_len=%d", self.model, len(user_prompt))
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except ResponseError as e:
            if "not found" in str(e).lower():
                raise OllamaConnectionError(
                    f"모델 '{self.model}'을(를) 찾을 수 없습니다. "
                    f"'ollama pull {self.model}' 명령으로 모델을 다운로드해 주세요."
                ) from e
            raise
        result = response["message"]["content"]
        logger.info("generate 완료: response_len=%d", len(result))
        return result

    def generate_with_image(
        self, system_prompt: str, user_prompt: str, images: list[bytes]
    ) -> str:
        """멀티모달 생성 (이미지 포함)."""
        self.ensure_connected()
        logger.debug("generate_with_image 호출: model=%s, images=%d장", self.model, len(images))
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt, "images": images},
                ],
            )
        except ResponseError as e:
            if "not found" in str(e).lower():
                raise OllamaConnectionError(
                    f"모델 '{self.model}'을(를) 찾을 수 없습니다. "
                    f"'ollama pull {self.model}' 명령으로 모델을 다운로드해 주세요."
                ) from e
            raise
        result = response["message"]["content"]
        logger.info("generate_with_image 완료: response_len=%d", len(result))
        return result

    def generate_stream(
        self, system_prompt: str, user_prompt: str
    ) -> Generator[str, None, None]:
        """스트리밍 텍스트 생성. 토큰 단위로 yield."""
        self.ensure_connected()
        logger.debug("generate_stream 호출: model=%s", self.model)
        try:
            stream = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                if token:
                    yield token
        except ResponseError as e:
            if "not found" in str(e).lower():
                raise OllamaConnectionError(
                    f"모델 '{self.model}'을(를) 찾을 수 없습니다. "
                    f"'ollama pull {self.model}' 명령으로 모델을 다운로드해 주세요."
                ) from e
            raise

    def list_models(self) -> list[str]:
        """사용 가능한 Ollama 모델 목록 반환."""
        models = ollama.list()
        return [m.model for m in models.models]
