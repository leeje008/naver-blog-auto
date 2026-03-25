"""블루오션 키워드 추천 엔진."""

import math
import os
import re

import requests
from bs4 import BeautifulSoup

from core.http_client import ThrottledSession
from core.llm_client import LLMClient
from core.logger import get_logger

logger = get_logger(__name__)

NAVER_SEARCH_API_URL = "https://openapi.naver.com/v1/search/blog.json"


def validate_naver_credentials(client_id: str, client_secret: str) -> tuple[bool, str]:
    """네이버 검색 API 키 유효성 검증.

    Returns:
        (success: bool, message: str)
    """
    if not client_id or not client_secret:
        return False, "Client ID 또는 Client Secret이 비어있습니다."
    try:
        resp = requests.get(
            NAVER_SEARCH_API_URL,
            params={"query": "테스트", "display": 1},
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            return True, "연결 성공! API 키가 유효합니다."
        elif resp.status_code in (401, 403):
            return False, "인증 실패: API 키를 확인하세요."
        else:
            return False, f"연결 실패: HTTP {resp.status_code}"
    except requests.RequestException as e:
        return False, f"네트워크 오류: {e}"


class KeywordEngine:
    """네이버 자동완성 + LLM 확장 + 경쟁도 조회."""

    def __init__(
        self,
        llm_client: LLMClient,
        naver_client_id: str = "",
        naver_client_secret: str = "",
    ):
        self.llm_client = llm_client
        self._session = ThrottledSession(min_interval=0.5)
        self._naver_client_id = naver_client_id or os.getenv("NAVER_CLIENT_ID", "")
        self._naver_client_secret = naver_client_secret or os.getenv("NAVER_CLIENT_SECRET", "")

    def expand_keywords(self, seed: str) -> list[dict]:
        """네이버 자동완성 + LLM으로 키워드 확장.

        Returns:
            [{"keyword": str, "source": "autocomplete" | "llm"}]
        """
        logger.info("키워드 확장 시작: seed='%s'", seed)
        ac_keywords: list[str] = []
        llm_keywords: list[str] = []

        # 1) 네이버 자동완성
        try:
            ac_url = "https://ac.search.naver.com/nx/ac"
            params = {"q": seed, "con": "1", "frm": "nv", "ans": "2"}
            resp = requests.get(ac_url, params=params, timeout=5)
            if resp.ok:
                data = resp.json()
                for item in data.get("items", [[]])[0]:
                    ac_keywords.append(item[0])
                logger.debug("자동완성 결과: %d개", len(ac_keywords))
        except Exception as e:
            logger.warning("자동완성 API 실패: %s", e)

        # 2) LLM 확장
        try:
            llm_result = self.llm_client.generate(
                system_prompt="네이버 블로그 키워드 전문가입니다.",
                user_prompt=(
                    f"'{seed}'에 대한 롱테일 검색 키워드 15개를 생성해 주세요. "
                    "키워드만 줄바꿈으로 출력해 주세요."
                ),
            )
            for line in llm_result.strip().split("\n"):
                line = line.strip().lstrip("0123456789.-) ")
                if line:
                    llm_keywords.append(line)
        except Exception as e:
            logger.warning("LLM 키워드 확장 실패: %s", e)

        # 중복 제거 + 출처 태깅 (자동완성 우선)
        seen: set[str] = set()
        results: list[dict] = []

        for kw in ac_keywords:
            if kw not in seen:
                seen.add(kw)
                results.append({"keyword": kw, "source": "autocomplete"})

        for kw in llm_keywords:
            if kw not in seen:
                seen.add(kw)
                results.append({"keyword": kw, "source": "llm"})

        logger.info("키워드 확장 완료: %d개 (자동완성 %d, LLM %d)",
                     len(results[:20]), len(ac_keywords), len(llm_keywords))
        return results[:20]

    def get_blog_count(self, keyword: str) -> int | None:
        """네이버 공식 검색 API로 블로그 검색 결과 수 조회.

        Returns:
            검색 결과 수. API 키 미설정 또는 조회 실패 시 None 반환.
        """
        if not self._naver_client_id or not self._naver_client_secret:
            logger.warning("네이버 검색 API 키가 설정되지 않았습니다. 설정 페이지에서 입력하세요.")
            return None

        headers = {
            "X-Naver-Client-Id": self._naver_client_id,
            "X-Naver-Client-Secret": self._naver_client_secret,
        }
        params = {"query": keyword, "display": 1}

        try:
            resp = requests.get(
                NAVER_SEARCH_API_URL,
                headers=headers,
                params=params,
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            total = data.get("total", 0)
            logger.debug("블로그 검색 수 조회 keyword='%s': %d건", keyword, total)
            return total
        except Exception as e:
            logger.warning("블로그 검색 수 조회 실패 keyword='%s': %s", keyword, e)
            return None

    def analyze(self, seed: str) -> list[dict]:
        """키워드 확장 + 경쟁도 조회 + 블루오션 점수 → 추천 리스트."""
        logger.info("키워드 분석 시작: seed='%s'", seed)
        keyword_items = self.expand_keywords(seed)

        # 시드 키워드 블로그 수 조회 (상대 경쟁도 기준선)
        seed_blog_count = self.get_blog_count(seed)
        logger.info("시드 '%s' 블로그 수: %s건", seed, seed_blog_count)

        results = []
        for item in keyword_items:
            kw = item["keyword"]
            source = item["source"]
            blog_count = self.get_blog_count(kw)

            blue_ocean_score = self._calc_blue_ocean_score(
                keyword=kw,
                source=source,
                blog_count=blog_count,
                seed=seed,
                seed_blog_count=seed_blog_count,
            )

            # 시드 대비 비율 계산
            ratio = None
            if blog_count is not None and seed_blog_count and seed_blog_count > 0:
                ratio = blog_count / seed_blog_count

            results.append({
                "keyword": kw,
                "source": source,
                "blog_count": blog_count if blog_count is not None else 0,
                "blog_count_available": blog_count is not None,
                "competition": self._relative_competition(ratio),
                "seed_ratio": ratio,
                "blue_ocean_score": blue_ocean_score,
            })

        results.sort(key=lambda x: x["blue_ocean_score"], reverse=True)
        logger.info("키워드 분석 완료: %d개 키워드", len(results))
        return results

    def _calc_blue_ocean_score(
        self,
        keyword: str,
        source: str,
        blog_count: int | None,
        seed: str,
        seed_blog_count: int | None,
    ) -> int:
        """블루오션 점수 계산 (0~100).

        시드 키워드 대비 상대적 경쟁도를 기반으로 점수 산출.

        구성:
        - 출처 점수 (30): 자동완성 = 실제 검색 수요 증거
        - 상대 경쟁도 점수 (40): 시드 대비 블로그 수 비율 (로그 스케일)
        - 구체성 점수 (30): 롱테일 키워드일수록 틈새 가능성
        """
        score = 0

        # 1) 출처 점수 (max 30)
        if source == "autocomplete":
            score += 30
        else:
            score += 10

        # 2) 상대 경쟁도 점수 (max 40) — 시드 대비 비율 기반
        if blog_count is None or seed_blog_count is None or seed_blog_count == 0:
            score += 20  # 데이터 없음 = 중립
        else:
            # 로그 스케일 차이: 클수록 시드보다 경쟁이 적음
            log_diff = math.log10(max(seed_blog_count, 1)) - math.log10(max(blog_count, 1))
            # log_diff 범위: 보통 -1 ~ 4+ (10배 ~ 10000배 차이)
            ratio = blog_count / seed_blog_count

            if ratio < 0.01:       # 시드 대비 1% 미만
                score += 40
            elif ratio < 0.05:     # 1~5%
                score += 35
            elif ratio < 0.15:     # 5~15%
                score += 28
            elif ratio < 0.30:     # 15~30%
                score += 18
            elif ratio < 0.60:     # 30~60%
                score += 10
            else:                  # 60%+ (시드와 비슷한 경쟁)
                score += 3

        # 3) 구체성 점수 (max 30) — 시드 대비 단어 수
        seed_words = len(seed.split())
        kw_words = len(keyword.split())
        extra_words = kw_words - seed_words

        if extra_words >= 3:
            score += 30
        elif extra_words == 2:
            score += 25
        elif extra_words == 1:
            score += 15
        else:
            score += 5

        return min(100, score)

    @staticmethod
    def _relative_competition(ratio: float | None) -> str:
        """시드 대비 비율로 상대적 경쟁도 판단."""
        if ratio is None:
            return "알수없음"
        if ratio < 0.05:
            return "매우 낮음"
        elif ratio < 0.15:
            return "낮음"
        elif ratio < 0.30:
            return "중간"
        elif ratio < 0.60:
            return "높음"
        else:
            return "매우 높음"

    def analyze_top_posts(self, keyword: str) -> dict:
        """상위 블로그 글 5개 크롤링 → 글 길이/이미지 수 분석."""
        url = "https://search.naver.com/search.naver"
        params = {"where": "blog", "query": keyword}

        try:
            resp = self._session.get(url, params=params)
            soup = BeautifulSoup(resp.text, "html.parser")

            # 상위 글 제목/설명 추출
            titles = soup.select(".title_link, .api_txt_lines.total_tit")[:5]
            descs = soup.select(".dsc_txt, .api_txt_lines.dsc_txt")[:5]

            avg_desc_len = 0
            if descs:
                lengths = [len(d.get_text(strip=True)) for d in descs]
                avg_desc_len = sum(lengths) // len(lengths) if lengths else 0

            post_count = len(titles)

            # 경쟁 강도 판단
            if avg_desc_len > 200 and post_count >= 5:
                quality_level = "높음"
            elif avg_desc_len > 100:
                quality_level = "중간"
            else:
                quality_level = "낮음"

            return {
                "top_post_count": post_count,
                "avg_desc_length": avg_desc_len,
                "quality_level": quality_level,
            }
        except Exception as e:
            logger.debug("상위 글 분석 실패 keyword='%s': %s", keyword, e)
            return {"top_post_count": 0, "avg_desc_length": 0, "quality_level": "알수없음"}

