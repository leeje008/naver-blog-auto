"""네이버 블로그 SEO 검증 모듈.

생성된 블로그 글의 SEO 품질을 분석하고 점수/피드백을 반환한다.
네이버 C-Rank/D.I.A.+ 알고리즘 기준에 맞춘 10개 항목 검증.
"""

import math
import re
import statistics

from bs4 import BeautifulSoup


# --- SEO 설정값 (SEO_RESEARCH.md 기반) ---

NAVER_SEO_CONFIG = {
    "title": {
        "max_length": 25,
        "keyword_position": "start",
    },
    "body": {
        "min_chars": 1500,
        "optimal_min": 2500,
        "optimal_max": 3000,
        "max_chars": 4000,
    },
    "keyword": {
        "density_min": 1.0,
        "density_max": 2.0,
        "first_200_required": True,
        "last_200_required": True,
    },
    "headings": {
        "h2_per_1000_chars_min": 3,
        "h2_per_1000_chars_max": 5,
    },
    "images": {
        "min_count": 3,
        "alt_min_chars": 20,
        "alt_max_chars": 50,
    },
    "hashtags": {
        "optimal_min": 5,
        "optimal_max": 10,
    },
}

# --- SEO 프로파일 시스템 ---

SEO_PROFILES: dict[str, dict[str, float]] = {
    "balanced": {
        "title": 0.15,
        "body_length": 0.10,
        "keyword_density": 0.18,
        "heading_structure": 0.12,
        "images": 0.08,
        "hashtags": 0.07,
        "readability": 0.12,
        "experience_signals": 0.08,
        "information_depth": 0.05,
        "ai_safety": 0.05,
    },
    "keyword_focused": {
        "title": 0.20,
        "body_length": 0.10,
        "keyword_density": 0.30,
        "heading_structure": 0.15,
        "images": 0.05,
        "hashtags": 0.05,
        "readability": 0.05,
        "experience_signals": 0.05,
        "information_depth": 0.03,
        "ai_safety": 0.02,
    },
    "authenticity": {
        "title": 0.10,
        "body_length": 0.05,
        "keyword_density": 0.10,
        "heading_structure": 0.05,
        "images": 0.03,
        "hashtags": 0.02,
        "readability": 0.15,
        "experience_signals": 0.20,
        "information_depth": 0.10,
        "ai_safety": 0.20,
    },
}

# 기본 가중치 (balanced)
WEIGHTS = SEO_PROFILES["balanced"]

# 프로파일 한글 레이블
PROFILE_LABELS: dict[str, str] = {
    "balanced": "균형 최적화",
    "keyword_focused": "키워드 상위 노출",
    "authenticity": "진정성 (저품질 방지)",
}


def get_profile_weights(profile: str = "balanced") -> dict[str, float]:
    """프로파일명으로 가중치 딕셔너리 반환."""
    return SEO_PROFILES.get(profile, SEO_PROFILES["balanced"])


def validate_seo(
    draft: dict,
    target_keyword: str,
    image_count: int = 0,
    profile: str = "balanced",
    custom_weights: dict[str, float] | None = None,
) -> dict:
    """전체 SEO 검증 → 종합 점수 + 항목별 결과 반환.

    Args:
        draft: {"title", "content" (HTML), "tags", "summary"}
        target_keyword: 타겟 키워드
        image_count: 업로드된 이미지 수
        profile: SEO 프로파일 ("balanced", "keyword_focused", "authenticity")
        custom_weights: 사용자 정의 가중치 (None이면 프로파일 사용)

    Returns:
        {"score": 0~100, "grade": "A"~"D", "profile": str, "checks": {...}}
    """
    title = draft.get("title", "")
    content = draft.get("content", "")
    tags = draft.get("tags", [])

    checks = {
        "title": _check_title(title, target_keyword),
        "body_length": _check_body_length(content),
        "keyword_density": _check_keyword_density(content, target_keyword),
        "heading_structure": _check_heading_structure(content, target_keyword),
        "images": _check_images(content, image_count),
        "hashtags": _check_hashtags(tags, target_keyword),
        "readability": _check_readability(content),
        "experience_signals": _check_experience_signals(content),
        "information_depth": _check_information_depth(content),
        "ai_safety": _check_ai_safety(content),
    }

    # 가중치 결정
    weights = custom_weights if custom_weights else get_profile_weights(profile)

    # 가중 평균 계산
    total_score = sum(
        checks[key]["score"] * weights.get(key, 0) for key in checks
    )
    total_score = round(total_score)

    # 등급 판정
    if total_score >= 90:
        grade = "A"
    elif total_score >= 70:
        grade = "B"
    elif total_score >= 50:
        grade = "C"
    else:
        grade = "D"

    return {
        "score": total_score,
        "grade": grade,
        "profile": profile,
        "checks": checks,
    }


# ── 기존 6개 검증 항목 ───────────────────────────────────────


def _check_title(title: str, keyword: str) -> dict:
    """제목 검증: 길이(25자), 키워드 위치(시작부분)."""
    score = 0
    suggestions = []

    title_len = len(title)
    cfg = NAVER_SEO_CONFIG["title"]

    if title_len <= cfg["max_length"]:
        score += 40
    elif title_len <= 35:
        score += 20
        suggestions.append(f"제목을 {cfg['max_length']}자 이내로 줄이세요 (현재 {title_len}자)")
    else:
        suggestions.append(f"제목이 너무 깁니다 ({title_len}자). {cfg['max_length']}자 이내 권장")

    if keyword and title.startswith(keyword):
        score += 40
    elif keyword and keyword in title[:len(title) // 2 + 1]:
        score += 20
        suggestions.append("키워드를 제목 맨 앞에 배치하면 더 좋습니다")
    elif keyword and keyword in title:
        score += 10
        suggestions.append("키워드를 제목 시작 부분으로 이동하세요")
    else:
        suggestions.append(f"제목에 키워드 '{keyword}'를 포함하세요")

    if re.search(r"\d", title):
        score += 10
    if title.count("!") >= 3 or title.count("~") >= 3:
        score = max(0, score - 10)
        suggestions.append("특수문자/느낌표 사용을 줄이세요")

    score = min(100, score)

    return {
        "pass": score >= 70,
        "score": score,
        "message": f"제목 {title_len}자" + (f", 키워드 '{keyword}' 포함" if keyword in title else ""),
        "suggestions": suggestions,
    }


def _check_body_length(html: str) -> dict:
    """본문 길이 검증."""
    text = _strip_html(html)
    char_count = len(text.replace(" ", "").replace("\n", ""))
    cfg = NAVER_SEO_CONFIG["body"]

    suggestions = []

    if cfg["optimal_min"] <= char_count <= cfg["optimal_max"]:
        score = 100
    elif cfg["optimal_min"] - 500 <= char_count < cfg["optimal_min"]:
        score = 80
        suggestions.append(f"본문을 {cfg['optimal_min']}자 이상으로 늘리면 좋습니다")
    elif cfg["optimal_max"] < char_count <= cfg["optimal_max"] + 500:
        score = 80
        suggestions.append(f"본문이 약간 깁니다. {cfg['optimal_max']}자 이내가 최적입니다")
    elif cfg["min_chars"] <= char_count < cfg["optimal_min"] - 500:
        score = 60
        suggestions.append(f"본문이 부족합니다 ({char_count}자). {cfg['optimal_min']}~{cfg['optimal_max']}자 권장")
    elif char_count < cfg["min_chars"]:
        score = 30
        suggestions.append(f"본문이 매우 부족합니다 ({char_count}자). 최소 {cfg['min_chars']}자 필요")
    else:
        score = 40
        suggestions.append(f"본문이 너무 깁니다 ({char_count}자). {cfg['max_chars']}자 이내 권장")

    return {
        "pass": score >= 70,
        "score": score,
        "message": f"본문 {char_count}자 (권장 {cfg['optimal_min']}~{cfg['optimal_max']}자)",
        "suggestions": suggestions,
    }


def _check_keyword_density(html: str, keyword: str) -> dict:
    """키워드 밀도 분석: 밀도 %, 초반/말미 배치 확인."""
    text = _strip_html(html)
    text_no_space = text.replace(" ", "").replace("\n", "")
    total_chars = len(text_no_space)

    if not keyword or total_chars == 0:
        return {
            "pass": False,
            "score": 0,
            "message": "키워드 또는 본문이 없습니다",
            "suggestions": ["키워드를 입력하세요"],
        }

    pattern = re.escape(keyword)
    matches = re.findall(pattern, text, re.IGNORECASE)
    count = len(matches)

    keyword_chars = len(keyword.replace(" ", ""))
    density = (keyword_chars * count / total_chars) * 100 if total_chars > 0 else 0

    cfg = NAVER_SEO_CONFIG["keyword"]
    suggestions = []

    if cfg["density_min"] <= density <= cfg["density_max"]:
        score = 70
    elif 0.5 <= density < cfg["density_min"]:
        score = 50
        suggestions.append(f"키워드를 1~2회 더 추가하세요 (현재 {count}회, 밀도 {density:.1f}%)")
    elif cfg["density_max"] < density <= 3.0:
        score = 50
        suggestions.append(f"키워드가 약간 많습니다 (현재 {count}회, 밀도 {density:.1f}%). 자연스럽게 줄이세요")
    elif density < 0.5:
        score = 30
        suggestions.append(f"키워드가 너무 적습니다 (현재 {count}회). 5~6회 권장")
    else:
        score = 20
        suggestions.append(f"키워드 과다 사용 ({count}회, 밀도 {density:.1f}%). 네이버 저품질 위험")

    first_200 = text[:200]
    if keyword.lower() in first_200.lower():
        score += 15
    else:
        suggestions.append("초반 200자에 키워드를 포함하세요 (네이버 알고리즘 최우선 분석 구간)")

    last_200 = text[-200:] if len(text) >= 200 else text
    if keyword.lower() in last_200.lower():
        score += 15
    else:
        suggestions.append("결론부(마지막 200자)에 키워드를 재언급하세요")

    score = min(100, score)

    return {
        "pass": score >= 70,
        "score": score,
        "message": f"키워드 '{keyword}' {count}회 출현, 밀도 {density:.1f}%",
        "suggestions": suggestions,
    }


def _check_heading_structure(html: str, keyword: str) -> dict:
    """HTML 헤딩 구조 검증."""
    soup = BeautifulSoup(html, "html.parser")
    headings = soup.find_all(["h1", "h2", "h3", "h4"])

    h1_tags = [h for h in headings if h.name == "h1"]
    h2_tags = [h for h in headings if h.name == "h2"]
    h3_tags = [h for h in headings if h.name == "h3"]

    text = _strip_html(html)
    char_count = len(text.replace(" ", "").replace("\n", ""))

    suggestions = []
    score = 0

    if len(h1_tags) == 0:
        score += 20
    elif len(h1_tags) == 1:
        score += 15
        suggestions.append("본문에서 H1 대신 H2를 사용하세요 (H1은 제목용)")
    else:
        suggestions.append(f"H1 태그가 {len(h1_tags)}개입니다. 본문에서는 H2를 사용하세요")

    if char_count > 0:
        expected_min = max(2, int(char_count / 1000 * NAVER_SEO_CONFIG["headings"]["h2_per_1000_chars_min"]))
        expected_max = max(3, int(char_count / 1000 * NAVER_SEO_CONFIG["headings"]["h2_per_1000_chars_max"]))
        h2_count = len(h2_tags)

        if expected_min <= h2_count <= expected_max:
            score += 30
        elif h2_count > 0 and h2_count < expected_min:
            score += 15
            suggestions.append(f"H2 소제목이 부족합니다 ({h2_count}개). {expected_min}~{expected_max}개 권장")
        elif h2_count > expected_max:
            score += 20
            suggestions.append(f"H2 소제목이 많습니다 ({h2_count}개). {expected_min}~{expected_max}개 권장")
        else:
            suggestions.append(f"H2 소제목이 없습니다. {expected_min}~{expected_max}개 추가하세요")
    else:
        suggestions.append("본문이 비어있습니다")

    hierarchy_valid = True
    prev_level = 0
    for h in headings:
        level = int(h.name[1])
        if prev_level > 0 and level > prev_level + 1:
            hierarchy_valid = False
            break
        prev_level = level

    if hierarchy_valid:
        score += 20
    else:
        suggestions.append("헤딩 계층 순서가 잘못되었습니다 (예: H2 다음에 바로 H4 사용 금지)")

    if keyword and h2_tags:
        keyword_in_h2 = sum(1 for h in h2_tags if keyword.lower() in h.get_text().lower())
        ratio = keyword_in_h2 / len(h2_tags)
        if ratio >= 0.3:
            score += 30
        elif ratio > 0:
            score += 15
            suggestions.append("H2 소제목에 키워드 변형을 더 포함하세요")
        else:
            suggestions.append("H2 소제목에 타겟 키워드를 자연스럽게 포함하세요")
    elif not h2_tags:
        pass

    score = min(100, score)

    return {
        "pass": score >= 70,
        "score": score,
        "message": f"H1 {len(h1_tags)}개, H2 {len(h2_tags)}개, H3 {len(h3_tags)}개",
        "suggestions": suggestions,
    }


def _check_images(html: str, image_count: int) -> dict:
    """이미지 SEO 검증."""
    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img")
    placeholder_count = len(re.findall(r"\[IMAGE_\d+\]", html))
    total_images = max(len(img_tags), placeholder_count, image_count)

    cfg = NAVER_SEO_CONFIG["images"]
    suggestions = []
    score = 0

    if total_images >= 6:
        score += 40
    elif total_images >= cfg["min_count"]:
        score += 25
        suggestions.append(f"이미지를 6장 이상 사용하면 더 좋습니다 (현재 {total_images}장)")
    elif total_images > 0:
        score += 10
        suggestions.append(f"이미지가 부족합니다 ({total_images}장). 최소 {cfg['min_count']}장 권장")
    else:
        suggestions.append("이미지가 없습니다. 최소 3장 이상 추가하세요")

    if img_tags:
        good_alt_count = 0
        for img in img_tags:
            alt = img.get("alt", "")
            if not alt or re.match(r"^image_?\d*$", alt, re.IGNORECASE):
                continue
            alt_len = len(alt)
            if cfg["alt_min_chars"] <= alt_len <= cfg["alt_max_chars"]:
                good_alt_count += 1

        if img_tags:
            alt_ratio = good_alt_count / len(img_tags)
            if alt_ratio >= 0.8:
                score += 40
            elif alt_ratio >= 0.5:
                score += 25
                suggestions.append("일부 이미지의 ALT 텍스트를 개선하세요 (20~50자 한국어 문장)")
            elif alt_ratio > 0:
                score += 10
                suggestions.append("대부분 이미지의 ALT 텍스트가 부족합니다")
            else:
                suggestions.append("이미지 ALT 텍스트를 키워드 포함 설명적 문장으로 작성하세요")
    elif total_images > 0:
        score += 20

    if placeholder_count >= 2:
        parts = re.split(r"\[IMAGE_\d+\]", html)
        text_parts = [_strip_html(p) for p in parts[1:-1]]
        if text_parts:
            avg_gap = sum(len(t.replace(" ", "")) for t in text_parts) / len(text_parts)
            if 200 <= avg_gap <= 600:
                score += 20
            else:
                suggestions.append("이미지를 300~500자 간격으로 분산 배치하세요")

    score = min(100, score)

    return {
        "pass": score >= 70,
        "score": score,
        "message": f"이미지 {total_images}장",
        "suggestions": suggestions,
    }


def _check_hashtags(tags: list[str], keyword: str) -> dict:
    """해시태그 검증."""
    tag_count = len(tags)
    cfg = NAVER_SEO_CONFIG["hashtags"]
    suggestions = []
    score = 0

    if cfg["optimal_min"] <= tag_count <= cfg["optimal_max"]:
        score += 50
    elif 3 <= tag_count < cfg["optimal_min"]:
        score += 30
        suggestions.append(f"해시태그를 {cfg['optimal_min']}~{cfg['optimal_max']}개로 늘리세요 (현재 {tag_count}개)")
    elif cfg["optimal_max"] < tag_count <= 15:
        score += 30
        suggestions.append(f"해시태그가 많습니다 (현재 {tag_count}개). {cfg['optimal_max']}개 이내 권장")
    elif tag_count <= 2:
        score += 10
        suggestions.append(f"해시태그가 너무 적습니다 (현재 {tag_count}개). {cfg['optimal_min']}개 이상 추가하세요")
    else:
        score += 20
        suggestions.append(f"해시태그가 과다합니다 ({tag_count}개)")

    if keyword:
        keyword_in_tags = any(keyword.lower() in tag.lower() for tag in tags)
        if keyword_in_tags:
            score += 30
        else:
            suggestions.append(f"해시태그에 핵심 키워드 '{keyword}'를 포함하세요")

    unique_tags = set(t.lower() for t in tags)
    if len(unique_tags) == tag_count:
        score += 20
    else:
        dup_count = tag_count - len(unique_tags)
        suggestions.append(f"중복 해시태그 {dup_count}개를 제거하세요")

    score = min(100, score)

    return {
        "pass": score >= 70,
        "score": score,
        "message": f"해시태그 {tag_count}개" + (f", 키워드 포함" if keyword and any(keyword.lower() in t.lower() for t in tags) else ""),
        "suggestions": suggestions,
    }


# ── 신규 4개 검증 항목 (D.I.A.+ 확장) ────────────────────────

# 가독성 분석 관련 상수
_COLLOQUIAL_ENDINGS = re.compile(
    r"(요|거든요|잖아요|네요|세요|겠죠|랍니다|에요|예요|구요|더라고요|던데요|던가요|을까요|나요|ㅋ|ㅎ)[.!?~]*$"
)
_SENTENCE_SPLIT = re.compile(r"[.!?。]+\s*")

# 경험 신호 관련 상수
_EXPERIENCE_MARKERS = [
    "직접", "체험", "경험", "사용해본", "사용해봤", "느꼈", "느낀", "방문",
    "실제로", "후기", "솔직히", "개인적으로", "써본", "써봤", "먹어본", "먹어봤",
    "가본", "가봤", "해본", "해봤", "다녀온", "다녀왔",
]
_PERSONAL_PRONOUNS = ["나는", "내가", "저는", "제가", "나의", "저의", "제"]
_EMOTION_WORDS = [
    "좋았", "좋은", "좋다", "맛있", "편하", "아쉽", "별로", "만족", "불만",
    "놀라", "감동", "실망", "기대", "추천", "행복", "즐거", "재미있",
    "맘에 들", "마음에 들", "인상적", "최고", "최악",
]

# AI 안전 관련 상수
_AI_STARTERS = [
    "먼저", "다음으로", "마지막으로", "또한", "그리고", "한편",
    "이번에는", "그 다음", "아울러",
]
_TEMPLATE_PHRASES = [
    "이 글을 통해", "결론적으로", "요약하면", "정리하면",
    "살펴보겠습니다", "알아보겠습니다", "소개해 드리겠습니다",
    "도움이 되셨으면", "참고하시기 바랍니다",
]


def _check_readability(html: str) -> dict:
    """가독성 분석: 문장 길이, 문단 길이, 구어체 비율."""
    text = _strip_html(html)
    if not text or len(text) < 50:
        return {
            "pass": False,
            "score": 0,
            "message": "본문이 너무 짧아 가독성 분석 불가",
            "suggestions": ["충분한 본문을 작성하세요"],
        }

    suggestions = []

    # 문장 분리
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip() and len(s.strip()) > 5]
    if not sentences:
        return {
            "pass": False,
            "score": 30,
            "message": "문장 구분이 어렵습니다",
            "suggestions": ["마침표(.)를 사용하여 문장을 구분하세요"],
        }

    # 1) 평균 문장 길이 (30~50자 최적)
    sentence_lengths = [len(s) for s in sentences]
    avg_sentence_len = statistics.mean(sentence_lengths)

    if 30 <= avg_sentence_len <= 50:
        sentence_score = 100
    elif 20 <= avg_sentence_len < 30:
        sentence_score = 70
    elif 50 < avg_sentence_len <= 70:
        sentence_score = 60
        suggestions.append(f"문장이 다소 깁니다 (평균 {avg_sentence_len:.0f}자). 30~50자가 최적")
    elif avg_sentence_len > 70:
        sentence_score = 30
        suggestions.append(f"문장이 너무 깁니다 (평균 {avg_sentence_len:.0f}자). 짧게 나눠 가독성을 높이세요")
    else:
        sentence_score = 50

    # 2) 문단 길이 (HTML <p> 태그 기반)
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    if paragraphs:
        para_lengths = [len(p) for p in paragraphs]
        avg_para_len = statistics.mean(para_lengths)
        if 100 <= avg_para_len <= 500:
            para_score = 100
        elif 50 <= avg_para_len < 100 or 500 < avg_para_len <= 700:
            para_score = 60
            if avg_para_len > 500:
                suggestions.append(f"문단이 길어 읽기 부담됩니다 (평균 {avg_para_len:.0f}자). 300~500자 권장")
        else:
            para_score = 30
            if avg_para_len > 700:
                suggestions.append("문단을 더 짧게 나누세요")
    else:
        para_score = 50

    # 3) 문장 길이 분산 (자연스러운 리듬)
    if len(sentence_lengths) >= 3:
        stdev = statistics.stdev(sentence_lengths)
        cv = stdev / avg_sentence_len if avg_sentence_len > 0 else 0
        if 0.3 <= cv <= 0.8:
            variance_score = 100
        elif 0.15 <= cv < 0.3:
            variance_score = 60
            suggestions.append("문장 길이가 너무 균일합니다. 길고 짧은 문장을 섞어보세요")
        elif cv < 0.15:
            variance_score = 30
            suggestions.append("문장 길이가 매우 균일합니다. 다양한 문장 길이로 리듬감을 주세요")
        else:
            variance_score = 70
    else:
        variance_score = 50

    # 4) 구어체 비율 (10~20% 최적)
    colloquial_count = sum(1 for s in sentences if _COLLOQUIAL_ENDINGS.search(s))
    colloquial_ratio = colloquial_count / len(sentences) * 100 if sentences else 0

    if 10 <= colloquial_ratio <= 30:
        colloquial_score = 100
    elif 5 <= colloquial_ratio < 10:
        colloquial_score = 70
    elif 30 < colloquial_ratio <= 50:
        colloquial_score = 70
    elif colloquial_ratio < 5:
        colloquial_score = 40
        suggestions.append(f"구어체 비율이 낮습니다 ({colloquial_ratio:.0f}%). 자연스러운 말투를 섞어보세요")
    else:
        colloquial_score = 50

    # 가중 점수
    score = round(
        sentence_score * 0.3 + para_score * 0.3 + variance_score * 0.2 + colloquial_score * 0.2
    )
    score = min(100, score)

    return {
        "pass": score >= 70,
        "score": score,
        "message": f"평균 문장 {avg_sentence_len:.0f}자, 구어체 {colloquial_ratio:.0f}%",
        "suggestions": suggestions,
        "details": {
            "avg_sentence_length": round(avg_sentence_len, 1),
            "sentence_count": len(sentences),
            "colloquial_ratio": round(colloquial_ratio, 1),
            "sentence_lengths": sentence_lengths,
        },
    }


def _check_experience_signals(html: str) -> dict:
    """경험 정보 감지: 경험 마커, 1인칭 대명사, 감정 표현."""
    text = _strip_html(html)
    if not text or len(text) < 50:
        return {
            "pass": False,
            "score": 0,
            "message": "본문이 너무 짧아 경험 신호 분석 불가",
            "suggestions": ["충분한 본문을 작성하세요"],
        }

    suggestions = []
    text_lower = text.lower()

    # 1) 경험 마커 탐지
    found_markers = []
    for marker in _EXPERIENCE_MARKERS:
        count = text_lower.count(marker)
        if count > 0:
            found_markers.extend([marker] * count)

    marker_count = len(found_markers)
    text_per_1000 = len(text) / 1000
    marker_density = marker_count / max(text_per_1000, 0.5)  # 1000자당 마커 수

    if marker_density >= 3:
        marker_score = 100
    elif marker_density >= 2:
        marker_score = 80
    elif marker_density >= 1:
        marker_score = 60
        suggestions.append("경험 표현을 더 추가하세요 (예: '직접 체험해본', '실제로 사용해봤')")
    elif marker_density > 0:
        marker_score = 40
        suggestions.append("경험 기반 표현이 부족합니다. 개인 체험담을 더 넣어주세요")
    else:
        marker_score = 10
        suggestions.append("경험 표현이 전혀 없습니다. '직접', '실제로' 등의 체험 표현을 추가하세요")

    # 2) 1인칭 대명사 비율
    pronoun_count = sum(text_lower.count(p) for p in _PERSONAL_PRONOUNS)
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip() and len(s.strip()) > 5]
    pronoun_ratio = pronoun_count / max(len(sentences), 1) * 100

    if 5 <= pronoun_ratio <= 20:
        pronoun_score = 100
    elif 2 <= pronoun_ratio < 5:
        pronoun_score = 70
    elif 20 < pronoun_ratio <= 35:
        pronoun_score = 70
    elif pronoun_ratio < 2:
        pronoun_score = 30
        suggestions.append("1인칭 표현('나는', '제가')이 부족합니다. 개인 시점을 더 넣어보세요")
    else:
        pronoun_score = 50

    # 3) 감정/감각 표현
    emotion_count = sum(text_lower.count(e) for e in _EMOTION_WORDS)
    emotion_density = emotion_count / max(text_per_1000, 0.5)

    if emotion_density >= 2:
        emotion_score = 100
    elif emotion_density >= 1:
        emotion_score = 70
    elif emotion_density > 0:
        emotion_score = 50
        suggestions.append("감정 표현을 더 추가하면 진정성이 높아집니다 (예: '좋았다', '아쉬웠다')")
    else:
        emotion_score = 20
        suggestions.append("감정/감각 표현이 없습니다. 느낌이나 평가를 자연스럽게 넣어보세요")

    score = round(marker_score * 0.50 + pronoun_score * 0.30 + emotion_score * 0.20)
    score = min(100, score)

    return {
        "pass": score >= 70,
        "score": score,
        "message": f"경험 마커 {marker_count}개, 1인칭 {pronoun_count}회",
        "suggestions": suggestions,
        "details": {
            "found_markers": list(set(found_markers)),
            "marker_count": marker_count,
            "pronoun_count": pronoun_count,
            "emotion_count": emotion_count,
        },
    }


def _check_information_depth(html: str) -> dict:
    """정보 충실성: 리스트, 수치 데이터, 비교 표현, 구체성."""
    soup = BeautifulSoup(html, "html.parser")
    text = _strip_html(html)

    if not text or len(text) < 50:
        return {
            "pass": False,
            "score": 0,
            "message": "본문이 너무 짧아 정보 충실성 분석 불가",
            "suggestions": ["충분한 본문을 작성하세요"],
        }

    suggestions = []

    # 1) 구조화된 리스트 수
    list_tags = soup.find_all(["ul", "ol"])
    list_count = len(list_tags)

    if list_count >= 3:
        list_score = 100
    elif list_count >= 2:
        list_score = 70
    elif list_count >= 1:
        list_score = 50
        suggestions.append("리스트/목록 구조를 더 활용하면 정보 전달력이 높아집니다")
    else:
        list_score = 20
        suggestions.append("구조화된 리스트(<ul>, <ol>)를 추가하여 핵심 정보를 정리하세요")

    # 2) 수치/통계 데이터
    data_patterns = re.findall(r"\d+[,.]?\d*\s*[%원명개건회장시간분초km]", text)
    data_count = len(data_patterns)

    if data_count >= 5:
        data_score = 100
    elif data_count >= 3:
        data_score = 80
    elif data_count >= 1:
        data_score = 50
        suggestions.append("구체적 수치를 더 포함하면 신뢰도가 높아집니다 (예: 가격, 시간, 거리)")
    else:
        data_score = 20
        suggestions.append("구체적 수치/통계 데이터를 추가하세요 (예: '약 30분 소요', '5,000원')")

    # 3) 비교/대조 표현
    comparison_words = ["반면", "한편", "대비", "차이점", "비교", "대신", "장단점", "장점", "단점", "vs"]
    comparison_count = sum(text.lower().count(w) for w in comparison_words)

    if comparison_count >= 3:
        comparison_score = 100
    elif comparison_count >= 2:
        comparison_score = 70
    elif comparison_count >= 1:
        comparison_score = 50
    else:
        comparison_score = 30
        suggestions.append("비교/대조 표현을 추가하면 정보 깊이가 향상됩니다 (예: '장단점', '반면')")

    # 4) 구체적 고유명사 (간단한 휴리스틱: 괄호 안 설명, 큰따옴표 등)
    specific_patterns = re.findall(r"['\"][\w\s]{2,20}['\"]|「[\w\s]{2,20}」", text)
    has_tables = len(soup.find_all("table")) > 0
    specificity_bonus = min(len(specific_patterns) * 10, 40) + (30 if has_tables else 0)
    specificity_score = min(100, 30 + specificity_bonus)

    score = round(list_score * 0.30 + data_score * 0.30 + comparison_score * 0.20 + specificity_score * 0.20)
    score = min(100, score)

    return {
        "pass": score >= 70,
        "score": score,
        "message": f"리스트 {list_count}개, 수치 {data_count}개, 비교 {comparison_count}회",
        "suggestions": suggestions,
        "details": {
            "list_count": list_count,
            "data_count": data_count,
            "comparison_count": comparison_count,
        },
    }


def _check_ai_safety(html: str) -> dict:
    """AI 콘텐츠 탐지 위험도 분석."""
    text = _strip_html(html)
    if not text or len(text) < 50:
        return {
            "pass": True,
            "score": 100,
            "message": "본문이 짧아 AI 탐지 분석 해당 없음",
            "suggestions": [],
        }

    suggestions = []
    penalty = 0

    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip() and len(s.strip()) > 5]
    if not sentences:
        return {"pass": True, "score": 80, "message": "문장 분석 불가", "suggestions": []}

    # 1) 반복 문장 시작 패턴
    starter_counts: dict[str, int] = {}
    for s in sentences:
        for starter in _AI_STARTERS:
            if s.startswith(starter):
                starter_counts[starter] = starter_counts.get(starter, 0) + 1
                break

    total_ai_starts = sum(starter_counts.values())
    ai_start_ratio = total_ai_starts / len(sentences) * 100 if sentences else 0

    if ai_start_ratio > 25:
        penalty += 30
        top_starters = sorted(starter_counts.items(), key=lambda x: -x[1])[:3]
        starter_list = ", ".join(f"'{s[0]}'({s[1]}회)" for s in top_starters)
        suggestions.append(f"반복 문장 시작 패턴 탐지: {starter_list}. 다양한 시작 표현을 사용하세요")
    elif ai_start_ratio > 15:
        penalty += 15
        suggestions.append("문장 시작이 반복적입니다. 시작 표현을 다양화하세요")

    # 2) 템플릿 문구 빈도
    template_count = 0
    found_templates = []
    for phrase in _TEMPLATE_PHRASES:
        count = text.lower().count(phrase)
        if count > 0:
            template_count += count
            found_templates.append(phrase)

    if template_count >= 4:
        penalty += 25
        suggestions.append(f"전형적인 AI 문구가 많습니다: {', '.join(found_templates[:3])}. 자연스러운 표현으로 바꾸세요")
    elif template_count >= 2:
        penalty += 10
        suggestions.append("일부 템플릿성 문구를 자연스러운 표현으로 바꿔보세요")

    # 3) 문단 길이 균일성
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    if len(paragraphs) >= 3:
        para_lengths = [len(p) for p in paragraphs]
        avg_para = statistics.mean(para_lengths)
        if avg_para > 0:
            para_cv = statistics.stdev(para_lengths) / avg_para
            if para_cv < 0.15:
                penalty += 20
                suggestions.append("문단 길이가 매우 균일합니다. 자연스러운 길이 변화를 주세요")
            elif para_cv < 0.25:
                penalty += 10

    # 4) 구어체 부족 (너무 격식체면 AI 의심)
    colloquial_count = sum(1 for s in sentences if _COLLOQUIAL_ENDINGS.search(s))
    colloquial_ratio = colloquial_count / len(sentences) * 100 if sentences else 0

    if colloquial_ratio < 3:
        penalty += 15
        suggestions.append("구어체가 거의 없습니다. 자연스러운 말투를 섞어 AI 탐지를 낮추세요")
    elif colloquial_ratio < 8:
        penalty += 5

    score = max(0, 100 - penalty)

    # AI 위험 등급 메시지
    if score < 40:
        risk_level = "높음"
    elif score < 60:
        risk_level = "보통"
    elif score < 80:
        risk_level = "낮음"
    else:
        risk_level = "안전"

    return {
        "pass": score >= 60,
        "score": score,
        "message": f"AI 탐지 위험: {risk_level} (반복패턴 {ai_start_ratio:.0f}%, 구어체 {colloquial_ratio:.0f}%)",
        "suggestions": suggestions,
        "details": {
            "ai_start_ratio": round(ai_start_ratio, 1),
            "template_count": template_count,
            "found_templates": found_templates,
            "colloquial_ratio": round(colloquial_ratio, 1),
            "risk_level": risk_level,
        },
    }


# ── 유틸리티 ──────────────────────────────────────────────────


def _strip_html(html: str) -> str:
    """HTML 태그 제거 → 순수 텍스트."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)
