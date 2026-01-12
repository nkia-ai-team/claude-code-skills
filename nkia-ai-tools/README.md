# NKIA-AI Tools Plugin

NKIA-AI 팀 개발 워크플로우를 위한 Claude Code 플러그인입니다.

## 포함된 스킬

### 1. Code Review (`/code-review`)

GitHub PR / GitLab MR 자동 코드 리뷰 수행

**사용법:**
```
/code-review <PR/MR URL>
```

**예시:**
```
/code-review https://github.com/owner/repo/pull/123
/code-review https://gitlab.com/owner/repo/-/merge_requests/456
```

**주요 기능:**
- 브랜치명 검증
- 커밋 메시지 검증
- 코드 품질 분석 (Clean Code, SOLID)
- 보안 취약점 탐지 (OWASP Top 10)
- 성능 이슈 탐지
- PR/MR에 리뷰 코멘트 자동 작성

### 2. Linear Issue Validator (`/linear-issue-validator`)

Linear 이슈의 DoD/AC 항목 검증

**사용법:**
```
/linear-issue-validator <issue-id-or-url>
```

**예시:**
```
/linear-issue-validator NKIA-123
/linear-issue-validator https://linear.app/nkia-ai/issue/NKIA-123
```

**주요 기능:**
- DoD/AC 항목별 결과물 검증
- 다양한 증거 유형 지원 (URL, PR, CI/CD, 이미지 등)
- 검증 결과 이슈 코멘트 작성
- 체크박스 자동 업데이트
- "In Review" 상태 전환 (선택)

## 설치 방법

### 방법 1: 로컬 설치
```bash
# 프로젝트 루트에서
cp -r .claude/plugins/nkia-ai-tools ~/.claude/plugins/
```

### 방법 2: GitHub에서 설치 (마켓플레이스 등록 후)
```
/plugin install nkia-ai/claude-code-plugins
```

## 요구사항

### Code Review
- GitHub CLI (`gh`) 또는 GitLab CLI (`glab`) 설치 및 인증

### Linear Issue Validator
- Linear MCP 서버 연결

## 라이선스

MIT License
