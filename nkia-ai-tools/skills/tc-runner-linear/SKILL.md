---
name: tc-runner-linear
description: Linear 이슈를 읽어 lucida-ui 소스로 기능을 파악해 Positive+Negative TC를 작성하고, https://192.168.230.104/ 에서 Playwright로 자동 수행한 뒤, 결과를 PIMS2(Redmine) 이슈에 등록한다. Linear 기반 TC 작성·수행, sjbang의 TC, Linear→PIMS 테스트 등록 요청 시 사용.
allowed-tools: Bash(node *), Bash(npx *), Bash(mkdir *), Read, Edit, Write, Grep, Glob, AskUserQuestion, TodoWrite, mcp__linear__get_issue, mcp__linear__list_comments
---

# tc-runner-linear — Linear 이슈 기반 TC 작성·수행, PIMS 결과 등록

Linear 이슈 ID를 입력받아:

1. Linear MCP로 이슈를 읽고 **lucida-ui 소스**(`./lucida-ui`)로 기능 파악
2. 4섹션 포맷의 **TC(Positive+Negative)** 작성
3. `https://192.168.230.104/` 에서 **Playwright 로 자동 수행** (스크린샷 + Pass/Fail)
4. 결과를 **PIMS2 이슈로 새로 생성** 후 본문 + 댓글로 등록

인자: `$ARGUMENTS` — 형식 `<LINEAR-ID> [PIMS-PROJECT-ID] [PIMS-TRACKER-ID]`
  - 예: `/tc-runner-linear NKIAAI-498` (PIMS project/tracker는 환경변수 또는 인터뷰)
  - PIMS 이슈를 별도로 만들지 않고 기존 이슈에 추가하려면 `--pims=<id>` 인자 사용

## 설정

| 항목 | 값 |
|------|-----|
| Linear | `mcp__linear__get_issue` (MCP 직접 호출) |
| PIMS2 URL | `http://pims2.nkia.co.kr` |
| 자격증명 저장 | `~/.config/tc-runner-linear/credentials.json` (chmod 600, OMC 무관). 최초 실행 시 인터뷰 (Step -1) |
| PIMS2 인증 | API Key 우선 → Basic Auth fallback. 출처: env (`REDMINE_API_KEY`/`REDMINE_USER`/`REDMINE_PASS`) → credentials.json `pims.api_key`/`user`/`pass` |
| PIMS 이슈 생성 기본값 | project=**494** (Polestar 10), tracker=**17** (테스트케이스), version=**2096** (테스트자동화). 모두 인자 (`--project=` 등) 또는 env 또는 credentials 로 덮어쓰기 가능 |
| 테스트 서버 | `https://192.168.230.104/` (NKIA 공통, env `TC_BASE_URL` 덮어쓰기) |
| 테스트 계정 | env `TC_USER`/`TC_PASS` → credentials `polestar10.user`/`pass`. 조직 `TC_ORG` (기본 `MyOrganization`) |
| lucida-ui | env `LUCIDA_UI_DIR` → credentials `lucida_ui_dir` (필수, 기본값 없음 — 환경마다 다름) |
| 스킬 경로 | `~/.claude/skills/tc-runner-linear` |

> 모든 `scripts/*` 명령은 스킬 폴더 기준 상대경로. 실행 전 `cd ~/.claude/skills/tc-runner-linear` 또는 절대경로 사용.

## 참고 문서 (작업 중 Read)

- `references/good-tc-template.md` — **품질팀 공식 원본 (PIMS #120773 첨부, 374줄)**. 가장 권위 있는 SoT.
- `references/tc-checklist.md` — 원본 요약 + NKIA 팀 작업 룰 (PIMS #120773 가이드 반영)
- `references/backend-tc.md` — **서버단(화면 없음) 이슈 TC 작성법** (curl/DB/로그/메트릭)
- `references/ui-map.md` — Linear 이슈 → `./lucida-ui` 소스 매핑 방법
- `references/linear-flow.md` — Linear MCP 호출 + 이슈에서 기능명·메뉴 추출
- `references/redmine-api.md` — PIMS 계정 인증 + create/append/note CLI
- `references/playwright-guide.md` — 230.104 서버 실행 + 스펙 작성 규칙
- `scripts/generated/_example.spec.mjs` — 생성 스펙 예시 (화면)

---

## 실행 절차

`TodoWrite` 로 단계 추적: 자격증명체크 / Linear조회 / 소스파악 / TC작성 / PIMS등록 / 자동수행 / 결과댓글.

### Step -1 — 자격증명 체크 (최초 사용 시 1회만)

```bash
node scripts/lib/credentials.mjs check
```

- **exit 0 ("OK")** → 자격증명 준비됨, Step 0 으로 진행.
- **exit 1 ("SETUP_NEEDED")** → `AskUserQuestion` 으로 한 번에 받기:
  1. **PIMS API key** — PIMS2 우측 상단 "내 계정" → "API 액세스 키" 에서 복사
  2. **Polestar10 ID** — `https://192.168.230.104/` 로그인 계정 ID (보통 PIMS ID 와 동일)
  3. **Polestar10 비밀번호**
  4. **lucida-ui 경로** — 로컬 lucida-ui 클론 절대경로 (예: `/home/<user>/dev/lucida-ui`)

받은 값으로 `/tmp/tc-runner-creds-<random>.json` 생성 → 즉시 저장 후 삭제:
```bash
node scripts/lib/credentials.mjs save /tmp/tc-runner-creds-XXX.json && rm /tmp/tc-runner-creds-XXX.json
```

저장 위치: `~/.config/tc-runner-linear/credentials.json` (chmod 600, OMC 무관).

> 자격증명 변경 시: `node scripts/lib/credentials.mjs reset` → 다음 실행에서 재인터뷰.
> 현재 저장값 확인 (마스킹): `node scripts/lib/credentials.mjs show`.

### Step 0 — 인자 확정
- `$ARGUMENTS` 에서 Linear ID 추출 (예: `NKIAAI-498`). 없으면 `AskUserQuestion`.
- PIMS 매핑 결정:
  - `--pims=<id>` 가 있으면 기존 이슈에 append.
  - 없으면 신규 생성 (project=494/tracker=17/fixed_version=2096 NKIA 공통 기본).

### Step 1 — Linear 이슈 조회
```
mcp__linear__get_issue(id="NKIAAI-498")
```
- title, description, state, labels 확인.
- 제목에서 기능명/메뉴 단서 추출. description에 PR 링크 있으면 메모.
- 정보 부족하면 `mcp__linear__list_comments` 로 댓글 보완.

### Step 2 — lucida-ui 소스로 기능 파악 (`references/ui-map.md`)
- 후보 `remotes/<모듈>` 좁히기. 제목 접두 코드(SMS/CMM/APM/...)나 기능명 키워드로 시작.
- `Grep(pattern="<라벨>", path="./lucida-ui/remotes", glob="*.tsx")` 로 실제 메뉴 라벨/필드/셀렉터 확보.
- i18n 키(`tt('cmm.xxx')`)와 한글 라벨 함께 확인.
- 자동선택/비활성/유효성 규칙은 TC 참고사항·예상결과에 반영.

### Step 3 — TC 작성 (`references/tc-checklist.md` 또는 `references/backend-tc.md`)
- **이슈 유형 분기**:
  - 화면 영향 있음 → `tc-checklist.md` 의 그리드/폼/위젯 패턴
  - 화면 없음 (API/DB/배치/인프라) → `backend-tc.md` 의 도구 매핑
- TC ID 형식: `TC-<도메인>-NNN` (예: `TC-NAMESPACE-001`, `TC-RCA-001`).
- 4섹션 헤더(`사전조건 / 참고사항 / 테스트절차 / 예상결과 (캡처포함)`) + **평문** (`~~~` 블록 X).
- 한 이슈/도메인당 **Positive 다수 + Negative 소수** (쌍 강제 X).
- 인터랙션마다 TC 분리 — 정렬 1개, 필터 1개, 다운로드 1개 식 원자화.
- 화면 진입/주요 API 호출 TC 에 **성능 측정 항목** 포함 (굵게 명시).
- 예상결과는 `selector + 기대값` 또는 `HTTP status + JSON path + 값` 으로 단언 가능하게.
- 메뉴·버튼·필드는 Step 2의 실제 값. 셀렉터 추측 금지.
- 초안 저장: `scripts/work/<LinearID>-tc.md`.
- **사용자 확인** (`AskUserQuestion`).

### Step 4 — PIMS 이슈 등록
사용자 승인 후, 두 갈래:

**Case A — 신규 생성** (project=494, tracker=17 기본 적용)
```bash
node scripts/redmine.mjs create \
  --version=2096 \
  --subject="[<모듈>-<하위모듈>] <화면> > <탭>" \
  scripts/work/<LinearID>-tc.md
```
- `--version=2096` → "테스트자동화" 마일스톤 (KCM 모범 사례와 동일).
- 카테고리는 PIMS 에 없을 수 있으니 일단 미지정. 등록 후 PIMS 화면에서 수동 지정 가능.
- 다른 프로젝트/카테고리/마일스톤이 필요하면 `--project=`, `--category=`, `--version=` 으로 덮어쓰기.
- stdout 에 생성된 PIMS 이슈 번호 출력 → 이후 단계에서 사용.

**Case B — 기존 이슈에 append**
```bash
node scripts/redmine.mjs append-desc <PIMS-ID> scripts/work/<LinearID>-tc.md
```

### Step 5 — 자동 수행

**화면 TC** (`references/playwright-guide.md`)
- `scripts/generated/_example.spec.mjs` 복사 → `scripts/generated/<LinearID>-<tcId>.spec.mjs`.
  - `run.step('<TC 절차 번호+문구>', ...)` 이름을 TC 절차와 1:1.
  - 셀렉터는 Step 2에서 확인한 실제 값.
  - **성능 측정**: `const t0 = Date.now()` ... `results.metrics.<name> = (Date.now()-t0)/1000`
  - 예상결과를 step 콜백 안에서 단언 → 실패 시 자동 Fail.
- 실행:
  ```bash
  TC_OUT_DIR=scripts/runs/<LinearID> node scripts/generated/<LinearID>-<tcId>.spec.mjs
  ```

**서버단 TC** (`references/backend-tc.md`)
- bash 스크립트로 작성: `scripts/generated/<LinearID>-backend.sh`
  - curl `-w '%{time_total}'` 로 응답 시간 측정.
  - 출력은 `scripts/runs/<LinearID>-backend/NN-<step>.txt` 또는 `.json`.
  - 절차 실패 시 `exit 1` 로 자동 Fail.
- 실행:
  ```bash
  LINEAR_ID=<LinearID> bash scripts/generated/<LinearID>-backend.sh
  ```

- 결과: 콘솔 `[PASS]/[FAIL]`, `scripts/runs/<LinearID>*/results.json` 또는 출력 파일.
- 화면 TC 의 로그인 첫 캡처(`01-login.png`)에서 2차 인증 보이면 스펙에 후속 단계 추가 후 재실행.

### Step 6 — 결과를 PIMS 댓글로 기록
- 각 `results.json` 을 읽어 `scripts/work/<LinearID>-result.md` 작성:
  - 수행 요약 (`pass/total`, 수행 일시, 서버, 계정, Linear 링크).
  - **절차별 Pass/Fail 표** (절차 문구 + 결과 + 실패 사유).
  - Positive/Negative 각각.
  - 첨부 스크린샷 파일명 목록 (인라인 `!파일.png!` 권장).
- 스크린샷과 함께 댓글 등록:
  ```bash
  node scripts/redmine.mjs note <PIMS-ID> scripts/work/<LinearID>-result.md \
    scripts/runs/<LinearID>-positive/*.png scripts/runs/<LinearID>-negative/*.png
  ```
  (대표 컷만 추리기 권장)
- 완료 후 사용자에게:
  - PIMS 링크: `http://pims2.nkia.co.kr/issues/<PIMS-ID>`
  - Linear 링크: `https://linear.app/.../issue/<LINEAR-ID>`
  - 요약: Positive PASS n/n, Negative PASS n/n

---

## ⚠️ 포맷 룰 — 본문 = markdown, 댓글 = textile (혼용 금지)

PIMS Redmine 은 본문과 댓글의 포맷이 다르다. **이 룰을 어기면 페이지가 깨진다** (실제 사고 사례: PIMS #121136 본문이 텍스타일로 작성돼 `h2.`/`h3.` 가 그대로 텍스트로 노출됨).

| 영역 | 포맷 | 헤더 | 표 |
|------|------|------|----|
| **본문 (description)** | **markdown** | `##` / `###` / `####` | `\| 항목 \| 내용 \|` + `\|---\|---\|` |
| **댓글 (note)** | **textile** | `h2.` / `h3.` | `\|. 항목 \|. 내용 \|` |

**Step 3 (TC 초안) / Step 6 (결과 댓글) 사용자 확인 전에 자체 검증 필수**:
- 본문에 `h1.` / `h2.` / `h3.` 텍스타일 헤더 → 거부
- `#### 사전조건` / `#### 참고사항` / `#### 테스트절차` / `#### 예상결과 (캡처포함)` 가 TC 수만큼 없음 → 거부
- `~~~` 블록이 (TC 수 × 4 × 2) 만큼 없음 → 거부
- 댓글에 `##` 마크다운 헤더 또는 `| ... | ... |` 마크다운 표 → 거부

자세한 룰: `references/tc-checklist.md` §2.0 / §7.

## 결과 댓글 본문 권장 양식 (Redmine 텍스타일)

```
h2. 테스트 실행 결과

|. 항목 |. 내용 |
| 실행일시 | YYYY-MM-DD HH:mm:ss |
| 총 테스트 | N개 |
| 성공 | n개 |
| 실패 | n개 |
| 성공률 | NN.N% |
| Linear | <LINEAR-ID> |
| 서버 | https://192.168.230.104/ |
| 계정 | jjy |

h3. 성능 측정

|. 항목 |. 결과 |
| 화면 로딩 시간 | 1010ms |
| 드로어 로딩 시간 | 370ms |
| (서버단) API 응답 시간 | 210ms |

h3. 테스트케이스별 결과

|. ID |. 테스트케이스 |. 결과 |. 소요시간 |. 비고 |
| TC-NAMESPACE-001 | [KCM] 네임스페이스 목록 화면 접속 및 그리드 표시 확인 | PASS | 3.1s | 화면 로딩 시간: 1010ms |
| TC-NAMESPACE-002 | [KCM] 네임스페이스 목록 리소스명 클릭 시 상세 드로어 열림 확인 | PASS | 8.5s | 드로어 로딩 시간: 370ms |
| ...

h3. 실패 상세

TC-NAMESPACE-NNN: <실패 사유 한 줄>

자동 테스트 실행기에 의해 작성됨
```

## 작업 룰 (PIMS #120773 가이드)

- **한 PIMS 이슈 = 한 화면**. 탭별 데이터가 많이 다르면 탭별 분리 이슈.
- **제목 형식**: `[<모듈>-<하위모듈>] <화면> > <탭> > <섹션>`
- **업무 범주 (category)**: `On-Premise <모듈명>`. PIMS 에 없으면 추가하지 말고 분류 없이 생성.
- **마일스톤 (fixed_version)**: "테스트자동화" (id=`2096`) 가 표준. `PIMS_FIXED_VERSION_ID=2096` 또는 `--version=2096`.
- **그리드 룰**: 전체 컬럼 정렬·필터는 **한 TC 안에 컬럼별 step**. TC 분리 X.
- **차트 룰**: Pin / 확대보기 / 공유노트 각각 **분리된 TC**.
- **결과 댓글**: 화면 로딩 시간 **ms 단위** 필수.
- **작업 방식**: 팀 에이전트 금지. 단독 모델(=Claude 직접 호출)로 진행.

## 주의사항

- PIMS 신규 생성 기본값: **project=494 (Polestar 10 (Lucida)), tracker=17 (테스트케이스)**. 다른 프로젝트면 `--project=` 또는 `PIMS_PROJECT_ID` env 로 덮어쓰기.
- 기존 PIMS 이슈에 append 할 때는 **본문 덮어쓰지 말 것** (`append-desc` 사용, `set-desc` 는 사용자 명시 시만).
- TC 초안과 결과 댓글은 **등록 전 사용자 확인** (`AskUserQuestion`).
- 셀렉터·라벨은 추측 금지 — `./lucida-ui` 소스에서 확인한 값만 사용.
- 자동 수행이 막히는 단계(권한·데이터 부재 등)는 댓글에 "수동 확인 필요"로 명시. 무리하게 PASS 처리 금지.
- 산출물 위치: `scripts/work/`(텍스트), `scripts/runs/<LinearID>-{positive,negative}/`(스크린샷·json).

추가 인자가 있으면 활용: $ARGUMENTS
