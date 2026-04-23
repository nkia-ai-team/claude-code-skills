# polestar10 지식베이스 — 사람 검토 필요 항목

ralph 종료 후 polestar10 웹에서 대조 후 수동 토글해야 하는 항목을 자동 기록합니다.

## 카테고리별 menu_path 초안 (Story 3~11 에서 자동 갱신)

_아직 비어 있습니다. Story 3 시작 시 alert 카테고리부터 채워집니다._

## 기타 자동 감지 이슈

- **pandoc flag 호환성 분기 (ralph rule #2 default-apply)**: 이 환경의 pandoc 은 2.9.2.1 로
  PRD 에 적힌 `--markdown-headings=atx` 옵션이 아직 없습니다. `convert-docx.sh` 는 런타임에
  `--help` 를 점검해서 2.11+ 에서는 PRD 그대로, 2.9.x 에서는 deprecated alias 인 `--atx-headers`
  를 사용합니다. 결과 마크다운은 동일(ATX 스타일 `#` 헤딩)이며 수동 액션 필요 없음.

### alert

**user** (29 file(s)):

| slug | menu_path (초안) | 경로 |
|---|---|---|
| alert-001 | AskLucida | manuals/user/alert/alert-001.md |
| alert-002 | SLO | manuals/user/alert/alert-002.md |
| alert-003 | SQLServer목록 | manuals/user/alert/alert-003.md |
| alert-004 | WebURL상세 | manuals/user/alert/alert-004.md |
| alert-005 | 개별알람정책 | manuals/user/alert/alert-005.md |
| alert-006 | 개인정보프로필 | manuals/user/alert/alert-006.md |
| alert-007 | 공통알람정책 | manuals/user/alert/alert-007.md |
| alert-008 | 관리대상추가 | manuals/user/alert/alert-008.md |
| alert-009 | 레이아웃 | manuals/user/alert/alert-009.md |
| alert-010 | 로그감시 | manuals/user/alert/alert-010.md |
| alert-011 | 복합알람정책 | manuals/user/alert/alert-011.md |
| alert-012 | 서버상세 | manuals/user/alert/alert-012.md |
| alert-013 | 시스로그목록 | manuals/user/alert/alert-013.md |
| alert-014 | 알람상세 | manuals/user/alert/alert-014.md |
| alert-015 | 알람심각도설정 | manuals/user/alert/alert-015.md |
| alert-016 | 알람컨디션로그표현식 | manuals/user/alert/alert-016.md |
| alert-017 | 알람패턴통보설정 | manuals/user/alert/alert-017.md |
| alert-018 | 오라클목록 | manuals/user/alert/alert-018.md |
| alert-019 | 오라클상세 | manuals/user/alert/alert-019.md |
| alert-020 | 요약대시보드 | manuals/user/alert/alert-020.md |
| alert-021 | 윈도우이벤트로그감시 | manuals/user/alert/alert-021.md |
| alert-022 | 장기예측정책 | manuals/user/alert/alert-022.md |
| alert-023 | 정적임계치 | manuals/user/alert/alert-023.md |
| alert-024 | 태그맵 | manuals/user/alert/alert-024.md |
| alert-025 | 태그트리 | manuals/user/alert/alert-025.md |
| alert-026 | 통합로그 | manuals/user/alert/alert-026.md |
| alert-027 | 트랩목록 | manuals/user/alert/alert-027.md |
| alert-028 | 포털서비스종합현황 | manuals/user/alert/alert-028.md |
| alert-029 | 포털서비스통합검색 | manuals/user/alert/alert-029.md |

> 위 `menu_path` 는 pandoc 이 추출한 md 본문 H1 제목을 그대로 초안으로 옮긴 것입니다.
> 사람이 polestar10 웹에서 대조 후 frontmatter 의 `menu_path_verified` 를 `true` 로 토글.

### perf

**user** (29 file(s)):

| slug | menu_path (초안) | 경로 |
|---|---|---|
| perf-001 | PMS | manuals/user/perf/perf-001.md |
| perf-002 | Ping감시 | manuals/user/perf/perf-002.md |
| perf-003 | SNMPOID템플릿 | manuals/user/perf/perf-003.md |
| perf-004 | SQLServer상세 | manuals/user/perf/perf-004.md |
| perf-005 | TCP포트감시 | manuals/user/perf/perf-005.md |
| perf-006 | 공유노트목록 | manuals/user/perf/perf-006.md |
| perf-007 | 공유노트상세 | manuals/user/perf/perf-007.md |
| perf-008 | 기본포트인증관리 | manuals/user/perf/perf-008.md |
| perf-009 | 대시보드생성및편집 | manuals/user/perf/perf-009.md |
| perf-010 | 로그이상감지 | manuals/user/perf/perf-010.md |
| perf-011 | 서버목록 | manuals/user/perf/perf-011.md |
| perf-012 | 성능예측 | manuals/user/perf/perf-012.md |
| perf-013 | 성능이상감지개별현황 | manuals/user/perf/perf-013.md |
| perf-014 | 성능이상감지시각화 | manuals/user/perf/perf-014.md |
| perf-015 | 성능이상감지정책 | manuals/user/perf/perf-015.md |
| perf-016 | 성능조회 | manuals/user/perf/perf-016.md |
| perf-017 | 성능조회시점분석 | manuals/user/perf/perf-017.md |
| perf-018 | 애플리케이션서비스상세 | manuals/user/perf/perf-018.md |
| perf-019 | 애플리케이션전체목록 | manuals/user/perf/perf-019.md |
| perf-020 | 윈도우서비스감시 | manuals/user/perf/perf-020.md |
| perf-021 | 윈도우성능카운터감시 | manuals/user/perf/perf-021.md |
| perf-022 | 이상감지분석 | manuals/user/perf/perf-022.md |
| perf-023 | 장기예측개별현황 | manuals/user/perf/perf-023.md |
| perf-024 | 즐겨찾기 | manuals/user/perf/perf-024.md |
| perf-025 | 토폴로지맵목록 | manuals/user/perf/perf-025.md |
| perf-026 | 토폴로지맵뷰어 | manuals/user/perf/perf-026.md |
| perf-027 | 토폴로지맵편집 | manuals/user/perf/perf-027.md |
| perf-028 | 파일감시 | manuals/user/perf/perf-028.md |
| perf-029 | 프로세스감시 | manuals/user/perf/perf-029.md |

> 위 `menu_path` 는 pandoc 이 추출한 md 본문 H1 제목을 그대로 초안으로 옮긴 것입니다.
> 사람이 polestar10 웹에서 대조 후 frontmatter 의 `menu_path_verified` 를 `true` 로 토글.
