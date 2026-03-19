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
4. [Interaction Graph 추출](references/interaction_graph.md) — Step 1.6 상세 절차
5. [Interaction Review](references/interaction_review.md) — Step 8.5 상세 절차
6. [디자인 토큰 관리 규칙](references/design_tokens.md)
7. [Code Connect 워크플로우](references/code_connect_workflow.md)
8. [QA Phase 워크플로우](references/qa_phase.md) — 독립 QA 서브에이전트 검증
9. [알려진 함정 목록](references/known_pitfalls.md) — 실험에서 발견된 구체적 함정 빠른 참조

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

    /figma-to-react -a <컴포넌트가-추가된-화면-url> [figma-spec-url]

    # 이미 빌드한 화면에 새 컴포넌트가 추가된 경우
    # 기존 화면 코드를 찾아서, 새 컴포넌트만 빌드 + 기존 코드에 삽입
    /figma-to-react -a https://...?node-id=5678-1234

### 화면 업데이트 (-u)

    /figma-to-react -u <변경된-화면-url> [figma-spec-url]

    # 기존 화면의 레이아웃/컴포넌트가 변경된 경우
    # 내부적으로 토큰 마이그레이션을 먼저 수행 후 디자인 diff 반영
    /figma-to-react -u https://...?node-id=5678-1234

    # 섹션/페이지 URL 지원 — 하위 프레임 자동 탐색 → 이름 기반 그룹화 → 그룹별 순차 처리
    /figma-to-react -u https://...?node-id=2101-46329

### 토큰 마이그레이션 (-m)

    /figma-to-react -m                              ← URL 없이 전체 일괄
    /figma-to-react -m <figma-url>                   ← URL 있으면 Figma 보완 매칭 추가

    # 전체 컴포넌트 일괄 토큰 치환 (Figma 불필요)
    /figma-to-react -m

    # 특정 컴포넌트/화면에 Figma 보완 매칭 포함
    /figma-to-react -m https://...?node-id=1234-5678

    핵심:
    - Figma URL 선택 사항 (없으면 정적 매핑 + HEX 매칭만)
    - 비즈니스 로직 변경 금지 (스타일만 변경)
    - 구 토큰 전수 교체 (매핑 테이블 기반)
    - 하드코딩 색상 적극 식별 및 토큰 전환
    - 디자인 변경(색상/크기/레이아웃 실제 변경)은 -u에서 처리

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

    1. Figma MCP 데이터 추출 → 1.5. 기획 스펙 보강 → 1.6. Interaction Graph 추출
    → 2. 어노테이션 파싱 → 3. 기존 컴포넌트 탐색 → 4. 아이콘/에셋 다운로드
    → 5. 디자인 토큰 매칭 → 6. React 컴포넌트 생성 → 6.5. 인터랙션 연결 → 화면 통합
    → 코드 변경이 있으면: 7. Storybook 스토리 → 8. QA Phase (dev 서버)
    → 8.5. Interaction Review → 9. Code Connect 등록
    → 10. 결과 요약

### 화면 수준 — 신규 (Top-down)

    1. 화면 MCP 추출 → 1.5. 기획 스펙 보강 → 1.6. Interaction Graph 추출
    → 2. 컴포넌트 인벤토리 → 3. 사용자 확인 → 4. 에셋 일괄 다운로드
    → 5. 미연결 컴포넌트 빌드 (Bottom-up, QA Phase 포함) → 6. 화면 조립 → 7. 결과 요약

### 화면 수준 — 증분 추가 (-a)

    1. 화면 MCP 추출 → 1.5. 기획 스펙 보강 → 2. 기존 코드 탐색
    → 3. 신규/기존 컴포넌트 분류 → 4. 신규 컴포넌트만 빌드
    → 5. 기존 화면 코드에 삽입
    → 코드 변경이 있으면: 6. QA Phase → 7. Storybook 업데이트 → 8. Code Connect 업데이트
    → 9. 결과 요약

### 화면 수준 — 업데이트 (-u)

    1. 화면/섹션 MCP 추출 (섹션 URL이면 하위 프레임 자동 탐색 → 이름 기반 그룹화)
    → 1.5. 기획 스펙 보강 → 2. 기존 코드 탐색
    → 2.5. 토큰 마이그레이션 (내부 자동 — 구 토큰 → 신 토큰 치환 + 하드코딩 제거)
    → 3. Figma ↔ 코드 diff (토큰 치환 후 비교) → 4. 변경 사항 분류 (추가/수정/삭제)
    → 5. 변경 사항 적용
    → 코드 변경이 있으면: 6. QA Phase → 7. Storybook 업데이트 → 8. Code Connect 업데이트
    → 9. 결과 요약
    → (그룹이 여러 개면 그룹별 순차 반복)

### 토큰 마이그레이션 (-m)

    URL 없이:
    1. 컴포넌트 탐색 → 2. 토큰 마이그레이션 맵 구성 (정적 매핑 + HEX 매칭)
    → 3. 변경 계획 사용자 확인 → 4. 변경 적용
    → 코드 변경이 있으면: 5. QA Phase → 6. Storybook 업데이트 → 7. Code Connect 업데이트
    → 8. 결과 요약

    URL 있으면:
    1. Figma MCP 추출 → 2. 컴포넌트 탐색
    → 3. 토큰 마이그레이션 맵 구성 (정적 매핑 + HEX 매칭 + Figma 보완)
    → 4. 변경 계획 사용자 확인 → 5. 변경 적용
    → 코드 변경이 있으면: 6. QA Phase → 7. Storybook 업데이트 → 8. Code Connect 업데이트
    → 9. 결과 요약

## 핵심 규칙 요약

- 재사용 우선: Code Connect 매핑 → 로컬 탐색 → 신규 생성 순. props 50% 이상 공유하면 재사용
- 과잉 생성 방지: 어노테이션 없으면 사용자에게 범위 확인. State(interaction)은 CSS pseudo만
- 아이콘: 근사치 SVG 금지. {config.iconSvgSource} 에서 실제 SVG 사용 또는 download_figma_images로 다운로드
- 디자인 토큰: **config.tokensCssPath에서 시맨틱 토큰을 먼저 매칭 (MUST)**. 매칭되면 Tailwind 유틸리티 클래스 직접 사용 (예: `bg-layer-01`, `text-text-primary`). 매칭 실패 시 config.portalCssPath에 신규 토큰 추가 후 Tailwind 유틸리티로 사용. HEX 임의값(`bg-[#HEX]`) 금지, CSS 변수 임의값(`bg-[var(--color-*)]`)은 허용. tokens.css 직접 수정 절대 금지
- 컴포넌트: @headlessui/react + Tailwind v4 + clsx. {config.componentPrefix} 접두사. forwardRef 필수
- Storybook: 개발 참고용(variant 확인, 빠른 이터레이션). globals.css에 @source 디렉티브 필수. **QA 검증 대상이 아님** — QA는 dev 서버에서 수행
- 컴포넌트 완전성: **모든 Figma variant를 빠짐없이 구현** (일부만 구현 금지). 디자이너가 라이브러리 등록하려면 완벽한 컴포넌트 필요
- Code Connect: .figma.tsx 매핑 생성. **모든 variant를 동적으로 매핑** (빈 props/{} 금지, 하드코딩 예시 금지). **Figma property만 매핑** (텍스트 콘텐츠는 figma.string() 대상 아님). **variant restriction은 단일 값만** (배열 불가). publish 전 parse + 프로퍼티명 검증 필수. publish 명령은 프로젝트 package.json 참조
- QA Phase: 컴포넌트를 화면에 통합 후 **dev 서버에서** 독립 QA 서브에이전트 3개를 병렬 실행 (QA-기능/QA-시각적/QA-토큰). Storybook이 아닌 **실제 앱 환경**에서 검증. 자기 테스트 금지 원칙. Playwright zoom 확대 검증. 미미한 차이도 타협 금지. QA FAIL → Dev 수정 → 재검증 (최대 3루프). 3루프 미해결 시 사용자 에스컬레이션. **매 루프마다 사용자에게 표 형식 보고**. **QA-기능은 실제 사용자 인터랙션 플로우(파일 업로드, 클릭 확대 등)를 Playwright로 시뮬레이션 필수**
- 오버레이/프리뷰: 모달, 프리뷰 등 오버레이는 **반드시 Portal(createPortal)로 document.body에 렌더링**. 이미지 확대는 transform: scale() 사용. event propagation 방지(stopPropagation) 필수
- 에셋: **근사치 생성 절대 금지** (텍스트/유니코드 대체 금지). 로고/비정사각 SVG는 NdsIcon 대신 raw import 사용
- SVG: **fill → currentColor 변환 필수** (어두운 배경에서 아이콘이 보이지 않는 문제 방지)
- 기획 스펙: 기획 URL 제공 시 인터랙션 플로우, 데이터 제약, 비즈니스 룰을 추출하여 컴포넌트 구현에 반영 (Step 1.5). 미제공 시 건너뛰기
- Main Component 조회: 컴포넌트 URL 입력 시 해당 노드에서, 화면 URL 입력 시 Code Connect 없는 INSTANCE의 componentId로 Main Component를 resolve하여 **interactions + dev 코멘트 추출 필수** (Step 1.6-5). 인스턴스에는 인터랙션/코멘트가 복사되지 않으므로 반드시 Main Component를 직접 조회
- Interaction Graph: REST API로 Figma interactions 추출 → State Machine/Navigation/Overlay/Variable Mode 그래프 자동 생성 (Step 1.6). Main Component의 dev 코멘트도 함께 추출. 추론된 인터랙션은 Step 8.5에서 사용자 확인
- 인터랙션: Figma variant 기반 인터랙션(isFocused, isCollapsed 등) 분석 및 연결 필수 (Step 6.5). Interaction Graph의 Navigation/Overlay 연결 포함. 기획 스펙이 있으면 기획서 인터랙션도 반영
- 레이아웃: **중첩 패딩 구조 반영** (중첩 프레임의 padding을 하나로 합치지 않는다). scrollbar 기본 숨김 (`[scrollbar-width:none]`). 형제 요소 너비 비율 반영
- 증분 모드: `-a`는 새 컴포넌트만 빌드+삽입, `-u`는 내부 토큰 마이그레이션 후 Figma↔코드 diff 반영 (섹션/페이지 URL로 하위 프레임 자동 탐색+그룹화 지원), `-m`은 구 토큰 → 신 토큰 이름 치환 + 하드코딩 제거 전용 (Figma URL 선택사항, 디자인 변경은 -u에서, 비즈니스 로직 불변). 기존 코드를 처음부터 다시 쓰지 않는다
- 구조적 추출: MCP 데이터에서 레이아웃 중첩, 형제 비율, fill 전수조사를 체계적으로 수행 (Step 1-5)
- 함정 목록: [known_pitfalls.md](references/known_pitfalls.md) — 실험에서 발견된 구체적 함정 빠른 참조

## 프로젝트 설정 파일 (.figma-to-react.config.md)

프로젝트 루트에 위치하며, 아래 섹션을 포함한다:

    ## 경로
    - componentPath: 컴포넌트 출력 경로
    - componentPrefix: 컴포넌트 접두사 (예: Nds)
    - tokensCssPath: 자동 생성 CSS 토큰 파일 경로 (tokens.css)
    - portalCssPath: 수동 관리 CSS 토큰 파일 경로 (portal.css)
    - tokenSourceDir: DTCG 토큰 소스 디렉토리 (참조용)
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
    - tokensCssPath: 자동 생성 CSS 토큰 (tokens.css) — 수정 금지
    - portalCssPath: 수동 관리 CSS 토큰 (portal.css) — AI Portal 전용
    - tokenSourceDir: DTCG 멀티파일 토큰 소스 디렉토리 (참조용)

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
- 디자인 토큰: tokens.css + portal.css 기반 CSS 변수 체계 구축 완료. Tailwind 유틸리티 클래스 직접 사용
- Claude 비결정성: 동일 입력에도 다른 코드 → Playwright 테스트로 품질 보장
- Interaction Graph: 프로토타입 미연결 시 NAVIGATE/OVERLAY 추출 불가 → 구조 추론 + Step 8.5 사용자 대화로 보완. 데이터 흐름/비즈니스 로직은 기획 스펙에서 보강
