# NKIA-AI Claude Code Skills

NKIA-AI 팀의 Claude Code 플러그인 마켓플레이스입니다.

## 설치 방법

```bash
# 1. 마켓플레이스 등록 (최초 1회)
/plugin marketplace add nkia-ai-team/claude-code-skills

# 2. 플러그인 설치
/plugin install nkia-ai-tools@nkia-ai-marketplace

# 3. Claude Code 재시작
```

## 포함된 스킬

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
# GitHub 사용 시
brew install gh
gh auth login

# GitLab 사용 시
brew install glab
glab auth login                                    # gitlab.com
glab auth login --hostname cims2.nkia.net:8443    # 회사 GitLab
```

**사용 예시:**
```bash
# GitHub PR 리뷰
/code-review https://github.com/owner/repo/pull/123

# GitLab MR 리뷰 (회사 GitLab)
/code-review https://cims2.nkia.net:8443/gitlab/lucida-domain-wpm/-/merge_requests/13

# 특정 영역 집중 리뷰
/code-review <URL> --focus security      # 보안만 집중
/code-review <URL> --focus performance   # 성능만 집중
/code-review <URL> --focus quality       # 코드 품질만 집중
```

---

### linear-issue-creator

Linear 이슈를 템플릿 기반으로 빠르게 생성합니다.

**주요 기능:**
- 8가지 작업 템플릿 지원 (빌드/배포, 데이터 작업, 평가, 기능 개발, 기능 개선, 리팩토링, 리서치, 버그 수정)
- 자연어 입력으로 이슈 자동 생성
- DoD (Definition of Done) / AC (Acceptance Criteria) 자동 생성
- 마감일 기반 사이클 자동 배정
- 작업 타입별 라벨 자동 적용

**사용 예시:**
```bash
# Auto Mode (자연어)
"chat ai llm모델을 aws bedrock 모델로 변경해야되는데 기간은 11월 30일까지야 담당자는 나야"
→ AI가 자동으로 이슈 구조화 및 생성

# Manual Mode (단계별 입력)
/linear-issue-creator
→ 템플릿 선택 및 상세 정보 입력
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
# 이슈 ID로 검증
/linear-issue-validator NKIA-123

# 이슈 URL로 검증
/linear-issue-validator https://linear.app/nkia-ai/issue/NKIA-123

# 옵션
/linear-issue-validator NKIA-123 --strict       # 모든 항목 통과 필수
/linear-issue-validator NKIA-123 --skip-move    # 상태 변경 스킵
/linear-issue-validator NKIA-123 --dod-only     # DoD만 검증
/linear-issue-validator NKIA-123 --ac-only      # AC만 검증
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
# 기본 사용 (자동 분석)
/commit

# 메시지 힌트와 함께
/commit API 엔드포인트 추가

# Type 직접 지정
/commit --type Fix

# PIMS 번호 직접 지정
/commit --pims 114667
```

---

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
→ 프로젝트 정보 입력 및 자동 문서 생성
```

---

### confluence-manager

Confluence 문서를 검색, 조회, 생성, 수정합니다.

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

## 업데이트

```bash
# 마켓플레이스 업데이트
/plugin marketplace update nkia-ai-marketplace

# 플러그인 업데이트
/plugin update nkia-ai-tools@nkia-ai-marketplace
```

## 라이선스

MIT
