---
name: v0.3.0 개선 완료
description: 2026-03-21 10개 미진 사항 개선 — 의존성, 에러 핸들링, 크롤링 안정성, 테스트, 패키징 등
type: project
---

v0.2.0 → v0.3.0 개선 작업 완료 (2026-03-21).

완료된 항목:
1. pandas 의존성 pyproject.toml 추가
2. Ollama 연결 검증 + 모델 존재 확인 (OllamaConnectionError)
3. NaverPublisher 환경변수 사전 검증
4. load_references()에 lru_cache 적용 + save 시 캐시 무효화
5. 네이버 블로그 검색 수 크롤링 — None 반환 구분, 셀렉터 확장, fallback 패턴
6. 이미지 validate_image() 추가 — 포맷 검증, RGBA→RGB 변환
7. sys.path.insert 해킹 제거 → hatchling build-system으로 editable install
8. pytest 34개 테스트 (generator, keyword, image_utils, seo_validator, publisher)
9. README.md 작성
10. ThrottledSession (core/http_client.py) — 공통 rate limiter

**Why:** v0.2.0은 기능은 완성이었으나 운영 안정성과 DX가 부족했음.
**How to apply:** 향후 새 모듈 추가 시 테스트 + ThrottledSession 사용 패턴 따를 것.
