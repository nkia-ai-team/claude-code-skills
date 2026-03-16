---
name: commit
description: Generate commit messages following NKIA team conventions. Analyzes staged changes and creates properly formatted commit messages with Linear issue number, type keyword, and clear description. Use this skill when you want to commit changes with a well-structured message.
---

# Commit Message Generator Skill

## Overview

Git 커밋 시 NKIA 팀 컨벤션에 맞는 커밋 메시지를 자동 생성합니다.

**주요 기능:**
- Staged 변경사항 분석
- Linear 이슈 번호 자동 추출 (브랜치명에서)
- Type 키워드 자동 결정
- 명확하고 간결한 커밋 메시지 생성

## Usage

```
/commit
```

또는 메시지 힌트와 함께:
```
/commit API 엔드포인트 추가
```

**Options:**

| 옵션 | 설명 |
|-----|------|
| `--type <Type>` | Type 키워드 직접 지정 (예: `--type Fix`) |
| `--linear <id>` | Linear 이슈 번호 직접 지정 (예: `--linear nkiaai-129`) |
| `--format ui` | UI 레포 (lucida-ui) 커밋 메시지 형식 사용 |

---

## Commit Message Format

### 제목

```regex
^[a-z]+-[0-9]+ (Feat|Fix|Refactor|Cleanup|Wip|Revert|Style|Merge|Docs|Config|Dependency|Test) : .+$
```

**구조:** `{Linear이슈번호} {Type} : {설명}`

**예시:** `nkiaai-129 Feat : API 변경 감지 시스템 구축`

### UI 레포 형식 (`--format ui`)

```regex
^#[0-9]+ (Feat|Fix|Refactor|Cleanup|Wip|Revert|Style|Merge|Docs|Config|Dependency|Test) : .+ [a-z]+-[0-9]+$
```

**구조:** `#{PIMS} {Type} : {설명} {Linear이슈번호}`

**예시:** `#117864 Feat : reasoning/answer 스트리밍 구현 nkiaai-306`

UI 레포 브랜치(`develop-ui-chat-*`)에는 Linear 이슈 번호가 없으므로, 최초 커밋 시 사용자에게 PIMS 번호와 Linear 이슈 번호를 한 번 확인하고 이후 같은 세션에서는 재사용합니다.

### 본문

제목 아래에 빈 줄 하나를 두고 본문을 작성한다.

**규칙:**
- 각 줄은 `- `로 시작하는 불릿
- **파일 단위가 아닌 변경 단위**로 작성 (파일 10개를 바꿔도 논리적 변경이 3개면 3줄)
- 간결하게 작성 — **"무엇을"** 했는지만 기술 ("왜"는 이슈 번호로 추적)

**본문 생략 조건:**
- 단일 파일 수정이고 제목만으로 충분한 경우 (예: typo 수정, config 값 변경)
- Type이 `Style`, `Config`, `Cleanup`이고 변경이 단순한 경우

**예시:**
```
nkiaai-129 Feat : 사용자 인증 API 엔드포인트 추가

- JWT 기반 인증 미들웨어 추가
- 로그인/로그아웃 API 엔드포인트 구현
- User 모델에 refreshToken 필드 추가
```

### Type Keywords

| Type | 용도 |
|------|------|
| Feat | 새로운 기능 추가 |
| Fix | 오류 수정 |
| Refactor | 리팩토링/성능 개선 |
| Cleanup | 불필요한 코드 정리 |
| Wip | 진행 중 작업 (MR 시 지양) |
| Revert | 이전 커밋 되돌리기 |
| Style | 코드 스타일 수정 |
| Merge | 브랜치 병합 |
| Docs | 문서 변경 |
| Config | 설정 파일 변경 |
| Test | 테스트 코드 |

---

## Workflow

1. **Check Git Status** — staged 변경사항 확인 (`git status`, `git diff --cached --stat`)
2. **Extract Linear Issue Number** — 브랜치명에서 자동 추출 (패턴: `{prefix}/{team-key}-{number}-*`)
3. **Analyze Changes** — `git diff --cached`로 변경사항 상세 분석
4. **Determine Type** — 변경 패턴 기반 Type 자동 결정
5. **Generate Message** — 제목(한글, 50자 이내, 동사로 시작) + 본문(변경 단위 불릿 리스트, 단순 변경 시 생략)
6. **Preview and Confirm** — 미리보기 후 사용자 확인
7. **Execute Commit** — `git commit -m "..."` 실행

상세는 [commit_workflow.md](references/commit_workflow.md) 참조 — Step별 상세 설명, Type 결정 규칙, 예시, 에러 처리

---

## Resources

- [commit_workflow.md](references/commit_workflow.md) — 워크플로우 상세 (Step 1-7), Type 결정 우선순위, 에러 처리, 커밋 예시
