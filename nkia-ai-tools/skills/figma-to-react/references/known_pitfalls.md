# 알려진 함정 목록

NKIAAI-188 실험(portalMain 화면 빌드)에서 발견된 구체적 함정 목록.
다음 실행 시 동일 실수를 방지하기 위한 빠른 참조용.

## A. 기존 리소스 무시

### A1. 디자인 토큰을 기존 파일 무시하고 새로 생성

    증상: config.designTeamTokens에 HSL 형식 토큰 파일(36KB)이 있는데,
          독자적 flat HEX 구조로 새 토큰을 생성함
    원인: Step 5에서 config.designTeamTokens 참조가 의무화되지 않았음
    영향: 기존 토큰과 구조/형식 불일치, 사용자 수동 재매핑 필요
    방지: design_tokens.md "기존 토큰 파일 우선 참조" 규칙 (CRITICAL)

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
