# PIMS2(Redmine) 연동 — 인증 + 신규 이슈 생성

`scripts/redmine.mjs` 가 모든 호출을 감싼다. **API Key 우선, Basic Auth fallback** 으로 접속.

## 인증

- URL: `http://pims2.nkia.co.kr`
- 기본 계정: **sjbang** (스킬에 API key + Basic Auth 둘 다 기본값 내장)
- 우선순위: `REDMINE_API_KEY` 환경변수 → 내장 sjbang API key → Basic Auth (`REDMINE_USER`/`REDMINE_PASS`)
- 다른 계정 사용:
  ```bash
  REDMINE_API_KEY=other-key node scripts/redmine.mjs get 120248
  # 또는
  REDMINE_API_KEY= REDMINE_USER=myid REDMINE_PASS=mypw node scripts/redmine.mjs get 120248
  ```

> Basic Auth 로 JSON API 를 쓰려면 Redmine 의 "REST 웹 서비스 사용"이 켜져 있어야 한다. API Key 는 항상 가능.
> 401 이면 키/계정 또는 REST 설정 확인.

## CLI 명령

| 명령 | 설명 |
|------|------|
| `node scripts/redmine.mjs get <id>` | 이슈 JSON 조회 (`journals,children,attachments` 포함) |
| `node scripts/redmine.mjs create --project=<pid> --tracker=<tid> --subject="..." <textFile>` | **신규 이슈 생성**. stdout 에 새 이슈 ID 출력 |
| `node scripts/redmine.mjs append-desc <id> <textFile>` | 본문(description) 끝에 파일 내용 append (원본 보존) |
| `node scripts/redmine.mjs set-desc <id> <textFile>` | 본문 전체 교체 (주의) |
| `node scripts/redmine.mjs note <id> <textFile> [img...]` | 댓글 등록 + 이미지 첨부 |

## 신규 이슈 생성

```bash
node scripts/redmine.mjs create \
  --subject="[chat] 개인 대화 메모리 CRUD — Linear NKIAAI-625" \
  scripts/work/NKIAAI-625-tc.md
```

기본값 내장:
- `--project=` 기본 **494** (Polestar 10 (Lucida))
- `--tracker=` 기본 **17** (테스트케이스)
- 옵션 인자: `--category=<id>`, `--version=<id>` (마일스톤)
- 환경변수로도 덮어쓰기 가능: `PIMS_PROJECT_ID`, `PIMS_TRACKER_ID`, `PIMS_CATEGORY_ID`, `PIMS_FIXED_VERSION_ID`

성공 시 stdout: `CREATED: <id>` + `URL: http://pims2.nkia.co.kr/issues/<id>`.
이 ID 를 이후 `note` / `append-desc` 에서 사용.

> 다른 프로젝트/트래커에 만들고 싶으면 `--project=` 또는 `--tracker=` 로 덮어쓰기.
> ID 모를 때: `node scripts/redmine.mjs get <기존이슈ID>` 출력의 `project.id` / `tracker.id` 확인.

## 동작 메모

- `create` 는 `POST /issues.json` 으로 `{ issue: { project_id, tracker_id, subject, description } }` 전송.
- `append-desc` 는 현재 description 을 GET 한 뒤 `\n\n` 로 이어붙여 PUT.
- `note` 는 이미지들을 먼저 `/uploads.json` 으로 업로드해 token 받고, `notes` 와 함께 `uploads[]` 로 첨부.
- 댓글에서 첨부 이미지 인라인 노출: 텍스타일은 `!파일명.png!`, 마크다운은 `![](파일명.png)`. 불확실하면 파일명 목록만 적어도 첨부로 노출됨.

## 본문/댓글 텍스트 포맷

`good-tc-template` 의 `~~~` 블록 4섹션 포맷을 그대로 사용. Redmine 의 텍스트 포맷(텍스타일/마크다운)에 따라 `###`, `~~~` 렌더가 달라질 수 있으므로 첫 등록 후 PIMS 화면 확인.
