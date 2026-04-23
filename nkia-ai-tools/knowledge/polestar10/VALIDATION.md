# polestar10 지식베이스 검증

## 1. 자동 검증 (ralph 완료)

### 1.1 파일 수 집계

| type | category | md 개수 | 분류표 기대값 | 일치 |
|---|---|---|---|---|
| _pending_ | _Story 15 에서 갱신됨_ |  |  |  |

### 1.2 frontmatter 스키마

| 파일 | 6개 필수 키 전부 존재 |
|---|---|
| _pending_ |  |

### 1.3 에이전트 install-spec 스키마

| agent | yq 파싱 | 필수 키 5개 | amd64/arm64 method 유효 |
|---|---|---|---|
| wpm | _pending_ | _pending_ | _pending_ |
| apm | _pending_ | _pending_ | _pending_ |
| kcm | _pending_ | _pending_ | _pending_ |
| sms | _pending_ | _pending_ | _pending_ |

## 2. 사람 확인 필요 (ralph 범위 밖)

> polestar10 웹 화면 대조 필요. ralph 종료 후 별도 세션에서 사용자가 채움.

### 2.1 대표 질문 세트 (20개)

| # | 질문 | expert 답변(초안) | 실제 웹 확인 | 비고 |
|---|---|---|---|---|
| 1 | 개별 알람 정책은 어떻게 추가해? | _미작성_ | _미확인_ |  |

### 2.2 menu_path 배치 검수

> 카테고리별 `menu_path_verified: false` 인 항목 사람이 웹에서 대조 후 `true` 로 토글.
> 상세 목록은 `REVIEW_NEEDED.md` 참조.
