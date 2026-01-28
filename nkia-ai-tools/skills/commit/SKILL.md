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

---

## Commit Message Format

### 정규식 패턴
```regex
^[a-z]+-[0-9]+ (Feat|Fix|Refactor|Cleanup|Wip|Revert|Style|Merge|Docs|Config|Dependency|Test) : .+$
```

### 구조
```
{Linear이슈번호} {Type} : {설명}
```

| 항목 | 규칙 | 예시 |
|------|------|------|
| Linear 이슈 번호 | `{팀키}-{이슈번호}` 형식 (소문자) | `nkiaai-129` |
| Type | 허용된 타입 키워드 | `Feat` |
| 구분자 | ` : ` (공백 포함 콜론) | ` : ` |
| 설명 | 한글/영문, 명확한 설명 | `API 변경 감지 시스템 구축` |

### Type Keywords

| Type | 용도 | 변경 범위 |
|------|------|----------|
| Feat | 새로운 기능 추가 | 신규 파일/메서드 추가 |
| Fix | 오류 수정 | 버그 수정 코드 |
| Refactor | 리팩토링/성능 개선 | 기존 코드 구조 변경 |
| Cleanup | 불필요한 코드 정리 | 파일/코드 삭제 |
| Wip | 진행 중 작업 | 임시 커밋 (MR 시 지양) |
| Revert | 이전 커밋 되돌리기 | revert 작업 |
| Style | 코드 스타일 수정 | 포맷팅, 공백 등 |
| Merge | 브랜치 병합 | merge 작업 |
| Docs | 문서 변경 | .md 파일 등 |
| Config | 설정 파일 변경 | 빌드/배포 설정 |
| Test | 테스트 코드 | *Test.java, *.spec.ts 등 |

---

## Workflow

### Step 1: Check Git Status

현재 staged 변경사항 확인:

```bash
git status
git diff --cached --stat
```

**staged 변경사항이 없는 경우:**
```
커밋할 staged 변경사항이 없습니다.

다음 명령어로 파일을 staging 하세요:
$ git add <파일명>
$ git add .  # 모든 변경사항
```

### Step 2: Extract Linear Issue Number from Branch

현재 브랜치에서 Linear 이슈 번호 추출:

```bash
git branch --show-current
```

**브랜치 패턴 (Linear 자동 생성):**
```regex
^(feature|bugfix|hotfix|refactor|docs|test|config)/([a-z]+-[0-9]+)-.*$
```

**예시:**
```
브랜치: feature/nkiaai-129-api-diff-notification
Linear 이슈 번호: nkiaai-129
```

**Linear 이슈 번호를 찾을 수 없는 경우:**
사용자에게 Linear 이슈 번호 입력 요청:
```
브랜치명에서 Linear 이슈 번호를 찾을 수 없습니다.
Linear 이슈 번호를 입력해주세요 (예: nkiaai-129):
```

### Step 3: Analyze Changes

변경사항 상세 분석:

```bash
git diff --cached
git diff --cached --name-only
```

**분석 항목:**
1. 변경된 파일 목록 및 확장자
2. 추가/수정/삭제된 코드 내용
3. 주요 변경 패턴 식별

### Step 4: Determine Type Keyword

변경사항을 기반으로 적절한 Type 결정:

| 변경 패턴 | Type |
|----------|------|
| 새 파일 추가, 새 기능 구현 | Feat |
| 버그 수정, 오류 해결 | Fix |
| 기존 코드 구조 변경 (기능 동일) | Refactor |
| 파일/코드 삭제, 정리 | Cleanup |
| 문서 파일만 변경 (.md, .txt 등) | Docs |
| 설정 파일만 변경 (.yml, .json 등) | Config |
| 테스트 파일만 변경 | Test |
| 포맷팅, 공백, 세미콜론 등 | Style |

**Type 결정 우선순위:**
1. 새 기능 코드가 있으면 → `Feat`
2. 버그 수정 코드가 있으면 → `Fix`
3. 기존 코드 리팩토링이면 → `Refactor`
4. 삭제만 있으면 → `Cleanup`
5. 문서만 변경되면 → `Docs`
6. 설정만 변경되면 → `Config`
7. 테스트만 변경되면 → `Test`

### Step 5: Generate Commit Message

**메시지 생성 규칙:**
1. 한글 사용 (또는 영문 - 프로젝트 컨벤션에 따름)
2. 50자 이내 권장
3. 무엇을 했는지 명확하게 설명
4. 동사로 시작 (추가, 수정, 개선, 삭제 등)

**예시:**
```
nkiaai-129 Feat : API 변경 감지 시스템 구축
nkiaai-129 Fix : Slack 웹훅 URL 오류 수정
nkiaai-129 Refactor : TraceService 쿼리 최적화
nkiaai-129 Docs : README 설치 가이드 추가
nkiaai-129 Config : Docker 환경변수 설정 추가
```

### Step 6: Show Preview and Confirm

생성된 커밋 메시지 미리보기:

```
=== 커밋 메시지 미리보기 ===

nkiaai-129 Feat : 사용자 인증 API 엔드포인트 추가

변경 파일:
- src/api/auth.ts (+150)
- src/utils/jwt.ts (+45)
- tests/auth.test.ts (+80)

============================

이 메시지로 커밋하시겠습니까?
1. 네, 커밋 실행
2. 메시지 수정
3. 취소

선택:
```

### Step 7: Execute Commit

사용자 확인 후 커밋 실행:

```bash
git commit -m "nkiaai-129 Feat : 사용자 인증 API 엔드포인트 추가"
```

**커밋 성공 시:**
```
커밋이 완료되었습니다!

커밋: abc1234
메시지: nkiaai-129 Feat : 사용자 인증 API 엔드포인트 추가
변경: 3 files changed, 275 insertions(+)
```

---

## Error Handling

### No Staged Changes
```
커밋할 staged 변경사항이 없습니다.

변경사항을 staging 하세요:
$ git add <파일명>
```

### Not a Git Repository
```
현재 디렉토리는 Git 저장소가 아닙니다.

Git 저장소를 초기화하거나 올바른 디렉토리로 이동하세요:
$ git init
```

### Invalid Linear Issue Number
```
Linear 이슈 번호 형식이 올바르지 않습니다.
{팀키}-{이슈번호} 형식으로 입력해주세요 (예: nkiaai-129)
```

---

## Examples

### Example 1: New Feature
```
브랜치: feature/nkiaai-129-user-auth
변경: src/api/auth.ts (신규), src/models/user.ts (수정)

생성 메시지: nkiaai-129 Feat : 사용자 인증 API 구현
```

### Example 2: Bug Fix
```
브랜치: bugfix/nkiaai-130-login-error
변경: src/services/login.ts (수정)

생성 메시지: nkiaai-130 Fix : 로그인 시 세션 만료 오류 수정
```

### Example 3: Documentation
```
브랜치: docs/nkiaai-131-api-docs
변경: docs/API.md (신규), README.md (수정)

생성 메시지: nkiaai-131 Docs : API 문서 및 README 업데이트
```

### Example 4: Multiple Changes
```
브랜치: feature/nkiaai-129-api-improvement
변경:
- src/api/trace.ts (수정 - 새 엔드포인트)
- src/utils/parser.ts (수정 - 리팩토링)
- tests/trace.test.ts (신규)

생성 메시지: nkiaai-129 Feat : Trace API 엔드포인트 추가 및 파서 개선
```

---

## Options

사용자가 직접 Type을 지정할 수 있음:

```
/commit --type Fix
/commit --type Refactor 쿼리 최적화
```

Linear 이슈 번호 직접 지정:

```
/commit --linear nkiaai-129
```
