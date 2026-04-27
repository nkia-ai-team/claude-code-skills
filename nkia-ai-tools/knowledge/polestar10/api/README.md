# polestar10 Web API 지식 베이스

polestar10 내부 HTTP API 를 Bash + curl 로 호출하기 위한 지식 자산.

**Linear**: [NKIAAI-539](https://linear.app/nkia/issue/NKIAAI-539)

## 구조

```
knowledge/polestar10/api/
├── README.md           # 이 문서
├── endpoints.md        # 전체 엔드포인트 스펙 (AC1)
└── recipes/            # 조작별 bash + curl 레시피 (AC2/AC3)
    ├── login.md                # 확정 ✅
    ├── list-targets.md         # 확정 ✅ (weburl/list-filter, sms/hosts-filter, standby filters)
    ├── list-groups.md          # 확정 ✅ (시스템 그룹)
    ├── service-group-tag.md    # 확정 ✅ (서비스 그룹 = tag system)
    ├── add-target.md           # 확정 ✅ Web URL + 서버 (다른 agent 타입 TBD)
    ├── delete-target.md        # 확정 ✅ Web URL + 서버 (다른 타입 TBD)
    ├── assign-owner.md         # TBD ⏳
    ├── register-nms.md         # TBD ⏳
    ├── register-dpm.md         # TBD ⏳
    └── add-alert-policy.md     # TBD ⏳
```

## 사용 대상

- **Claude Code 스킬** (예: NKIAAI-542 오케스트레이터의 `testbed-polestar10-register`) 이 `Read` 툴로 recipe 파일을 읽고 `Bash` 툴로 그대로 실행
- **팀원이 수동으로** polestar10 API 를 호출하고 싶을 때 복사-붙여넣기

## 런타임 의존성

- `bash` (또는 `sh` 에서도 동작하도록 작성됨)
- `curl`
- `jq` — JSON 파싱
- `sha512sum` — 비밀번호 해싱 (coreutils 기본)

모두 Linux/Mac 기본 내장. Python·venv·pip 불필요.

## 공통 환경변수

모든 recipe 가 기대하는 환경변수:

| 이름 | 설명 | 기본값 / 예 |
|---|---|---|
| `POLESTAR10_BASE_URL` | polestar10 진입 URL | `https://192.168.230.104` |
| `POLESTAR10_USER` | 로그인 계정 | (필수) |
| `POLESTAR10_PASS` | 평문 비밀번호 | (필수) |
| `POLESTAR10_COOKIE_JAR` | 세션 쿠키 저장 경로 | `/tmp/polestar10.cookies` |
| `POLESTAR10_CURL_OPTS` | curl 공통 옵션 | `-sk` (self-signed 무시 + silent) |

`login.md` 를 먼저 실행하면 `$POLESTAR10_COOKIE_JAR` 에 accessToken/refreshToken JWT 가 심어짐. 이후 다른 recipe 는 `--cookie` 로 이 파일을 참조해서 인증된 상태로 호출.

## 탐색 도구 (마켓플레이스 외부)

본 지식은 일회성 탐색 도구(Python + Playwright)를 사용해 HAR 녹화 후 분석으로 확보됨. 탐색 도구는 **이 플러그인 밖** 개인 작업 영역 `/home/sjbang/dev/polestar10-api-explore/` 에 보관 (NKIAAI-539 재설계 결정).

polestar10 업그레이드 시 recipe 검증 방법:
1. `/home/sjbang/dev/polestar10-api-explore/.venv/bin/python scripts/01_login.py` 로 재녹화
2. HAR 에서 URL/payload 변동 확인
3. 변동된 recipe 파일 업데이트 + PR

## TBD 엔드포인트 확정 절차

write 조작의 실제 POST URL + payload 는 **크롬 DevTools** 로 확정:

1. 크롬에서 `https://192.168.230.104/login` 접속 후 로그인
2. `F12` → **Network** 탭, "Preserve log" 체크
3. UI 에서 해당 조작 수행 (예: 관리대상 추가 → 폼 제출 → 저장)
4. Network 패널에서 해당 `POST` 요청 선택 → Headers/Payload/Response 복사
5. 해당 `recipes/<op>.md` 의 TBD 섹션을 실제 curl 블록으로 교체
