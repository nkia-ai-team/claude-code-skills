---
name: figma-to-react
description: Figma MCP에서 컴포넌트 데이터를 추출하여 Headless UI + Tailwind CSS 기반 React 컴포넌트를 생성하고, Storybook 스토리와 Playwright E2E 테스트까지 자동화하는 파이프라인. Figma 컴포넌트 변환, 디자인 시스템 자동화, NDS 컴포넌트 생성 요청 시 사용.
disable-model-invocation: true
argument-hint: <figma-node-url>
---

# Figma → React 자동화 파이프라인

Figma 컴포넌트를 React로 변환하고 Storybook + Playwright 테스트까지 생성하는 스킬.

## CRITICAL: 레퍼런스 먼저 읽기

실행 전 반드시 아래 파일을 순서대로 읽을 것:
1. [MCP:ComponentSpec 어노테이션 규칙](references/component_spec.md)
2. [파이프라인 상세 워크플로우](references/pipeline_workflow.md)
3. [디자인 토큰 관리 규칙](references/design_tokens.md)
4. [Code Connect 워크플로우](references/code_connect_workflow.md)

## 사용법

    /figma-to-react <figma-node-url>
    /figma-to-react https://www.figma.com/design/XXXX?node-id=1234-5678

## 파이프라인 개요

### 컴포넌트 단위 생성

    1. Figma MCP 데이터 추출 (node-id 지정)
    2. [MCP:ComponentSpec] 어노테이션 파싱 (있으면)
    3. 기존 컴포넌트 탐색 (Code Connect 매핑 + 로컬 탐색)
    4. 디자인 토큰 매칭/생성 (tokens.json)
    5. React 컴포넌트 생성 또는 수정
    6. Storybook 스토리 생성
    7. Playwright E2E 테스트 실행
    8. Code Connect 매핑 등록 (.figma.tsx 생성 + publish)
    9. 결과 요약 보고

### 화면 수준 생성 (Top-down 자동 발견)

화면 URL을 주면 시스템이 자동으로 컴포넌트를 발견 → 빌드 → 등록 → 조립한다.
사용자가 컴포넌트를 일일이 찾아서 실행할 필요 없다.

    1. 화면 Figma MCP 데이터 추출
    2. 컴포넌트 인벤토리 생성 (연결됨/미연결 분류)
    3. 사용자 확인 (빌드 대상 승인)
    4. 미연결 컴포넌트 자동 빌드 (리프부터 Bottom-up)
       → 각 컴포넌트마다 컴포넌트 단위 파이프라인 실행 + Code Connect 등록
    5. 화면 조립 (연결된 스니펫 + 레이아웃)
    6. 결과 요약 보고

## 핵심 규칙

### 기존 컴포넌트 재사용 우선
- Code Connect 매핑이 있으면 MCP의 CodeConnectSnippet을 우선 참조한다
- CodeConnectSnippet이 없는 경우 컴포넌트 경로에서 로컬 탐색한다
- 동일하거나 유사한 컴포넌트가 있으면 **재사용을 우선**한다
- 기존 컴포넌트에 prop 추가, 스타일 변형 추가 등 **소폭 확장**은 허용한다
- 단, 기존 인터페이스 변경이 크거나 용도가 본질적으로 다르면 **신규 생성**한다
- 재사용/신규 판단 기준:
  - 기존 props의 50% 이상 공유 → 재사용 (확장)
  - 기존 props의 50% 미만 공유 또는 용도가 다름 → 신규 생성
- 판단이 애매하면 사용자에게 확인한다

### Code Connect 매핑 등록
- 컴포넌트 생성/수정 후 반드시 .figma.tsx 매핑 파일을 생성한다
- 매핑 작성 규칙은 [Code Connect 워크플로우](references/code_connect_workflow.md) 참조
- 3회 이상 재사용되는 공통 컴포넌트는 반드시 등록한다

### 과잉 생성 방지
- Figma prop 값이 존재한다고 해서 모든 변형을 구현하지 않는다
- [MCP:ComponentSpec] 어노테이션이 있으면 반드시 따른다
- 어노테이션이 없으면 사용자에게 구현 범위를 확인한다
- State(interaction) 값(hover, focus, active)은 CSS pseudo로만 처리, prop으로 만들지 않는다

### 디자인 토큰
- 컴포넌트 생성 전 tokens.json을 읽어 기존 토큰 확인
- Figma RGBA → HEX 변환 시 기존 토큰에 동일 색상이 있으면 재사용
- 없으면 시맨틱 이름으로 신규 토큰 생성 후 tokens.json에 추가
- Tailwind 임의값(bg-[#1D1F20]) 대신 토큰 참조 사용

### 컴포넌트 구현
- 기술 스택: @headlessui/react + Tailwind CSS v4 + clsx
- 컴포넌트 경로: shared/components/commons/ai-portal/
- forwardRef 패턴, TypeScript interface export 필수
- Nds 접두사 (NdsButton, NdsInput 등)

### Storybook
- 스토리 경로: temp/ai-portal-storybook/stories/
- Storybook 포트: 6007
- @tailwindcss/vite 플러그인으로 Tailwind v4 통합
- 스토리 구성: Default, AllVariants, Sizes, DisabledStates (최소)

### Playwright 테스트
- Playwright MCP (browser_run_code) 사용
- 셀렉터: #storybook-root 하위만 대상
- 테스트 범위: 렌더링 검증, 디자인 토큰 검증, 인터랙션 검증

## 입력 파싱

$ARGUMENTS에서 Figma URL을 파싱한다:

    URL: https://www.figma.com/design/{fileKey}?node-id={nodeId}
    → fileKey: XXXX
    → nodeId: 1234-5678 (하이픈을 콜론으로 변환하지 않음)

## 출력

파이프라인 완료 후 아래 형식으로 요약:

    ## 변환 결과
    - 컴포넌트: {컴포넌트명}
    - 생성 파일: {파일 목록}
    - 토큰 변경: {신규 N개 / 재사용 N개}
    - 스토리: {N개}
    - 테스트: {N passed, N failed}
    - 한계/주의: {발견된 이슈}
