# QA Phase 워크플로우

## 개요

Dev 에이전트가 Step 7(Storybook 스토리)까지 완료하면,
독립 QA 서브에이전트 3개를 Task 도구로 **병렬 실행**하여 검증한다.

핵심 원칙: **자기 테스트 금지** — Dev가 작성한 코드를 Dev가 검증하지 않는다.
QA 에이전트는 Dev의 컨텍스트를 공유하지 않고, 독립적으로 검증한다.

    Dev (Step 1~7 완료)
        ↓ Storybook URL + Figma 원본 이미지 + tokens.json 경로 전달
    QA Phase (3개 병렬)
        ├── QA-기능: Playwright 기능/인터랙션/접근성 테스트
        ├── QA-시각적: Figma ↔ Storybook 픽셀 단위 비교
        └── QA-토큰: 디자인 토큰 정합성 검증
        ↓ 결과 종합
    QA 리포트 → 사용자 보고 (매 루프)
        ↓ FAIL 항목 존재 시
    Dev 수정 → QA 재검증 (최대 3루프)
        ↓ 3루프 후에도 미해결
    경고로 남기고 사용자에게 에스컬레이션

## QA 에이전트 실행

### 공통 입력 (Dev → QA)

QA 서브에이전트 생성 시 아래 정보를 프롬프트에 포함한다:

    필수 전달 정보:
    - storybookUrl: http://localhost:{config.storybookPort}/iframe.html?id={story-id}&viewMode=story
    - storybookAllVariantsUrl: AllVariants 스토리 URL
    - figmaOriginalImage: temp/visual-comparison/{ComponentName}/figma-original.png 절대경로
    - tokensJsonPath: {config.tokensPath} 절대경로
    - designTeamTokensPath: {config.designTeamTokens} 절대경로 (있는 경우)
    - componentFilePath: 생성된 컴포넌트 .tsx 파일 절대경로
    - componentName: 컴포넌트 이름 (예: NdsButton)
    - variantList: 구현된 variant 전체 목록 (tone, variant, size 등)
    - propsInterface: 컴포넌트의 props interface 전문

### QA-기능 서브에이전트

    Task 도구 설정:
    - subagent_type: general-purpose
    - model: sonnet (비용 최적화)

    프롬프트 핵심:
    "너는 독립 QA 엔지니어다. 개발자가 작성한 코드를 검증한다.
     개발자의 의도가 아니라 실제 동작을 기준으로 판단한다.
     미미한 차이도 타협하지 않는다."

#### 검증 항목

##### 렌더링 완전성
- 모든 variant 조합이 렌더링되는지 (AllVariants 스토리에서 갯수 확인)
- disabled 상태가 모든 variant에서 동작하는지
- 사이즈별 렌더링이 누락 없는지

##### 인터랙션 동작
- 클릭 이벤트 발생 여부 (onClick 콜백)
- disabled 시 클릭 차단 여부 (이벤트 미발생 + cursor: not-allowed)
- hover/focus/active 상태 전환 (Playwright hover() 후 스타일 변화 확인)
- 키보드 접근성 (Tab 이동, Enter/Space 활성화)

##### 접근성
- aria 속성 존재 (aria-disabled, aria-label 등)
- role 속성 적절성
- 포커스 표시 가시성 (focus-visible 링)

#### Playwright 실행 방식

browser_run_code를 사용하되, 반드시 #storybook-root 하위에서만 셀렉터를 사용한다.

    // QA-기능 테스트 코드 패턴
    async (page) => {
        await page.goto(storybookUrl, { waitUntil: 'networkidle', timeout: 15000 })
        await page.waitForSelector('#storybook-root', { timeout: 10000 })

        const root = page.locator('#storybook-root')

        // 렌더링 확인
        const buttons = root.locator('button')
        const count = await buttons.count()

        // 인터랙션 확인
        const firstButton = buttons.first()
        await firstButton.hover()
        const hoverBg = await firstButton.evaluate(el =>
            getComputedStyle(el).backgroundColor
        )

        // disabled 확인
        const disabledButton = root.locator('button[disabled]').first()
        const cursor = await disabledButton.evaluate(el =>
            getComputedStyle(el).cursor
        )

        return { count, hoverBg, cursor }
    }

#### 결과 형식

    {
        "agent": "QA-기능",
        "items": [
            { "id": "FN-001", "name": "Default 렌더링", "status": "PASS" },
            { "id": "FN-002", "name": "AllVariants 갯수", "status": "FAIL",
              "expected": 60, "actual": 48,
              "detail": "ghost+danger, ghost+secondary 조합 누락" },
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
     Figma 원본과 Storybook 렌더링을 비교하여 모든 차이를 찾아낸다.
     '거의 비슷하다'는 PASS가 아니다. 눈에 보이는 차이가 있으면 FAIL이다.
     Playwright zoom을 사용하여 세부 영역을 확대 검증한다."

#### 검증 절차

##### 1단계: 전체 비교

Figma 원본 이미지와 Storybook 스크린샷을 나란히 비교한다:

    1. Storybook Default 스토리 스크린샷 캡처
       도구: browser_take_screenshot
       저장: temp/visual-comparison/{ComponentName}/qa-visual-loop-{N}.png

    2. Figma 원본 이미지 Read
       경로: temp/visual-comparison/{ComponentName}/figma-original.png

    3. 두 이미지를 비전으로 비교하여 차이점 목록 생성

##### 2단계: Zoom 확대 검증 (CRITICAL)

전체 비교에서 의심되는 영역 + 주요 variant를 **Playwright zoom으로 확대**하여 정밀 검증한다.

    // Zoom 확대 방식: CSS transform으로 특정 영역 확대
    async (page) => {
        await page.goto(storybookUrl, { waitUntil: 'networkidle', timeout: 15000 })
        await page.waitForSelector('#storybook-root', { timeout: 10000 })

        // 방법 1: 특정 요소를 확대 스크린샷
        const target = page.locator('#storybook-root button').first()
        await target.screenshot({ path: 'temp/visual-comparison/zoom-button-1.png' })

        // 방법 2: 페이지 전체를 200% 확대 후 캡처
        await page.evaluate(() => {
            document.querySelector('#storybook-root').style.transform = 'scale(2)'
            document.querySelector('#storybook-root').style.transformOrigin = 'top left'
        })
        await page.screenshot({ path: 'temp/visual-comparison/zoom-2x.png' })

        // 방법 3: viewport를 좁혀서 특정 variant만 캡처
        await page.setViewportSize({ width: 400, height: 200 })
        await page.screenshot({ path: 'temp/visual-comparison/zoom-variant.png' })
    }

    확대 검증 대상 (최소):
    - 각 tone별 대표 variant 1개씩 (primary, secondary, danger 등)
    - disabled 상태 1개
    - 가장 작은 사이즈 (sm) — 작은 사이즈에서 차이가 두드러짐
    - 아이콘이 포함된 variant (있는 경우) — 아이콘 크기/정렬 확인

##### 3단계: AllVariants 매트릭스 비교

AllVariants 스토리를 캡처하여 Figma 원본 매트릭스와 비교한다:

    비교 대상:
    - 전체 variant 갯수가 일치하는지
    - 각 행/열의 정렬이 Figma와 동일한지
    - 색상 분포가 전체적으로 일치하는지

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
     tokens.json에 정의된 값이 실제 렌더링에 정확히 반영되었는지 검증한다.
     designTeamTokens 원본과의 일관성도 확인한다."

#### 검증 항목

##### tokens.json ↔ 렌더링 정합성
- tokens.json의 각 색상 토큰이 실제 computed style과 일치하는지
- Playwright로 실제 요소의 style을 추출하여 비교

    // 토큰 검증 코드 패턴
    async (page) => {
        await page.goto(storybookUrl, { waitUntil: 'networkidle', timeout: 15000 })
        await page.waitForSelector('#storybook-root', { timeout: 10000 })

        const root = page.locator('#storybook-root')
        const button = root.locator('button').first()

        const styles = await button.evaluate(el => {
            const cs = getComputedStyle(el)
            return {
                backgroundColor: cs.backgroundColor,
                color: cs.color,
                borderRadius: cs.borderRadius,
                fontWeight: cs.fontWeight,
                padding: cs.padding,
                height: cs.height
            }
        })

        return styles
    }

##### designTeamTokens ↔ tokens.json 일관성
- designTeamTokens(원본)와 tokens.json(프로젝트 토큰)의 값이 일치하는지
- HSL → HEX 변환 후 비교 (ΔE < 5 기준)

##### 토큰 누락 검사
- 컴포넌트에서 사용된 색상 중 tokens.json에 없는 임의값(bg-[#HEX]) 존재 여부
- 컴포넌트 파일을 Grep하여 하드코딩된 색상값 탐지

#### 결과 형식

    {
        "agent": "QA-토큰",
        "items": [
            { "id": "TK-001", "name": "color.primary.filled 렌더링 일치",
              "status": "PASS" },
            { "id": "TK-002", "name": "color.danger.ghost.hover 누락",
              "status": "FAIL",
              "detail": "tokens.json에 정의되지 않음. 컴포넌트에서 bg-[#FEE2E2] 하드코딩 사용" },
            { "id": "TK-003", "name": "designTeamTokens 일관성",
              "status": "FAIL",
              "expected": "hsl(195,4%,67%) → #A5ABAE",
              "actual": "#ABB2B5",
              "detail": "ΔE=6.1, 임계값 5 초과" },
            ...
        ]
    }

## QA 결과 종합 및 사용자 보고

### 결과 종합

3개 QA 에이전트의 결과를 수집하여 하나의 리포트로 통합한다.

    통합 판정:
    - ALL PASS: 3개 에이전트 모두 PASS → QA 통과, Step 10으로 진행
    - FAIL 존재: 하나라도 FAIL → Dev 수정 루프 진입

### 사용자 보고 (매 루프 필수)

QA 루프가 끝날 때마다 사용자에게 간단한 표로 보고한다:

    ## QA 루프 {N}/3 리포트: {ComponentName}

    | QA 에이전트 | PASS | FAIL | 주요 FAIL 항목 |
    |------------|------|------|---------------|
    | QA-기능    | 8    | 2    | disabled 클릭 미차단, ghost hover 미동작 |
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

    **판정: PASS** — QA 통과, Step 10 진행

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
    - Storybook 스토리 구조 변경 금지

    Dev 수정 후:
    - Storybook HMR로 자동 리로드 대기
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

    미해결 항목은 **경고(WARNING)**로 Step 11 결과 요약에 포함됩니다.
    파이프라인은 계속 진행합니다 (Step 10 Code Connect).

## QA 스크린샷 관리

    저장 경로:
    temp/visual-comparison/{ComponentName}/
    ├── figma-original.png          # Step 1에서 다운로드 (기존)
    ├── qa-visual-loop-1.png        # QA 루프 1 전체 스크린샷
    ├── qa-visual-loop-2.png        # QA 루프 2 전체 스크린샷
    ├── qa-visual-loop-3.png        # QA 루프 3 전체 스크린샷
    ├── zoom-primary-filled.png     # Zoom 확대 캡처
    ├── zoom-sm-size.png            # Zoom 확대 캡처
    ├── zoom-disabled.png           # Zoom 확대 캡처
    └── zoom-icon-variant.png       # Zoom 확대 캡처

    정리:
    - QA PASS 후: 최종 루프 스크린샷만 보존할지 사용자에게 확인
    - zoom 스크린샷은 FAIL 디버깅 근거로 보존

## Step 11 결과 요약에 QA 섹션 추가

    ### QA 검증
    - 판정: PASS / PARTIAL (미해결 {N}건) / FAIL (에스컬레이션)
    - 루프: {N}/3
    - QA-기능: {PASS}/{TOTAL} 통과
    - QA-시각적: {PASS}/{TOTAL} 통과
    - QA-토큰: {PASS}/{TOTAL} 통과
    - 미해결 경고: (있을 경우 항목 목록)
