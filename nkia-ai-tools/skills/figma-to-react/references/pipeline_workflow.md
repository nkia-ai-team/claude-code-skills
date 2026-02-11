# 파이프라인 상세 워크플로우

## Step 1: Figma URL 파싱 및 MCP 데이터 추출

### URL 파싱

    입력: https://www.figma.com/design/{fileKey}?node-id={nodeId}&...
    추출: fileKey, nodeId

### Figma MCP 호출

Figma MCP의 get_file 또는 get_node 함수로 컴포넌트 데이터를 요청한다.
node-id를 지정하여 해당 컴포넌트만 조회한다 (페이지 전체 조회 금지 — 토큰 절약).

### 추출 대상 데이터
- variant property 이름과 값 목록
- 각 변형의 fill/stroke 색상 (RGBA)
- 텍스트 스타일 (font-family, font-size, font-weight, line-height)
- 레이아웃 정보 (padding, gap, border-radius)
- 컴포넌트 Description ([MCP:ComponentSpec] 어노테이션 포함 여부 확인)

## Step 2: 어노테이션 파싱

### [MCP:ComponentSpec] 존재 시
1. Description 또는 텍스트 레이어에서 [MCP:ComponentSpec] 블록 추출
2. 섹션별 파싱: State(interaction), Prop, Rule, Priority
3. component_spec.md 규칙에 따라 props와 CSS pseudo 분리
4. 유효 조합 규칙 적용

### [MCP:ComponentSpec] 없음 (폴백)
1. Figma variant property에서 props 추론
2. state 관련 property는 CSS pseudo로 분류
3. **사용자에게 구현 범위 확인 질문**:
   - "Figma에 {N}개 variant property가 있습니다. 모두 구현할까요?"
   - contentType 등 변형이 있으면 "iconEnd, iconOnly 등도 구현할까요?"
4. 확인 후 진행

## Step 3: 기존 컴포넌트 탐색

### 목적
신규 생성 전에 재사용 가능한 기존 컴포넌트가 있는지 확인한다.
불필요한 중복 컴포넌트 생성을 방지한다.

### 탐색 순서

#### 1순위: Code Connect 매핑 확인 (MCP 응답)
MCP 응답에 CodeConnectSnippet이 포함되어 있으면 해당 컴포넌트는 이미 등록되어 있다.
- CodeConnectSnippet에 import 경로와 사용법이 포함됨
- 추가 탐색 없이 바로 사용 가능
- 이 경우 Step 4~5를 건너뛰고 조립 단계로 진행

#### 2순위: 로컬 코드베이스 탐색
CodeConnectSnippet이 없는 경우 기존 방식으로 탐색한다.
컴포넌트 경로(기본: shared/components/commons/ai-portal/)에서
동일 이름 또는 유사 용도의 컴포넌트를 검색한다.

### 판단 기준

#### 재사용 (기존 컴포넌트 확장)
- 기존 컴포넌트와 Figma 스펙의 props가 50% 이상 겹침
- 추가할 prop이 2~3개 이하
- 기존 인터페이스의 breaking change 없이 확장 가능
- 예시: 기존 NdsButton에 `loading` prop 하나 추가

#### 신규 생성
- 기존 컴포넌트와 props 공유가 50% 미만
- 용도가 본질적으로 다름 (예: NdsButton vs NdsIconButton)
- 기존 인터페이스를 크게 변경해야 함
- 확장 시 기존 사용처에 영향이 가는 경우

#### 판단 애매 시
사용자에게 확인한다:
- "기존 Nds{Name} 컴포넌트가 있습니다. {차이점 목록}. 기존 컴포넌트를 확장할까요, 새로 만들까요?"

### 재사용 시 절차
1. 기존 컴포넌트 파일 읽기
2. 기존 interface와 Figma 스펙 diff 확인
3. 추가할 props, 스타일 변형 목록 정리
4. 기존 코드에 확장 (기존 사용처 영향 없도록)
5. 결과 요약에 "기존 컴포넌트 확장" 명시

### 신규 생성 시
Step 5로 진행한다.

## Step 4: 디자인 토큰 매칭/생성

### tokens.json 경로
    shared/styles/tokens.json

### 절차
1. tokens.json 읽기 (없으면 빈 객체 {} 로 생성)
2. Figma에서 추출한 색상값(RGBA)을 HEX로 변환
3. 기존 토큰에서 동일 HEX 검색
   - 있으면: 기존 토큰 이름 사용
   - 없으면: 시맨틱 이름으로 신규 토큰 생성
4. 사이즈, border-radius, font-weight 등도 동일 절차
5. tokens.json 업데이트 (신규 토큰 추가)
6. 변경 사항 기록 (결과 요약에 포함)

### 토큰 네이밍 규칙
    color.{tone}.{variant}: "#XXXXXX"      (예: color.primary.filled)
    color.{tone}.{variant}.hover: "#XXXXXX" (예: color.primary.filled.hover)
    color.disabled.bg: "#XXXXXX"
    color.disabled.text: "#XXXXXX"
    size.{component}.{size}: "{value}"       (예: size.button.xl)
    radius.{component}: "{value}"            (예: radius.button)
    font.weight.{name}: "{value}"            (예: font.weight.normal)

## Step 5: React 컴포넌트 생성 또는 수정

### 기술 스택
- @headlessui/react: 접근성 보장 기본 컴포넌트
- Tailwind CSS v4: 스타일링 (@tailwindcss/vite 플러그인)
- clsx: 조건부 클래스 조합
- TypeScript: 타입 안전성

### 파일 구조
    shared/components/commons/ai-portal/
    ├── {ComponentName}.tsx   # 컴포넌트
    └── index.ts              # barrel export

### 코드 구조

    import { forwardRef } from 'react'
    import { {HeadlessComponent} } from '@headlessui/react'
    import clsx from 'clsx'

    // Figma variant props (또는 MCP:ComponentSpec의 Prop 섹션)
    type {Tone} = ...
    type {Variant} = ...

    export interface Nds{Name}Props extends ... {
        // MCP:ComponentSpec의 Prop 섹션에서 정의된 것만
        // State(interaction)은 여기에 포함하지 않음
    }

    // 토큰 기반 스타일 맵
    const toneVariantStyles = { ... }  // tokens.json 참조

    export const Nds{Name} = forwardRef(...)

### 기존 컴포넌트 수정 시
- 기존 interface에 optional prop만 추가 (기존 사용처 영향 없음)
- 기존 스타일 맵에 새 키 추가 (기존 키 수정 금지)
- 변경 전후 diff를 결과 요약에 포함

### 주의사항
- forwardRef 패턴 필수
- Nds 접두사 필수 (NdsButton, NdsInput 등)
- interface와 컴포넌트 모두 export
- index.ts에서 barrel export
- hover/focus/active는 Tailwind pseudo-class(hover:, focus:, active:)로만 처리
- disabled는 Headless UI의 disabled prop + disabled: pseudo-class

## Step 6: Storybook 스토리 생성

### 경로
    temp/ai-portal-storybook/stories/{ComponentName}.stories.tsx

### 필수 스토리
1. **Default**: 기본 상태
2. **AllVariants**: 유효 조합 전체 × 사이즈 (매트릭스)
3. **Sizes**: 사이즈 비교
4. **DisabledStates**: 모든 유효 조합의 disabled 상태

### 선택 스토리 (어노테이션 Prop에 정의된 경우만)
- WithIcons: iconStart, iconOnly 등
- CustomContent: 슬롯 콘텐츠

### Storybook 설정
- 포트: 6007
- .storybook/main.ts: @storybook/react-vite + @tailwindcss/vite 플러그인
- .storybook/preview.ts: globals.css import
- globals.css: @import "tailwindcss" + @source 디렉티브

### import 주의
- render 함수 사용 시 import React from 'react' 필수
- 컴포넌트는 상대경로로 import

## Step 7: Playwright E2E 테스트

### 실행 방식
Playwright MCP (browser_run_code)를 사용한다. npx playwright test가 아님.

### 셀렉터 규칙
- 반드시 #storybook-root 하위에서 검색 (Storybook UI 버튼 회피)
- 예: #storybook-root button, #storybook-root [data-testid="..."]

### 테스트 구성 (최소)

#### 렌더링 검증
- TC-{PREFIX}-001: Default 렌더링
- TC-{PREFIX}-002: 전체 유효 조합 렌더링 (갯수 확인)
- TC-{PREFIX}-003: 사이즈별 렌더링
- TC-{PREFIX}-004: Disabled 상태 렌더링

#### 디자인 토큰 검증
- TC-{PREFIX}-005: 기본 배경색 = tokens.json의 해당 토큰 값
- TC-{PREFIX}-006: 기본 텍스트색
- TC-{PREFIX}-007: Disabled 텍스트색
- TC-{PREFIX}-008: border-radius
- TC-{PREFIX}-009: font-weight

#### 인터랙션 검증
- TC-{PREFIX}-010: 클릭 이벤트 동작
- TC-{PREFIX}-011: Disabled 시 cursor: not-allowed

### 스토리 URL 패턴
    http://localhost:6007/iframe.html?id={story-id}&viewMode=story

### loadStory 헬퍼 패턴

    async function loadStory(page, storyId) {
        await page.goto(`http://localhost:6007/iframe.html?id=${storyId}&viewMode=story`, {
            waitUntil: 'networkidle',
            timeout: 15000
        })
        await page.waitForSelector('#storybook-root', { timeout: 10000 })
    }

## Step 8: Code Connect 매핑 등록

### 목적
생성된 컴포넌트를 Figma Code Connect에 등록하여,
이후 화면 수준 생성 시 MCP가 CodeConnectSnippet으로 제공할 수 있도록 한다.

### 등록 대상 판단

#### 반드시 등록
- 디자인 시스템 공통 컴포넌트 (Button, Input, Select 등)
- 3회 이상 재사용이 예상되는 컴포넌트
- 내부 노드가 복잡한 컴포넌트 (토큰 절감 효과가 큰 것)

#### 등록 생략
- 특정 화면 전용 일회성 컴포넌트
- 구조가 매우 단순한 컴포넌트 (아이콘, 디바이더)

### 절차
1. 컴포넌트 파일과 동일 디렉토리에 .figma.tsx 파일 생성
2. figma.connect()로 Figma 노드 URL과 코드 컴포넌트 연결
3. props 매핑 (figma.enum, figma.boolean, figma.string 등)
4. example 함수로 사용 예시 작성
5. npx figma connect publish로 배포
6. 상세 규칙은 code_connect_workflow.md 참조

### 파일 구조

    shared/components/commons/ai-portal/
    ├── NdsButton.tsx           # 컴포넌트
    ├── NdsButton.figma.tsx     # Code Connect 매핑
    └── index.ts

## Step 9: 결과 요약

모든 단계 완료 후 아래 형식으로 보고:

    ## 변환 결과: {컴포넌트명}

    ### 생성 파일
    | 파일 | 용도 | 크기 |
    |------|------|------|
    | ... | ... | ... |

    ### 토큰 변경
    - 신규: {N}개 ({토큰 이름 목록})
    - 재사용: {N}개

    ### 테스트
    - {N} passed, {N} failed

    ### 한계/주의
    - {발견된 이슈 목록}

## 화면 수준 생성

화면(프레임) URL이 입력된 경우 code_connect_workflow.md의
"화면 수준 생성 워크플로우 (Top-down)" 절차를 따른다.

핵심 흐름:
1. 화면 MCP 데이터 추출
2. 컴포넌트 인벤토리 생성 (연결됨/미연결 분류)
3. 사용자 확인
4. 미연결 컴포넌트 자동 빌드 (리프부터 Bottom-up, 각각 Step 1~8 실행)
5. 화면 조립
6. 결과 요약

컴포넌트 노드와 화면 프레임 노드의 구분:
- 컴포넌트 노드: type이 COMPONENT 또는 COMPONENT_SET
- 화면 프레임 노드: type이 FRAME이고, 내부에 INSTANCE 노드들을 포함

## 에러 처리

### Figma MCP 연결 실패
- PAT 토큰 만료 확인 안내
- claude mcp add 명령어 안내

### Storybook 미실행
- "Storybook이 포트 6007에서 실행 중이어야 합니다" 안내
- 실행 명령: cd temp/ai-portal-storybook && npx storybook dev -p 6007

### Playwright MCP 브라우저 충돌
- 기존 브라우저 세션 닫기 안내
- browser_close 후 재시도

### [MCP:ComponentSpec] 파싱 실패
- 어노테이션 형식 오류 시 사용자에게 원문 표시 후 확인 요청
- 폴백 모드로 전환 (variant property 기반)
