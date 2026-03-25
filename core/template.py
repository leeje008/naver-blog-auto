"""블로그 글 템플릿 관리 (CRUD)."""

import json
from datetime import datetime
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent.parent / "data" / "templates"


class TemplateManager:
    """블로그 글 템플릿 저장/조회/삭제."""

    def __init__(self) -> None:
        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

    def save_template(self, name: str, template_data: dict) -> None:
        """템플릿 저장."""
        safe_name = name.replace(" ", "_").replace("/", "_")[:30]
        filepath = TEMPLATE_DIR / f"{safe_name}.json"
        template_data["name"] = name
        template_data["created_at"] = datetime.now().isoformat()
        filepath.write_text(
            json.dumps(template_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_template(self, name: str) -> dict | None:
        """템플릿 로드."""
        safe_name = name.replace(" ", "_").replace("/", "_")[:30]
        filepath = TEMPLATE_DIR / f"{safe_name}.json"
        if not filepath.exists():
            return None
        try:
            return json.loads(filepath.read_text(encoding="utf-8"))
        except Exception:
            return None

    def list_templates(self) -> list[str]:
        """템플릿 이름 목록."""
        names = []
        for hf in sorted(TEMPLATE_DIR.glob("*.json")):
            try:
                data = json.loads(hf.read_text(encoding="utf-8"))
                names.append(data.get("name", hf.stem))
            except Exception:
                names.append(hf.stem)
        return names

    def delete_template(self, name: str) -> None:
        """템플릿 삭제."""
        safe_name = name.replace(" ", "_").replace("/", "_")[:30]
        filepath = TEMPLATE_DIR / f"{safe_name}.json"
        filepath.unlink(missing_ok=True)
