# polestar10 지식베이스 — 사람 검토 필요 항목

ralph 종료 후 polestar10 웹에서 대조 후 수동 토글해야 하는 항목을 자동 기록합니다.

## 카테고리별 menu_path 초안 (Story 3~11 에서 자동 갱신)

_아직 비어 있습니다. Story 3 시작 시 alert 카테고리부터 채워집니다._

## 기타 자동 감지 이슈

- **pandoc flag 호환성 분기 (ralph rule #2 default-apply)**: 이 환경의 pandoc 은 2.9.2.1 로
  PRD 에 적힌 `--markdown-headings=atx` 옵션이 아직 없습니다. `convert-docx.sh` 는 런타임에
  `--help` 를 점검해서 2.11+ 에서는 PRD 그대로, 2.9.x 에서는 deprecated alias 인 `--atx-headers`
  를 사용합니다. 결과 마크다운은 동일(ATX 스타일 `#` 헤딩)이며 수동 액션 필요 없음.
