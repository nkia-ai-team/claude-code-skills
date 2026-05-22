# NKIA-AI Claude Code Skills

NKIA-AI 팀의 Claude Code 플러그인 마켓플레이스입니다. 개발 워크플로우(kickoff → commit → submit → wrap-up), Linear 이슈/프로젝트/이니셔티브 관리, Confluence·Figma·주간보고 자동화, Polestar 운영/검증 도구를 하나의 플러그인에 모았습니다.

현재 버전: **v1.10.0**

## 설치 방법

```bash
# 1. 마켓플레이스 등록 (최초 1회)
/plugin marketplace add nkia-ai-team/claude-code-skills

# 2. 플러그인 설치
/plugin install nkia-ai-tools@nkia-ai-marketplace

# 3. Claude Code 재시작
```

## 스킬 개요

개발 한 사이클 동안 아래 순서로 조합해서 사용합니다.

```
/kickoff → (개발) → /commit → /submit → (머지) → /wrap-up
```

| 카테고리 | 스킬 | 설명 |
|---------|------|------|
| **개발 워크플로우** | [kickoff](#kickoff) | Linear 이슈로 작업 시작, 브랜치 생성, In Progress 전환 |
| | [commit](#commit) | NKIA 컨벤션 커밋 메시지 자동 생성 |
| | [code-review](#code-review) | GitHub PR / GitLab MR 자동 리뷰 |
| | [submit](#submit) | 커밋 → 푸시 → PR/MR → 리뷰 루프 오케스트레이터 |
| | [wrap-up](#wrap-up) | 머지 후 브랜치 정리 + 증빙 수집 + AC 검증 + In Review 전환 |
| **Linear 이슈** | [linear-issue-creator](#linear-issue-creator) | 템플릿 기반 이슈 생성 (자연어 / 단계별) |
| | [linear-issue-evidence](#linear-issue-evidence) | 완료 AC 체크 + 증빙 첨부 |
| | [linear-issue-validator](#linear-issue-validator) | DoD/AC 항목 자동 검증 및 결과 게시 |
| **Linear 리포팅** | [linear-project-creator](#linear-project-creator) | 프로젝트 생성 및 문서화 |
| | [linear-project-updater](#linear-project-updater) | 프로젝트 주간 상태 업데이트 자동 생성 |
| | [linear-initiative-updater](#linear-initiative-updater) | 소속 프로젝트 Health 집계 → 이니셔티브 업데이트 |
| **문서 & 자동화** | [confluence-manager](#confluence-manager) | Confluence 문서 검색·조회·생성·수정 |
| | [figma-to-react](#figma-to-react) | Figma → React + Storybook + Playwright 파이프라인 |
| | [weekly-report](#weekly-report) | 팀 주간업무보고 자동 수집 및 시트 기록 |
| | [openapi-llm-spec](#openapi-llm-spec) | Lucida Spring Boot 도메인 → LLM tool OpenAPI 3.1 spec 자동 추출 |
| **Polestar 운영** | [ask-polestar10](#ask-polestar10) | polestar10 웹/에이전트(KCM/APM/WPM/SMS) 사용법·설치 Q&A |
| | [testbed-build](#testbed-build) | RCA 테스트베드 인터뷰→코드→배포→등록→시나리오→알람→closed-loop verify |
| | [testbed-polestar10-register](#testbed-polestar10-register) | testbed 자원을 Polestar10 에 자동 등록 |
| | [testbed-tune-alarms](#testbed-tune-alarms) | testbed 알람 임계치 자동 튜닝 (시계열 분포 기반) |
| | [testbed-generate-scenarios](#testbed-generate-scenarios) | RCA 시나리오 자동 생성 |
| **Polestar 검증** | [polestar-eval-test](#polestar-eval-test) | Polestar AI E2E 자동 평가 (Challenger/Runner/Verifier + chrome-devtools + 7축 채점 + screenshot evidence) |

---

## 개발 워크플로우 스킬

### kickoff

Linear 이슈를 읽어 브랜치를 만들고, 이슈를 **In Progress**로 전환하여 개발 착수 준비까지 자동화합니다.

**주요 기능:**
- Linear 이슈 정보 조회 (title, description, labels, AC)
- 레포 유형에 맞는 **최신 버전 develop 브랜치** 기반으로 feature 브랜치 생성
- 이슈 상태 전환 (Todo → In Progress)
- 설계 AC가 있는 경우 설계 문서 scaffold 생성
- uncommitted 변경사항 사전 점검 및 안내

**사용 예시:**
```bash
/kickoff NKIAAI-305
```

---

### commit

Git 커밋 시 NKIA 팀 컨벤션에 맞는 커밋 메시지를 자동 생성합니다.

**주요 기능:**
- 브랜치명에서 PIMS 번호 자동 추출
- 변경사항 분석하여 Type 키워드 자동 결정
- `#{PIMS번호} {Type} : {설명}` 형식 메시지 생성
- 커밋 전 미리보기 및 수정 가능

**Type Keywords:**

| Type | 용도 |
|------|------|
| Feat | 새로운 기능 추가 |
| Fix | 오류 수정 |
| Refactor | 리팩토링/성능 개선 |
| Cleanup | 불필요한 코드 정리 |
| Docs | 문서 변경 |
| Config | 설정 파일 변경 |
| Test | 테스트 코드 |
| Style | 코드 스타일 수정 |

**사용 예시:**
```bash
/commit                          # 기본 (자동 분석)
/commit API 엔드포인트 추가      # 메시지 힌트
/commit --type Fix               # Type 직접 지정
/commit --pims 114667            # PIMS 번호 직접 지정
```

---

### code-review

GitHub PR 또는 GitLab MR의 코드를 자동으로 리뷰하고 댓글로 결과를 게시합니다.

**주요 기능:**
- 브랜치명 규칙 검증 (PIMS 번호 포함 여부)
- 커밋 메시지 규칙 검증
- 코드 품질 검토 (Clean Code, SOLID 원칙)
- 보안 취약점 검토 (OWASP Top 10)
- 성능 이슈 검토 (N+1, 페이징 등)
- 테스트 코드 검토
- 리뷰 결과를 PR/MR 댓글로 자동 게시

**사전 요구사항:**
```bash
# GitHub
brew install gh && gh auth login

# GitLab
brew install glab
glab auth login                                     # gitlab.com
glab auth login --hostname cims2.nkia.net:8443      # 회사 GitLab
```

**사용 예시:**
```bash
# GitHub PR 리뷰
/code-review https://github.com/owner/repo/pull/123

# GitLab MR 리뷰 (회사 GitLab)
/code-review https://cims2.nkia.net:8443/gitlab/lucida-domain-wpm/-/merge_requests/13

# 특정 영역 집중 리뷰
/code-review <URL> --focus security      # 보안만
/code-review <URL> --focus performance   # 성능만
/code-review <URL> --focus quality       # 코드 품질만
```

---

### submit

개발 완료 후 **커밋 → 푸시 → PR/MR 생성 → 코드 리뷰 → 자동 수정** 루프까지 한 번에 실행하는 오케스트레이터 스킬입니다.

**주요 기능:**
- `/commit` 워크플로우로 커밋
- 원격 푸시
- PR/MR 생성 (레포 유형에 맞는 제목, 타겟 브랜치, 본인 assignee)
- `/code-review` 워크플로우로 리뷰 실행
- 지적사항 자동 수정 → 재커밋 → 재리뷰 (최대 3회)
- **merge는 절대 실행하지 않음** (사용자가 직접 수행)

**사용 예시:**
```bash
/submit                    # 타겟 브랜치 자동 판별
/submit develop-ui-chat    # 타겟 브랜치 직접 지정
```

---

### wrap-up

PR/MR 머지 후의 마무리 작업(브랜치 정리 → 증빙 수집 → AC 검증 → In Review 전환)을 자동화합니다.

**주요 기능:**
- 머지 대상 브랜치로 전환 + pull + prune + 머지된 로컬 브랜치 삭제
- `/linear-issue-evidence` 워크플로우로 증빙 수집·등록
- 증빙 자가 점검 및 미흡 항목 자동 보강
- 수동 업로드 안내 및 업로드 미디어 AC 자동 매핑
- `/linear-issue-validator` 워크플로우로 AC 검증
- 검증 실패 시 자동 보강 → 재검증 (최대 3회)
- 검증 통과 시 이슈 상태 In Review로 전환

**사용 예시:**
```bash
/wrap-up NKIAAI-305
```

---

## Linear 이슈 관리 스킬

### linear-issue-creator

Linear 이슈를 템플릿 기반으로 빠르게 생성합니다.

**주요 기능:**
- 9가지 작업 템플릿 지원 (빌드/배포, 데이터 작업, 평가, 기능 개발, 기능 개선, 리팩토링, 리서치, 버그 수정, 문서)
- 자연어 또는 회의록 입력으로 이슈 자동 생성
- 구체적인 DoD / AC 자동 생성
- 마감일 기반 사이클 자동 배정
- 작업 타입별 라벨 자동 적용

**사용 예시:**
```bash
# Auto Mode (자연어 또는 회의록)
"chat ai llm모델을 aws bedrock 모델로 변경해야 되는데 기간은 11월 30일까지야 담당자는 나야"
→ AI가 자동으로 이슈 구조화 및 생성

# Manual Mode (단계별 입력)
/linear-issue-creator
→ 템플릿 선택 및 상세 정보 입력
```

---

### linear-issue-evidence

완료된 Linear 이슈의 AC 항목에 대해 체크박스를 체크하고 증빙 자료를 첨부합니다. 일반적으로 `/wrap-up` 내부에서 자동 실행되지만, 개별 호출도 가능합니다.

**주요 기능:**
- 완료된 AC 항목 자동 판단
- AC에 명시된 증빙 유형별 실제 증빙 수집 (PR 조회, 테스트 실행, 스크린샷 캡처 등)
- AC 체크박스 업데이트 (`[ ]` → `[x]`)
- 증빙 자료를 `→ 결과물:` 뒤에 삽입
- PR/MR 링크는 이슈 리소스(`links`)로 첨부
- 터미널 출력은 반드시 코드 블록으로 감싸 가독성 유지

**사용 예시:**
```bash
/linear-issue-evidence NKIAAI-137
```

---

### linear-issue-validator

완료된 Linear 이슈의 DoD/AC 항목을 검증하고 평가합니다.

**주요 기능:**
- DoD/AC 항목별 결과물 자동 검증
- 다양한 결과물 유형 지원 (PR/MR, CI/CD 로그, URL, 이미지, 문서, API 등)
- 인증 필요 시 사용자에게 입력 요청 후 진행
- 검증 통과 항목 체크박스 자동 업데이트
- 검증 결과를 이슈 코멘트로 자동 작성
- 전체 통과 시 "In Review" 상태 이동 옵션

**지원하는 결과물 유형:**

| 유형 | 검증 방법 |
|-----|----------|
| PR/MR 링크 | gh/glab CLI로 merged/approved 상태 확인 |
| CI/CD 로그 | Jenkins, GitHub Actions, GitLab CI 빌드 결과 확인 |
| 프론트엔드 URL | 접속 + 페이지 내용 확인 |
| 문서 링크 | Notion, Confluence, Google Docs 접속 및 내용 확인 |
| API 엔드포인트 | curl로 응답 코드/시간 확인 |
| 모니터링 링크 | Grafana, Datadog 대시보드 메트릭 확인 |
| 이미지 | Vision으로 내용 확인 |
| 텍스트/메트릭 | 목표 달성 여부 확인 |

**사용 예시:**
```bash
/linear-issue-validator NKIA-123
/linear-issue-validator https://linear.app/nkia-ai/issue/NKIA-123

# 옵션
/linear-issue-validator NKIA-123 --strict       # 모든 항목 통과 필수
/linear-issue-validator NKIA-123 --skip-move    # 상태 변경 스킵
/linear-issue-validator NKIA-123 --dod-only     # DoD만 검증
/linear-issue-validator NKIA-123 --ac-only      # AC만 검증
```

---

## Linear 리포팅 스킬

### linear-project-creator

Linear 프로젝트를 체계적인 문서와 함께 생성합니다.

**주요 기능:**
- 프로젝트 개요 및 목표 설정
- 단계별 구현 계획 (Phases) 자동 생성
- 기술 스택 및 팀 구성 정보 관리
- 마일스톤 및 성공 지표 설정
- 리스크 관리 계획 포함

**사용 예시:**
```bash
/linear-project-creator
```

---

### linear-project-updater

프로젝트에 속한 이슈의 **이번 주 활동**을 기반으로 주간 상태 업데이트를 생성합니다.

**주요 기능:**
- 이번 주 이슈 활동 자동 수집 (신규 생성, AC/증빙 업데이트, Done 전환, In Progress 전환, 블로커)
- 이전 업데이트의 "다음 주 계획" 참조 → 달성 여부 비교
- Health 자동 제안 (On Track / At Risk / Off Track)
- 가이드라인 템플릿으로 렌더링
- Linear Project Status Update로 저장

**사용 예시:**
```bash
/linear-project-updater                  # 내가 리드인 프로젝트 전체
/linear-project-updater "My Project"     # 특정 프로젝트

# 옵션
/linear-project-updater --week 2026-04-20    # 기준 주 지정
/linear-project-updater --skip-previous      # 이전 업데이트 비교 생략
```

---

### linear-initiative-updater

이니셔티브에 속한 **소속 프로젝트들의 최신 상태 업데이트**를 집계하여 이니셔티브 수준 현황 리포트를 생성합니다.

**주요 기능:**
- 소속 프로젝트 목록 자동 조회
- 각 프로젝트의 최신 Status Update에서 Health 수집
- 프로젝트 리드 정보 수집
- Initiative Health 자동 제안 (worst-case 집계)
- 가이드라인 템플릿으로 렌더링
- Linear Initiative Status Update로 저장

**사용 예시:**
```bash
/linear-initiative-updater                    # 전체 또는 선택
/linear-initiative-updater "My Initiative"    # 특정 이니셔티브

# 옵션
/linear-initiative-updater --include-stale    # 최근 2주 업데이트 없는 프로젝트도 포함
```

---

## 문서 & 자동화 스킬

### confluence-manager

NKIA-AI 스페이스 전용 Confluence 문서를 검색, 조회, 생성, 수정합니다.

**주요 기능:**
- Confluence 문서 검색
- 페이지 내용 조회
- 새 페이지 생성
- 기존 페이지 수정

**사용 예시:**
```bash
/confluence-manager
→ 작업 유형 선택 및 실행
```

---

### figma-to-react

Figma MCP에서 컴포넌트 데이터를 추출하여 Headless UI + Tailwind CSS 기반 React 컴포넌트를 생성하고, Storybook 스토리와 Playwright E2E 테스트까지 자동화하는 파이프라인입니다.

**주요 기능:**
- 컴포넌트/화면 신규 빌드
- 증분 추가 (`-a`): 기존 화면에 새 컴포넌트 추가
- 화면 업데이트 (`-u`): 레이아웃/컴포넌트 변경 반영 (토큰 마이그레이션 포함)
- 토큰 마이그레이션 (`-m`): 디자인 토큰 체계 갱신
- Component Spec 기반 Storybook / Playwright 자동 생성
- QA 서브에이전트 검증 단계 포함

**사전 요구사항:**
- 프로젝트 루트에 `.figma-to-react.config.md` 설정 파일
- Figma MCP 연결

**사용 예시:**
```bash
# 신규 생성
/figma-to-react https://...?node-id=1234-5678

# 기획 스펙 URL 포함
/figma-to-react https://...?node-id=1234-5678 https://...?node-id=2811-65001

# 증분 추가
/figma-to-react -a https://...?node-id=5678-1234

# 화면 업데이트
/figma-to-react -u https://...?node-id=5678-1234
```

---

### weekly-report

이번 주 Linear 이슈, Git 커밋, Google Calendar 이벤트를 자동 수집하여 팀 주간 업무 보고 구글 시트에 기록합니다.

**주요 기능:**
- Linear 이슈 자동 수집 (Done → 금주 실적, Todo → 차주 계획)
- 이슈 MR/PR URL에서 레포 식별 → 해당 레포 Git 커밋 수집
- Google Calendar에서 본인 휴가/반차 이벤트 조회 및 반영
- 이번 주 목요일 날짜 탭 → 본인 행에 자동 기록
- 최초 사용 시 설정 저장 (이름, 이메일, 캘린더명), 이후 자동 실행
- Cycle 기반 이슈 수집 및 `--next` 옵션 지원

**사전 요구사항:**
```bash
# Google Workspace CLI 설치 (택 1)
npm install -g @googleworkspace/cli
brew install googleworkspace-cli

# 인증 (최초 1회)
gws auth setup
gws auth login
```

**사용 예시:**
```bash
/weekly-report                       # 이번 주 보고서 작성
/weekly-report --dry-run             # 미리보기만 (시트 기록 안 함)
/weekly-report --week 2026-04-02     # 특정 주 지정
/weekly-report --next                # 다음 사이클 계획 포함
/weekly-report --reconfigure         # 설정 재입력
```

---

## Polestar 검증 스킬

### polestar-eval-test

Polestar AI (lucida-chat-ai) ai-portal 을 chrome-devtools 로 자동 검증하는 E2E 평가 도구. **Agentic Self-Instruct** 패턴으로 Challenger 가 시나리오 별 쿼리 생성 → Runner 가 chrome 으로 send + screenshot + 백엔드 log 수집 → Verifier 가 7축 채점 → strict template 으로 report 자동 생성.

**주요 기능:**
- **시나리오 카테고리 10종** — inventory / live-state / threshold-breach / trend / alarm-management / rca / change-mgmt / cross-domain / memory-application / conversation-flow
- **메모리 hint 적용 검증** — 사용자 메모리 (호칭/조회 선호/alias) 가 응답에 reflected 됐는지 검증
- **Phase B/C/Layer 3 회귀 추적** — prior_context 주입, wrap_tools_with_prior, wide table merge, union override 등 chat-ai 내부 흐름 검증
- **chrome-devtools fetch + SSE reader 패턴** — React onClick / Broken pipe 우회 (100% send 도달)
- **결과 checkpoint** — query 별 즉시 file 저장. `--resume` 으로 중단 복구
- **자동 report generator** — `scripts/gen_report.py` 가 screenshot/answer/axes/verdict 5요소 strict embed (LLM 누락 방지)

**평가 7축**:
| 축 | 가중치 | 기준 |
|---|---|---|
| 정확성 | 25 | expected columns/fields/threshold 매칭 |
| 완성도 | 15 | min_rows / 필수 fields |
| 형식 | 10 | table/chart/narrative 매칭 |
| 백엔드 | 15 | 11 step (routing/memory inject/agent tool/tool args/...) |
| 화면 (vision) | 10 | Claude vision 으로 PNG 직접 분석 |
| 메모리 적용 | 15 | memory-snapshot.items × 응답 매칭 |
| 응답시간 | 10 | <30s=full / 30~60=partial / >60=reduced |

**사용 예시:**
```bash
/polestar-eval-test 104 cross-domain --per-category=5      # cross-domain 5 query (Phase B/C 회귀, ~10분)
/polestar-eval-test 104 all --count=30                     # 10 카테고리에 30개 분배
/polestar-eval-test 57 memory-application --per-category=8 # 메모리 hint hard 8개
/polestar-eval-test 104 all --per-category=10              # 전체 100 query (full, 1~2시간)
```

**출력:** `runs/<run-id>/`
- `memory-snapshot.json` — 평가 시점 메모리 ground truth
- `queries-<category>.json` — Challenger 산출
- `<NNN>-<cat>-<qid>.png/.json` — query 별 screenshot + checkpoint
- `verifier-<category>.json` — 7축 채점 결과
- `report.md` — strict template (모든 query screenshot embed + answer + axes table + verdict)

---

## 업데이트

```bash
# 마켓플레이스 업데이트
/plugin marketplace update nkia-ai-marketplace

# 플러그인 업데이트
/plugin update nkia-ai-tools@nkia-ai-marketplace
```

## 라이선스

MIT
