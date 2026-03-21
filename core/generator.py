"""LLM 기반 블로그 초안 생성 모듈."""

import json
import re
from collections.abc import Generator
from pathlib import Path

import yaml

from core.llm_client import LLMClient
from core.logger import get_logger

logger = get_logger(__name__)


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> dict:
    """YAML 프롬프트 템플릿 로드."""
    path = PROMPTS_DIR / f"{name}.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_reference_context(reference_posts: list[dict]) -> tuple[str, str]:
    """레퍼런스 글 목록에서 프롬프트용 텍스트를 생성.

    Returns:
        (ref_text, img_pos_text) 튜플
    """
    ref_text = ""
    img_pos_text = ""
    if not reference_posts:
        return "(레퍼런스 없음)", "(없음)"

    for i, ref in enumerate(reference_posts, 1):
        ref_text += (
            f"\n### 레퍼런스 {i}: {ref.get('title', '')}\n"
            f"{ref.get('content', '')[:1500]}\n"
        )
        positions = ref.get("image_positions", [])
        img_pos_text += f"레퍼런스 {i}: {positions}\n"

    return ref_text, img_pos_text


def generate_draft(
    llm_client: LLMClient,
    target_keyword: str,
    image_descriptions: list[str],
    reference_posts: list[dict],
) -> dict:
    """키워드 + 이미지 설명 + 레퍼런스 기반으로 블로그 초안 생성.

    Returns:
        {"title", "content" (HTML), "tags", "summary"}
    """
    prompt_template = load_prompt("draft_generation")

    ref_text, img_pos_text = _build_reference_context(reference_posts)

    # 이미지 설명 구성
    img_desc_text = ""
    for i, desc in enumerate(image_descriptions, 1):
        img_desc_text += f"이미지 {i}: {desc}\n"

    # 프롬프트 렌더링
    system_prompt = prompt_template["system"].format(
        reference_posts=ref_text,
        image_positions=img_pos_text,
        target_keyword=target_keyword,
    )
    user_prompt = prompt_template["user"].format(
        target_keyword=target_keyword,
        image_count=len(image_descriptions),
        image_descriptions=img_desc_text,
    )

    raw = llm_client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
    result = _parse_json_response(raw)
    logger.info("초안 생성 완료: title='%s'", result.get("title", "")[:40])
    return result


def revise_draft(
    llm_client: LLMClient,
    original: dict,
    instruction: str,
    reference_posts: list[dict] | None = None,
) -> dict:
    """기존 초안을 수정 지시에 따라 재생성.

    Args:
        reference_posts: 레퍼런스 글 목록 (톤 & 매너 유지용)
    """
    ref_context = ""
    if reference_posts:
        ref_text, _ = _build_reference_context(reference_posts)
        ref_context = (
            f"\n## 레퍼런스 글 (톤 & 매너 유지 필수)\n{ref_text}\n"
            "위 레퍼런스 글의 톤 & 매너, 문체를 반드시 유지하세요.\n"
        )

    system_prompt = (
        "당신은 네이버 블로그 전문 작가입니다. "
        "기존 글을 수정 요청에 맞게 수정합니다.\n\n"
        f"{ref_context}"
        "## 규칙\n"
        "1. 수정 요청 사항만 반영하고 나머지는 유지하세요.\n"
        "2. 이미지 플레이스홀더([IMAGE_N])는 유지하세요.\n"
        "3. HTML 형식을 유지하세요.\n"
        "4. 한국어로 작성하세요.\n"
        "5. 레퍼런스 글의 톤 & 매너를 유지하세요.\n\n"
        '## 출력 형식\nJSON: {{"title": "...", "content": "...", "tags": [...], "summary": "..."}}'
    )

    user_prompt = (
        f"## 기존 글\n"
        f"제목: {original.get('title', '')}\n"
        f"본문:\n{original.get('content', '')}\n"
        f"태그: {', '.join(original.get('tags', []))}\n\n"
        f"## 수정 요청\n{instruction}"
    )

    raw = llm_client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
    result = _parse_json_response(raw)
    logger.info("수정 완료: title='%s'", result.get("title", "")[:40])
    return result


def seo_optimize_draft(
    llm_client: LLMClient,
    original: dict,
    seo_feedback: str,
    target_keyword: str,
    reference_posts: list[dict] | None = None,
) -> dict:
    """SEO 분석 결과를 기반으로 글을 최적화 재작성.

    Args:
        original: 기존 초안 {"title", "content", "tags", "summary"}
        seo_feedback: SEO 검증에서 나온 개선 사항 텍스트
        target_keyword: 타겟 키워드
        reference_posts: 레퍼런스 글 목록 (톤 & 매너 유지용)
    """
    prompt_template = load_prompt("seo_optimization")

    ref_text, img_pos_text = _build_reference_context(reference_posts or [])

    system_prompt = prompt_template["system"].format(
        reference_posts=ref_text,
        image_positions=img_pos_text,
        seo_feedback=seo_feedback,
        target_keyword=target_keyword,
    )
    user_prompt = prompt_template["user"].format(
        title=original.get("title", ""),
        content=original.get("content", ""),
        tags=", ".join(original.get("tags", [])),
    )

    raw = llm_client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
    result = _parse_json_response(raw)
    logger.info("SEO 최적화 완료: title='%s'", result.get("title", "")[:40])
    return result


def generate_draft_stream(
    llm_client: LLMClient,
    target_keyword: str,
    image_descriptions: list[str],
    reference_posts: list[dict],
) -> Generator[str, None, None]:
    """스트리밍 방식으로 블로그 초안 생성. 토큰 단위로 yield."""
    prompt_template = load_prompt("draft_generation")

    ref_text, img_pos_text = _build_reference_context(reference_posts)

    img_desc_text = ""
    for i, desc in enumerate(image_descriptions, 1):
        img_desc_text += f"이미지 {i}: {desc}\n"

    system_prompt = prompt_template["system"].format(
        reference_posts=ref_text,
        image_positions=img_pos_text,
        target_keyword=target_keyword,
    )
    user_prompt = prompt_template["user"].format(
        target_keyword=target_keyword,
        image_count=len(image_descriptions),
        image_descriptions=img_desc_text,
    )

    yield from llm_client.generate_stream(
        system_prompt=system_prompt, user_prompt=user_prompt
    )


def revise_draft_stream(
    llm_client: LLMClient,
    original: dict,
    instruction: str,
    reference_posts: list[dict] | None = None,
) -> Generator[str, None, None]:
    """스트리밍 방식으로 수정 생성. 토큰 단위로 yield."""
    ref_context = ""
    if reference_posts:
        ref_text, _ = _build_reference_context(reference_posts)
        ref_context = (
            f"\n## 레퍼런스 글 (톤 & 매너 유지 필수)\n{ref_text}\n"
            "위 레퍼런스 글의 톤 & 매너, 문체를 반드시 유지하세요.\n"
        )

    system_prompt = (
        "당신은 네이버 블로그 전문 작가입니다. "
        "기존 글을 수정 요청에 맞게 수정합니다.\n\n"
        f"{ref_context}"
        "## 규칙\n"
        "1. 수정 요청 사항만 반영하고 나머지는 유지하세요.\n"
        "2. 이미지 플레이스홀더([IMAGE_N])는 유지하세요.\n"
        "3. HTML 형식을 유지하세요.\n"
        "4. 한국어로 작성하세요.\n"
        "5. 레퍼런스 글의 톤 & 매너를 유지하세요.\n\n"
        '## 출력 형식\nJSON: {{"title": "...", "content": "...", "tags": [...], "summary": "..."}}'
    )

    user_prompt = (
        f"## 기존 글\n"
        f"제목: {original.get('title', '')}\n"
        f"본문:\n{original.get('content', '')}\n"
        f"태그: {', '.join(original.get('tags', []))}\n\n"
        f"## 수정 요청\n{instruction}"
    )

    yield from llm_client.generate_stream(
        system_prompt=system_prompt, user_prompt=user_prompt
    )


def seo_optimize_draft_stream(
    llm_client: LLMClient,
    original: dict,
    seo_feedback: str,
    target_keyword: str,
    reference_posts: list[dict] | None = None,
) -> Generator[str, None, None]:
    """스트리밍 방식으로 SEO 최적화 재작성. 토큰 단위로 yield."""
    prompt_template = load_prompt("seo_optimization")

    ref_text, img_pos_text = _build_reference_context(reference_posts or [])

    system_prompt = prompt_template["system"].format(
        reference_posts=ref_text,
        image_positions=img_pos_text,
        seo_feedback=seo_feedback,
        target_keyword=target_keyword,
    )
    user_prompt = prompt_template["user"].format(
        title=original.get("title", ""),
        content=original.get("content", ""),
        tags=", ".join(original.get("tags", [])),
    )

    yield from llm_client.generate_stream(
        system_prompt=system_prompt, user_prompt=user_prompt
    )


def _parse_json_response(raw: str) -> dict:
    """LLM 응답에서 JSON 추출. 실패 시 fallback."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"title": "", "content": raw, "tags": [], "summary": ""}
