# Kickoff Workflow — 브랜치 생성 규칙

## 1. 레포 유형 판별

현재 작업 디렉토리의 레포 특성으로 자동 판별합니다.

| 판별 기준 | 레포 유형 |
|-----------|----------|
| `develop-ui` 브랜치 존재 + `package.json`에 UI 프레임워크 (Vue, React 등) | UI 레포 |
| 그 외 | 일반 레포 |

판별 명령:

    # develop-ui 브랜치 존재 확인
    git branch -a | grep develop-ui

    # package.json에 UI 프레임워크 확인
    cat package.json | grep -E '"vue"|"react"|"angular"|"nuxt"|"next"'

---

## 2. 일반 레포 브랜치 — `{prefix}/{team-key}-{no}-{slug}`

### Label → Prefix 매핑

| Label | Prefix |
|-------|--------|
| `feature` | `feature/` |
| `improve` | `feature/` |
| `bug` | `fix/` |
| `refactor` | `refactor/` |
| `research` | `feature/` |
| `build` | `config/` |
| `data` | `feature/` |
| `document` | `docs/` |
| 기타/없음 | `feature/` |

### Slug 생성

이슈 제목에서 핵심 키워드를 추출하여 kebab-case로 변환합니다.

**변환 규칙:**
1. 이슈 제목에서 프로젝트명 접두사 제거 (예: "Chat AI: " → "")
2. 한글 키워드는 영문 번역
3. kebab-case 변환 (소문자, 단어 사이 `-`)
4. 5단어 이내로 축약

**예시:**
- "Chat AI: streaming 구조 리팩토링 (WriterEmitterAdapter 전환)" → `streaming-writer-emitter-adapter`
- "프롬프트 입력 시 감사 이력 기록 (Audit Trail API 연동)" → `audit-trail-api`
- "모델 선택 드롭다운 UI 개선" → `model-dropdown-ui-improvement`

### 브랜치 생성

    git checkout -b {prefix}/{team-key}-{no}-{slug}
    # 예: git checkout -b refactor/nkiaai-305-streaming-writer-emitter-adapter

---

## 3. UI 레포 브랜치 — `develop-ui-chat-{function}`

### 계층 구조

    master → develop → develop-ui → develop-ui-chat → develop-ui-chat-{function}

module은 `chat` 고정이므로 사용자에게 확인하지 않습니다.

### Function 추론

이슈 제목에서 핵심 기능을 추출하여 camelCase로 변환합니다.

**변환 규칙:**
1. 이슈 제목에서 프로젝트명 접두사 제거
2. 핵심 기능 키워드 1~3개 추출
3. camelCase 변환

**예시:**
- "프롬프트 입력 시 감사 이력 기록" → `auditTrail`
- "스트리밍 구조 리팩토링" → `streamingRefactor`
- "모델명 표시 기능 추가" → `modelNameDisplay`
- "reasoning/answer 스트리밍 및 tool_call UI 구현" → `reasoningStreaming`

### 브랜치 생성

    git checkout -b develop-ui-chat-{function}
    # 예: git checkout -b develop-ui-chat-auditTrail

### 주의사항

- UI 레포에서는 Linear 이슈 번호가 브랜치명에 포함되지 않음
- Linear 이슈 번호는 **커밋 메시지**에 포함됨

---

## 4. 타겟 브랜치 판별 (참고)

kickoff에서는 직접 사용하지 않지만, `/submit` 스킬에서 사용하는 타겟 브랜치 기본값:

| 레포 | 기본 타겟 |
|------|----------|
| lucida-ui | `develop-ui-chat` |
| lucida-chat-ap | `develop` |
| lucida-chat-ai | `develop-sandbox` |
| 기타 | `develop` |

---

## 5. 에러 처리

### 이슈를 찾을 수 없는 경우

    이슈 {issue-id}를 찾을 수 없습니다.
    이슈 ID를 확인해주세요 (예: NKIAAI-305)

### 브랜치가 이미 존재하는 경우

    브랜치 '{branch-name}'이 이미 존재합니다.
    기존 브랜치로 전환할까요?

기존 브랜치로 전환 여부를 `AskUserQuestion`으로 확인합니다.

### Git 저장소가 아닌 경우

    현재 디렉토리는 Git 저장소가 아닙니다.
    프로젝트 디렉토리로 이동한 후 다시 시도해주세요.
