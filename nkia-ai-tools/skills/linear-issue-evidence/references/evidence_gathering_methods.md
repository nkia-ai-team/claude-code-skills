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

식별 불가 시 텍스트 기반 증빙으로 처리합니다.

---

## 2. PR/MR 링크 수집

### GitHub PR

    # 현재 브랜치의 PR 조회 (상태, 리뷰 정보 포함)
    gh pr list --head $(git branch --show-current) --json url,number,title,state,reviewDecision,mergedAt

    # PR이 있으면 URL + 상태 정보 추출
    # PR이 없으면 → 수집 실패 (PR 미생성 상태)

### GitLab MR

    # glab CLI로 현재 브랜치의 MR 조회
    glab mr list --source-branch $(git branch --show-current)

    # glab 미설치 시 → 수집 실패, 사용자에게 URL 직접 입력 안내

### 수집 결과 형식

URL과 함께 슈퍼바이저가 클릭 없이 판단할 수 있는 핵심 상태를 포함합니다:

    PR #42 "브랜치명 검증 패턴 수정" (MERGED, approved) https://github.com/org/repo/pull/42

포함 정보:
- PR 번호 + 제목
- 상태: `OPEN` / `MERGED` / `CLOSED`
- 리뷰: `approved` / `changes_requested` / `pending review`

---

## 3. 테스트 결과 수집

### 프로젝트 테스트 프레임워크 감지

| 감지 파일 | 프레임워크 | 실행 명령 |
|----------|----------|----------|
| `pytest.ini`, `pyproject.toml` (pytest 섹션) | pytest | `pytest --tb=short -q` |
| `package.json` (jest/vitest/mocha) | Node.js 테스트 | `npm test` 또는 `npx jest` |
| `Cargo.toml` | Rust | `cargo test` |
| `go.mod` | Go | `go test ./...` |

### 실행 및 결과 파싱

테스트 출력에서 다음 정보를 추출하여 요약합니다:

**1) 전체 결과 요약**

| 프레임워크 | 출력 패턴 | 파싱 결과 |
|-----------|----------|----------|
| pytest | `32 passed, 2 failed, 1 skipped` | passed: 32, failed: 2, skipped: 1, total: 35 |
| jest | `Tests: 2 failed, 15 passed, 17 total` | passed: 15, failed: 2, total: 17 |
| vitest | `Tests 12 passed (12)` | passed: 12, failed: 0, total: 12 |
| go test | `ok ... 1.234s`, `FAIL ...` 라인 수 집계 | passed/failed 패키지 수 |
| cargo test | `test result: ok. 8 passed; 0 failed` | passed: 8, failed: 0, total: 8 |

**2) 통과 테스트 상세**

통과한 테스트의 이름을 전부 수집합니다. 슈퍼바이저가 Linear만 보고 어떤 테스트가 통과했는지 확인할 수 있어야 합니다.

    통과 테스트:
    - test_login_success
    - test_login_redirect
    - test_session_create
    - test_session_refresh
    - test_logout

건수 제한 없이 모든 통과 테스트를 나열합니다.

**3) 실패 테스트 상세 (실패가 있는 경우)**

실패한 테스트의 이름과 실패 원인 첫 줄을 수집합니다:

    실패 테스트:
    - test_login_invalid_password: AssertionError: expected 401, got 200
    - test_session_timeout: TimeoutError: session did not expire

건수 제한 없이 모든 실패 테스트를 나열합니다.

**4) 커버리지 (있는 경우)**

| 프레임워크 | 커버리지 플래그 | 출력 패턴 |
|-----------|---------------|----------|
| pytest | `--cov` | `TOTAL ... 85%` |
| jest | `--coverage` | `All files ... 85.3%` |
| vitest | `--coverage` | `All files ... 85.3%` |

커버리지 옵션이 프로젝트 설정에 포함되어 있으면 자동으로 수집합니다. 없으면 생략.

**5) 테스트 케이스 문서 연관 (있는 경우)**

프로젝트에 테스트 케이스 문서가 있으면 (CLAUDE.md 테스트 규칙 참조) 테스트 ID별 결과를 매핑합니다:

    [TC-AUTH-001] 로그인 성공 테스트 ✅
    [TC-AUTH-002] 잘못된 비밀번호 테스트 ❌ — AssertionError
    [TC-AUTH-003] 세션 만료 테스트 ✅

### 수집 결과 형식

**전체 통과 시:**

    pytest 5/5 passed (coverage: 85%)
    통과: test_login_success, test_login_redirect, test_session_create, test_session_refresh, test_logout

**실패 포함 시:**

    pytest 3/5 passed, 2 failed (coverage: 85%)
    통과: test_login_success, test_login_redirect, test_session_create
    실패: test_login_invalid_password (AssertionError), test_session_timeout (TimeoutError)

**테스트 케이스 문서 연관 시:**

    pytest 32/32 passed (coverage: 85%)
    [TC-AUTH-001] 로그인 성공 테스트 ✅
    [TC-AUTH-002] 잘못된 비밀번호 테스트 ❌ — AssertionError
    [TC-AUTH-003] 세션 만료 테스트 ✅

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

    # glab CLI로 파이프라인 조회
    glab ci list --branch $(git branch --show-current)

### Jenkins

    # Jenkins URL이 AC에 명시된 경우 해당 URL 사용
    # 미명시 시 수집 불가 → 수집 실패

### 수집 결과 형식

URL과 함께 빌드 성공 여부를 바로 확인할 수 있는 정보를 포함합니다:

    CI "Build & Test" success (2m 34s) https://github.com/org/repo/actions/runs/12345678

포함 정보:
- 워크플로우 이름
- 결과: `success` / `failure` / `cancelled`
- 소요 시간

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

### 파일 존재 확인

    # AC에 명시된 경로 또는 패턴으로 확인
    ls -la {{expected_path}}

    # 데이터 건수 확인 (CSV/JSONL 등)
    wc -l {{data_file}}

    # 파일 크기, 수정 시간 확인
    stat --format='%s bytes, modified %y' {{data_file}}

### 수집 결과 형식

건수와 함께 파일이 실제로 최근 생성된 것인지 확인할 수 있는 정보를 포함합니다:

    /data/output/result.csv (1,024건, 2.3MB, 2026-03-01 수정)

파일이 존재하지 않으면 수집 실패.

---

## 8. 메트릭 결과 수집

### 평가 스크립트 실행

AC에 평가 방법이 명시된 경우 해당 스크립트를 실행합니다.

    # 예: "정확도 90% 이상" AC 항목
    # → 평가 스크립트 실행 후 수치 추출
    uv run python evaluate.py --output json

### 수집 결과 형식

    Accuracy: 95.2% (목표: 90%)

스크립트 경로 불명 시 수집 실패.

---

## 9. API 응답 수집

### 엔드포인트 호출

    # AC에 명시된 API 엔드포인트 호출
    curl -s -w '\n%{http_code} %{time_total}s' {{api_url}}

    # 응답 상태 코드 + 응답 시간 + 본문 주요 필드 추출

### 수집 결과 형식

상태 코드와 함께 응답 본문의 핵심 필드를 포함하여 올바른 데이터가 반환되는지 확인할 수 있게 합니다:

    GET /api/v1/users → 200 OK (120ms), 응답: {count: 42, items: [...]}

포함 정보:
- HTTP 메서드 + 경로
- 상태 코드
- 응답 시간
- 응답 본문 요약 (최상위 키 + 건수/길이, 200자 이내)

인증 필요 시 수집 실패로 처리하고 사용자에게 안내합니다.

---

## 10. 수집 실패 처리

### 실패 원인별 메시지

| 원인 | 메시지 |
|------|--------|
| 도구 미설치 (gh, glab 등) | `WARNING: {{tool}} CLI가 설치되지 않았습니다` |
| MCP 미연결 (Playwright, Confluence) | `WARNING: {{mcp}} MCP가 연결되지 않았습니다` |
| PR/MR 미생성 | `WARNING: 현재 브랜치에 PR/MR이 없습니다` |
| 파일 미존재 | `WARNING: {{path}} 경로에 파일이 없습니다` |
| 테스트 실행 실패 | `WARNING: 테스트 실행에 실패했습니다 — {{error}}` |
| 인증 필요 | `WARNING: 인증이 필요합니다 — 수동으로 증빙을 첨부해주세요` |

### 실패 시 동작

1. 해당 AC 항목은 건너뜁니다 (체크하지 않음)
2. 콘솔에 WARNING 출력
3. 나머지 항목은 정상 진행
4. Step 7 (Apply Changes)에서 수집 성공한 항목만 업데이트
