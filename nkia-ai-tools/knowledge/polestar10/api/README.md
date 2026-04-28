# polestar10 Web API 지식 베이스

polestar10 내부 HTTP API 를 Bash + curl 로 호출하기 위한 지식 자산.

## 구조

```
knowledge/polestar10/api/
├── README.md           # 이 문서
├── endpoints.md        # 전체 엔드포인트 스펙 (AC1)
└── recipes/            # 조작별 bash + curl 레시피 (AC2/AC3)
    ├── login.md                # 확정
    ├── list-targets.md         # 확정 (weburl/list-filter, sms/hosts-filter, standby filters)
    ├── list-groups.md          # 확정 (시스템 그룹)
    ├── service-group-tag.md    # 확정 (서비스 그룹 = tag system)
    ├── add-target.md           # 확정 Web URL + 서버 (DB/APM/KCM/NMS TBD)
    ├── delete-target.md        # 확정 Web URL + 서버 (다른 타입 TBD)
    ├── slo.md                  # 확정 SLO 2-step (register/standby → register)
    ├── dpm-lifecycle.md        # 확정 DPM (DB) 풀 라이프사이클 + cascade rule
    ├── nms-lifecycle.md        # 확정 NMS (SNMP) 풀 라이프사이클
    ├── add-alert-policy.md     # 확정 공통 + 개별 알람 정의 + 메트릭 카탈로그
    ├── anomaly-policy.md       # 확정 이상감지 정책 조회 (CRUD TBD)
    └── assign-owner.md         # TBD (담당자 권한 부여)
```

agent-based register/unregister 풀 라이프사이클 (서버/APM/KCM) 은 [add-target.md](recipes/add-target.md), [delete-target.md](recipes/delete-target.md) 참조.

## 사용 대상

- **Claude Code 스킬** (예: `testbed-polestar10-register` 등 오케스트레이터 스킬) 이 `Read` 툴로 recipe 파일을 읽고 `Bash` 툴로 그대로 실행
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
| `POLESTAR10_BASE_URL` | polestar10 진입 URL | `https://192.168.230.104` (기본) |
| `POLESTAR10_USER` | 로그인 계정 | (필수) |
| `POLESTAR10_PASS` | 평문 비밀번호 | (필수) |
| `POLESTAR10_COOKIE_JAR` | 세션 쿠키 저장 경로 | `/tmp/polestar10.cookies` |
| `POLESTAR10_CURL_OPTS` | curl 공통 옵션 | `-sk` (self-signed 무시 + silent) |

`login.md` 를 먼저 실행하면 `$POLESTAR10_COOKIE_JAR` 에 accessToken/refreshToken JWT 가 심어짐. 이후 다른 recipe 는 `--cookie` 로 이 파일을 참조해서 인증된 상태로 호출.

## TBD 엔드포인트 확정 절차

write 조작의 실제 POST URL + payload 는 **크롬 DevTools** 로 확정:

1. 크롬에서 `https://192.168.230.104/login` (또는 사용자별 인스턴스 URL) 접속 후 로그인
2. `F12` → **Network** 탭, "Preserve log" 체크
3. UI 에서 해당 조작 수행 (예: 관리대상 추가 → 폼 제출 → 저장)
4. Network 패널에서 해당 `POST` 요청 선택 → Headers/Payload/Response 복사
5. 해당 `recipes/<op>.md` 의 TBD 섹션을 실제 curl 블록으로 교체

---

## 알려진 polestar10 인스턴스

오케스트레이터 스킬이 사용자에게 보여줄 dropdown 후보:

| 라벨 | URL | 비고 |
|---|---|---|
| NKIA dev (104) | `https://192.168.230.104` | 기본 개발/통합 환경 (polestar-app-itg-1) |
| (자유 입력) | (사용자 직접 입력) | 다른 고객사·스테이징 인스턴스 등 |

자유 입력 시 검증 권장: `POST $url/api/account/pre-login` 으로 더미 자격증명 한 번 시도해서 200 응답 (또는 `success:false + errorCode:"INVALID_CREDENTIALS"`) 받으면 폴리스타10 인스턴스 맞음. 404 / 연결 거부 / HTML 응답이면 잘못된 URL.

## 오케스트레이터 빌더용 핸드오프 노트

본 recipe 들을 소비할 오케스트레이터 스킬이 알아야 할 것:

### 1. 세션 시작 시 환경 셋업

오케스트레이터가 사용자에게 prompt → env 주입 → recipe 호출.

```
AI: Polestar10 Web 주소를 알려주세요.
    1) https://192.168.230.104 (NKIA dev)
    2) 자유 입력
사용자: 1 (또는 2 + URL)
AI: [URL 검증] → POST /api/account/pre-login 시도 → 200 응답 확인
    [세션 env 주입] → export POLESTAR10_BASE_URL=...
    [자격증명 prompt] → POLESTAR10_USER, POLESTAR10_PASS
    이후 recipe 호출 시 환경 자동 주입됨
```

env 보관 정책 (오케스트레이터 결정):
- 세션 한정 (현재 Claude Code 세션 종료 시 사라짐) — 보안상 권장
- 또는 사용자 동의 시 `~/.polestar10rc` 같은 파일에 저장 + chmod 600

### 2. recipe 실행 패턴

각 작업마다 다음 구조:

1. recipe md 파일 `Read` → bash 블록 추출
2. 환경변수 주입 + `Bash` 툴로 실행
3. 응답 JSON 의 `success` 필드 + `errorCode` 체크
4. 실패 시 사용자에게 UI Fallback 안내 (recipe 의 `## UI Fallback` 섹션 표시)

### 3. 동적 식별자 흐름

오케스트레이터는 doc 의 placeholder 값을 사용하지 않고, 모두 **API 응답에서 동적 획득**:

| 사용처 | 출처 |
|---|---|
| `AGENT_ID` (서버 register) | `sms/standby-hosts-filter-step1` 응답의 `content[].agentId` |
| `WURL_ID` (Web URL 작업) | `weburl/save` 응답의 `data.id` 또는 `weburl/list-filter` 의 `content[].id` |
| `groupId` (모든 register) | `cm/groups/list` 응답에서 사용자 선택 (보통 1=Default) |
| `serviceGroupTagValue` | 사용자 입력 또는 `cm/tag/value/insert` 로 사전 생성 |

### 4. 멱등성 패턴

오케스트레이터가 같은 작업 두 번 호출돼도 안전하게 처리:

- 등록 전: `count` 또는 `list-filter` 로 이미 존재하는지 체크
- 삭제 전: `count` 비교 (전후) 로 실제 삭제 확인
- agent-based 삭제 후: heartbeat 사이클 내 standby 재출현 가능 — 영구 제거 원하면 에이전트 stop 안내

### 5. 캐시 가능한 메타

매 호출마다 다시 받지 말 것 (세션 캐시):
- `cm/groups/list` (그룹은 잘 안 변함)
- `cm/tag/key/list` (스키마)
- `aiops/v1/anomaly-policies/names` (정책 이름)
- `alarm/severity/find-all` (severity 메타)

### 6. 에러 처리 분류

| 응답 패턴 | 의미 | 권장 처리 |
|---|---|---|
| `success:true` | 정상 | 다음 단계 |
| `success:false, errorCode:"POLESTAR_xxxx"` | 비즈니스 에러 | errorMsgArgs 사용자에게 표시 + UI fallback 제안 |
| HTTP 401/403 + HTML 본문 | 세션 만료 | login recipe 재실행 |
| HTTP 404 | 잘못된 endpoint (recipe 가 outdated) | recipe 갱신 follow-up 이슈 등록 |
| 연결 거부 / 타임아웃 | polestar10 다운 또는 URL 잘못 | 사용자에게 BASE_URL 재확인 prompt |
