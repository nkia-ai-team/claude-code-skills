# Linear 이슈 조회 가이드

이 스킬은 PIMS API Key 대신 **Linear MCP** 로 이슈를 읽는다.

## 호출

```
mcp__linear__get_issue(id="NKIAAI-498")
```

응답에서 사용할 필드:
- `title` — 제목. 접두 코드(`[SMS-..]`)와 기능명 추출
- `description` — 본문 markdown. 메뉴 경로, AC, PR 링크
- `state.name` — 상태 (In Progress, In Review, Done…)
- `labels` — 라벨 (모듈·우선순위 힌트)
- `url` — Linear 웹 링크 (PIMS 댓글에 포함)
- `assignee.name` / `creator.name`

## 댓글 확인

description 만으로 정보 부족하면:
```
mcp__linear__list_comments(issueId="NKIAAI-498")
```
PR 링크, 디자인 결정, 추가 요구사항이 댓글에 있을 수 있음.

## 이슈 → TC 매핑 패턴

1. **제목** → 기능명 + 기능코드 추출
   - `[SMS-01-02] 서버목록 Hostname 필터 추가` → 기능코드 `SMS-01-02`, 기능 "서버목록 Hostname 필터"
2. **description** → AC(Acceptance Criteria) 항목별로 절차 1개 매핑
   - AC가 명확하면 TC 절차는 거의 그대로 따라감
3. **labels** → 모듈 좁히기 (`module:sms` → `remotes/sms`)
4. **PR 링크** → 변경 파일에서 셀렉터·라벨 확정

## 정보 부족 시

description 이 한 줄짜리거나 AC 가 없으면:
- `AskUserQuestion` 으로 메뉴 경로/대상 데이터 보완 받기
- 또는 PR diff 직접 읽기 (description 의 PR URL 우선)

## NKIAAI Linear 워크스페이스 메모

- 일반적인 이슈 prefix: `NKIAAI-` (대표), 팀에 따라 다른 prefix 도 사용
- 모듈 라벨이 붙어 있으면 `remotes/<모듈>` 매핑에 활용
- "In Review" 또는 "Done" 상태의 이슈를 대상으로 TC 작성하는 것이 일반적
