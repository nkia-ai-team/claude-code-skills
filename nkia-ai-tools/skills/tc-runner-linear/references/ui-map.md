# lucida-ui 소스 매핑 가이드 (Linear 버전)

목적: Linear 이슈의 기능을 `./lucida-ui` 의 실제 소스로 연결해 **메뉴 라벨·필드명·셀렉터·업무 규칙**을 확보한다. TC 의 "테스트절차/예상결과" 는 추측이 아니라 **소스에서 확인한 실제 값**으로 작성한다.

## 루트

```
<LUCIDA_UI_DIR>                      ← credentials/env 로 설정 (예: ~/dev/lucida-ui)
  remotes/<모듈>/src/...              ← 기능별 화면 (대부분 여기)
  shared/                              ← 공통 컴포넌트·유틸·sirius 래퍼
  host/                                ← 셸/레이아웃/메뉴
```

다른 위치에서 작업 시 `LUCIDA_UI_DIR` 환경변수로 덮어쓰기.

## 모듈(remotes) ↔ 도메인 힌트

Linear 이슈 제목의 접두 코드(`[SMS-..]`, `[CMM-..]`, `[APM-..]` 등) 또는 기능 키워드로 모듈을 좁힌다. **출발점 힌트일 뿐, Grep 으로 실제 라벨 확인 필수.**

| remotes 모듈 | 도메인(추정) |
|-------------|------------|
| account | 로그인·사용자·역할·조직 관리 |
| management | 운영관리/메뉴 관리/기능 관리 등 공통(CMM) |
| sms | 서버 관리(서버목록 등) |
| nms | 네트워크 관리 |
| dpm / doms | DB/스토리지 성능 |
| apm / performance | 애플리케이션·성능 |
| alarm / notification | 알람·통보 |
| assets | 자원 관리 |
| automap / topology | 토폴로지·맵 |
| automation / rulechain | 룰체인·자동화 |
| dashboard / widget | 대시보드·위젯 |
| itg | 통합(ITG) |
| kcm | 쿠버네티스/컨테이너 관리 |
| lms | 라이선스 |
| metering | 미터링 |
| report | 리포트 |

## 확보 절차

1. Linear 이슈(title/description/labels)에서 기능명·메뉴 경로 추출.
2. 후보 모듈에서 Grep:
   ```
   Grep(pattern="서버목록", path="$LUCIDA_UI_DIR/remotes", glob="*.tsx")
   ```
   i18n 키(`tt('cmm.xxx')`)로 라벨을 쓰는 경우가 많으므로 키와 한글 라벨 둘 다 확인.
3. 화면 컴포넌트에서 수집:
   - 메뉴/탭/버튼 텍스트 → 절차 문구
   - input `name`/`id`, `placeholder`, AG Grid 컬럼 field → 셀렉터
   - 비활성/자동선택/유효성 규칙 → 참고사항·예상결과
4. 확신 안 서면 사용자에게 한 번 확인. 절대 추측 금지.

## 자주 쓰는 셀렉터 (sirius/AG Grid 공통 패턴)

| 대상 | 셀렉터 |
|------|--------|
| 로그인 ID | `#loginId` |
| 로그인 PW | `#password` (입력 후 Enter 로 로그인) |
| 조직 선택 박스 | `.login-body-org-content-body-list-box` |
| 사이드바 확장 | `.st-first-menu-left-button-area` |
| AG Grid 루트 | `div.ag-root` |
| AG Grid 행 | `.ag-center-cols-container .ag-row` |
| AG Grid "결과 없음" 오버레이 | `.ag-overlay-no-rows-wrapper` |
| 상세 패널 | `div.st-hybrid-detail` |

> 안정성 우선순위: `id` / `name` > 역할+텍스트(`getByRole`, `getByText`) > 안정적 className > 구조 의존 XPath(지양).

## Linear 이슈가 PR 링크를 포함할 때

description 또는 댓글에 GitHub/GitLab PR 링크가 있으면:
- PR diff 의 `remotes/<모듈>/src/` 변경 파일을 직접 Read.
- 변경된 컴포넌트의 실제 셀렉터/라벨이 TC 의 정답.
