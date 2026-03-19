# QA Phase 워크플로우

## 개요

Dev 에이전트가 Step 7(Storybook 스토리)까지 완료하면,
컴포넌트를 화면에 통합한 후 **dev 서버에서** 독립 QA 서브에이전트 3개를 **병렬 실행**하여 검증한다.

핵심 원칙:
- **자기 테스트 금지** — Dev가 작성한 코드를 Dev가 검증하지 않는다
- **dev 서버에서 검증** — Storybook이 아닌 실제 앱 환경에서 동작을 확인한다

    Dev (Step 1~7 완료, 컴포넌트를 화면에 통합)
        ↓ dev 서버 URL + Figma 원본 이미지 + tokens.css/portal.css 경로 전달
    QA Phase (3개 병렬)
        ├── QA-기능: Playwright 기능/인터랙션/E2E 플로우 테스트
        ├── QA-시각적: Figma ↔ dev 서버 렌더링 비교
        └── QA-토큰: 디자인 토큰 정합성 검증
        ↓ 결과 종합
    QA 리포트 → 사용자 보고 (매 루프)
        ↓ FAIL 항목 존재 시
    Dev 수정 → QA 재검증 (최대 3루프)
        ↓ 3루프 후에도 미해결
    경고로 남기고 사용자에게 에스컬레이션

### Storybook이 아닌 dev 서버를 사용하는 이유

Storybook 환경에서는 실제 앱과 차이가 발생한다:
- import.meta.glob 미동작 → 아이콘 렌더링 불가
- SCSS 의존성 빌드 실패 → 관련 없는 컴포넌트가 전체 빌드를 깨뜨림
- 정적 데이터만 검증 → 실제 파일 업로드, API 연동 등 미확인
- "Storybook에서 PASS인데 dev 서버에서 안 됨" → QA를 한 의미가 없음

Storybook은 개발 참고용(variant 확인, 빠른 이터레이션)으로 유지하되,
QA 검증은 반드시 dev 서버에서 수행한다.

## QA 전 준비: 컴포넌트 화면 통합

QA Phase 진입 전에 Dev가 수행할 작업:

    1. 생성/수정한 컴포넌트를 대상 화면 코드에 통합
       - 신규: 화면 파일에 import + JSX 삽입
       - 업데이트(-u): 이미 통합되어 있으므로 추가 작업 없음
    2. dev 서버가 실행 중인지 확인 (포트 확인)
    3. 필요 시 로그인하여 대상 화면까지 Playwright로 접근 가능한지 확인

## QA 에이전트 실행

### 공통 입력 (Dev → QA)

QA 서브에이전트 생성 시 아래 정보를 프롬프트에 포함한다:

    필수 전달 정보:
    - devServerUrl: 대상 화면의 dev 서버 URL (예: http://localhost:3000/portal/ai)
    - loginInfo: dev 서버 로그인 방법 (URL, 계정 정보 또는 "로그인 불필요")
    - figmaOriginalImage: temp/visual-comparison/{ComponentName}/figma-original.png 절대경로
    - tokensCssPath: {config.tokensCssPath} 절대경로 (tokens.css)
    - portalCssPath: {config.portalCssPath} 절대경로 (portal.css)
    - componentFilePath: 생성된 컴포넌트 .tsx 파일 절대경로
    - componentName: 컴포넌트 이름 (예: NdsButton)
    - variantList: 구현된 variant 전체 목록 (tone, variant, size 등)
    - propsInterface: 컴포넌트의 props interface 전문
    - targetSelector: 대상 컴포넌트를 찾기 위한 셀렉터 힌트 (예: "[data-testid='prompt-input']")

### QA-기능 서브에이전트

    Task 도구 설정:
    - subagent_type: general-purpose
    - model: sonnet (비용 최적화)

    프롬프트 핵심:
    "너는 독립 QA 엔지니어다. 개발자가 작성한 코드를 검증한다.
     개발자의 의도가 아니라 실제 동작을 기준으로 판단한다.
     미미한 차이도 타협하지 않는다.
     dev 서버의 실제 앱 환경에서 검증한다."

#### 검증 항목

##### 렌더링 완전성
- 컴포넌트가 화면에 정상 렌더링되는지
- 모든 variant가 표시되는지 (props 변경으로 variant 전환 가능한 경우)
- disabled 상태가 동작하는지

##### 인터랙션 동작
- 클릭 이벤트 발생 여부 (onClick 콜백)
- disabled 시 클릭 차단 여부 (이벤트 미발생 + cursor: not-allowed)
- hover/focus/active 상태 전환 (Playwright hover() 후 스타일 변화 확인)
- 키보드 접근성 (Tab 이동, Enter/Space 활성화)

##### Interaction Graph 동작 검증 (Step 1.6 결과가 있는 경우)

State Machine 동작 검증:
- Interaction Graph의 각 State Machine 항목이 코드에서 실제로 동작하는지
- 예: Log 컴포넌트 클릭 → collapsed 상태 토글 확인 (Playwright)

Navigation 연결 검증:
- Navigation Map의 각 항목에 대응하는 onClick 핸들러가 존재하는지
- 클릭 시 실제로 뷰/라우트가 전환되는지
- 프로토타입 미연결(추론)인 항목: 코드에 TODO 또는 placeholder가 있는지

Overlay 동작 검증:
- Overlay Map의 각 항목에 대응하는 모달/팝오버가 열리는지
- CLOSE 액션이 있으면 닫기 동작이 구현되었는지

##### 사용자 인터랙션 플로우 E2E 검증 (CRITICAL)

정적 렌더링 확인만으로는 실제 동작을 보장할 수 없다.
dev 서버에서 실제 사용자 시나리오를 Playwright로 시뮬레이션한다.

    검증 대상 (핸들러가 있는 모든 인터랙션):
    - 파일 첨부: 클립 버튼 클릭 → 파일 선택 → 파일 카드 표시 확인
    - 이미지 프리뷰: 이미지 썸네일 클릭 → 프리뷰 오버레이 열림 → 클릭 확대 → 닫기
    - 상태 토글: 접기/펼치기 버튼 클릭 → 실제 영역 접힘/펼쳐짐
    - 삭제: 삭제 버튼 클릭 → 해당 항목 제거 확인
    - 폼 제출: 입력 → 전송 버튼 클릭 → 결과 표시

    Playwright MCP 사용:
    - browser_navigate: dev 서버 페이지로 이동
    - browser_click: 실제 UI 요소 클릭
    - browser_file_upload: 파일 선택 다이얼로그에 파일 전달
    - browser_fill_form: 입력 필드에 텍스트 입력
    - browser_take_screenshot: 상태 변화 스크린샷 캡처
    - browser_snapshot: DOM 구조 확인

    금지:
    ❌ 렌더링 존재 여부만 확인하고 PASS 처리 (실제 동작 미검증)
    ❌ 정적 데이터로 미리 채워진 상태만 검증
    ❌ 실제 핸들러 동작을 Playwright로 시뮬레이션하지 않고 PASS 처리

##### 접근성
- aria 속성 존재 (aria-disabled, aria-label 등)
- role 속성 적절성
- 포커스 표시 가시성 (focus-visible 링)

#### dev 서버 접근 방식

Playwright MCP 도구로 dev 서버에 접근한다.

    // QA-기능 접근 패턴
    1. browser_navigate로 dev 서버 로그인 페이지 이동
    2. browser_fill_form + browser_click으로 로그인
    3. browser_navigate로 대상 화면 이동
    4. browser_snapshot으로 화면 구조 확인
    5. 대상 컴포넌트 셀렉터로 요소 찾기
    6. browser_click, browser_hover 등으로 인터랙션 테스트
    7. browser_take_screenshot으로 결과 캡처

    로그인이 불필요한 경우 (개발 환경 설정):
    - 바로 대상 화면 URL로 이동

#### 결과 형식

    {
        "agent": "QA-기능",
        "items": [
            { "id": "FN-001", "name": "컴포넌트 렌더링", "status": "PASS" },
            { "id": "FN-002", "name": "파일 첨부 플로우",
              "status": "FAIL",
              "detail": "클립 버튼 클릭 후 파일 선택 다이얼로그 미표시" },
            { "id": "FN-003", "name": "disabled 클릭 차단", "status": "PASS" },
            ...
        ]
    }

### QA-시각적 서브에이전트

    Task 도구 설정:
    - subagent_type: general-purpose
    - model: opus (비전 비교 정밀도를 위해 Opus 필수)

    프롬프트 핵심:
    "너는 픽셀 단위 시각적 QA 엔지니어다.
     Figma 원본과 dev 서버의 실제 렌더링을 비교하여 모든 차이를 찾아낸다.
     '거의 비슷하다'는 PASS가 아니다. 눈에 보이는 차이가 있으면 FAIL이다.
     Playwright zoom을 사용하여 세부 영역을 확대 검증한다."

#### 검증 절차

##### 1단계: 전체 비교

Figma 원본 이미지와 dev 서버 스크린샷을 나란히 비교한다:

    1. dev 서버에서 대상 화면 스크린샷 캡처
       도구: browser_take_screenshot (browser_resize로 1920x1080 설정 후)
       저장: temp/visual-comparison/{ComponentName}/qa-visual-loop-{N}.png

    2. Figma 원본 이미지 Read
       경로: temp/visual-comparison/{ComponentName}/figma-original.png

    3. 두 이미지를 비전으로 비교하여 차이점 목록 생성

##### 2단계: Zoom 확대 검증 (CRITICAL)

전체 비교에서 의심되는 영역을 **Playwright로 확대**하여 정밀 검증한다.

    // Zoom 확대 방식
    1. 대상 요소 직접 스크린샷 (element screenshot)
       → browser_click으로 요소 선택 후 해당 영역만 캡처

    2. viewport 크기 조정하여 특정 영역 확대
       → browser_resize(width=800, height=600) 등으로 좁혀서 캡처

    확대 검증 대상 (최소):
    - 대상 컴포넌트의 핵심 UI 요소
    - 아이콘이 포함된 영역 — 아이콘 렌더링/크기/색상 확인
    - 가장 세밀한 요소 (작은 텍스트, 얇은 보더 등)

##### 3단계: 주변 컨텍스트 비교

dev 서버에서는 컴포넌트가 실제 화면에 통합된 상태이므로,
주변 컴포넌트와의 관계(간격, 정렬, 색상 조화)도 확인한다:

    비교 대상:
    - 컴포넌트와 주변 요소 사이 간격이 Figma와 일치하는지
    - 화면 내에서 컴포넌트의 위치/비율이 Figma와 일치하는지
    - 배경색과 컴포넌트 색상의 대비가 Figma와 동일한지

#### 비교 항목 (타협 금지)

    | 항목 | 검증 방식 | FAIL 기준 |
    |------|-----------|-----------|
    | 배경색 | computed backgroundColor vs Figma fill | HEX 불일치 (ΔE > 3) |
    | 텍스트색 | computed color vs Figma text fill | HEX 불일치 |
    | 보더색 | computed borderColor vs Figma stroke | HEX 불일치 |
    | 보더 두께 | computed borderWidth vs Figma strokeWeight | 1px 이상 차이 |
    | border-radius | computed borderRadius vs Figma cornerRadius | 1px 이상 차이 |
    | 패딩 | computed padding vs Figma padding | 1px 이상 차이 |
    | gap | computed gap vs Figma itemSpacing | 1px 이상 차이 |
    | 폰트 크기 | computed fontSize vs Figma fontSize | 1px 이상 차이 |
    | 폰트 굵기 | computed fontWeight vs Figma fontWeight | 값 불일치 |
    | 높이 | computed height vs Figma height | 2px 이상 차이 |
    | 아이콘 크기 | SVG 영역 크기 vs Figma 아이콘 노드 크기 | 2px 이상 차이 |
    | 아이콘 가시성 | 어두운 배경에서 아이콘 보이는지 | 보이지 않으면 FAIL |
    | 스크롤바 | Figma에 없는데 표시되는지 | 표시되면 FAIL |
    | 에셋 근사치 | 텍스트/유니코드로 대체된 것 | 존재하면 FAIL |
    | 형제 비율 | 나란한 요소의 너비 비율 | 5% 이상 차이 |
    | 중첩 패딩 | 실효 패딩 합산 | 2px 이상 차이 |

#### 결과 형식

    {
        "agent": "QA-시각적",
        "items": [
            { "id": "VS-001", "name": "primary/filled 배경색",
              "status": "FAIL",
              "expected": "#4A90D9", "actual": "#5599E2",
              "detail": "ΔE=8.3, 허용 임계값 3 초과",
              "zoomScreenshot": "temp/visual-comparison/zoom-primary-filled.png" },
            { "id": "VS-002", "name": "sm 사이즈 패딩",
              "status": "FAIL",
              "expected": "4px 8px", "actual": "4px 12px",
              "detail": "수평 패딩 4px 초과" },
            ...
        ]
    }

### QA-토큰 서브에이전트

    Task 도구 설정:
    - subagent_type: general-purpose
    - model: haiku (토큰 비교는 경량 모델로 충분)

    프롬프트 핵심:
    "너는 디자인 토큰 정합성 검증 엔지니어다.
     tokens.css + portal.css에 정의된 CSS 변수가 Tailwind 유틸리티 클래스로 올바르게 사용되었는지 검증한다.
     실제 렌더링된 스타일과 토큰 값의 일치를 확인한다.
     구 토큰명 사용, 하드코딩 HEX, Core 팔레트 직접 참조를 탐지한다.
     dev 서버에서 실제 렌더링된 스타일을 추출하여 비교한다."

#### 검증 항목

##### tokens.css + portal.css ↔ 렌더링 정합성
- 컴포넌트에서 사용한 Tailwind 유틸리티 클래스가 tokens.css/portal.css의 CSS 변수와 일치하는지
- dev 서버에서 Playwright로 실제 요소의 style을 추출하여 비교

    // 토큰 검증 — dev 서버에서 실행
    1. browser_navigate로 대상 화면 이동 (로그인 필요 시 로그인 먼저)
    2. browser_evaluate로 대상 컴포넌트의 computed style 추출:
       - backgroundColor, color, borderColor, borderRadius, fontWeight, padding, height 등
    3. tokens.css/portal.css의 CSS 변수 값과 비교

##### 금지 패턴 검사 (CRITICAL)
- 구 토큰명 사용 여부 (fill-standard-*, text-standard-*, line-standard-*, text-accent-*, fill-inverse-* 등)
- 하드코딩 HEX 임의값 (bg-[#HEX], text-[#HEX], border-[#HEX])
- Core 팔레트 직접 참조 (bg-gray-cool-500 등 — 다크 모드에서 안 바뀜)
- 컴포넌트 파일을 Grep하여 위 패턴을 자동 탐지

    금지 패턴 Grep 대상:
    - fill-standard|fill-inverse|fill-tertiary|fill-disable|fill-transparent
    - text-standard-default|text-secondary-default|text-tertiary-default
    - text-inverse-default|text-disable-default|text-accent-
    - line-standard|line-disable
    - bg-\[#|text-\[#|border-\[#  (HEX 임의값)
    - bg-gray-cool-|bg-gray-warm-|bg-blue-|bg-red-  (Core 팔레트)

##### 허용 패턴 확인
- Tailwind 유틸리티 클래스 사용 (bg-layer-01, text-text-primary 등)
- CSS 변수 참조 (var(--comp-height-md), var(--color-*) 등)
- portal.css 전용 토큰 참조 (bg-prompt-bg, bg-avatar 등)

##### 테마 검증 (다크 모드)
- data-theme="dark" 적용 시 색상이 정상 전환되는지 확인
- Playwright로 테마 전환 후 computed style 재추출하여 비교

    // 테마 검증 절차
    1. browser_evaluate로 document.documentElement.setAttribute('data-theme', 'dark') 실행
    2. 대상 컴포넌트의 computed style 재추출
    3. tokens.css의 [data-theme="dark"] 블록의 값과 비교
    4. 검증 완료 후 원래 테마로 복원

#### 결과 형식

    {
        "agent": "QA-토큰",
        "items": [
            { "id": "TK-001", "name": "bg-layer-01 렌더링 일치",
              "status": "PASS" },
            { "id": "TK-002", "name": "구 토큰명 사용 탐지",
              "status": "FAIL",
              "detail": "bg-fill-standard-default 사용 — bg-layer-01로 교체 필요" },
            { "id": "TK-003", "name": "하드코딩 HEX 탐지",
              "status": "FAIL",
              "detail": "bg-[#F3F5F7] 사용 — bg-layer-01-hover로 교체 필요" },
            { "id": "TK-004", "name": "다크 모드 전환",
              "status": "PASS",
              "detail": "data-theme='dark' 적용 시 배경/텍스트 색상 정상 전환" },
            ...
        ]
    }

## QA 결과 종합 및 사용자 보고

### 결과 종합

3개 QA 에이전트의 결과를 수집하여 하나의 리포트로 통합한다.

    통합 판정:
    - ALL PASS: 3개 에이전트 모두 PASS → QA 통과, Step 8.5 또는 Step 9로 진행
    - FAIL 존재: 하나라도 FAIL → Dev 수정 루프 진입

### 사용자 보고 (매 루프 필수)

QA 루프가 끝날 때마다 사용자에게 간단한 표로 보고한다:

    ## QA 루프 {N}/3 리포트: {ComponentName}

    | QA 에이전트 | PASS | FAIL | 주요 FAIL 항목 |
    |------------|------|------|---------------|
    | QA-기능    | 8    | 2    | 파일 첨부 플로우 실패, ghost hover 미동작 |
    | QA-시각적  | 12   | 3    | primary 배경색 ΔE=8, sm 패딩 초과, 아이콘 미표시 |
    | QA-토큰    | 5    | 1    | danger.ghost.hover 토큰 누락 |
    | **합계**   | **25** | **6** | |

    **판정: FAIL** — Dev 수정 후 재검증 진행 (루프 {N+1}/3)

    ALL PASS인 경우:

    ## QA 루프 {N}/3 리포트: {ComponentName}

    | QA 에이전트 | PASS | FAIL | 주요 FAIL 항목 |
    |------------|------|------|---------------|
    | QA-기능    | 10   | 0    | — |
    | QA-시각적  | 15   | 0    | — |
    | QA-토큰    | 6    | 0    | — |
    | **합계**   | **31** | **0** | |

    **판정: PASS** — QA 통과, Step 8.5 또는 Step 9 진행

## Dev 수정 → QA 재검증 루프

### 수정 루프 규칙

    최대 루프: 3회
    루프 1: QA FAIL → Dev 수정 → QA 재검증
    루프 2: QA FAIL → Dev 수정 → QA 재검증
    루프 3: QA FAIL → 미해결 항목 경고 + 사용자 에스컬레이션

### Dev 수정 절차

QA FAIL 항목을 Dev에게 전달하여 수정한다.

    Dev에게 전달하는 정보:
    - FAIL 항목 전체 목록 (id, name, expected, actual, detail)
    - QA-시각적의 zoom 스크린샷 경로 (있는 경우)
    - 수정 우선순위: 시각적 > 토큰 > 기능 (시각적 차이가 가장 눈에 띔)

    Dev 수정 범위:
    - QA FAIL 항목에 해당하는 코드만 수정
    - 인터페이스(props) 변경 금지

    Dev 수정 후:
    - dev 서버 HMR/hot reload 대기 (Vite/Webpack dev server)
    - QA 3개 에이전트를 다시 병렬 실행 (이전 FAIL 항목 중심으로 재검증)

### 재검증 최적화

루프 2~3에서는 이전 PASS 항목을 생략하고 FAIL 항목만 재검증할 수 있다.
단, QA-시각적은 전체 비교를 매번 수행한다 (수정이 다른 부분에 영향을 줄 수 있음).

    재검증 범위:
    - QA-기능: 이전 FAIL 항목 + 수정 영향 범위
    - QA-시각적: 전체 비교 (매번)
    - QA-토큰: 이전 FAIL 항목만

### 3루프 미해결 시 에스컬레이션

3회 수정 후에도 FAIL이 남아있으면 사용자에게 에스컬레이션한다.

    ## QA 에스컬레이션: {ComponentName}

    3회 수정 루프를 완료했으나 아래 항목이 해결되지 않았습니다.

    ### 미해결 항목
    | ID | QA | 항목 | 기대값 | 실제값 | 수정 시도 |
    |----|-----|------|--------|--------|-----------|
    | VS-001 | 시각적 | primary/filled 배경색 | #4A90D9 | #5599E2 | 3회 시도, ΔE 8→6→5.2 (임계값 3) |
    | FN-002 | 기능 | ghost hover 배경 | 색상 변화 | 변화 없음 | Headless UI 제한으로 추정 |

    ### 가능한 원인
    - VS-001: Figma 원본의 색상이 토큰과 다를 수 있음 (디자이너 확인 필요)
    - FN-002: Headless UI Button의 hover 상태 제어 방식 한계

    ### 권장 조치
    - [ ] 디자이너에게 Figma 색상 확인 요청
    - [ ] hover 구현 방식 변경 검토 (CSS :hover vs JS onMouseEnter)

    미해결 항목은 **경고(WARNING)**로 Step 10 결과 요약에 포함됩니다.
    파이프라인은 계속 진행합니다 (Step 8.5 또는 Step 9 Code Connect).

## QA 스크린샷 관리

    저장 경로:
    temp/visual-comparison/{ComponentName}/
    ├── figma-original.png          # Step 1에서 다운로드 (기존)
    ├── qa-visual-loop-1.png        # QA 루프 1 dev 서버 스크린샷
    ├── qa-visual-loop-2.png        # QA 루프 2 dev 서버 스크린샷
    ├── qa-visual-loop-3.png        # QA 루프 3 dev 서버 스크린샷
    ├── zoom-primary-filled.png     # Zoom 확대 캡처
    ├── zoom-sm-size.png            # Zoom 확대 캡처
    ├── zoom-disabled.png           # Zoom 확대 캡처
    └── zoom-icon-variant.png       # Zoom 확대 캡처

    정리:
    - QA PASS 후: 최종 루프 스크린샷만 보존할지 사용자에게 확인
    - zoom 스크린샷은 FAIL 디버깅 근거로 보존

## Step 10 결과 요약에 QA 섹션 추가

    ### QA 검증
    - 판정: PASS / PARTIAL (미해결 {N}건) / FAIL (에스컬레이션)
    - 검증 환경: dev 서버 ({devServerUrl})
    - 루프: {N}/3
    - QA-기능: {PASS}/{TOTAL} 통과
    - QA-시각적: {PASS}/{TOTAL} 통과
    - QA-토큰: {PASS}/{TOTAL} 통과
    - 미해결 경고: (있을 경우 항목 목록)
