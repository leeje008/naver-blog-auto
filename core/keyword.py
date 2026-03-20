"""블루오션 키워드 추천 엔진."""

import re
from functools import lru_cache

import requests
from bs4 import BeautifulSoup

from core.http_client import ThrottledSession
from core.llm_client import LLMClient
from core.logger import get_logger

logger = get_logger(__name__)


class KeywordEngine:
    """네이버 자동완성 + LLM 확장 + 경쟁도 조회."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self._session = ThrottledSession(min_interval=0.5)

    def expand_keywords(self, seed: str) -> list[str]:
        """네이버 자동완성 + LLM으로 키워드 확장."""
        logger.info("키워드 확장 시작: seed='%s'", seed)
        keywords = []

        # 1) 네이버 자동완성
        try:
            ac_url = "https://ac.search.naver.com/nx/ac"
            params = {"q": seed, "con": "1", "frm": "nv", "ans": "2"}
            resp = requests.get(ac_url, params=params, timeout=5)
            if resp.ok:
                data = resp.json()
                for item in data.get("items", [[]])[0]:
                    keywords.append(item[0])
                logger.debug("자동완성 결과: %d개", len(keywords))
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
                    keywords.append(line)
        except Exception as e:
            logger.warning("LLM 키워드 확장 실패: %s", e)

        # 중복 제거 후 최대 15개
        seen = set()
        unique = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)
        logger.info("키워드 확장 완료: %d개", len(unique[:15]))
        return unique[:15]

    def get_blog_count(self, keyword: str) -> int | None:
        """네이버 블로그 검색 결과 수 조회.

        Returns:
            검색 결과 수. 조회 실패 시 None 반환 (0과 구분).
        """
        url = "https://search.naver.com/search.naver"
        params = {"where": "blog", "query": keyword}

        try:
            resp = self._session.get(url, params=params)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # selector fallback (네이버 DOM 변경 대응)
            selectors = [
                ".title_num",
                ".title_desc",
                ".sub_text",
                ".result_num",
                "span.num",
            ]
            text = None
            for sel in selectors:
                elem = soup.select_one(sel)
                if elem:
                    text = elem.text
                    break

            if text:
                text = text.replace(",", "")
                match = re.search(r"([\d,]+)\s*건", text)
                if match:
                    return int(match.group(1).replace(",", ""))

            # 모든 셀렉터 실패 — 숫자 패턴 직접 탐색
            all_text = soup.get_text()
            match = re.search(r"([\d,]+)\s*건", all_text)
            if match:
                count = int(match.group(1).replace(",", ""))
                if count > 0:
                    logger.debug("fallback 패턴으로 블로그 수 추출: %d", count)
                    return count

            logger.warning(
                "블로그 검색 수 셀렉터 매칭 실패 keyword='%s' — DOM 구조 변경 가능성",
                keyword,
            )
            return None
        except Exception as e:
            logger.warning("블로그 검색 수 조회 실패 keyword='%s': %s", keyword, e)
            return None

    def analyze(self, seed: str) -> list[dict]:
        """키워드 확장 + 경쟁도 조회 → 추천 리스트."""
        logger.info("키워드 분석 시작: seed='%s'", seed)
        keywords = self.expand_keywords(seed)

        results = []
        for kw in keywords:
            blog_count = self.get_blog_count(kw)
            top_quality = self.analyze_top_posts(kw)
            results.append({
                "keyword": kw,
                "blog_count": blog_count if blog_count is not None else 0,
                "blog_count_available": blog_count is not None,
                "competition": self._competition_level(blog_count),
                "top_post_quality": top_quality,
            })

        results.sort(key=lambda x: x["blog_count"])
        logger.info("키워드 분석 완료: %d개 키워드", len(results))
        return results

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

    def _competition_level(self, blog_count: int | None) -> str:
        """경쟁도 등급 판단."""
        if blog_count is None:
            return "알수없음"
        if blog_count < 1000:
            return "낮음"
        elif blog_count < 5000:
            return "중간"
        else:
            return "높음"
