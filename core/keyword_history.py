"""키워드 분석 이력 관리."""

import json
from datetime import datetime
from pathlib import Path

HISTORY_DIR = Path(__file__).parent.parent / "data" / "keywords"


class KeywordHistoryManager:
    """키워드 분석 이력 저장/조회."""

    def __init__(self) -> None:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    def save_analysis(
        self,
        seed: str,
        results: list[dict],
        selected: str | None = None,
    ) -> Path:
        """키워드 분석 결과 저장."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_seed = seed.replace(" ", "_")[:20]
        filepath = HISTORY_DIR / f"{ts}_{safe_seed}.json"
        data = {
            "timestamp": datetime.now().isoformat(),
            "seed": seed,
            "selected_keyword": selected,
            "results": results,
            "used_for_post": False,
        }
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return filepath

    def mark_used(self, seed: str, keyword: str) -> None:
        """가장 최근 분석에서 선택된 키워드를 '사용됨'으로 표시."""
        for hf in sorted(HISTORY_DIR.glob("*.json"), reverse=True):
            try:
                data = json.loads(hf.read_text(encoding="utf-8"))
                if data.get("seed") == seed:
                    data["selected_keyword"] = keyword
                    data["used_for_post"] = True
                    hf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    return
            except Exception:
                continue

    def load_all(self) -> list[dict]:
        """모든 키워드 분석 이력 로드 (최신순)."""
        items = []
        for hf in sorted(HISTORY_DIR.glob("*.json"), reverse=True):
            try:
                data = json.loads(hf.read_text(encoding="utf-8"))
                data["_filename"] = hf.name
                items.append(data)
            except Exception:
                continue
        return items

    def get_keyword_frequency(self) -> dict[str, int]:
        """글 작성에 사용된 키워드 빈도 집계."""
        freq: dict[str, int] = {}
        for item in self.load_all():
            kw = item.get("selected_keyword")
            if kw and item.get("used_for_post"):
                freq[kw] = freq.get(kw, 0) + 1
        return freq
