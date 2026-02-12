---
name: figma-to-react
description: Figma MCP에서 컴포넌트 데이터를 추출하여 Headless UI + Tailwind CSS 기반 React 컴포넌트를 생성하고, Storybook 스토리와 Playwright E2E 테스트까지 자동화하는 파이프라인. Figma 컴포넌트 변환, 디자인 시스템 자동화, NDS 컴포넌트 생성 요청 시 사용.
---

# Figma → React 자동화 파이프라인

## 실행 전 필수 단계

1. **프로젝트 설정 파일 탐색 및 읽기**:
   - 프로젝트 디렉토리 내에서 `.figma-to-react.config.md` 파일을 Glob으로 검색한다.
     Glob 패턴: `**/.figma-to-react.config.md`
   - 여러 개 발견 시: 프로젝트 루트에 가장 가까운 것을 사용한다.
   - 발견하면: 읽고 {config.*} 값을 이후 단계에서 참조한다.
   - 미발견 시: 사용자에게 안내하고, 프로젝트 구조를 탐색하여 경로를 추론한 뒤 설정 파일 생성을 제안한다.
2. [MCP:ComponentSpec 어노테이션 규칙](references/component_spec.md)
3. [파이프라인 상세 워크플로우](references/pipeline_workflow.md) — Step별 상세 절차
4. [디자인 토큰 관리 규칙](references/design_tokens.md)
5. [Code Connect 워크플로우](references/code_connect_workflow.md)

## 사용법

    /figma-to-react <figma-node-url>
    /figma-to-react https://www.figma.com/design/XXXX?node-id=1234-5678

## MCP 전략

작업 유형으로 MCP를 선택한다 (실험 NKIAAI-188 근거):

| 작업 | MCP | 도구 |
|------|-----|------|
| 신규 컴포넌트 빌드 | Framelink | get_figma_data |
| 화면 조립 (기존 컴포넌트 조합) | 공식 MCP | get_design_context |

- Framelink: 시각적 일치도 최고(79/100), 토큰 98% 절감
- 공식 MCP: Code Connect 매핑된 컴포넌트의 도구 호출 92% 절감. 매핑 없으면 이점 없음
- Raw JSON (REST API curl): 사용 금지 (706KB 폭발, 시각적 일치도 55/100)
- 상세: [pipeline_workflow.md Step 1](references/pipeline_workflow.md) 참조

## 파이프라인 (상세는 레퍼런스 참조)

### 컴포넌트 단위

    1. Figma MCP 데이터 추출 → 2. 어노테이션 파싱 → 3. 기존 컴포넌트 탐색
    → 4. 아이콘/에셋 다운로드 → 5. 디자인 토큰 매칭 → 6. React 컴포넌트 생성
    → 7. Storybook 스토리 → 8. Playwright 테스트 → 9. 시각적 비교 루프
    → 10. Code Connect 등록 → 11. 결과 요약

### 화면 수준 (Top-down)

    1. 화면 MCP 추출 → 2. 컴포넌트 인벤토리 → 3. 사용자 확인
    → 4. 에셋 일괄 다운로드 → 5. 미연결 컴포넌트 빌드 (Bottom-up)
    → 6. 화면 조립 → 7. 결과 요약

## 핵심 규칙 요약

- 재사용 우선: Code Connect 매핑 → 로컬 탐색 → 신규 생성 순. props 50% 이상 공유하면 재사용
- 과잉 생성 방지: 어노테이션 없으면 사용자에게 범위 확인. State(interaction)은 CSS pseudo만
- 아이콘: 근사치 SVG 금지. {config.iconSvgSource} 에서 실제 SVG 사용 또는 download_figma_images로 다운로드
- 디자인 토큰: {config.tokensPath} 에서 중복 검색 후 재사용 또는 신규 생성. 임의값(bg-[#HEX]) 금지
- 컴포넌트: @headlessui/react + Tailwind v4 + clsx. {config.componentPrefix} 접두사. forwardRef 필수
- Storybook: globals.css에 @source 디렉티브 필수. 실행 명령은 프로젝트 package.json 참조
- Code Connect: .figma.tsx 매핑 생성. publish 명령은 프로젝트 package.json 참조
- Playwright: browser_run_code 사용. #storybook-root 하위 셀렉터만
- 시각적 비교: Storybook 스크린샷 ↔ Figma 이미지 비교 후 차이가 있으면 컴포넌트 수정 반복. 기본 최대 {config.maxVisualComparisonLoops} 회 (기본값 10)

## 프로젝트 설정 파일 (.figma-to-react.config.md)

프로젝트 루트에 위치하며, 아래 섹션을 포함한다:

    ## 경로
    - componentPath: 컴포넌트 출력 경로
    - componentPrefix: 컴포넌트 접두사 (예: Nds)
    - tokensPath: 디자인 토큰 파일 경로
    - storybookPath: Storybook 경로
    - storybookPort: Storybook 포트
    - assetPath: 에셋 출력 경로 (icons/, logos/, images/)

    ## 시각적 비교
    - maxVisualComparisonLoops: 시각적 비교 루프 최대 반복 횟수 (기본값: 10)

    ## 아이콘
    - iconSvgSource: SVG 원본 경로
    - iconFontPath: 아이콘 폰트 경로 (사용 시)
    - iconUsage: 아이콘 사용 방식 설명

    ## 디자인 토큰
    - designTeamTokens: 디자인팀 원본 토큰 경로
    - legacyTokens: 레거시 토큰 참조 경로 (있을 경우)

    ## Figma
    - figmaFileKey: 디자인 파일 키
    - figmaFileName: 디자인 파일 이름

    ## 스타일
    - cssFramework: CSS 프레임워크 (예: Tailwind CSS v4)
    - uiLibrary: UI 라이브러리 (예: @headlessui/react)

설정 파일이 없는 프로젝트에서 실행 시:
- 사용자에게 경로를 질문하여 설정 파일을 생성한다
- 또는 프로젝트 구조를 탐색하여 경로를 추론한 후 사용자 확인을 받는다

## 알려진 한계

- 아이콘/로고: 벡터 데이터 MCP 미포함 → SVG 에셋 별도 필요
- 아바타/이미지: placeholder 대체 → 에셋 별도 제공
- 디자인 토큰 CSS 변수: 미구축 → fallback 값 사용 중
- Claude 비결정성: 동일 입력에도 다른 코드 → Playwright 테스트로 품질 보장
