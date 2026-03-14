# Evidence Gathering Methods

증빙 유형별 실제 수집 방법을 정의합니다.

AC 항목의 `→ 결과물:` 뒤에 명시된 증빙 유형을 파악하고, 해당 유형에 맞는 수집 방법을 실행합니다.

---

## 1. 증빙 유형 식별

AC 항목에서 증빙 유형을 자동 판별합니다.

| 키워드 패턴 | 증빙 유형 | 예시 |
|------------|----------|------|
| `PR`, `MR`, `Pull Request`, `Merge Request`, `PR 링크` | PR/MR 링크 | `→ 결과물: PR 링크 {{pr_link}}` |
| `테스트`, `test`, `pytest`, `jest`, `통과` | 테스트 결과 | `→ 결과물: 테스트 결과 {{test_result}}` |
| `스크린샷`, `screenshot`, `캡처` | 스크린샷 | `→ 결과물: 스크린샷 {{screenshot_path}}` |
| `CI`, `CD`, `빌드`, `build`, `파이프라인`, `pipeline` | CI/CD 로그 | `→ 결과물: CI 빌드 로그 {{ci_url}}` |
| `문서`, `document`, `Confluence`, `wiki` | 문서 링크 | `→ 결과물: 설계 문서 {{doc_url}}` |
| `데이터`, `경로`, `path`, `파일` | 데이터 경로 | `→ 결과물: 데이터 경로 {{data_path}}` |
| `메트릭`, `metric`, `정확도`, `accuracy`, `성능` | 메트릭 결과 | `→ 결과물: 정확도 {{accuracy}}` |
| `API`, `엔드포인트`, `endpoint`, `응답` | API 응답 | `→ 결과물: API 응답 {{api_response}}` |
| `코드`, `변경`, `diff`, `리팩토링`, `구현`, `전환` | 코드 변경 | `→ 결과물: {{diff_summary}}` |

식별 불가 시 텍스트 기반 증빙으로 처리합니다.

---

## 2. PR/MR 링크 수집

### GitHub PR

    # 현재 브랜치의 PR 조회 (상태, 리뷰 정보 포함)
    gh pr list --head $(git branch --show-current) --json url,number,title,state,reviewDecision,mergedAt

    # PR이 있으면 URL + 상태 정보 추출
    # PR이 없으면 → 수집 실패 (PR 미생성 상태)

### GitLab MR

    # GitLab self-hosted: ~/.config/glab-cli/config.yml에서 토큰 사전 추출
    # ⚠️ config 키에 포트가 없을 수 있음 (예: cims2.nkia.net vs cims2.nkia.net:8443)
    #    → 포트 제외 호스트명으로도 매칭
    # config에 없으면 환경변수 확인 (GITLAB_TOKEN, GITLAB_PRIVATE_TOKEN)
    # 토큰 확보 후:
    GITLAB_TOKEN={token} GITLAB_HOST={hostname} glab mr list --source-branch $(git branch --show-current)

    # 토큰 확보 실패 또는 glab 미설치 시 → 수집 실패, 사용자에게 URL 직접 입력 안내

### 수집 결과 형식

URL과 함께 슈퍼바이저가 클릭 없이 판단할 수 있는 핵심 상태를 포함합니다:

    PR #42 "브랜치명 검증 패턴 수정" (MERGED, approved) https://github.com/org/repo/pull/42

포함 정보:
- PR 번호 + 제목
- 상태: `OPEN` / `MERGED` / `CLOSED`
- 리뷰: `approved` / `changes_requested` / `pending review`

### 첨부 방식: 이슈 리소스(links)

PR/MR 링크는 description 텍스트에 삽입하지 않고, **이슈 리소스**로 첨부합니다.

    mcp__linear__save_issue({
      id: "issue-uuid",
      links: [{ url: "https://github.com/org/repo/pull/42", title: "PR #42 브랜치명 검증 패턴 수정" }]
    })

- `links` 필드는 append-only (기존 리소스를 제거하지 않음)
- 첨부된 링크는 이슈 `attachments`에 표시됨
- validator는 `attachments`에서 PR/MR URL을 확인하여 검증

---

## 3. 테스트 결과 수집

### 프로젝트 테스트 프레임워크 감지

| 감지 파일 | 프레임워크 | 실행 명령 |
|----------|----------|----------|
| `pytest.ini`, `pyproject.toml` (pytest 섹션) | pytest | `pytest --tb=short -q` |
| `package.json` (jest/vitest/mocha) | Node.js 테스트 | `npm test` 또는 `npx jest` |
| `Cargo.toml` | Rust | `cargo test` |
| `go.mod` | Go | `go test ./...` |

### 실행

AC 항목에서 테스트 대상을 파악하여 적절한 범위로 실행합니다.

- AC에 특정 테스트 파일/클래스가 명시되면 해당 범위만 실행
- 범위 미명시 시 관련 테스트 전체 실행
- **반드시 verbose 모드(-v)로 실행** — 개별 테스트 이름과 PASSED/FAILED가 출력에 포함되어야 함

| 감지 파일 | 프레임워크 | 실행 명령 |
|----------|----------|----------|
| `pytest.ini`, `pyproject.toml` (pytest 섹션) | pytest | `pytest -v` |
| `package.json` (jest/vitest/mocha) | Node.js 테스트 | `npx jest --verbose` 또는 `npx vitest run` |
| `Cargo.toml` | Rust | `cargo test -- --nocapture` |
| `go.mod` | Go | `go test -v ./...` |

### 수집 결과 형식: 요약 + 실제 출력

**구조: 요약 한 줄 → 빈 줄 → 실행 명령어(`$` 접두사) + 실제 터미널 출력 전체**

슈퍼바이저가 요약만 보고 통과 여부를 판단하고, 필요하면 실제 출력에서 개별 테스트를 확인할 수 있습니다.

**전체 통과 시:**

    pytest 5/5 passed, 1 warning in 0.04s

    $ .venv/bin/python -m pytest tests/shared/models/test_vllm_chat_model.py::TestCreateChatResult -v
    ============================= test session starts ==============================
    platform linux -- Python 3.13.8, pytest-9.0.2, pluggy-1.6.0
    rootdir: /home/jwchoi/workspace/2026/lucida-chat-ai
    configfile: pytest.ini
    plugins: cov-7.0.0, anyio-4.12.1
    collected 5 items

    tests/shared/models/test_vllm_chat_model.py::TestCreateChatResult::test_reasoning_preserved PASSED
    tests/shared/models/test_vllm_chat_model.py::TestCreateChatResult::test_no_reasoning_field PASSED
    tests/shared/models/test_vllm_chat_model.py::TestCreateChatResult::test_empty_reasoning PASSED
    tests/shared/models/test_vllm_chat_model.py::TestCreateChatResult::test_multiple_choices PASSED
    tests/shared/models/test_vllm_chat_model.py::TestCreateChatResult::test_model_dump PASSED

    ========================= 5 passed, 1 warning in 0.04s =========================

**실패 포함 시:**

    pytest 3/5 passed, 2 failed in 0.12s

    $ .venv/bin/python -m pytest tests/auth/ -v
    ============================= test session starts ==============================
    ...
    tests/auth/test_login.py::test_login_success PASSED
    tests/auth/test_login.py::test_login_redirect PASSED
    tests/auth/test_login.py::test_login_invalid_password FAILED
    tests/auth/test_session.py::test_session_create PASSED
    tests/auth/test_session.py::test_session_timeout FAILED

    FAILURES
    ...
    ========================= 3 passed, 2 failed in 0.12s ==========================

**요약 줄 파싱:**

| 프레임워크 | 출력 패턴 | 요약 형식 |
|-----------|----------|----------|
| pytest | `5 passed, 1 warning in 0.04s` | `pytest 5/5 passed, 1 warning in 0.04s` |
| jest | `Tests: 2 failed, 15 passed, 17 total` | `jest 15/17 passed, 2 failed` |
| vitest | `Tests 12 passed (12)` | `vitest 12/12 passed` |
| go test | `ok`/`FAIL` 라인 집계 | `go test 8/8 packages passed` |
| cargo test | `test result: ok. 8 passed; 0 failed` | `cargo test 8/8 passed` |

**테스트 케이스 문서 연관 (있는 경우):**

프로젝트에 테스트 케이스 문서가 있으면 (CLAUDE.md 테스트 규칙 참조), 요약 줄 아래에 TC ID별 결과를 추가합니다:

    pytest 32/32 passed in 1.23s
    [TC-AUTH-001] 로그인 성공 테스트 ✅
    [TC-AUTH-002] 잘못된 비밀번호 테스트 ✅
    [TC-AUTH-003] 세션 만료 테스트 ✅

    $ .venv/bin/python -m pytest tests/auth/ -v
    ...

테스트 실패 시에도 결과를 수집합니다 (실패 사실 자체가 증빙). 체크 여부는 Step 5에서 판단합니다.

---

## 4. 스크린샷 수집

### Playwright MCP 사용

CLAUDE.md 증빙 스크린샷 규칙을 따릅니다:
- 저장 경로: `temp/playwright-mcp/{이슈번호 소문자}/`
- 컴포넌트/UI: 해당 요소 + 주변 컨텍스트가 보이도록 상위 컨테이너 캡처
- 전체 화면: viewport 전체 캡처

### 캡처 대상 판단

AC 항목의 텍스트에서 캡처 대상을 추론합니다:
- "로그인 화면" → 로그인 페이지로 이동 후 캡처
- "대시보드 레이아웃" → 대시보드 페이지 전체 캡처
- "에러 메시지 표시" → 에러 발생 시키고 캡처

### Playwright MCP 미연결 시

수집 실패로 처리합니다. 사용자에게 수동 캡처를 안내합니다.

### 수집 결과 형식

    temp/playwright-mcp/nkiaai-137/login-screen.png

---

## 5. CI/CD 로그 수집

### GitHub Actions

    # 현재 브랜치의 최근 워크플로우 실행 조회 (결론, 소요시간 포함)
    gh run list --branch $(git branch --show-current) --limit 1 --json databaseId,status,conclusion,url,name,updatedAt,createdAt

    # 결과 정보 추출

### GitLab CI

    # GitLab self-hosted: 위 "GitLab MR" 섹션과 동일하게 config에서 토큰 사전 확보
    GITLAB_TOKEN={token} GITLAB_HOST={hostname} glab ci list --branch $(git branch --show-current)

### Jenkins

    # Jenkins URL이 AC에 명시된 경우 해당 URL 사용
    # 미명시 시 수집 불가 → 수집 실패

### 수집 결과 형식: 요약 + 실제 출력

**구조: 요약 한 줄 → 빈 줄 → 실행 명령어(`$` 접두사) + 실제 터미널 출력**

**GitHub Actions:**

    CI "Build & Test" success (2m 34s) https://github.com/org/repo/actions/runs/12345678

    $ gh run view 12345678 --log --job build
    2026-03-14T10:00:01Z Run npm ci
    2026-03-14T10:00:15Z Run npm test
    ...
    2026-03-14T10:02:35Z ✓ All tests passed
    2026-03-14T10:02:35Z Process completed with exit code 0.

**GitLab CI:**

    GitLab CI "test" passed (1m 12s) https://cims2.nkia.net:8443/gitlab/project/-/jobs/456

    $ GITLAB_TOKEN={token} glab ci view 456
    Name:    test
    Status:  passed
    Duration: 1m 12s
    ...

포함 정보:
- 워크플로우/잡 이름
- 결과: `success`(`passed`) / `failure`(`failed`) / `cancelled`
- 소요 시간
- URL
- 실제 로그 출력 (주요 구간)

---

## 6. 문서 링크 수집

### Confluence

Confluence MCP가 연결되어 있으면:

    # 문서 제목으로 검색
    mcp__confluence__searchConfluenceUsingCql(cql: 'title ~ "설계 문서"')

    # 검색 결과에서 URL 추출

MCP 미연결 시 수집 실패로 처리합니다.

### 기타 문서

AC에 URL이 이미 명시되어 있으면 해당 URL을 사용합니다. 미명시 시 수집 실패.

### 수집 결과 형식

문서 제목을 포함하여 무슨 문서인지 URL 클릭 없이 파악할 수 있게 합니다:

    "WSS 모델 설계 문서" https://confluence.example.com/pages/viewpage.action?pageId=123456

---

## 7. 데이터 경로 수집

### 파일 존재 및 내용 확인

    # AC에 명시된 경로 또는 패턴으로 확인
    ls -la {{expected_path}}

    # 데이터 건수 확인 (CSV/JSONL 등)
    wc -l {{data_file}}

    # 데이터 구조 및 샘플 확인
    head -5 {{data_file}}

### 수집 결과 형식: 요약 + 실제 출력

**구조: 요약 한 줄 → 빈 줄 → 실행 명령어(`$` 접두사) + 파일 정보 + 데이터 샘플**

슈퍼바이저가 요약에서 파일 존재와 건수를 확인하고, 샘플 데이터에서 스키마와 내용이 올바른지 판단할 수 있습니다.

    /data/output/result.csv — 1,024건, 2.3MB

    $ ls -la /data/output/result.csv
    -rw-r--r-- 1 jwchoi jwchoi 2359296 Mar 14 10:00 /data/output/result.csv

    $ wc -l /data/output/result.csv
    1024 /data/output/result.csv

    $ head -5 /data/output/result.csv
    id,name,score,category
    1,item_a,95.2,A
    2,item_b,88.1,B
    3,item_c,92.7,A
    4,item_d,76.3,C

**바이너리/대용량 파일인 경우:**

파일 형식에 따라 적절한 확인 명령을 사용합니다:

| 파일 형식 | 확인 명령 |
|----------|----------|
| CSV/TSV/JSONL | `head -5` (스키마 + 샘플 행) |
| JSON | `python -m json.tool \| head -20` (구조 확인) |
| Parquet | `python -c "import pandas; print(pandas.read_parquet('file.parquet').head())"` |
| 이미지/바이너리 | `file {{path}}` (파일 타입 확인만) |

파일이 존재하지 않으면 수집 실패.

---

## 8. 메트릭 결과 수집

### 평가 스크립트 실행

AC에 평가 방법이 명시된 경우 해당 스크립트를 실행합니다.

    # 예: "정확도 90% 이상" AC 항목
    # → 평가 스크립트 실행 후 수치 추출
    uv run python evaluate.py --output json

### 수집 결과 형식: 요약 + 실제 출력

**구조: 요약 한 줄(핵심 수치 + 목표 대비 달성 여부) → 빈 줄 → 실행 명령어(`$` 접두사) + 평가 스크립트 출력**

슈퍼바이저가 요약에서 달성 여부를 즉시 확인하고, 실제 출력에서 산출 근거를 검증할 수 있습니다.

**달성 시:**

    Accuracy: 95.2% (목표: 90% 이상) — 달성

    $ uv run python evaluate.py --output json
    {
      "accuracy": 0.952,
      "precision": 0.941,
      "recall": 0.963,
      "f1_score": 0.952,
      "total_samples": 1000,
      "correct": 952
    }

**미달성 시:**

    Accuracy: 82.3% (목표: 90% 이상) — 미달성

    $ uv run python evaluate.py --output json
    {
      "accuracy": 0.823,
      "precision": 0.801,
      "recall": 0.845,
      "f1_score": 0.823,
      "total_samples": 1000,
      "correct": 823
    }

**요약 줄 작성 규칙:**
- AC에 목표가 명시된 경우: `{{메트릭}}: {{실측값}} (목표: {{목표값}}) — 달성/미달성`
- 목표 미명시 시: `{{메트릭}}: {{실측값}}`
- 여러 메트릭이 있으면 핵심 메트릭 1개만 요약, 나머지는 실제 출력에서 확인

스크립트 경로 불명 시 수집 실패.

---

## 9. API 응답 수집

### 엔드포인트 호출

    # AC에 명시된 API 엔드포인트 호출
    curl -s -w '\n%{http_code} %{time_total}s' {{api_url}}

    # 응답 상태 코드 + 응답 시간 + 본문 주요 필드 추출

### 수집 결과 형식: 요약 + 실제 출력

**구조: 요약 한 줄 → 빈 줄 → 실행 명령어(`$` 접두사) + 실제 응답 출력**

    GET /api/v1/users → 200 OK (120ms)

    $ curl -s -w '\n%{http_code} %{time_total}s' http://localhost:8000/api/v1/users
    {
      "count": 42,
      "items": [
        {"id": 1, "name": "user1"},
        ...
      ]
    }
    200 0.120s

포함 정보:
- 요약: HTTP 메서드 + 경로 + 상태 코드 + 응답 시간
- 실제 출력: curl 명령어 + 응답 본문 전체 (1KB 이하) 또는 주요 부분 (1KB 초과 시 앞 50줄)

인증 필요 시 수집 실패로 처리하고 사용자에게 안내합니다.

---

## 10. 코드 변경 수집

AC 항목이 특정 코드 변경(리팩토링, 구현, 전환 등)을 요구하는 경우, `git diff --stat`과 주요 변경 요약으로 증빙합니다.

### 변경 범위 파악

    # 현재 브랜치에서 base 브랜치(main/develop 등) 이후의 커밋 범위 확인
    git merge-base HEAD origin/main
    # → base_commit_hash

    # AC에 특정 파일이 명시된 경우 해당 파일만
    git diff {base}..HEAD --stat -- src/specific/file.py

    # 파일 미명시 시 전체 변경
    git diff {base}..HEAD --stat

### 수집 결과 형식: 요약 + 실제 출력

**구조: 요약 한 줄 → 빈 줄 → 실행 명령어(`$` 접두사) + diff --stat 출력 + 주요 변경 요약**

    1 file changed, 14 insertions(+), 57 deletions(-)

    $ git diff 2cb3d4f..445b349 --stat -- src/core/streaming.py
     src/core/streaming.py | 71 ++++---------------------
     1 file changed, 14 insertions(+), 57 deletions(-)

    주요 변경:
    - StreamEventEmitter(Thread-safe Queue + 50ms 폴링) 완전 제거
    - WriterEmitterAdapter(get_stream_writer()) 신규 — emitter 인터페이스 래핑
    - emit_done(), mark_workflow_done(), consume() 제거

**여러 파일 변경 시:**

    5 files changed, 240 insertions(+), 207 deletions(-)

    $ git diff 2cb3d4f..445b349 --stat -- src/
     src/shared/models/vllm_chat_model.py | 89 ++++++++++++++++
     src/shared/models/llm_factory.py     | 123 ++++++++++++----
     src/core/streaming.py                | 71 ++++--------
     src/core/main_workflow.py            | 45 +++----
     app/api/endpoints.py                 | 324 ++++++++++++++++-----------
     5 files changed, 240 insertions(+), 207 deletions(-)

    주요 변경:
    - ChatVLLM(BaseChatOpenAI) 클래스 신규 구현
    - llm_factory 레지스트리 패턴 리팩토링
    - StreamEventEmitter → get_stream_writer() 전환

**주요 변경 작성 규칙:**
- 3~5개 핵심 변경 사항만 기술
- "무엇을 → 어떻게" 형식 (예: "Thread+Queue 패턴 → astream() 직접 사용")
- 단순 파일 목록이 아닌 의미 있는 변경 설명

---

## 11. 수집 실패 처리

### 실패 원인별 메시지

| 원인 | 메시지 |
|------|--------|
| 도구 미설치 (gh, glab 등) | `WARNING: {{tool}} CLI가 설치되지 않았습니다` |
| MCP 미연결 (Playwright, Confluence) | `WARNING: {{mcp}} MCP가 연결되지 않았습니다` |
| PR/MR 미생성 | `WARNING: 현재 브랜치에 PR/MR이 없습니다` |
| 파일 미존재 | `WARNING: {{path}} 경로에 파일이 없습니다` |
| 테스트 실행 실패 | `WARNING: 테스트 실행에 실패했습니다 — {{error}}` |
| glab 인증 실패 (fallback 성공) | fallback으로 토큰 확보 후 정상 진행 (WARNING 없음) |
| 인증 필요 (fallback 포함 전부 실패) | `WARNING: 인증이 필요합니다 — 수동으로 증빙을 첨부해주세요` |

### 실패 시 동작

1. 해당 AC 항목은 건너뜁니다 (체크하지 않음)
2. 콘솔에 WARNING 출력
3. 나머지 항목은 정상 진행
4. Step 7 (Apply Changes)에서 수집 성공한 항목만 업데이트
