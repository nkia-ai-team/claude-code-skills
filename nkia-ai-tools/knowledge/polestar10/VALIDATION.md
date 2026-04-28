# polestar10 지식베이스 검증

## 1. 자동 검증

### 1.1 파일 수 집계

| type | category | md 개수 | 분류표 기대값 | 일치 |
|---|---|---|---|---|
| admin | agent-install | 23 | 23 | ✓ |
| admin | db | 2 | 2 | ✓ |
| admin | k8s | 1 | 1 | ✓ |
| admin | system | 1 | 1 | ✓ |
| user | account | 43 | 43 | ✓ |
| user | agent-install | 8 | 8 | ✓ |
| user | alert | 29 | 29 | ✓ |
| user | db | 2 | 2 | ✓ |
| user | k8s | 20 | 20 | ✓ |
| user | network | 9 | 9 | ✓ |
| user | perf | 29 | 29 | ✓ |
| user | system | 19 | 19 | ✓ |

불일치 행 수: **0**

### 1.2 frontmatter 스키마

| 파일 | 6개 필수 키 전부 존재 |
|---|---|
| (전체 186 개) | ✓ |

frontmatter 통과: **186 / 186**

### 1.3 에이전트 install-spec 스키마

| agent | yq 파싱 | 필수 키 5개 | amd64/arm64 method 유효 |
|---|---|---|---|
| wpm | ✓ | ✓ | ✓ |
| apm | ✓ | ✓ | ✓ |
| kcm | ✓ | ✓ | ✓ |
| sms | ✓ | ✓ | ✓ |

### 1.4 메뉴 검색 기반 menu_path 검증 (2026-04-28 추가)

Playwright Node 로 polestar10 데모(`https://192.168.230.104/`) 통합 검색창에 매뉴얼 frontmatter `feature` 값을 입력 → `.portal-auto-complete-dropdown` 결과의 `keyword` / `category` 추출 → 정확 일치 항목의 풀 메뉴 경로를 frontmatter `menu_path_full` 로 추가하고 `menu_path_verified: true` 토글.

| 분류 | 건수 | 비율 |
|---|---:|---:|
| EXACT 매치 (`menu_path_verified: true` 자동 토글) | 96 | 51.6% |
| PARTIAL 매치 (사람 검토 후보) | 47 | 25.3% |
| 검색 미존재 (메타/동적/미설치) | 43 | 23.1% |
| **합계** | **186** |  |

상세 카테고리별 분포·후보 표·미존재 분류 사유는 [`REVIEW_NEEDED.md`](REVIEW_NEEDED.md) 참조.

검증 절차:

1. 통합 검색창 셀렉터: `input[placeholder*="장비, IP, 메뉴"]`
2. 결과 컨테이너: `.portal-auto-complete-dropdown`
3. 결과 항목: `.result-content` 내 `.category` (풀 경로) + `.keyword` (leaf 명)
4. K8s 카테고리는 "쿠버네티스 X" prefix 변형 라운드도 시도 (라운드 1 → 0/20, 라운드 2 → 18/20)

실행 스크립트: `scripts/validate-menu-paths.md` (요약), 원본 작업 산출물은 검증 시점 임시 디렉토리.

## 2. 사람 확인 필요 (ralph 범위 밖)

### 2.1 대표 질문 세트 (20개)

`menu_path_full` 자동 검증 결과를 매뉴얼별로 미리 매핑한 표. expert 답변(초안) 은 ask-polestar10 호출 시 polestar10-expert 서브에이전트가 작성하는 영역이며, 이 표는 답변 출처(어느 매뉴얼·어느 메뉴 경로) 의 신뢰도를 알리기 위한 가이드입니다.

| # | 질문 | 출처 매뉴얼 | 메뉴 경로 검증 |
|---|---|---|---|
| 1 | 개별 알람 정책은 어떻게 추가해? | `manuals/user/alert/alert-005.md` | ✓ 알람 & 이벤트 > 알람 정책 > 개별 알람 정책 |
| 2 | 공통 알람 정책과 개별 알람 정책의 차이는? | `manuals/user/alert/alert-005.md`, `manuals/user/alert/alert-007.md` | ✓ 알람 & 이벤트 > 알람 정책 > 공통 알람 정책 / 개별 알람 정책 |
| 3 | 서비스 그룹 생성 절차? | _매뉴얼 미상_ — `manuals/user/account/account-024.md` (서비스 수준 관리) 또는 `account-026.md` (서비스 카탈로그) 후보 | ⚠ 검색 미존재 (사람 확인 필요) |
| 4 | 담당자 권한 부여 메뉴? | `manuals/user/account/account-006.md` | ✓ 운영관리 > EMS > 담당자 구분 |
| 5 | NMS에서 네트워크 장비 등록? | `manuals/user/network/network-002.md` | ✓ 전체구성 > 관리대상 > 네트워크 |
| 6 | DPM에서 MySQL 인스턴스 등록? | _매뉴얼에 MySQL 명시적 항목 없음_ (CUBRID 만 존재: `manuals/user/db/db-001.md`) | ⚠ 매뉴얼 부재 — "메뉴얼에서 확인되지 않습니다" 답변 |
| 7 | APM Java Agent 설치 순서? | `manuals/admin/agent-install/agent-install-003.md`, `agents/apm/install-guide.md` | ⚠ admin 운영 가이드 (메뉴 검색 대상 아님) |
| 8 | WPM Agent 설치 시 사전 조건? | `manuals/user/agent-install/agent-install-001.md`, `agents/wpm/install-guide.md` | ⚠ 운영 가이드 (메뉴 검색 대상 아님) |
| 9 | KCM Agent를 ARM 서버에 설치하려면? | `manuals/admin/agent-install/agent-install-010.md`, `agents/kcm/install-spec.yaml` (`arch_support.arm64.method`) | ⚠ 운영 가이드 (메뉴 검색 대상 아님) |
| 10 | SMS Agent가 ARM에서도 동작하나? | `agents/sms/install-spec.yaml` (`arch_support.arm64.method`) | ⚠ install-spec 인용 |
| 11 | 알람 수신자 그룹 설정? | `manuals/user/system/system-019.md` (통보 설정), `manuals/user/alert/alert-017.md` (알람 패턴 통보 설정) | ⚠ partial — 사람 확인 필요 |
| 12 | 성능 이상 감지 정책 생성? | `manuals/user/perf/perf-015.md` | ✓ 알람 & 이벤트 > AIOps Lucida 정책 > 성능 이상감지 정책 |
| 13 | 토폴로지 맵 뷰어 접근? | `manuals/user/perf/perf-026.md` | ✓ 토폴로지 맵 |
| 14 | 보고서 템플릿 관리? | `manuals/user/system/system-006.md` | ✓ 운영관리 > EMS > 보고서 템플릿 관리 |
| 15 | 라이선스 관리 메뉴? | `manuals/user/system/system-004.md` | ✓ 운영관리 > 기본 설정 > 라이선스 관리 |
| 16 | 사용자 2차 인증 설정? | `manuals/user/account/account-031.md` | ⚠ 검색 미존재 — 데모 환경 미설치 또는 시스템 설정 하위 메뉴 |
| 17 | 업무시간/휴일 설정은 어디서? | `manuals/user/system/system-012.md` | ⚠ partial — 사람 확인 필요 |
| 18 | 로그 감시 정책 등록? | `manuals/user/alert/alert-010.md` | ✓ 전체구성 > 사용자 정의 항목 > 로그 |
| 19 | 프로세스 감시 설정? | `manuals/user/perf/perf-029.md` | ✓ 전체구성 > 사용자 정의 항목 > 프로세스 |
| 20 | 파일 감시 설정? | `manuals/user/perf/perf-028.md` | ✓ 전체구성 > 사용자 정의 항목 > 파일 |

기호: ✓ EXACT 자동 검증 / ⚠ partial · 미존재 · 운영 가이드 (사람 확인 또는 별도 출처).

### 2.2 menu_path 배치 검수

자동 라운드(§1.4) 후 남은 PARTIAL 47 건 + NONE 43 건은 [`REVIEW_NEEDED.md`](REVIEW_NEEDED.md) §3 (PARTIAL), §4 (NONE) 의 카테고리별 표 참조. 사람이 polestar10 웹에서 대조 후:

- PARTIAL: 가장 가까운 후보 메뉴 경로가 맞으면 frontmatter 의 `feature` 를 일치시키고 `menu_path_verified: true` + `menu_path_full` 추가.
- NONE: 메뉴가 아닌 동적 화면·메타 챕터·미설치 모듈 중 어떤 사유인지 기록.
