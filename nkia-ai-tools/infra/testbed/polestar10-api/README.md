# polestar10-api

polestar10 웹 조작을 HTTP 직호출로 자동화하기 위한 라이브러리 + 탐색 자료.

**Linear**: [NKIAAI-539](https://linear.app/nkia/issue/NKIAAI-539)

## 목적

테스트베드 자동화(NKIAAI-542 오케스트레이터)가 polestar10 웹 UI를 거치지 않고
서비스 등록 · 담당자 권한 · NMS/DPM 등록 · 알람 정책 설정을 수행할 수 있도록
다음을 제공한다.

1. `har-captures/` — Playwright 로 녹화한 주요 조작 HAR 파일 (AC1)
2. `endpoints.md` — HAR 분석으로 추출한 URL/method/payload/CSRF 스펙 (AC2)
3. `src/polestar10_client/` — HTTP 직호출 함수 라이브러리 (AC3)
4. `fall_through` 훅 포인트 — API 실패 시 UI 가이드로 위임 (AC4)

## 폴더 구조

```
polestar10-api/
├── README.md                 # 이 문서
├── endpoints.md              # 엔드포인트 스펙 (AC2 결과물)
├── pyproject.toml            # 의존성 선언 (playwright, pytest, httpx)
├── har-captures/             # AC1 결과물
│   ├── 01-login.har
│   ├── 02-add-target.har
│   ├── 03-assign-owner.har
│   ├── 04-register-nms.har
│   ├── 05-add-alert-policy.har
│   └── MANIFEST.md
├── scripts/
│   ├── record_har.py         # HAR 녹화 공통 러너
│   ├── 01_login.py
│   ├── 02_add_target.py
│   ├── 03_assign_owner.py
│   ├── 04_register_nms.py
│   └── 05_add_alert_policy.py
├── src/polestar10_client/
│   ├── __init__.py
│   ├── client.py             # Polestar10Client
│   └── errors.py             # PolestarApiError, FallThroughRequired
└── tests/
    └── test_roundtrip.py     # login -> add -> list -> delete 통합 테스트
```

## 환경변수

| 이름 | 설명 | 기본값 |
|---|---|---|
| `POLESTAR10_BASE_URL` | polestar10 진입 URL | `https://192.168.230.104` |
| `POLESTAR10_USER` | 로그인 계정 | (필수) |
| `POLESTAR10_PASS` | 로그인 패스워드 | (필수) |
| `POLESTAR10_VERIFY_SSL` | SSL 인증서 검증 여부 | `false` (self-signed) |

## 실행 절차

```bash
# 1. 로컬 venv 준비
cd nkia-ai-tools/infra/testbed/polestar10-api
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m playwright install chromium

# 2. 자격증명 주입
export POLESTAR10_USER=<username>
export POLESTAR10_PASS=<password>

# 3. HAR 녹화 (AC1)
for s in scripts/0*.py; do .venv/bin/python "$s"; done

# 4. 통합 테스트 (AC3)
.venv/bin/pytest tests/ -v
```

## Usage (요약)

```python
from polestar10_client import Polestar10Client, FallThroughRequired

client = Polestar10Client.from_env()
client.login()

try:
    target = client.add_target({"name": "demo-host-1", "ip": "10.0.0.10"})
    print("added:", target["id"])
except FallThroughRequired as ft:
    # API 가 스펙 변경/차단됨. 오케스트레이터가 UI 가이드로 전환.
    print(f"fall through to UI: {ft.operation} - {ft.ui_hint}")
```

## Fallback 훅 포인트 (AC4)

클라이언트는 다음 상황에서 `FallThroughRequired` 를 raise 한다.

- HTTP 4xx/5xx 응답 중 명시적으로 비복구 가능(401/403 제외 — 재로그인)
- 응답 스키마가 `endpoints.md` 에 기술된 형태와 어긋남 (polestar10 업그레이드 시 자주 발생)
- 엔드포인트 자체가 셀렉터·DOM 의존 조작으로만 가능한 경우 (처음부터 raise)

Issue 6 (NKIAAI-542) 오케스트레이터는 이 예외를 잡아 사용자에게
`ui_hint`(예: "SMS 메뉴 > 네트워크 > NMS 등록 클릭") 를 출력한다.
