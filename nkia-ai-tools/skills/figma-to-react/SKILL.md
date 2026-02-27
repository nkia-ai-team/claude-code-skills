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
6. [QA Phase 워크플로우](references/qa_phase.md) — 독립 QA 서브에이전트 검증
7. [알려진 함정 목록](references/known_pitfalls.md) — 실험에서 발견된 구체적 함정 빠른 참조

## 사용법

### 신규 생성 (기본)

    /figma-to-react <figma-url> [figma-spec-url]

    # 컴포넌트 신규 빌드
    /figma-to-react https://...?node-id=1234-5678

    # 화면 신규 빌드
    /figma-to-react https://...?node-id=5678-1234

    # 기획 스펙 보강 (선택 — 두 번째 URL)
    /figma-to-react https://...?node-id=1234-5678 https://...?node-id=2811-65001

### 증분 추가 (-a)

    /figma-to-react <컴포넌트가-추가된-화면-url> -a [figma-spec-url]

    # 이미 빌드한 화면에 새 컴포넌트가 추가된 경우
    # 기존 화면 코드를 찾아서, 새 컴포넌트만 빌드 + 기존 코드에 삽입
    /figma-to-react https://...?node-id=5678-1234 -a

### 화면 업데이트 (-u)

    /figma-to-react <변경된-화면-url> -u [figma-spec-url]

    # 기존 화면의 레이아웃/컴포넌트가 변경된 경우
    # Figma ↔ 기존 코드를 비교하여 변경 사항만 반영
    /figma-to-react https://...?node-id=5678-1234 -u

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

    1. Figma MCP 데이터 추출 → 1.5. 기획 스펙 보강 → 2. 어노테이션 파싱
    → 3. 기존 컴포넌트 탐색 → 4. 아이콘/에셋 다운로드 → 5. 디자인 토큰 매칭
    → 6. React 컴포넌트 생성 → 6.5. 인터랙션 연결 → 7. Storybook 스토리
    → 8. QA Phase (독립 서브에이전트 3개 병렬 검증 + Dev 수정 루프)
    → 9. Code Connect 등록 → 10. 결과 요약

### 화면 수준 — 신규 (Top-down)

    1. 화면 MCP 추출 → 1.5. 기획 스펙 보강 → 2. 컴포넌트 인벤토리
    → 3. 사용자 확인 → 4. 에셋 일괄 다운로드
    → 5. 미연결 컴포넌트 빌드 (Bottom-up, QA Phase 포함) → 6. 화면 조립 → 7. 결과 요약

### 화면 수준 — 증분 추가 (-a)

    1. 화면 MCP 추출 → 1.5. 기획 스펙 보강 → 2. 기존 코드 탐색
    → 3. 신규/기존 컴포넌트 분류 → 4. 신규 컴포넌트만 빌드
    → 5. 기존 화면 코드에 삽입 → 6. 결과 요약

### 화면 수준 — 업데이트 (-u)

    1. 화면 MCP 추출 → 1.5. 기획 스펙 보강 → 2. 기존 코드 탐색
    → 3. Figma ↔ 코드 diff → 4. 변경 사항 분류 (추가/수정/삭제)
    → 5. 변경 사항 적용 → 6. 결과 요약

## 핵심 규칙 요약

- 재사용 우선: Code Connect 매핑 → 로컬 탐색 → 신규 생성 순. props 50% 이상 공유하면 재사용
- 과잉 생성 방지: 어노테이션 없으면 사용자에게 범위 확인. State(interaction)은 CSS pseudo만
- 아이콘: 근사치 SVG 금지. {config.iconSvgSource} 에서 실제 SVG 사용 또는 download_figma_images로 다운로드
- 디자인 토큰: **config.designTeamTokens 기존 토큰 우선 참조 (MUST)**. {config.tokensPath} 에서 중복 검색 후 재사용 또는 신규 생성. 임의값(bg-[#HEX]) 금지. 독자적 토큰 구조 생성 금지
- 컴포넌트: @headlessui/react + Tailwind v4 + clsx. {config.componentPrefix} 접두사. forwardRef 필수
- Storybook: globals.css에 @source 디렉티브 필수. 실행 명령은 프로젝트 package.json 참조
- 컴포넌트 완전성: **모든 Figma variant를 빠짐없이 구현** (일부만 구현 금지). 디자이너가 라이브러리 등록하려면 완벽한 컴포넌트 필요
- Code Connect: .figma.tsx 매핑 생성. **모든 variant를 동적으로 매핑** (빈 props/{} 금지, 하드코딩 예시 금지). **Figma property만 매핑** (텍스트 콘텐츠는 figma.string() 대상 아님). **variant restriction은 단일 값만** (배열 불가). publish 전 parse + 프로퍼티명 검증 필수. publish 명령은 프로젝트 package.json 참조
- QA Phase: Dev 완료 후 **독립 QA 서브에이전트 3개를 Task 도구로 병렬 실행** (QA-기능/QA-시각적/QA-토큰). 자기 테스트 금지 원칙. Playwright zoom 확대 검증. 미미한 차이도 타협 금지. QA FAIL → Dev 수정 → 재검증 (최대 3루프). 3루프 미해결 시 사용자 에스컬레이션. **매 루프마다 사용자에게 표 형식 보고**
- 에셋: **근사치 생성 절대 금지** (텍스트/유니코드 대체 금지). 로고/비정사각 SVG는 NdsIcon 대신 raw import 사용
- SVG: **fill → currentColor 변환 필수** (어두운 배경에서 아이콘이 보이지 않는 문제 방지)
- 기획 스펙: 기획 URL 제공 시 인터랙션 플로우, 데이터 제약, 비즈니스 룰을 추출하여 컴포넌트 구현에 반영 (Step 1.5). 미제공 시 건너뛰기
- 인터랙션: Figma variant 기반 인터랙션(isFocused, isCollapsed 등) 분석 및 연결 필수 (Step 6.5). 기획 스펙이 있으면 기획서 인터랙션도 반영
- 레이아웃: **중첩 패딩 구조 반영** (중첩 프레임의 padding을 하나로 합치지 않는다). scrollbar 기본 숨김 (`[scrollbar-width:none]`). 형제 요소 너비 비율 반영
- 증분 모드: `-a`는 새 컴포넌트만 빌드+삽입, `-u`는 Figma↔코드 diff 후 변경분만 반영. 기존 코드를 처음부터 다시 쓰지 않는다
- 구조적 추출: MCP 데이터에서 레이아웃 중첩, 형제 비율, fill 전수조사를 체계적으로 수행 (Step 1-5)
- 함정 목록: [known_pitfalls.md](references/known_pitfalls.md) — 실험에서 발견된 구체적 함정 빠른 참조

## 프로젝트 설정 파일 (.figma-to-react.config.md)

프로젝트 루트에 위치하며, 아래 섹션을 포함한다:

    ## 경로
    - componentPath: 컴포넌트 출력 경로
    - componentPrefix: 컴포넌트 접두사 (예: Nds)
    - tokensPath: 디자인 토큰 파일 경로
    - storybookPath: Storybook 경로
    - storybookPort: Storybook 포트
    - assetPath: 에셋 출력 경로 (icons/, logos/, images/)

    ## QA
    - maxQALoops: QA → Dev 수정 루프 최대 반복 횟수 (기본값: 3)

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
