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

```bash
/code-review https://github.com/owner/repo/pull/123
```

### linear-issue-creator
Linear 이슈를 템플릿 기반으로 빠르게 생성합니다.

```bash
/linear-issue-creator
```

### linear-issue-validator
완료된 Linear 이슈의 DoD/AC 항목을 검증하고 평가합니다.

```bash
/linear-issue-validator NKIA-123
```

### linear-project-creator
Linear 프로젝트를 체계적인 문서와 함께 생성합니다.

```bash
/linear-project-creator
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
