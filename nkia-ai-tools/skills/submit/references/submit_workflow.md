# PR/MR 메타데이터와 플랫폼 절차

[submit](../SKILL.md)의 Evidence·Validation Gate 통과 후 사용한다. 본문과 댓글은 [출력 템플릿](templates.md)을 따른다.

## 1. 제목과 담당자

- 저장소의 최신 PR/MR 규칙·필수 템플릿과 사용자 지정 값을 우선한다.
- 일반 NKIA 저장소는 `{Linear 이슈 ID} {제품·화면·서비스와 변경 결과}` 형식을 기본으로 한다. 이슈는 입력·브랜치·커밋에서 식별하고 브랜치에 ID가 없다는 이유로 새 이슈를 만들지 않는다.
- `lucida-ui`는 저장소 규칙에 따라 `#{PIMS} {Type} : {설명} {Linear ID}`를 사용한다. `/commit --format ui`에서 확인한 번호를 재사용한다.
- `lucida-next`의 제목·커밋 규칙은 `docs/05-개발가이드/거버넌스/README.md`가 연결하는 정본에서 확인한다. 한글·영문 prefix를 고정 가정하지 않는다.
- assignee는 CLI 인증 계정 본인으로 지정하며 사용자 지정 값이 있으면 따른다.

## 2. 통합 대상 브랜치

1. 사용자의 명시 대상과 저장소 정본을 대조한다.
2. 기존 PR/MR이 있으면 실제 base/target을 확인한다. kickoff에서 사용한 base 기록과 현재 원격 브랜치도 확인한다.
3. 버전별 develop을 쓰는 저장소는 kickoff의 실제 base를 사용한다. 사이클 변경 후 최신 버전이라는 이유로 기존 작업의 대상을 바꾸지 않는다.
4. main 중심 저장소는 실제 main/default branch를 확인한다. 모든 저장소에 `develop` 또는 `develop-sandbox`를 기본 적용하지 않는다.
5. 불명확하거나 기록이 충돌하면 필요한 대상만 확인하고 생성·push를 보류한다.

## 3. 인증·기존 PR/MR 조회

[code-review 플랫폼 절차](../../code-review/references/platform_operations.md)의 URL 파싱·인증·페이지네이션을 따른다. 저장된 CLI 인증을 사용하고 토큰 원문을 출력하지 않는다.

```bash
gh pr list --head "{branch}" --state open --json url,number,isDraft,baseRefName,headRefOid
# GitLab: URL에서 검증한 hostname과 실제 project ID로 조회
GITLAB_HOST={hostname} glab api "/projects/{id}/merge_requests?source_branch={branch}&state=opened&per_page=100"
```

현재 저장소·source·target에 대응하는 열린 PR/MR을 재사용한다. 닫힌 PR/MR이나 다른 작업의 PR/MR을 임의 재개하지 않는다. 생성 응답이 불확실하면 조회로 성공 여부를 확인하고 중복 생성하지 않는다.

## 4. Draft 생성·Ready 전환

본문은 템플릿에 따라 임시 UTF-8 파일에 작성한다. 제목·브랜치·경로는 shell 인자로 안전하게 인용하며 본문을 명령 문자열로 실행하지 않는다.

```bash
gh pr create --draft --title "{title}" --body-file "{body_path}" \
  --base "{target}" --head "{branch}" --assignee @me
```

GitLab은 현재 CLI/API의 Draft 기능을 사용한다. 제목 접두사가 Draft 표시에 쓰이면 `Draft: {title}`로 생성하고 상태를 재조회한다. `glab api`의 description은 본문을 읽은 구조화 JSON 입력으로 전달하며 안전하게 직렬화한다. project ID·source·target·title·description·assignee ID를 저장한다.

생성·재사용 후 Linear에 실제 URL을 직접 연결하고 attachments에서 재조회한다. 기존 같은 URL은 중복 등록하지 않는다.

Ready 전환은 현재 SHA의 AC PASS·리뷰 PASS·Critical 0·Warning 0·충돌 없음·필수 CI 통과를 확인한 뒤에만 수행한다. GitHub는 `gh pr ready`, GitLab은 실제 제공하는 Ready 기능을 사용한다. 해제 후 Draft·SHA·병합 조건을 다시 조회한다. 자동 approve·merge는 수행하지 않는다.

## 5. 본문 판정과 재시도

- `# MR 코드 리뷰 결과`로 시작하는 댓글 하나에서 현재 head SHA·본문 전체 판정·상세 지적·차단 사유를 함께 확인한다. 제목의 아이콘 또는 옛 `승인` 문자열만으로 통과시키지 않는다.
- 현재 SHA 판정이 없거나 본문이 상충하거나 읽지 못한 diff·충돌·필수 검사 차단이 있으면 통과시키지 않는다. 별도 기계용 판정 블록은 생성하지 않는다.
- 자동 수정은 `autofix-safe`만 수행한다. `manual-required`·`owner-decision`은 원인과 필요한 판단을 보고한다. 수정·재검증은 최대 3회다.
- push 실패는 원인을 확인한다. 원격 새 커밋이 있으면 내용을 읽고 작업 범위와 충돌을 확인한 뒤 안전한 rebase를 수행하며 force push로 우회하지 않는다.
