"""블루오션 키워드 추천 엔진."""

import re
import time

import requests
from bs4 import BeautifulSoup

from core.llm_client import LLMClient


class KeywordEngine:
    """네이버 자동완성 + LLM 확장 + 경쟁도 조회."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def expand_keywords(self, seed: str) -> list[str]:
        """네이버 자동완성 + LLM으로 키워드 확장."""
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
        except Exception:
            pass

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
        except Exception:
            pass

        # 중복 제거 후 최대 15개
        seen = set()
        unique = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)
        return unique[:15]

    def get_blog_count(self, keyword: str) -> int:
        """네이버 블로그 검색 결과 수 조회."""
        url = "https://search.naver.com/search.naver"
        params = {"where": "blog", "query": keyword}
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")

            # selector fallback (네이버 DOM 변경 대응)
            selectors = [".title_num", ".title_desc", ".sub_text"]
            text = None
            for sel in selectors:
                elem = soup.select_one(sel)
                if elem:
                    text = elem.text
                    break

            if text:
                text = text.replace(",", "")
                match = re.search(r"(\d+)건", text)
                if match:
                    return int(match.group(1))
        except Exception:
            pass

        return 0

    def analyze(self, seed: str) -> list[dict]:
        """키워드 확장 + 경쟁도 조회 → 추천 리스트."""
        keywords = self.expand_keywords(seed)

        results = []
        for kw in keywords:
            blog_count = self.get_blog_count(kw)
            results.append({
                "keyword": kw,
                "blog_count": blog_count,
                "competition": self._competition_level(blog_count),
            })
            time.sleep(0.5)  # rate limiting

        results.sort(key=lambda x: x["blog_count"])
        return results

    def _competition_level(self, blog_count: int) -> str:
        if blog_count < 1000:
            return "낮음"
        elif blog_count < 5000:
            return "중간"
        else:
            return "높음"
