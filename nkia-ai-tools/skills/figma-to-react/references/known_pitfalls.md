# 알려진 함정 목록

NKIAAI-188 실험(portalMain 화면 빌드)에서 발견된 구체적 함정 목록.
다음 실행 시 동일 실수를 방지하기 위한 빠른 참조용.

## A. 기존 리소스 무시

### A1. 디자인 토큰을 기존 파일 무시하고 새로 생성

    증상: (구) config.designTeamTokens에 HSL 형식 토큰 파일(36KB)이 있는데,
          독자적 flat HEX 구조로 새 토큰을 생성함
    원인: Step 5에서 토큰 소스 참조가 의무화되지 않았음
    영향: 기존 토큰과 구조/형식 불일치, 사용자 수동 재매핑 필요
    방지: design_tokens.md "토큰 소스 (CRITICAL)" 규칙 — config.tokensCssPath + config.portalCssPath 우선 참조

### A2. 로고를 텍스트 근사치로 대체

    증상: 로고 SVG 대신 <span>+</span>Lucida<span>beta</span> 텍스트로 렌더링
    원인: Step 4 에셋 다운로드에서 로고 SVG 탐색을 건너뜀
    영향: 시각적으로 완전히 다른 결과
    방지: pipeline_workflow.md "근사치 에셋 생성 절대 금지" 규칙 (CRITICAL)

### A3. 아이콘을 유니코드 문자로 대체

    증상: 설정 아이콘 자리에 ★ 유니코드 문자, 메뉴 아이콘에 ☰ 사용
    원인: SVG 에셋 탐색/다운로드를 건너뛰고 즉석 대체
    영향: 시각적 불일치, 크기/색상 제어 불가
    방지: pipeline_workflow.md "근사치 에셋 생성 절대 금지" + 에셋 체크리스트 (MUST)

## B. SVG/아이콘 처리 결함

### B1. SVG 하드코딩 fill 색상으로 다크 배경에서 안 보임

    증상: fill="#222D44" 아이콘이 #06050A 배경에서 거의 보이지 않음
    원인: SVG의 fill 색상을 currentColor로 변환하지 않음
    영향: 특정 배경색에서 아이콘이 사라짐
    방지: pipeline_workflow.md "SVG fill → currentColor 변환" 규칙 (MUST)

### B2. NdsIcon import.meta.glob 경로 3번 시행착오

    증상: 절대경로 → 잘못된 상대경로 → 올바른 상대경로 (3회 시도)
    원인: componentPath에서 assetPath까지의 상대경로 계산 가이드 없음
    영향: 시각적 비교 루프 3회 소진
    방지: pipeline_workflow.md "import.meta.glob 경로 계산" 가이드

### B3. 아이콘 잘못 매핑 (star → 실제로는 theme toggle sunny)

    증상: application-star-o.svg를 사용했지만 실제로는 weather-sunny-f.svg가 필요
    원인: 노드명만 보고 추측, 상위 컨텍스트(설정 영역 내 테마 토글) 미확인
    영향: 사용자가 스크린샷 비교로 발견하여 수동 수정
    방지: pipeline_workflow.md "아이콘 매핑 정확성" 절차 (상위 프레임 용도 확인)

## C. 레이아웃/스타일 불일치

### C1. 3중 패딩 구조 미반영

    증상: promptInput(p-2) + InputWrapper(p-2) = 실효 16px인데, 코드에서 8px만 반영
    원인: 중첩 프레임의 padding을 하나로 합치거나 내부 프레임 padding 누락
    영향: 인풋 영역이 좁게 보임
    방지: pipeline_workflow.md "중첩 패딩 구조 반영" + Step 1-5-a "레이아웃 중첩 구조 추출"

### C2. 형제 요소 너비 비율 불일치

    증상: PromptArea와 QuickCards의 너비 비율이 Figma와 다름
    원인: 형제 요소의 너비 비교를 하지 않고 각각 독립적으로 코딩
    영향: 레이아웃 비율이 원본과 다름
    방지: pipeline_workflow.md Step 1-5-b "형제 요소 너비/비율 비교"

### C3. 스크롤바가 Figma에 없는데 Storybook에 표시됨

    증상: overflow-auto로 인해 스크롤바가 표시됨 (Figma에는 스크롤바 없음)
    원인: overflow 기본값 문제 — scrollbar 숨기기를 하지 않음
    영향: 시각적 불일치 (사용자가 수동 발견)
    방지: pipeline_workflow.md "overflow/scrollbar 기본 규칙" — 기본 [scrollbar-width:none]

### C4. 번개 버튼 variant 오류 (text → outline)

    증상: variant="text"여야 하는데 variant="outline"으로 생성
    원인: MCP 데이터에서 variant 값을 정확히 추출하지 않음
    영향: 버튼 스타일이 원본과 다름
    방지: Step 1-5-c "fill/stroke 색상 전수 조사" — variant 결정 근거 명시

## D. 인터랙션 미구현

### D1. Figma variant 기반 인터랙션 전체 미연결

    증상: isFocused, isCollapsed, theme 등 variant가 있는데 코드에 반영 없음
    원인: Step 2에서 인터랙션 variant 분석 절차 없음
    영향: 사용자가 별도 세션에서 인터랙션 하나씩 요청
    방지: pipeline_workflow.md Step 2 "인터랙션 variant 분석" + Step 6.5 "인터랙션 연결"

### D2. 퀵카드 클릭 → 프롬프트 채우기 미구현

    증상: 퀵카드를 클릭해도 프롬프트 인풋에 텍스트가 채워지지 않음
    원인: 화면 수준 인터랙션(컴포넌트 간 상호작용) 가이드 없음
    영향: 핵심 기능 누락
    방지: Step 6.5 "D. 컴포넌트 간 상호작용 (화면 수준)"

### D3. 배경 그라데이션 조건부 표시 미구현

    증상: focus 상태에서만 표시되어야 하는 배경 그라데이션이 항상 표시 또는 항상 숨김
    원인: 상태 기반 조건부 렌더링 가이드 없음
    영향: 시각적 상태 전환 효과 없음
    방지: Step 6.5 "C. 조건부 렌더링"

### D4. 로고 애니메이션을 단순 회전으로 오해

    증상: 로고 loading 애니메이션을 rotate로 구현했지만, 실제로는 SVG 모핑 효과
    원인: 모핑 애니메이션 처리 가이드 없음
    영향: 사용자가 스크린샷으로 지적하여 수동 수정
    방지: Step 6.5 "CSS crossfade (SVG 모핑)" 가이드

## E. Code Connect 실패

### E1. figma.string() — 존재하지 않는 props 매핑

    증상: figma.string('title'), figma.string('description') 등으로 매핑했지만
          Figma componentProperties에 해당 Text property가 없어서 publish 실패
    원인: 텍스트 콘텐츠와 Figma property 구분 가이드 없음
    영향: publish 4회 재시도
    방지: code_connect_workflow.md "figma.string() 매핑 규칙" (CRITICAL)

### E2. variant restriction 배열 오류

    증상: variant: { ContentType: ['none', 'start', 'end'] } 로 매핑 → publish 실패
    원인: 배열 미지원 경고 없음
    영향: publish 재시도
    방지: code_connect_workflow.md "Variant Restriction 제한사항" (CRITICAL)

### E3. Figma 프로퍼티명 오타 ('varient')

    증상: 'varient'으로 오타 → Figma에서 프로퍼티를 찾지 못해 publish 실패
    원인: 프로퍼티명 정확성 검증 절차 없음
    영향: publish 재시도
    방지: code_connect_workflow.md "Publish 전 검증 절차" 2단계 — MCP 데이터에서 복사 사용

## F. Interaction Graph 관련

### F1. REST API depth 부족으로 중첩 인스턴스 interactions 누락

    증상: 화면 내 컴포넌트 인스턴스의 내부 인터랙션이 추출되지 않음
    원인: depth가 부족하여 인스턴스 내부까지 탐색하지 못함
    방지: depth=10으로 호출, 필요 시 하위 노드 별도 호출

### F2. CHANGE_TO destination이 같은 파일 내에 없음

    증상: destinationId resolve 실패, 인터랙션 대상을 알 수 없음
    원인: 외부 라이브러리 컴포넌트의 variant를 참조하는 경우
    방지: resolve 실패 시 "미확인"으로 표시, Step 8.5에서 사용자 확인

### F3. 프로토타입 미연결을 "인터랙션 없음"으로 오해

    증상: 명백히 클릭 가능한 버튼인데 인터랙션 0개로 표시
    원인: 디자이너가 프로토타입 연결을 걸지 않았을 뿐, 인터랙션이 없는 건 아님
    방지: interactions 0개일 때 구조 추론 시도 + Step 8.5에서 사용자에게 질문

### F4. 인스턴스에서 interactions를 읽으려 하여 0개로 나옴

    증상: 화면 내 컴포넌트 인스턴스에서 interactions를 추출했는데 0개
    원인: Figma의 프로토타입 인터랙션과 dev 코멘트는 Main Component에만 달려 있고,
          인스턴스에는 복사되지 않음
    방지: INSTANCE 노드의 componentId로 Main Component를 resolve하여
          Main Component에서 interactions + dev 코멘트 추출 (Step 1.6-5)

### F5. Main Component dev 코멘트를 무시하고 MCP 데이터만으로 빌드

    증상: 디자이너가 "hover 시 opacity 0.9", "300ms delay" 등 구현 의도를 코멘트로 남겼는데
          코드에 반영되지 않음
    원인: Comments API를 호출하지 않고 MCP 구조 데이터만 사용
    방지: Step 1.6-5에서 Comments API로 dev 코멘트 추출 → Step 6, 6.5에서 반영

## G. 오버레이/프리뷰 구현 결함

### G1. 오버레이를 컴포넌트 내부에 렌더링하여 z-index 문제 발생

    증상: 이미지 프리뷰 오버레이가 화면 전체를 덮지 않고 부모 컨테이너에 갇힘
    원인: fixed 포지션 오버레이를 컴포넌트 JSX 내부에 렌더링 → 부모의 transform이나
          overflow가 stacking context를 만들어 fixed가 무효화
    방지: 오버레이는 반드시 React Portal(createPortal)로 document.body에 렌더링
          (Step 6.5 "오버레이/프리뷰 구현 시 필수 고려사항" 참조)

### G2. 이미지 프리뷰 클릭 시 확대 대신 닫힘

    증상: 이미지 클릭 → 확대되어야 하는데 프리뷰가 닫힘
    원인: 이미지 클릭 이벤트가 배경의 닫기 핸들러로 전파 (stopPropagation 누락)
    방지: 오버레이 콘텐츠 영역에 onClick stopPropagation 필수

### G3. 작은 이미지가 프리뷰에서 확대되지 않음

    증상: maxWidth/maxHeight 제거 방식으로 확대했지만, 원본이 작은 이미지는 변화 없음
    원인: max 속성 제거는 원본보다 크게 만들지 않음
    방지: CSS transform: scale()로 실제 확대 구현 (작은 이미지도 2x로 커짐)

### G4. hover 시 tooltip/tag가 overflow 컨테이너에서 잘림

    증상: 카드 hover 시 하단에 표시되어야 하는 파일명 Tag가 부모의 overflow-x-auto에 의해 클리핑
    원인: absolute 요소가 overflow: hidden/auto 부모 밖으로 나갈 수 없음
    방지: overflow가 있는 컨테이너 내부의 tooltip/tag는 Portal로 렌더링하거나,
          부모에 overflow: visible을 적용하고 스크롤은 별도 wrapper로 분리

## H. Storybook 빌드/실행 결함

### H1. 무관한 스토리의 SCSS 의존성이 Storybook 전체 빌드를 깨뜨림

    증상: NdsResultCard → sirius → SCSS 체인으로 Storybook 빌드 전체 실패
    원인: 하나의 스토리 파일이 Webpack SCSS 로더 미설정 모듈을 import
    방지: 빌드 실패 시 에러 로그에서 문제 스토리 식별 → 임시 비활성화(.bak)하여 진행
          QA 완료 후 반드시 복원. 근본 해결은 해당 컴포넌트의 의존성 분리

### H2. QA가 정적 데이터 스토리만 확인하고 실제 인터랙션 미검증

    증상: WithPreAttachedFiles(정적 데이터)에서 카드가 보여서 PASS 처리했지만,
          실제 파일 선택 → 등록 플로우는 동작하지 않았음
    원인: QA-기능이 렌더링 존재 여부만 확인하고 사용자 시나리오를 시뮬레이션하지 않음
    방지: qa_phase.md "사용자 인터랙션 플로우 E2E 검증" 규칙 준수
          (파일 업로드, 클릭 확대 등 실제 핸들러 동작 Playwright로 시뮬레이션)

## I. 토큰 시스템 관련

### I1. tokens.css를 직접 수정하여 빌드 시 덮어써짐

    증상: tokens.css에 수동으로 추가한 CSS 변수가 npm run build:tokens 실행 후 사라짐
    원인: tokens.css는 자동 생성 파일이라 빌드 시 완전히 덮어씀
    방지: 새 토큰은 반드시 portal.css에 추가. tokens.css 직접 수정 절대 금지
          design_tokens.md "tokens.css 수정 금지 원칙" 참조

### I2. 구 토큰명으로 Tailwind 클래스 사용하여 다크 모드 깨짐

    증상: bg-fill-standard-default, text-text-standard-default 등 구 토큰명 사용 시
          tokens.css에 해당 CSS 변수가 없어 Tailwind가 클래스를 생성하지 못함
    원인: portal.css에서 구 토큰 정의를 제거한 후 컴포넌트 코드는 미교체
    영향: 스타일이 완전히 사라짐 (배경 투명, 텍스트 기본색)
    방지: portal.css 토큰 제거와 컴포넌트 코드 교체를 반드시 동시에 진행
          design_tokens.md "정적 매핑 테이블" 참조

### I3. Core 팔레트 직접 참조로 다크 모드에서 색상 안 바뀜

    증상: bg-gray-cool-100 등 Core 팔레트 클래스 사용 시 다크 모드에서도 라이트 색상 유지
    원인: Core 팔레트는 테마에 따라 값이 변하지 않는 고정값
    영향: 다크 모드에서 흰 배경이 그대로 표시됨
    방지: 시맨틱 토큰 우선 사용 (bg-layer-01 등). Core 팔레트는 불가피한 경우만
          design_tokens.md "토큰 우선순위" 참조

### I4. brand-default 토큰의 컨텍스트 무시 매핑

    증상: 링크 텍스트에 text-text-brand를, 포커스 링에 bg-interactive-primary를 적용
    원인: brand-default가 컨텍스트에 따라 다르게 매핑되는데 일괄 치환함
    영향: 링크 색상이 의도와 다르거나 포커스 링이 배경색이 됨
    방지: Tailwind 접두사로 컨텍스트 판별 후 매핑
          - text- (링크) → text-link-primary
          - text- (강조) → text-text-brand
          - bg- (버튼) → bg-interactive-primary
          - outline- (포커스) → outline-focus-default
          design_tokens.md "brand-default 분기 처리" 참조

### I5. 하드코딩 HEX 색상을 토큰으로 교체하지 않음

    증상: bg-[#F3F5F7], text-[#121314], style={{ backgroundColor: '#101213' }} 등이
          컴포넌트에 남아있음
    원인: 토큰 마이그레이션 시 정적 매핑만 적용하고 하드코딩 HEX 탐색을 건너뜀
    영향: 다크 모드 전환 시 하드코딩 색상은 변하지 않아 시각적 불일치
    방지: -m 모드 M-3-4 단계에서 하드코딩 HEX 패턴을 반드시 Grep으로 탐색
          bg-[#, text-[#, border-[#, style={{ color:, style={{ backgroundColor: 패턴
