# 파이프라인 상세 워크플로우

## Step 1: Figma URL 파싱, 이미지 확인, MCP 데이터 추출

### 1-1. URL 파싱

    입력: https://www.figma.com/design/{fileKey}?node-id={nodeId}&...
    추출: fileKey, nodeId

### 1-2. Figma 원본 이미지 다운로드 (최우선)

MCP 데이터 추출보다 먼저 이미지를 다운로드한다.
사용자가 올바른 노드를 지정했는지 시각적으로 확인하기 위함이다.

    도구: download_figma_images (Framelink MCP)
    입력: nodeId, format: "png"
    저장: temp/visual-comparison/{ComponentName}/figma-original.png

### 1-3. 이미지 검증 및 사용자 확인

다운로드 후 이미지를 Read 도구로 열어서 확인한다:

    검증 항목:
    1. 파일 존재 여부: 이미지 파일이 정상적으로 저장되었는지
    2. 빈 이미지 여부: 완전히 빈(흰색/투명) 이미지가 아닌지
    3. 컴포넌트 식별: 기대하는 컴포넌트(버튼, 인풋 등)가 보이는지
    4. variant 포함 여부: 주요 variant(톤, 사이즈 등)가 렌더링되어 있는지

검증 통과 후 사용자에게 이미지를 보여주고 확인한다:

    "Figma에서 다운로드한 이미지입니다. 이 컴포넌트가 맞습니까?"
    → 사용자 확인 후 다음 단계로 진행

    INVALID 또는 사용자가 아니라고 한 경우:
    1. nodeId를 확인하고 download_figma_images 1회 재시도
    2. 재시도에도 실패하면 사용자에게 올바른 node-id를 요청
    3. 다운로드 자체 실패 시: 경고 출력 후 진행 (Step 9 시각적 비교 루프는 건너뜀)

이 이미지는 이후 Step 6(컴포넌트 생성) 시 시각적 참고 자료로,
Step 9(시각적 비교 루프)에서 비교 기준 이미지로 재사용한다.

### 1-4. 노드 타입 판별 및 MCP 선택

사용자 확인이 완료되면 노드 타입에 따라 MCP를 선택하여 데이터를 추출한다.

    노드 타입 판별:
    - 컴포넌트 노드: type이 COMPONENT 또는 COMPONENT_SET → Framelink MCP
    - 화면 프레임 노드: type이 FRAME이고, 내부에 INSTANCE 노드들을 포함 → 공식 MCP

#### Framelink MCP — 컴포넌트 빌드용

    도구: get_figma_data
    입력: url (Figma URL), nodeId
    응답: Compact YAML (~13KB) — 레이아웃, 색상, 폰트, componentProperties 포함
    특징: componentProperties에 Figma variant 값(tone, variant, size) 포함
    토큰: ~3.4K tokens
    용도: 개별 컴포넌트를 처음 만들 때 (시각적 일치도 최고 79/100)

#### Figma 공식 MCP + Code Connect — 화면 조립용

    도구: get_design_context
    입력: url (Figma URL)
    응답: React 코드 + 디자인 토큰 + CodeConnectSnippet (~10.5KB)
    특징: 등록된 컴포넌트는 import 경로+props가 바로 제공 → 코드베이스 탐색 불필요
    토큰: ~2.6K tokens
    용도: Code Connect 매핑된 컴포넌트들로 화면을 조립할 때

#### Raw JSON (REST API curl) — 사용 금지

    706KB(~176K 토큰) 응답으로 컨텍스트 폭발
    숨김 요소(visible 플래그 없음) 오판으로 레이아웃 왜곡
    시각적 일치도 최저(55/100)

node-id를 지정하여 해당 노드만 조회한다 (페이지 전체 조회 금지 — 토큰 절약).

### 추출 대상 데이터
- variant property 이름과 값 목록
- 각 변형의 fill/stroke 색상 (RGBA 또는 HEX)
- 텍스트 스타일 (font-family, font-size, font-weight, line-height)
- 레이아웃 정보 (padding, gap, border-radius)
- 컴포넌트 Description ([MCP:ComponentSpec] 어노테이션 포함 여부 확인)
- CodeConnectSnippet (공식 MCP 사용 시 — import 경로 + props 매핑)
- 디자인 토큰 이름 (공식 MCP 사용 시 — text-secondary-default 등)

### 구조적 추출 전략 (MUST)

MCP 응답을 수동적으로 읽지 않고, 아래 체크리스트에 따라 **체계적으로** 추출한다.
세션 로그 분석에서 중첩 레이아웃, 형제 요소 비율, fill 색상 등을 놓쳐 시각적 비교 루프가 소진된 사례가 있었다.

#### 1-5-a. 레이아웃 중첩 구조 추출

MCP 응답의 노드 트리에서 중첩된 프레임(FRAME)을 식별하고, 각 수준의 padding/gap을 기록한다:

    예: 3중 중첩 구조
    OuterFrame (padding: 8px)
    └── InnerFrame (padding: 8px)
        └── ContentFrame (padding: 0)
    → 실효 패딩: 8 + 8 = 16px (코드에서 반드시 반영)

    추출 형식:
    | 프레임 | padding | gap | direction |
    |--------|---------|-----|-----------|
    | Outer  | 8px     | 12px| column    |
    | Inner  | 8px     | 8px | row       |
    | Content| 0       | 4px | row       |

#### 1-5-b. 형제 요소 너비/비율 비교

같은 부모 아래 형제 요소들의 너비 비율을 명시적으로 기록한다:

    예: Sidebar와 MainContent가 형제인 경우
    Parent (row, gap: 0)
    ├── Sidebar (width: 240px, fixed)
    └── MainContent (flex: 1)

    예: PromptArea와 QuickCards가 형제인 경우
    Parent (row, gap: 16px)
    ├── PromptArea (width: 60%)
    └── QuickCards (width: 40%)

    MUST: 형제 요소의 width가 비율/고정값 중 어느 것인지 반드시 구분하여 기록한다.

#### 1-5-c. fill/stroke 색상 전수 조사

모든 FRAME과 TEXT 노드의 fill/stroke 색상을 추출한다:

    추출 형식:
    | 노드 | fill RGBA | fill HEX | 용도 |
    |------|-----------|----------|------|
    | Background | 0.024, 0.020, 0.039, 1 | #06050A | 배경 |
    | Text Label | 1, 1, 1, 1 | #FFFFFF | 텍스트 |
    | Border | 0.114, 0.122, 0.125, 0.2 | #1D1F2033 | 보더 |

    특히 어두운 배경(#06050A 등)에 어두운 fill 색상(#222D44 등)이 있으면
    해당 SVG/아이콘은 currentColor 변환이 필수임을 표기한다.

#### 1-5-d. 인터랙션 관련 variant 식별

Figma variant property 중 인터랙션 상태를 나타내는 것을 별도 분류한다:

    인터랙션 variant 예시:
    - isFocused: true/false → focus 상태 전환
    - isCollapsed: true/false → 접기/펼치기 전환
    - state: default/hover/active → CSS pseudo 또는 React state
    - theme: light/dark → 테마 전환

    분류:
    - CSS pseudo로 처리: hover, focus, active, pressed
    - React state로 처리: isFocused, isCollapsed, isExpanded, isSelected
    - 조건부 렌더링으로 처리: theme, mode, visibility

## Step 1.5: 기획 스펙 보강

### 목적

Figma 기획 페이지(FigNotion 위젯, 텍스트 프레임 등)에서 인터랙션 플로우, 데이터 제약,
비즈니스 룰을 추출하여 컴포넌트 구현의 완성도를 높인다.

컴포넌트 MCP 데이터는 시각적 정보(색상, 크기, variant)만 포함하므로,
"대화 제목 최대 20자", "파일 첨부 최대 10개", "관리자만 표시" 같은 기획 의도는 담지 못한다.
이 Step에서 기획 페이지를 읽어 그 간극을 메운다.

### 실행 조건

- 기획 URL이 제공된 경우: 이 Step 실행
- 기획 URL이 없는 경우: 이 Step **건너뛰기** (기존 동작 유지, 파이프라인에 영향 없음)

### 1-5-1. 기획 페이지 MCP 추출

Framelink MCP `get_figma_data`로 기획 노드 데이터를 추출한다.

    도구: get_figma_data
    입력: url (기획 페이지 Figma URL), nodeId
    대상: FigNotion 위젯, 텍스트 레이어, 프레임 내 텍스트 등 모든 텍스트 콘텐츠

기획 페이지는 주로 아래 형태로 존재한다:
- FigNotion 위젯: Notion 문서를 Figma에 동기화한 위젯 (가장 일반적)
- 텍스트 프레임: 디자이너가 직접 작성한 텍스트 레이어 모음
- 스티키 노트: FigJam에서 가져온 기획 메모

### 1-5-2. 기획 스펙 파싱

추출된 텍스트에서 아래 4가지 카테고리로 분류한다:

    | 카테고리 | 추출 대상 | 식별 키워드 |
    |----------|-----------|-------------|
    | 인터랙션 플로우 | 사용자 동작 → 시스템 반응 시퀀스 | 클릭, 선택, 입력, 이동, 전환, 열기, 닫기 |
    | 데이터 제약 | 최대/최소값, 허용 타입, 필수 여부, 글자수 | 최대, 이하, 이내, 제한, 필수, ~만 허용 |
    | 비즈니스 룰 | 조건부 로직, 권한, 상태 전이, 삭제 보호 | ~만, ~경우, 불가, 금지, 관리자, 권한 |
    | 미결정 사항 | TBD, 미정, 추후 결정 항목 | 미정, TBD, 추후, 논의 필요, 결정 필요 |

파싱 결과를 구조화된 형식으로 정리한다:

    ## 기획 스펙 요약: {컴포넌트/화면명}

    ### 인터랙션 플로우
    - [IF-01] 새 채팅 버튼 클릭 → 초기 화면으로 리셋
    - [IF-02] 프롬프트 입력 후 전송 → 최근 대화 기록에 새 항목 추가
    - [IF-03] 대화 기록 항목 클릭 → 중앙 영역에 이전 대화 내용 로드

    ### 데이터 제약
    - [DC-01] 대화 제목: 프롬프트 요약 자동 생성, 최대 20자
    - [DC-02] 프롬프트 사전 설명: 최대 20자, 초과 시 말줄임(...)
    - [DC-03] 파일 첨부: 이미지/텍스트/PDF만 허용, 최대 10개

    ### 비즈니스 룰
    - [BR-01] DLP 설정: 관리자 계정만 표시 (역할 기반 가시성)
    - [BR-02] 로컬 모델: 삭제 불가 (삭제 보호)
    - [BR-03] 권한 관리/감사 로그: 기존 Polestar 10 기능 그대로 사용

    ### 미결정 사항
    - [TBD-01] 사용자 포탈 이동: 화면 전환 vs 새 창 (미정)
    - [TBD-02] 도구 선택 UI: SelectBox vs 클릭 컴포넌트 (UX 권장: 클릭 컴포넌트)

### 1-5-3. 사용자 확인

파싱 결과를 사용자에게 보여주고 확인한다:

    확인 항목:
    1. 누락된 스펙이 있는지 (기획서에 있지만 파싱에서 빠진 항목)
    2. 미결정 사항에 대한 방향 (구현 시 어떤 선택지를 따를지)
    3. 구현 범위 (모든 스펙 구현 vs 현재 컴포넌트에 해당하는 것만)

사용자에게 질문:
- "기획 스펙 {N}개 항목을 추출했습니다. 누락되거나 수정할 항목이 있습니까?"
- "미결정 사항 {N}개가 있습니다. 현재 구현에서 어떻게 처리할까요?"

### 1-5-4. 스펙 매핑 (빌드 대상 컴포넌트 대응)

기획 스펙 항목을 현재 빌드 대상 컴포넌트/화면에 매핑한다:

    매핑 형식:
    | 스펙 ID | 카테고리 | 내용 | 대상 컴포넌트 | 반영 Step |
    |---------|----------|------|---------------|-----------|
    | DC-01   | 데이터 제약 | 대화 제목 최대 20자 | ConversationItem | Step 6 (props) |
    | IF-02   | 인터랙션 | 전송 → 기록 추가 | PromptInput | Step 6.5 (인터랙션) |
    | BR-01   | 비즈니스 룰 | DLP 관리자만 | SettingsModal | Step 6 (조건부 렌더링) |

    판단 기준:
    - 현재 빌드 대상 컴포넌트에 직접 관련: 반영 (해당 Step에서 구현)
    - 다른 컴포넌트에 관련: 기록만 (결과 요약에 포함, 추후 구현 시 참조)
    - 시스템 수준 요구사항: 기록만 (백엔드/인프라 관련)

### 이후 Step에서의 활용

    | Step | 활용 방식 | 예시 |
    |------|-----------|------|
    | Step 2 | 인터랙션 플로우로 variant 분석 보강 | 기획서의 상태 전이를 React state 후보에 추가 |
    | Step 6 | 데이터 제약을 props type/validation에 반영 | maxLength, accept, max 등 제약 props 추가 |
    | Step 6.5 | 인터랙션 플로우를 구현 근거로 활용 | 기획서 [IF-xx] 기반 이벤트 핸들러 구현 |
    | Step 8 | 데이터 제약/비즈니스 룰 기반 테스트 추가 | 20자 초과 입력 시 truncation 검증 등 |
    | Step 11 | 기획 스펙 반영률 보고 | 전체 N개 중 M개 반영, K개 미반영(사유) |

## Step 1.6: Interaction Graph 추출

Figma REST API에서 interactions 필드를 추출하여 State Machine / Navigation / Overlay / Variable Mode 그래프를 자동 생성한다.
MCP 도구는 interactions를 생략하므로 REST API 직접 호출이 필수.

상세 절차는 [interaction_graph.md](interaction_graph.md) 참조.

### 요약

1. REST API 호출: `GET /v1/files/{fileKey}/nodes?ids={nodeId}&depth=10` (FIGMA_ACCESS_TOKEN 사용)
2. 응답에서 interactions 배열이 있는 노드를 재귀 수집
3. 4가지 그래프로 분류:
   - A. State Machine (CHANGE_TO) → 컴포넌트 내부 상태 설계
   - B. Navigation Map (NAVIGATE) → 라우팅/뷰 전환
   - C. Overlay Map (OVERLAY + CLOSE) → 모달/팝오버
   - D. Variable Mode (SET_VARIABLE_MODE) → 테마/모드 전환
4. **Main Component 조회** (MUST):
   - 컴포넌트 URL 입력 시: 해당 노드에서 바로 interactions + dev 코멘트 추출
   - 화면 URL 입력 시: INSTANCE의 componentId로 Main Component resolve → interactions + dev 코멘트 추출
   - Code Connect가 있는 인스턴스는 건너뛰기 (이미 매핑됨)
   - Comments API(`GET /v1/files/{fileKey}/comments`)로 dev 코멘트 추출, node_id로 필터링
5. 프로토타입 미연결 시 구조 추론 (variant property, 노드 naming, 기획 스펙)
6. 기획 스펙(Step 1.5)과 교차 대조

### Main Component 조회가 중요한 이유

인스턴스에는 prototype interaction과 dev 코멘트가 복사되지 않는다.
Main Component에만 디자이너가 설정한 hover/click/focus 인터랙션과
구현 의도를 설명하는 dev 코멘트가 달려 있다.
이 정보 없이 컴포넌트를 빌드하면 인터랙션이 누락되고 사용자가 별도로 요청해야 한다.

### 이후 Step에서의 활용

| Step | 활용 방식 |
|------|-----------|
| Step 2 | State Machine을 React state 후보에 추가 |
| Step 6 | Dev 코멘트의 스타일 지시를 컴포넌트 생성에 반영 |
| Step 6.5 | Main Component interactions + Navigation/Overlay 연결 |
| Step 8 | QA-기능에 Interaction Graph 검증 항목 추가 |
| Step 8.5 | 추론된 인터랙션 사용자 확인 |

## Step 2: 어노테이션 파싱

### [MCP:ComponentSpec] 존재 시
1. Description 또는 텍스트 레이어에서 [MCP:ComponentSpec] 블록 추출
2. 섹션별 파싱: State(interaction), Prop, Rule, Priority
3. component_spec.md 규칙에 따라 props와 CSS pseudo 분리
4. 유효 조합 규칙 적용

### [MCP:ComponentSpec] 없음 (폴백)
1. Figma variant property에서 props 추론
2. state 관련 property는 CSS pseudo로 분류
3. **인터랙션 variant 분석** (Step 1-5-d에서 식별한 목록 활용):
   - 인터랙션 variant(isFocused, isCollapsed 등)를 React state로 구현할 대상 목록 작성
   - 각 variant가 어떤 시각적 변화를 일으키는지 MCP 데이터에서 확인
   - CSS pseudo로 충분한 것(hover, active)과 React state가 필요한 것(isFocused, isCollapsed) 구분
3-a. **Interaction Graph 기반 보강** (Step 1.6에서 그래프가 생성된 경우):
   - State Machine의 각 항목을 React state 후보에 추가
   - CHANGE_TO destination의 variant 값을 실제 state 이름으로 사용
   - State Machine의 트리거를 이벤트 핸들러 후보에 추가 (ON_CLICK → onClick, ON_HOVER → onMouseEnter, AFTER_TIMEOUT → useEffect)
   - Navigation Map의 항목을 라우팅 후보에 추가 (대상 화면명 → kebab-case route path)
   - Overlay Map의 항목을 모달/팝오버 후보에 추가 (대상 오버레이 → Headless UI 컴포넌트 매핑)
3-b. **기획 스펙 기반 보강** (Step 1.5에서 기획 스펙이 추출된 경우):
   - 기획서의 인터랙션 플로우([IF-xx])를 variant 분석에 추가
   - Figma variant에 없지만 기획서에 명시된 인터랙션을 React state 후보에 포함
   - 기획서의 데이터 제약([DC-xx])을 props 타입 제약 목록에 추가
   - 기획서의 비즈니스 룰([BR-xx])을 조건부 렌더링/로직 대상에 추가
4. **화면 수준 상태 전환 분석** (화면 프레임인 경우):
   - 화면 내 컴포넌트 간 상호작용 파악 (예: 퀵카드 클릭 → 프롬프트 입력 채우기)
   - 조건부 렌더링 요소 식별 (예: 배경 그라데이션이 특정 상태에서만 표시)
   - 상태 전환 다이어그램 작성 (간단한 텍스트 형식)
   - 기획 스펙의 인터랙션 플로우가 있으면 상태 전환 근거로 활용
5. **사용자에게 구현 범위 확인 질문**:
   - "Figma에 {N}개 variant property가 있습니다. 모두 구현할까요?"
   - "인터랙션 variant {목록}이 발견되었습니다. 구현할까요?"
   - contentType 등 변형이 있으면 "iconEnd, iconOnly 등도 구현할까요?"
6. 확인 후 진행

## Step 3: 기존 컴포넌트 탐색

### 목적
신규 생성 전에 재사용 가능한 기존 컴포넌트가 있는지 확인한다.
불필요한 중복 컴포넌트 생성을 방지한다.

### 탐색 순서

#### 1순위: Code Connect 매핑 확인 (MCP 응답) — 최우선

MCP 응답에 CodeConnectSnippet이 포함되어 있으면 해당 컴포넌트는 이미 등록되어 있다.
- CodeConnectSnippet에 import 경로와 사용법이 포함됨
- **Glob/Grep/Read 코드베이스 탐색을 하지 않는다** (도구 호출 92% 절감의 핵심)
- 추가 탐색 없이 바로 사용 가능
- 이 경우 Step 4~5를 건너뛰고 조립 단계로 진행
- 단, props 인터페이스 확인이 필요하면 Read 1회만 허용

#### 2순위: 로컬 코드베이스 탐색
CodeConnectSnippet이 없는 경우 기존 방식으로 탐색한다.
프로젝트 설정의 {config.componentPath} 에서
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

## Step 4: 아이콘/에셋 다운로드

### 목적
MCP 방식과 무관하게 아이콘(IMAGE-SVG 타입)은 벡터 데이터가 응답에 포함되지 않는다.
인라인 근사치 SVG를 생성하면 시각적 일치도가 크게 떨어진다 (실험 M10 아이콘 항목 8~13/25).
실제 SVG 에셋을 다운로드하여 사용한다.

### 근사치 에셋 생성 절대 금지 (CRITICAL)

아래 행위는 어떤 경우에도 허용하지 않는다:

    금지 사항:
    ❌ 로고를 텍스트로 대체 (예: <span>+</span>Lucida<span>beta</span>)
    ❌ 아이콘을 유니코드 문자로 대체 (예: ★, ☰, ⚙)
    ❌ SVG를 직접 손으로 작성하여 근사치 생성
    ❌ 빈 div에 배경색만 넣어 아이콘 자리 대체

    허용 사항:
    ✅ 실제 SVG 파일 사용 ({config.iconSvgSource} 또는 download_figma_images)
    ✅ 실제 SVG 파일을 찾을 수 없는 경우에만 placeholder + TODO 주석
    ✅ placeholder는 반드시 빈 사각형 + TODO 주석 형태 (텍스트/유니코드 아님)

### 대상 식별 — 에셋 체크리스트 (MUST)

MCP 응답에서 아래 유형의 노드를 **전수 조사**하여 체크리스트를 작성한다:

    | # | 노드명 | 유형 | nodeId | 상태 |
    |---|--------|------|--------|------|
    | 1 | logo   | 로고 SVG | 1234:5678 | 미확보 |
    | 2 | settings-icon | 아이콘 SVG | 2345:6789 | 로컬 발견 |
    | 3 | hero-image | 일러스트 | 3456:7890 | 미확보 |
    | 4 | theme-toggle | 아이콘 SVG | 4567:8901 | 미확보 |

    식별 기준:
    - IMAGE-SVG 타입 노드 (아이콘, 로고, 일러스트)
    - 에셋 URL이 포함된 노드 (공식 MCP의 경우 7일 만료 URL)
    - 노드 이름에 icon, logo, image, illustration, asset 등이 포함된 것
    - INSTANCE 노드 중 내부에 벡터(VECTOR) 또는 이미지(IMAGE) 포함된 것

    화면 수준 빌드 시에는 화면 전체에 사용된 모든 에셋을 누락 없이 목록화한다.

### 에셋 유형별 처리 방식

#### 아이콘 (정사각형 SVG)
- NdsIcon 컴포넌트의 `import.meta.glob`으로 로딩
- {config.iconSvgSource}에서 검색 → 없으면 download_figma_images

#### 로고/비정사각형 SVG (CRITICAL — 실험에서 발견된 함정)
- NdsIcon 대신 **raw SVG import**로 직접 사용
- 로고는 비율이 다양하므로 정사각형 아이콘 컴포넌트에 맞지 않는다

    // 로고 사용 — raw import 방식
    import logoSvg from '{config.assetPath}/logos/logo.svg?raw'

    <div dangerouslySetInnerHTML={{ __html: logoSvg }} />

    // 또는 img 태그로 사용
    import logoUrl from '{config.assetPath}/logos/logo.svg'
    <img src={logoUrl} alt="Logo" />

#### 일러스트/이미지
- img 태그 또는 background-image로 사용
- placeholder는 빈 div + aspect-ratio + TODO 주석

### 다운로드 방식

#### Framelink MCP 사용 시

    도구: download_figma_images
    입력: nodeId, format: "svg"
    저장: {config.assetPath}/icons/{icon-name}.svg (아이콘)
          {config.assetPath}/logos/{logo-name}.svg (로고)

#### 공식 MCP 사용 시
응답에 포함된 에셋 URL로 직접 다운로드한다.
단, URL은 7일 만료이므로 즉시 다운로드하여 로컬에 저장한다.

### 다운로드 불가 시
- placeholder SVG + TODO 주석을 남긴다
- 결과 요약에 "placeholder {N}개 — 수동 에셋 제공 필요" 명시
- 사용자에게 SVG 에셋 제공을 안내한다
- 절대 텍스트나 유니코드로 대체하지 않는다

### 에셋 파일 구조

    {config.assetPath}/
    ├── icons/         # 정사각형 아이콘 SVG
    ├── logos/         # 로고 SVG (비정사각형 포함)
    └── images/        # 아바타, 일러스트 등

### 아이콘 소스 우선순위

프로젝트 설정에 {config.iconSvgSource} 가 있으면 로컬 SVG 파일을 먼저 검색한다:
1. {config.iconSvgSource} 에서 아이콘 이름으로 Glob 검색 (부분 일치 포함)
2. 있으면: 로컬 파일을 {config.assetPath}/icons/ 에 복사하여 사용
3. 없으면: download_figma_images로 Figma에서 다운로드
4. 다운로드도 실패 시: placeholder + TODO (텍스트/유니코드 대체 금지)

### 아이콘 매핑 정확성 (MUST)

MCP 데이터에서 아이콘 노드의 **정확한 이름**을 확인하고 매핑한다:

    잘못된 매핑 예시:
    ❌ 노드명 "star" → application-star-o.svg (이름만 보고 추측)
    실제로는 "theme toggle sunny" 아이콘이었음

    올바른 매핑 절차:
    1. MCP 응답에서 아이콘 노드의 정확한 이름과 상위 컨텍스트를 확인
    2. 상위 프레임의 용도 확인 (예: "settings" 프레임 안 → 설정 아이콘)
    3. {config.iconSvgSource}에서 매칭되는 SVG 검색
    4. 확신이 없으면 download_figma_images로 Figma 원본 다운로드

### SVG fill → currentColor 변환 (MUST)

다운로드하거나 복사한 SVG의 하드코딩된 fill/stroke 색상을 `currentColor`로 변환한다:

    변환 대상:
    - fill="#XXXXXX" → fill="currentColor"
    - fill="rgb(...)" → fill="currentColor"
    - stroke="#XXXXXX" → stroke="currentColor"

    변환 제외:
    - fill="none" (투명 fill은 유지)
    - 로고 등 다색 SVG (원본 색상 유지)

    이유: 하드코딩된 어두운 fill(#222D44)이 어두운 배경(#06050A)에서 보이지 않는 문제가
    실험에서 발견되었다. currentColor로 변환하면 부모의 text 색상을 상속하여 자동 대응한다.

## Step 5: 디자인 토큰 매칭

### 토큰 소스 (CRITICAL)

    토큰 소스:
    - config.tokensCssPath → tokens.css (자동 생성, 수정 금지)
    - config.portalCssPath → portal.css (수동 관리, AI Portal 전용)
    - config.tokenSourceDir → tokens/ (DTCG 소스, 참조용)

    tokens.css는 npm run build:tokens로 자동 생성.
    절대 수동 수정하지 않는다. 새 토큰이 필요하면 portal.css에 추가한다.

### 절차

#### 5-1. tokens.css 파싱

config.tokensCssPath 파일을 Read로 읽고 `@theme { }` 블록에서 CSS 변수명 → 값 맵을 구성한다.

    파싱:
    1. @theme { } 블록에서 --변수명: 값; 패턴 추출
    2. [data-theme="dark"] { } 블록에서 다크 모드 오버라이드 추출
    3. [data-theme="contrast"] { } 블록에서 고대비 모드 오버라이드 추출

    결과: { 변수명: { light: 값, dark: 값, contrast: 값 } }

#### 5-2. portal.css 파싱

config.portalCssPath 파일을 Read로 읽고 동일하게 파싱하여 맵에 병합한다.

#### 5-3. Figma 색상 RGBA → HEX 변환

Figma MCP에서 추출한 색상값(RGBA)을 HEX로 변환한다. (기존과 동일)

    변환: Math.round(value * 255).toString(16).padStart(2, '0')
    alpha가 1이면 6자리, 아니면 8자리 HEX

#### 5-4. 시맨틱 토큰 매칭 (우선)

Theme 카테고리 토큰에서 우선 검색한다.

    검색 대상 카테고리 (시맨틱):
    background, layer, field, border, text, icon, link,
    feedback, interactive, focus, overlay

    매칭 시: Tailwind 유틸리티 클래스로 직접 출력
    예: --color-layer-01: #ffffff → bg-layer-01

#### 5-5. 컴포넌트 전용 토큰 매칭

시맨틱 매칭 실패 시 컴포넌트 전용 토큰에서 검색한다.

    검색 대상 카테고리:
    chip, tag, badge, toggle, tooltip, notification,
    codeblock, prompt-input, chatting-bubble

#### 5-6. Core 토큰 매칭

시맨틱/컴포넌트 매칭 실패 시 Core 팔레트에서 검색한다. (지양)

    지양 이유: Core 팔레트(gray-cool-500 등)는 테마 전환 시 값이 변하지 않아
    다크 모드에서 문제가 발생한다.
    불가피한 경우에만 사용하되, 결과 보고에 명시한다.

#### 5-7. 사이즈 토큰 매칭

Figma에서 추출한 height/padding/gap 값을 컴포넌트 사이즈 토큰으로 매칭한다.

    --comp-height-* → h-[var(--comp-height-*)]
    --comp-padding-x-* → px-[var(--comp-padding-x-*)]
    --comp-padding-y-* → py-[var(--comp-padding-y-*)]
    --comp-gap-* → gap-[var(--comp-gap-*)]

#### 5-8. 타이포 토큰 매칭

Figma에서 추출한 fontSize/lineHeight 조합을 text-* 클래스로 매칭한다.

    | fontSize | lineHeight | Tailwind 클래스 |
    |----------|-----------|-----------------|
    | 11px     | 16px      | text-caption    |
    | 12px     | 18px      | text-helper     |
    | 14px     | 20px      | text-body       |
    | 16px     | 24px      | text-body-reading 또는 text-subtitle |
    | 20px     | 28px      | text-title      |
    | 28px     | 36px      | text-heading    |
    | 36px     | 44px      | text-display    |
    | 48px     | 56px      | text-hero       |

    fontWeight은 별도 유틸리티:
    Medium (500) → font-medium, SemiBold (600) → font-semibold, Bold (700) → font-bold

#### 5-9. 미매칭 토큰 처리

매칭 실패한 색상은 portal.css에 신규 CSS 변수를 추가한다.

    추가 규칙:
    - portal.css의 @theme { } 블록 내에 정의
    - 기존 portal.css의 네이밍 패턴 준수
    - 주석으로 용도를 명시
    - tokens.css는 절대 수정하지 않는다

#### 5-10. 매칭 결과 보고

사용된 토큰 목록과 미매칭 목록을 출력한다.

    ### 토큰 매칭 결과
    - 매칭: {N}개
      - bg-layer-01 (--color-layer-01: #ffffff)
      - text-text-primary (--color-text-primary: #101213)
    - portal.css 추가: {N}개
      - --color-{name}: #HEX (용도: ...)
    - Core 팔레트 사용 (지양): {N}개
      - bg-gray-cool-100 (불가피한 사유: ...)

## Step 6: React 컴포넌트 생성 또는 수정

### Variant 완전 구현 (CRITICAL)

컴포넌트의 **모든 Figma variant를 빠짐없이** 구현한다.
일부 variant만 구현하면 Code Connect 매핑이 불완전해지고,
디자이너가 라이브러리에 등록해주지 않는다.

    완전 구현 기준:
    1. Figma componentProperties의 모든 variant enum 값에 대한 스타일 구현
    2. 모든 variant 조합(유효 조합)에 대한 시각적 결과가 Figma와 일치
    3. 인터랙션 상태(hover, focus, active, disabled)의 시각적 변화 모두 구현
    4. 사이즈 variant가 있으면 모든 사이즈의 padding/font-size/height 값 정확히 반영

    예시 — Button 컴포넌트:
    - tone: primary, secondary, danger → 3개 모두 배경색/텍스트색 구현
    - variant: filled, ghost, outline, text, link → 5개 모두 스타일 맵 구현
    - size: xl, lg, md, sm → 4개 모두 padding/height/fontSize 값 구현
    - disabled: true/false → disabled 스타일 구현
    - hover/focus/active → CSS pseudo-class로 각 tone×variant 조합의 상태 색상 구현

    금지:
    ❌ "나머지 variant는 나중에 추가" — 모든 variant를 한 번에 구현
    ❌ 일부 tone/variant만 구현하고 나머지는 default 폴백 — Figma 값 정확히 반영
    ❌ 사이즈별 값을 추측 — MCP 데이터에서 정확한 값 추출

    이유: Code Connect 매핑은 컴포넌트의 props를 Figma variant에 1:1로 연결한다.
    컴포넌트가 variant를 지원하지 않으면 매핑도 불가능하고,
    디자이너가 Figma에서 variant를 바꿔도 코드 스니펫이 변하지 않아 신뢰를 잃는다.

### 시각적 참조
Step 1에서 다운로드한 Figma 원본 이미지(temp/visual-comparison/{ComponentName}/figma-original.png)를
참고하면서 코드를 작성한다. MCP 구조 데이터만으로는 놓칠 수 있는 시각적 디테일(간격, 비율, 정렬 등)을
이미지를 보면서 확인한다.

### 기술 스택
- @headlessui/react: 접근성 보장 기본 컴포넌트
- Tailwind CSS v4: 스타일링 (@tailwindcss/vite 플러그인)
- clsx: 조건부 클래스 조합
- TypeScript: 타입 안전성

### 파일 구조
    {config.componentPath}/
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
    const toneVariantStyles = { ... }  // tokens.css 시맨틱 토큰 → Tailwind 유틸리티 클래스

    export const Nds{Name} = forwardRef(...)

### 기획 스펙 데이터 제약 반영 (Step 1.5 결과가 있는 경우)

Step 1.5에서 추출한 데이터 제약([DC-xx])과 비즈니스 룰([BR-xx])을 컴포넌트에 반영한다.

#### 데이터 제약 → props 제약

    기획 스펙의 데이터 제약을 props interface와 내부 로직에 반영한다:

    예시 — 파일 첨부 컴포넌트:
    기획 스펙: [DC-03] 이미지/텍스트/PDF만 허용, 최대 10개

    interface NdsFileUploadProps {
        /** @constraint 허용 파일 타입: image/*, text/*, application/pdf */
        accept?: string
        /** @constraint 최대 첨부 파일 수: 10 */
        maxFiles?: number
    }

    예시 — 대화 제목 컴포넌트:
    기획 스펙: [DC-01] 프롬프트 요약 자동 생성, 최대 20자

    interface NdsConversationItemProps {
        /** @constraint 최대 20자, 초과 시 truncation */
        title: string
    }

#### 비즈니스 룰 → 조건부 로직

    기획 스펙의 비즈니스 룰을 컴포넌트 내부 로직으로 반영한다:

    예시 — 삭제 보호:
    기획 스펙: [BR-02] 로컬 모델 삭제 불가

    interface NdsModelItemProps {
        isDeletable?: boolean  // false이면 삭제 버튼 비활성화/숨김
    }

    예시 — 역할 기반 가시성:
    기획 스펙: [BR-01] DLP 설정 관리자만 표시

    interface NdsSettingsSectionProps {
        requiredRole?: 'admin' | 'user'  // 'admin'이면 관리자만 렌더링
    }

#### 반영 추적

    기획 스펙 ID를 코드 주석에 기록하여 추적성을 확보한다:

    // [DC-03] 파일 첨부: 이미지/텍스트/PDF만, 최대 10개
    const DEFAULT_ACCEPT = 'image/*,text/*,application/pdf'
    const DEFAULT_MAX_FILES = 10

### 기존 컴포넌트 수정 시
- 기존 interface에 optional prop만 추가 (기존 사용처 영향 없음)
- 기존 스타일 맵에 새 키 추가 (기존 키 수정 금지)
- 변경 전후 diff를 결과 요약에 포함

### 아이콘 로딩: import.meta.glob 경로 계산 (MUST)

NdsIcon 컴포넌트에서 `import.meta.glob`을 사용할 때, 상대경로를 정확히 계산한다:

    경로 계산 기준:
    - 기준점: 컴포넌트 파일 위치 ({config.componentPath}/{ComponentName}.tsx)
    - 대상: 에셋 경로 ({config.assetPath}/icons/)
    - 상대경로: 기준점에서 대상까지의 상대 경로

    예시:
    componentPath: shared/components/commons/ai-portal
    assetPath: shared/assets/icons
    → 상대경로: ../../../assets/icons

    코드:
    const svgModules = import.meta.glob('../../../assets/icons/*.svg', {
        query: '?raw',
        eager: true,
        import: 'default',
    })

    MUST: 경로 계산 후 실제 파일 구조와 대조하여 검증한다.
    절대경로(/src/...)나 프로젝트 루트 기준 경로는 Vite에서 동작하지 않는다.

### 레이아웃 규칙

#### 중첩 패딩 구조 반영 (MUST)

Step 1-5-a에서 추출한 중첩 프레임의 padding을 모두 반영한다:

    Figma 구조:
    OuterFrame (padding: 8px)
    └── InnerFrame (padding: 8px)
        └── Content

    코드 반영:
    <div className="p-2">          {/* OuterFrame: 8px */}
        <div className="p-2">      {/* InnerFrame: 8px */}
            {/* Content: 실효 패딩 16px */}
        </div>
    </div>

    금지: 중첩 padding을 하나로 합치는 것 (레이아웃 구조가 달라짐)

#### 형제 요소 너비 반영

Step 1-5-b에서 추출한 형제 요소의 너비/비율을 반영한다:

    고정 너비: w-[240px]
    비율 너비: flex-[0.6] 또는 w-[60%]
    나머지 채우기: flex-1

#### overflow/scrollbar 기본 규칙

Figma에서 별도 scrollbar 표시가 없으면 scrollbar를 숨긴다:

    기본: overflow-auto [scrollbar-width:none]
    Figma에 scrollbar가 명시된 경우에만: overflow-auto (scrollbar 표시)

### 주의사항
- forwardRef 패턴 필수
- {config.componentPrefix} 접두사 필수 (예: NdsButton, NdsInput)
- interface와 컴포넌트 모두 export
- index.ts에서 barrel export
- hover/focus/active는 Tailwind pseudo-class(hover:, focus:, active:)로만 처리
- disabled는 Headless UI의 disabled prop + disabled: pseudo-class
- SVG 아이콘의 fill은 반드시 currentColor 사용 (Step 4의 변환 규칙 참조)

## Step 6.5: 인터랙션 연결

### 목적
Step 2에서 분석한 인터랙션 variant를 실제 코드에 연결한다.
Figma variant(isFocused, isCollapsed, theme 등)이 존재하는데 코드에 반영하지 않으면
사용자가 별도 세션에서 하나씩 요청해야 하므로, 이 단계에서 미리 구현한다.

### 구현 유형 분류

#### A. CSS pseudo-class (Tailwind)
코드 변경 최소 — Tailwind pseudo-class만 추가:

    대상: hover, focus, active, focus-within, focus-visible
    구현: hover:bg-[...] focus:ring-2 active:scale-95 등
    예시: 버튼 hover 효과, 인풋 focus 링

#### B. React state (useState/useReducer)
사용자 동작에 따라 컴포넌트 내부 상태가 변하는 경우:

    대상: isFocused, isCollapsed, isExpanded, isSelected, isOpen
    구현:
    const [isCollapsed, setIsCollapsed] = useState(false)

    예시:
    - Sider 접기/펼치기: isCollapsed 토글
    - 드롭다운 열기/닫기: isOpen 토글
    - 아코디언 접기/펼치기: isExpanded 토글

#### C. 조건부 렌더링
특정 상태에서만 UI 요소가 표시/숨김되는 경우:

    대상: 배경 그라데이션 조건부 표시, 로딩 애니메이션, 빈 상태
    구현:
    {isFocused && <div className="absolute inset-0 bg-gradient-..." />}

#### D. 컴포넌트 간 상호작용 (화면 수준)
여러 컴포넌트가 협력하여 동작하는 경우:

    대상: 퀵카드 클릭 → 프롬프트 입력 채우기, 사이드바 토글 → 본문 너비 변경
    구현:
    // 부모에서 state 관리
    const [promptValue, setPromptValue] = useState('')

    <QuickCard onClick={() => setPromptValue(card.text)} />
    <PromptInput value={promptValue} onChange={setPromptValue} />

### 애니메이션 처리

#### CSS keyframe (간단한 경우)
회전, 페이드, 슬라이드 등 단순 애니메이션:

    @keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
    Tailwind: animate-spin, animate-pulse 등

#### CSS crossfade (SVG 모핑)
여러 SVG가 순차적으로 전환되는 로고 애니메이션:

    @keyframes morph {
        0%, 33% { opacity: 1 }
        34%, 66% { opacity: 0 }
        ...
    }

    로고 SVG 여러 장을 position: absolute로 겹쳐놓고
    각각 다른 animation-delay로 crossfade

    IMPORTANT: 단순 회전(rotate)으로 오해하지 않는다.
    Figma에서 로고 variant가 여러 개이면 모핑 애니메이션일 가능성이 높다.

#### Lottie (복잡한 경우)
경로 모핑, 물리 기반 애니메이션 등은 CSS로 한계:
- 사용자에게 Lottie JSON 에셋 제공을 안내한다
- lottie-react 또는 @lottiefiles/react-lottie-player 사용

### E. Navigation 연결 (Interaction Graph 결과가 있는 경우)

Interaction Graph의 Navigation Map 항목을 코드에 연결한다.

    판단 기준:
    - 같은 페이지 내 전환: useState 기반 뷰 전환
    - 별도 페이지 이동: React Router navigate
    - 외부 URL: window.open

    구현 패턴 — 화면 내 뷰 전환:
    const [currentView, setCurrentView] = useState<'main' | 'tools' | 'analysis'>('main')
    <NdsButton onClick={() => setCurrentView('tools')}>도구</NdsButton>

    구현 패턴 — 라우터 기반:
    import { useNavigate } from 'react-router-dom'
    const navigate = useNavigate()
    <NdsButton onClick={() => navigate('/tools')}>도구</NdsButton>

### F. Overlay 연결 (Interaction Graph 결과가 있는 경우)

Interaction Graph의 Overlay Map 항목을 코드에 연결한다.

    Headless UI 컴포넌트 매핑:
    | Overlay 유형 | Headless UI | 트리거 |
    |-------------|-------------|--------|
    | 모달 (전체 화면 오버레이) | Dialog | ON_CLICK |
    | 팝오버 (부분 오버레이) | Popover | ON_CLICK |
    | 툴팁 (호버 오버레이) | Popover + hover 제어 | ON_HOVER |
    | 드롭다운 메뉴 | Menu | ON_CLICK |

    구현 패턴 — 모달:
    import { Dialog } from '@headlessui/react'
    const [isModalOpen, setIsModalOpen] = useState(false)

    <NdsButton onClick={() => setIsModalOpen(true)}>설정</NdsButton>
    <Dialog open={isModalOpen} onClose={() => setIsModalOpen(false)}>
        <SettingsModal />
    </Dialog>

    구현 패턴 — 팝오버/툴팁:
    import { Popover } from '@headlessui/react'

    <Popover>
        <Popover.Button>카테고리</Popover.Button>
        <Popover.Panel>
            <CategoryTooltip />
        </Popover.Panel>
    </Popover>

### 오버레이/프리뷰 구현 시 필수 고려사항 (MUST)

오버레이(모달, 프리뷰, 툴팁)를 구현할 때 아래 패턴을 반드시 따른다.
실험에서 이미지 프리뷰 구현 시 Portal 미사용, event propagation, z-index 문제로
여러 차례 수정 루프가 발생했다.

#### Portal 렌더링 (MUST)

오버레이는 반드시 React Portal(createPortal)로 document.body에 렌더링한다.
컴포넌트 내부에 렌더링하면 부모의 overflow, transform, z-index stacking context에 갇힌다.

    import { createPortal } from 'react-dom'

    {isPreviewOpen && createPortal(
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999 }}>
            <Overlay />
        </div>,
        document.body
    )}

    금지: 컴포넌트 내부에 fixed/absolute로 오버레이 배치 (stacking context 문제 발생)

#### Event Propagation 방지

오버레이 내부 클릭이 배경의 닫기 핸들러로 전파되지 않도록 한다.

    <div onClick={() => setOpen(false)}>       {/* 배경: 클릭 시 닫기 */}
        <div onClick={(e) => e.stopPropagation()}>  {/* 콘텐츠: 전파 차단 */}
            <img src={...} />
        </div>
    </div>

#### 이미지 확대 (transform: scale)

이미지 프리뷰에서 클릭 시 확대는 maxWidth/maxHeight 제거가 아닌 CSS transform: scale()을 사용한다.
원본이 화면보다 작은 이미지도 확대 효과가 적용되어야 한다.

    const [zoomed, setZoomed] = useState(false)

    <img
        onClick={() => setZoomed(!zoomed)}
        style={{
            maxWidth: '90vw', maxHeight: '90vh',
            transform: zoomed ? 'scale(2)' : 'scale(1)',
            transition: 'transform 0.3s ease',
            cursor: zoomed ? 'zoom-out' : 'zoom-in',
        }}
    />

### G. 기획 스펙 기반 인터랙션 (Step 1.5 결과가 있는 경우)

Step 1.5에서 추출한 인터랙션 플로우([IF-xx])를 구현에 반영한다.
Figma variant에 없더라도 기획서에 명시된 인터랙션은 이 단계에서 구현한다.

    기획서 인터랙션 반영 절차:
    1. Step 1.5의 스펙 매핑 테이블에서 현재 컴포넌트에 해당하는 [IF-xx] 항목 확인
    2. 각 인터랙션 플로우를 구현 유형(B/C/D)으로 분류
    3. 코드에 기획 스펙 ID를 주석으로 기록

    예시 — 대화 기록 케밥 메뉴:
    기획 스펙: [IF-04] [...] 버튼 클릭 → 이름 변경/삭제 메뉴 표시
    구현 유형: B (React state — isMenuOpen)

    // [IF-04] 케밥 메뉴: 이름 변경/삭제
    const [isMenuOpen, setIsMenuOpen] = useState(false)

    예시 — 프롬프트 샘플 선택:
    기획 스펙: [IF-05] 프롬프트 샘플 클릭 → 프롬프트 입력창에 텍스트 채우기
    구현 유형: D (컴포넌트 간 상호작용)

    // [IF-05] 프롬프트 샘플 → 입력창 채우기
    <PromptSample onClick={() => setPromptValue(sample.text)} />

    Figma variant vs 기획서 인터랙션 구분:
    - Figma variant 기반: 시각적 변화가 MCP 데이터에서 확인 가능 (Step 2에서 분석)
    - 기획서 기반: 시각적 변화가 없거나 MCP에 미반영, 기획서에만 명시 (이 섹션에서 구현)
    - 둘 다 있는 경우: 기획서가 더 구체적이면 기획서 기준, 아니면 Figma 기준

### 체크리스트 (Step 6.5 완료 시)

    ✅ Step 2에서 분석한 인터랙션 variant가 모두 코드에 연결되었는가
    ✅ CSS pseudo로 처리할 것과 React state로 처리할 것이 정확히 구분되었는가
    ✅ 화면 수준 빌드 시: 컴포넌트 간 상호작용이 구현되었는가
    ✅ 애니메이션이 필요한 경우 적절한 방식(CSS/Lottie)으로 구현되었는가
    ✅ Interaction Graph가 있는 경우: Navigation Map의 모든 항목에 onClick → navigate/setView가 연결되었는가
    ✅ Interaction Graph가 있는 경우: Overlay Map의 모든 항목에 Dialog/Popover/Menu가 연결되었는가
    ✅ 기획 스펙이 있는 경우: 매핑된 [IF-xx] 항목이 모두 코드에 반영되었는가

## Step 7: Storybook 스토리 생성 (개발 참고용)

Storybook은 개발 중 variant 확인과 빠른 이터레이션을 위한 참고 도구이다.
**QA 검증은 Storybook이 아닌 dev 서버에서 수행한다** (Step 8 참조).

### 경로
    {config.storybookPath}/stories/{ComponentName}.stories.tsx

### 필수 스토리
1. **Default**: 기본 상태
2. **AllVariants**: 유효 조합 전체 × 사이즈 (매트릭스)
3. **Sizes**: 사이즈 비교
4. **DisabledStates**: 모든 유효 조합의 disabled 상태

### 선택 스토리 (어노테이션 Prop에 정의된 경우만)
- WithIcons: iconStart, iconOnly 등
- CustomContent: 슬롯 콘텐츠

### Storybook 설정
- 포트: {config.storybookPort}
- .storybook/main.ts: @storybook/react-vite + @tailwindcss/vite 플러그인
- .storybook/preview.ts: globals.css import
- globals.css: 아래 템플릿 필수 (없으면 Tailwind 임의값 클래스가 생성되지 않음)

### globals.css 템플릿 (필수)

    @import "tailwindcss";
    @source "./*.tsx";
    @source "./stories/*.tsx";
    @source "{config.componentPath 로의 상대경로}/*.tsx";

CRITICAL: @source 디렉티브가 없으면 bg-[#1D1F20], w-[280px] 등 Tailwind 임의값 클래스가
CSS에 포함되지 않아 스타일이 적용되지 않는다.
@source 경로는 globals.css 위치 기준 상대경로로, {config.componentPath}를 가리켜야 한다.

### 인터랙티브 요소 핸들러 검증 (MUST)

Default 스토리를 포함한 모든 스토리에서, 인터랙티브 UI 요소가 실제로 동작하는지 확인한다.

    규칙:
    - 핸들러(onClick, onFileSelect 등)가 없는데 클릭 가능한 UI 요소(버튼, 아이콘)가 보이면 안 됨
    - Default 스토리에서 핸들러가 없으면: 해당 요소를 숨기거나 disabled 처리
    - 또는 Default 스토리에도 기본 핸들러를 제공하여 동작하게 함

    이유:
    - 사용자가 Default 스토리에서 클립 버튼을 클릭했는데 아무 반응이 없으면
      "파일 첨부가 안 된다"고 오해하게 됨 (실제로는 핸들러가 없을 뿐)
    - 기능 검증 시 Default 스토리만 보고 판단하는 경우가 많음

    검증 체크리스트:
    ✅ Default 스토리에서 모든 버튼/아이콘이 클릭 시 반응하는가
    ✅ 파일 첨부, 검색 등 콜백이 필요한 기능에 적절한 mock 핸들러가 있는가
    ✅ 핸들러가 없는 상태를 보여주려면 별도 스토리(NoHandlers)로 분리하는가

### import 주의
- render 함수 사용 시 import React from 'react' 필수
- 컴포넌트는 상대경로로 import

## Step 8: QA Phase (독립 서브에이전트 검증 — dev 서버 대상)

컴포넌트를 화면에 통합한 후, **dev 서버에서** 독립 QA 에이전트 3개로 검증한다.
Storybook이 아닌 dev 서버에서 QA를 수행한다 (실제 앱 환경에서의 동작 보장).
상세 절차는 [qa_phase.md](qa_phase.md) 참조.

### QA 전 준비

Dev가 Step 7까지 완료하면, QA Phase 진입 전에:
1. 생성/수정한 컴포넌트를 **대상 화면 코드에 통합** (import + JSX 삽입)
2. dev 서버가 실행 중인지 확인
3. Playwright MCP로 대상 화면까지 접근 가능한지 확인 (로그인 포함)

### 요약

3개 QA 서브에이전트를 Task 도구로 병렬 실행한다.

    QA-기능 (sonnet): Playwright E2E — dev 서버에서 기능/인터랙션/접근성 테스트
    QA-시각적 (opus): Figma ↔ dev 서버 렌더링 비교 (zoom 확대 포함)
    QA-토큰 (haiku): 디자인 토큰 정합성 검증

### QA → Dev 수정 루프

    최대 3루프:
    QA FAIL → Dev 수정 → QA 재검증 → ... → 3루프 미해결 시 사용자 에스컬레이션

### 사용자 보고 (매 루프)

매 QA 루프 완료 시 사용자에게 표 형식으로 보고한다:

    ## QA 루프 {N}/3 리포트: {ComponentName}

    | QA 에이전트 | PASS | FAIL | 주요 FAIL 항목 |
    |------------|------|------|---------------|
    | QA-기능    | 8    | 2    | 파일 첨부 플로우 실패, ghost hover 미동작 |
    | QA-시각적  | 12   | 3    | primary 배경색 ΔE=8, sm 패딩 초과 |
    | QA-토큰    | 5    | 1    | danger.ghost.hover 토큰 누락 |
    | **합계**   | **25** | **6** | |

    **판정: FAIL** — Dev 수정 후 재검증 (루프 {N+1}/3)

### 전제 조건
- Step 1에서 다운로드한 Figma 원본 이미지 존재: temp/visual-comparison/{ComponentName}/figma-original.png
- 원본 이미지가 없으면 QA-시각적만 건너뛰고 QA-기능, QA-토큰은 실행
- dev 서버가 실행 중이어야 함 (접근 불가 시 사용자에게 안내)
- 컴포넌트가 화면에 통합되어 dev 서버에서 볼 수 있어야 함

## Step 8.5: Interaction Review (사용자 대화)

QA Phase를 통과한 후, Step 1.6에서 추론(inferred)으로 생성한 인터랙션을
사용자와 확인하여 최종 코드를 완성한다.

상세 절차는 [interaction_review.md](interaction_review.md) 참조.

### 실행 조건

- Step 1.6에서 신뢰도가 "추론" 또는 "기획 기반"인 항목이 1개 이상: 이 Step 실행
- 모든 항목이 "확인됨" (프로토타입 연결 기반): 이 Step **스킵**
- Step 1.6에서 interactions가 0개여서 건너뛴 경우: 이 Step 실행 (사용자에게 인터랙션 질문)

### 요약

1. 추론된 인터랙션을 표로 보여주고 사용자에게 확인
2. 사용자 응답(Y/N/수정/추가) 반영하여 코드 수정
3. 사용자가 "완료" 또는 "넘어가기"라고 하면 Step 9로 진행

## Step 9: Code Connect 매핑 등록

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

### 완전 매핑 의무화 (CRITICAL)

Code Connect 매핑은 **컴포넌트의 모든 variant를 빠짐없이** 매핑해야 한다.
최소한의 스텁(props 비어있음, 하드코딩된 예시만)으로 매핑하면
디자이너가 Figma에서 variant를 바꿔도 코드 스니펫이 변하지 않아 신뢰를 잃는다.

    완전 매핑 기준:
    1. 컴포넌트의 모든 variant enum → figma.enum()으로 매핑
    2. 모든 boolean property → figma.boolean()으로 매핑
    3. 모든 Text property → figma.string()으로 매핑 (텍스트 콘텐츠가 아닌 Figma property만)
    4. 중첩 컴포넌트 → figma.instance() 또는 figma.children()으로 매핑
    5. example 함수에서 모든 매핑된 props를 사용

    금지:
    ❌ props: {} 빈 객체 — 반드시 모든 variant props 매핑
    ❌ 하드코딩된 예시만 (예: <NdsButton tone="primary">) — figma.enum()으로 동적 매핑
    ❌ variant가 4개인데 2개만 매핑 — 전부 매핑

    이유: 디자이너가 라이브러리에 등록해주려면 Code Connect가 완벽해야 한다.
    디자이너가 Figma에서 tone을 primary→danger로 바꾸면
    코드 스니펫도 tone="danger"로 바뀌어야 신뢰가 생긴다.

### 절차
1. 컴포넌트 파일과 동일 디렉토리에 .figma.tsx 파일 생성
2. figma.connect()로 Figma 노드 URL과 코드 컴포넌트 연결
3. **MCP 응답의 componentProperties에서 모든 property를 추출**하여 매핑
   - variant enum → figma.enum() (모든 옵션값 포함)
   - boolean → figma.boolean()
   - Text property → figma.string() (componentProperties에 type:"TEXT"로 존재하는 것만)
   - Instance swap → figma.instance()
4. example 함수에서 **매핑된 모든 props를 사용**하는 예시 작성
5. code_connect_workflow.md의 "Publish 전 검증 절차" 수행
6. 프로젝트 package.json의 figma 관련 scripts를 확인하여 publish 실행 (명령어가 변경될 수 있음)
7. 상세 규칙은 code_connect_workflow.md 참조

### 파일 구조

    {config.componentPath}/
    ├── {Prefix}Button.tsx           # 컴포넌트
    ├── {Prefix}Button.figma.tsx     # Code Connect 매핑
    └── index.ts

## Step 10: 결과 요약

모든 단계 완료 후 아래 형식으로 보고:

    ## 변환 결과: {컴포넌트명}

    ### 생성 파일
    | 파일 | 용도 | 크기 |
    |------|------|------|
    | ... | ... | ... |

    ### 토큰 변경
    - 신규: {N}개 ({토큰 이름 목록})
    - 재사용: {N}개

    ### QA 검증
    - 판정: PASS / PARTIAL (미해결 {N}건) / FAIL (에스컬레이션)
    - QA 루프: {N}/3
    - QA-기능: {PASS}/{TOTAL} 통과
    - QA-시각적: {PASS}/{TOTAL} 통과
    - QA-토큰: {PASS}/{TOTAL} 통과
    - 미해결 경고: (있을 경우 항목 목록)

    ### Interaction Graph (Step 1.6 실행 시)
    - 총 추출: {N}개 (State Machine {a}, Navigation {b}, Overlay {c}, Variable {d})
    - 프로토타입 기반: {N}개 (확인됨)
    - 구조 추론: {N}개 → Step 8.5에서 {M}개 확정, {K}개 제거
    - 미구현: {N}개 (사유: 데이터 흐름 필요, 백엔드 연동 필요 등)

    ### 기획 스펙 반영 (Step 1.5 실행 시)
    - 전체: {N}개 항목
    - 반영: {M}개 (인터랙션 {a}개, 데이터 제약 {b}개, 비즈니스 룰 {c}개)
    - 미반영: {K}개 (사유: 다른 컴포넌트 대상 / 백엔드 영역 / 미결정)
    - 미결정 사항: {L}개

    ### 한계/주의
    - {발견된 이슈 목록}

## 화면 수준 생성

화면(프레임) URL이 입력된 경우 code_connect_workflow.md의
"화면 수준 생성 워크플로우 (Top-down)" 절차를 따른다.

핵심 흐름:
1. 화면 MCP 데이터 추출
2. 컴포넌트 인벤토리 생성 (연결됨/미연결 분류)
3. **미연결 컴포넌트의 Main Component 조회** (MUST):
   - 각 INSTANCE의 componentId로 Main Component resolve
   - Main Component의 interactions + dev 코멘트 추출 (Step 1.6-5)
   - 추출 결과를 해당 컴포넌트 빌드 시 입력으로 전달
4. 사용자 확인
5. 미연결 컴포넌트 자동 빌드 (리프부터 Bottom-up, 각각 Step 1~9 실행)
   - **빌드 시 Main Component에서 추출한 interactions + dev 코멘트를 활용**
6. 화면 조립
7. 결과 요약

컴포넌트 노드와 화면 프레임 노드의 구분:
- 컴포넌트 노드: type이 COMPONENT 또는 COMPONENT_SET
- 화면 프레임 노드: type이 FRAME이고, 내부에 INSTANCE 노드들을 포함

## 증분 추가 모드 (-a)

이미 빌드한 화면에 새 컴포넌트가 추가된 경우 사용한다.
기존 화면 코드를 처음부터 다시 쓰지 않고, 새 컴포넌트만 빌드하여 기존 코드에 삽입한다.

    예시 상황:
    - Screen 1 (초기 화면) 이미 빌드 완료
    - Screen 2 = Screen 1 + ChatBubble, resultCard 등 대화 컴포넌트 추가
    - /figma-to-react -a https://...?node-id=screen2

### A-1. 화면 MCP 추출

일반 화면 수준 생성과 동일하게 MCP 데이터를 추출한다.

### A-2. 기존 화면 코드 탐색

{config.componentPath} 및 프로젝트 내에서 이 화면의 기존 코드를 찾는다.

    탐색 방법:
    1. MCP에서 추출한 화면 이름(예: portalMain)으로 Glob/Grep 검색
    2. 기존 화면 컴포넌트 파일 (예: PortalMain.tsx) 발견
    3. 파일을 Read하여 현재 import된 컴포넌트 목록 파악

    기존 코드를 찾지 못한 경우:
    - 사용자에게 기존 화면 파일 경로를 질문
    - 또는 신규 화면 생성 모드(기본)로 전환 제안

### A-3. 신규/기존 컴포넌트 분류

MCP 데이터의 컴포넌트를 기존 코드와 비교하여 분류한다.

    | 분류 | 판단 기준 | 처리 |
    |------|-----------|------|
    | 기존 (코드에 있음) | 기존 화면 코드에 import/사용됨 | 건드리지 않음 |
    | 신규 (코드에 없음) | MCP에 있지만 기존 코드에 없음 | 빌드 대상 |
    | Code Connect 연결됨 | CodeConnectSnippet 존재 | import만 추가 |

    출력 형식:
    ## 증분 분석: {화면명}

    ### 기존 컴포넌트 (변경 없음)
    - sider, promptInput, quickCard, ...

    ### 신규 컴포넌트 (빌드 필요)
    - ChatBubble (user/LLM 타입)
    - resultCard/type1

    ### Code Connect 연결됨 (import만 추가)
    - (해당 시)

사용자에게 분류 결과를 보여주고 확인 후 진행한다.

### A-4. 신규 컴포넌트 빌드

신규 컴포넌트를 기존 파이프라인(Step 1~9)으로 빌드한다.
기존 컴포넌트에 대해서는 빌드/수정을 하지 않는다.

### A-5. 기존 화면 코드에 삽입

신규 컴포넌트를 기존 화면 코드에 삽입한다.

    삽입 절차:
    1. 기존 화면 파일에 새 컴포넌트 import 추가
    2. MCP 데이터의 레이아웃 구조를 참고하여 삽입 위치 결정
    3. 기존 JSX 구조 내에 새 컴포넌트를 추가
    4. 필요한 state/handler 추가 (기존 state는 변경하지 않음)

    금지:
    ❌ 기존 컴포넌트의 props/스타일 변경
    ❌ 기존 레이아웃 구조 재작성
    ❌ 기존 import 순서 변경
    ❌ 기존 state/handler 삭제 또는 이름 변경

    허용:
    ✅ 새 import 추가 (기존 import 블록 끝에)
    ✅ 새 state/handler 추가
    ✅ 기존 JSX 내에 새 요소 삽입
    ✅ 기존 컨테이너의 children에 새 컴포넌트 추가

### A-6. 결과 요약

    ## 증분 추가 결과: {화면명}

    ### 신규 빌드
    | 컴포넌트 | 파일 | 상태 |
    |---------|------|------|
    | ChatBubble | NdsChatBubble.tsx | 생성 완료 |
    | resultCard | NdsResultCard.tsx | 생성 완료 |

    ### 화면 코드 변경
    - 파일: {화면파일.tsx}
    - 추가된 import: {N}개
    - 추가된 state: {N}개
    - 추가된 JSX 요소: {N}개
    - 기존 코드 변경: 없음

## 화면 업데이트 모드 (-u)

기존 화면의 레이아웃, 컴포넌트 props, 스타일 등이 변경된 경우 사용한다.
Figma의 최신 디자인과 기존 코드를 비교하여 변경분만 반영한다.
**내부적으로 토큰 마이그레이션을 먼저 수행**한 후 디자인 diff를 한다. 별도 `-m` 실행이 필요 없다.

    예시 상황:
    - 이미 빌드한 화면의 디자인이 변경됨 (레이아웃 수정, 색상 변경, 컴포넌트 교체 등)
    - /figma-to-react -u https://...?node-id=screen-updated

    섹션/페이지 URL 지원:
    - 개별 프레임 URL뿐 아니라 하위 프레임을 포함하는 상위 노드 URL도 지원
    - /figma-to-react -u https://...?node-id=2101-46329  ← 페이지 노드
    - 하위 프레임 자동 탐색 → 이름 기반 그룹화 → 그룹별 순차 처리

### U-0. 섹션/페이지 URL 처리 (해당 시)

입력 노드가 개별 프레임이 아닌 상위 노드(섹션/페이지)인 경우:

    1. 하위 프레임 전체 탐색 (MCP로 하위 노드 목록 추출)
    2. 프레임 이름으로 자동 그룹화 (예: "01.사용자포탈", "02.첨부파일 업로드" 등)
    3. 제외 대상 필터링 (예: "알람분석" 포함 프레임 제외)
    4. 사용자에게 그룹 확인
       "{N}개 프레임을 {M}개 플로우로 분류했습니다. 맞습니까?"
    5. 확인 후 그룹별 순차 처리 (U-1 ~ U-6을 그룹마다 반복)

    주의:
    - 같은 컴포넌트 파일(예: PortalMain.tsx)의 다른 상태가 여러 프레임으로 표현될 수 있음
      → 모든 상태에서의 스타일을 종합하여 반영
    - 그룹별로 처리해야 컨텍스트 폭발을 방지할 수 있음

### U-1. 화면 MCP 추출

일반 화면 수준 생성과 동일하게 MCP 데이터를 추출한다.

### U-2. 기존 화면 코드 탐색

-a 모드의 A-2와 동일. 기존 화면 코드를 찾아 Read한다.

### U-2.5. 토큰 마이그레이션 (내부 자동)

디자인 diff 전에 **구 토큰 → 신 토큰 치환**을 먼저 수행한다.
코드가 신 토큰을 사용해야 정확한 디자인 diff가 가능하다.

    처리 내용:
    1. tokens.css + portal.css 파싱 → CSS 변수 맵 구성
    2. 기존 코드에서 구 토큰 클래스 추출
    3. 정적 매핑 테이블로 구 → 신 치환
    4. 하드코딩 HEX → tokens.css 매칭
    5. Storybook(.stories.tsx) 동기화

    이 단계는 -m 모드의 M-2 ~ M-4와 동일한 로직이지만,
    -u 모드에서는 내부적으로 자동 실행된다.
    디자인 변경(색상 값 실제 변경, 크기/레이아웃 변경)은 U-3에서 처리.

### U-3. Figma ↔ 코드 diff

MCP 데이터와 기존 코드를 비교하여 변경 사항을 식별한다.

    비교 항목:

    1. 컴포넌트 구성 변경
       - 추가: MCP에 있지만 코드에 없는 컴포넌트
       - 삭제: 코드에 있지만 MCP에 없는 컴포넌트
       - 교체: 같은 위치에 다른 컴포넌트 (예: Select → ClickMenu)

    2. 레이아웃 변경
       - flex 방향 변경 (row ↔ column)
       - 비율/너비 변경 (60:40 → 70:30)
       - 간격 변경 (gap, padding)
       - 요소 순서 변경

    3. 스타일 변경
       - 배경색, 텍스트색, 보더 변경
       - 폰트 크기/굵기 변경
       - border-radius 변경

    4. Props 변경
       - 기존 컴포넌트의 props 값 변경 (예: tone="primary" → tone="secondary")
       - 새로운 props 추가

    diff 출력 형식:
    ## Figma ↔ 코드 diff: {화면명}

    ### 컴포넌트 변경
    - [추가] ChatBubble — 대화 영역에 신규
    - [삭제] OnboardingBanner — 초기 화면 전용, 대화 상태에서 불필요
    - [교체] Select → ClickMenu — 도구 선택 UI 변경

    ### 레이아웃 변경
    - 중앙 영역: 단일 컬럼 → 2컬럼 (대화 + 결과 패널)
    - 하단 프롬프트: padding 16px → 12px

    ### 스타일 변경
    - 배경색: #06050A → #0A0B10

    ### Props 변경
    - PromptInput: isFocused prop 추가

사용자에게 diff 결과를 보여주고 확인 후 진행한다.

### U-4. 변경 사항 분류

diff 결과를 실행 가능한 작업으로 분류한다.

    | 변경 유형 | 작업 |
    |-----------|------|
    | 컴포넌트 추가 | -a 모드와 동일: 빌드 + 삽입 |
    | 컴포넌트 삭제 | 사용자 확인 후 import/JSX 제거 |
    | 컴포넌트 교체 | 새 컴포넌트 빌드 + 기존 JSX 교체 |
    | 레이아웃 변경 | Tailwind 클래스 수정 |
    | 스타일 변경 | 토큰/Tailwind 클래스 수정 |
    | Props 변경 | JSX의 props 값 수정 |

    삭제 시 주의:
    - 사용자에게 삭제 대상을 반드시 확인
    - 삭제할 컴포넌트가 다른 화면에서도 사용되는지 확인
    - 컴포넌트 파일 자체는 삭제하지 않음 (다른 화면에서 사용 가능)
    - 화면 코드에서 import와 JSX만 제거

### U-5. 변경 사항 적용

확인된 변경 사항을 기존 코드에 적용한다.

    적용 순서:
    1. 신규 컴포넌트 빌드 (있는 경우)
    2. import 수정 (추가/제거)
    3. JSX 구조 수정 (추가/삭제/교체/순서 변경)
    4. 스타일 수정 (Tailwind 클래스, 토큰)
    5. Props 수정
    6. State/handler 수정 (추가/제거)

    기존 코드 보존 원칙:
    - 변경하지 않는 부분은 한 글자도 건드리지 않는다
    - diff에서 식별되지 않은 코드는 원본 유지
    - 코드 포매팅/스타일 변경 금지 (들여쓰기, 줄바꿈 등)

### U-6. 결과 요약

    ## 화면 업데이트 결과: {화면명}

    ### 변경 적용
    | 유형 | 내용 | 상태 |
    |------|------|------|
    | 컴포넌트 추가 | ChatBubble | 빌드+삽입 완료 |
    | 컴포넌트 삭제 | OnboardingBanner | 제거 완료 |
    | 레이아웃 변경 | 중앙 영역 2컬럼화 | 적용 완료 |
    | 스타일 변경 | 배경색 수정 | 적용 완료 |

    ### 신규 빌드 컴포넌트
    | 컴포넌트 | 파일 |
    |---------|------|
    | ChatBubble | NdsChatBubble.tsx |

    ### 화면 코드 변경
    - 파일: {화면파일.tsx}
    - 변경 라인 수: +{N} / -{M}

## 토큰 마이그레이션 모드 (-m)

기존 컴포넌트의 토큰 이름을 치환한다.
구 토큰 → 신 토큰 자동 교체 + 하드코딩 HEX 제거.
**디자인 변경(색상 값/크기/레이아웃 실제 변경)은 반영하지 않는다** — 그것은 `-u`에서 처리.
비즈니스 로직은 일절 변경하지 않는다.

    입력:
    /figma-to-react -m                          ← URL 없이 전체 일괄
    /figma-to-react -m <figma-url>              ← URL 있으면 Figma 보완 매칭 추가

    Figma URL은 선택 사항:
    - 토큰 마이그레이션의 90% 이상은 정적 매핑 + HEX 매칭으로 처리
    - Figma 데이터는 매핑 불가 항목의 보완용

### M-1. 대상 컴포넌트 탐색

{config.componentPath} 하위 전체 .tsx 파일을 탐색한다.
Figma URL이 있으면 MCP에서 추출한 컴포넌트 목록으로 범위를 좁힌다.

    URL 없는 경우:
    - {config.componentPath} 하위 모든 .tsx 파일을 대상으로 함
    - .stories.tsx 파일도 포함

    URL 있는 경우:
    - Figma MCP로 데이터 추출 후, 해당 컴포넌트/화면의 코드를 탐색
    - Code Connect 매핑 → 로컬 Glob/Grep → 사용자 질문 순서

### M-2. 토큰 마이그레이션 맵 구성

#### M-2-1. tokens.css + portal.css 파싱

Step 5의 5-1, 5-2와 동일. CSS 변수명 → 값 맵을 구성한다.

#### M-2-2. 기존 코드에서 구 토큰 클래스 추출

기존 코드에서 구 토큰 체계의 Tailwind 클래스를 추출한다.

    탐색 패턴:
    - fill-standard-*, fill-inverse-*, fill-tertiary-*, fill-disable-*, fill-transparent-*
    - text-standard-*, text-secondary-default, text-tertiary-default,
      text-inverse-default, text-disable-default, text-accent-*
    - line-standard-*, line-disable-*
    - brand-default (outline 컨텍스트)
    - button-danger-*, button-link-*
    - text-h-2 (구 타이포그래피)
    - bg-[#HEX], text-[#HEX], border-[#HEX] (하드코딩)
    - style={{ color: '#HEX' }}, style={{ backgroundColor: '#HEX' }} (inline 하드코딩)

#### M-2-3. 정적 매핑 테이블 적용

design_tokens.md의 "정적 매핑 테이블 (구 → 신 토큰)" 섹션을 참조하여 자동 치환한다.

    치환 규칙:
    - Tailwind 접두사(bg-/text-/border-/hover:bg-/active:bg- 등)는 유지
    - 토큰 이름 부분만 교체

    치환 예시:
    bg-fill-standard-default              → bg-layer-01
    hover:bg-fill-standard-hover          → hover:bg-layer-01-hover
    text-text-standard-default            → text-text-primary
    text-text-inverse-default             → text-text-on-color
    border-line-standard-default          → border-border-default
    focus-visible:outline-brand-default   → focus-visible:outline-focus-default

    brand-default 분기 처리:
    - text-brand-default (링크 컨텍스트) → text-link-primary
    - text-brand-default (강조 컨텍스트) → text-text-brand
    - bg-brand-default → bg-interactive-primary
    - outline-brand-default → outline-focus-default

#### M-2-4. 하드코딩 HEX → tokens.css 매칭

코드에서 bg-[#HEX], text-[#HEX], style={{ color: '#HEX' }} 패턴을 찾아 tokens.css에서 매칭한다.

    예시:
    코드: bg-[#F3F5F7] → tokens.css: --color-layer-01-hover: #f3f5f7 → bg-layer-01-hover
    코드: style={{ backgroundColor: '#101213' }} → tokens.css: --color-background-inverse: #101213
         → className="bg-background-inverse"

#### M-2-5. Figma 데이터로 미매칭 보완 (URL 있을 때만)

Figma URL이 제공된 경우에만 실행. 정적 매핑으로 해결되지 않는 토큰은
M-1에서 추출한 Figma MCP 데이터에서 해당 위치의 색상을 추출하여 tokens.css에서 매칭한다.

URL이 없는 경우: 매핑 실패 항목은 건너뛰고 결과 요약에 목록으로 출력한다.

### M-3. 변경 계획 사용자 확인

사용자에게 아래 내용을 표 형식으로 보여주고 확인한다.

    ## 토큰 마이그레이션 계획: {ComponentName}

    ### 토큰 교체 (자동 매핑)
    | 구 클래스 | 신 클래스 | 매핑 근거 |
    |----------|----------|----------|
    | bg-fill-standard-default | bg-layer-01 | 정적 매핑 |
    | text-text-standard-default | text-text-primary | 정적 매핑 |
    | bg-[#F3F5F7] | bg-layer-01-hover | HEX 매칭 |

    ### 하드코딩 색상 교체
    | 하드코딩 값 | 매칭 토큰 | 근거 |
    |-----------|----------|------|
    | text-[#121314] | text-text-primary | HEX 매칭 |

    ### 매핑 불확실 항목 (사용자 결정 필요)
    | 구 값 | 후보 | 질문 |
    |------|------|------|
    | bg-[#CEF3FA] | (tokens.css에 없음) | 유지? portal.css에 추가? |

### M-4. 변경 적용

#### M-4-1. 구 토큰 → 신 토큰 치환

M-2-3의 정적 매핑 결과를 코드에 적용한다.

#### M-4-2. 하드코딩 → 토큰 치환

M-2-4의 HEX 매칭 결과를 코드에 적용한다.
가능한 경우 inline style의 색상을 Tailwind 클래스로 전환한다.

#### M-4-3. Storybook 동기화

.stories.tsx 파일에서도 구 토큰 참조가 있으면 함께 교체한다.

### M-5. 결과 요약

    ## 토큰 마이그레이션 결과

    ### 토큰 교체
    | 유형 | 건수 |
    |------|------|
    | 정적 매핑 교체 | {N}개 |
    | HEX → 토큰 교체 | {N}개 |
    | inline → className 전환 | {N}개 |
    | Storybook 동기화 | {N}개 |

    ### 매핑 실패 항목 (→ -u 모드에서 Figma 확인 후 처리)
    | 구 값 | 위치 | 사유 |
    |------|------|------|
    | bg-[#CEF3FA] | FileUploadCard:23 | tokens.css에 매칭 없음 |

    ### 미처리 항목
    - (매핑 불확실하여 사용자 결정 보류 등)

### -m 모드 변경 적용 원칙

| 원칙 | 설명 |
|------|------|
| 토큰 이름 치환 전용 | 구 토큰 클래스명 → 신 토큰 클래스명 교체, 하드코딩 HEX → 토큰 전환 |
| 디자인 변경 반영 안 함 | 색상 값 변경, 크기 변경, 레이아웃 변경은 `-u`에서 처리 |
| 로직 불변 | useState, useEffect, 이벤트 핸들러, 조건 분기, API 호출 등 일체 불변 |
| 포매팅 불변 | 들여쓰기, 줄바꿈, 변수명 등 스타일과 무관한 코드 포매팅 변경 금지 |
| inline → className 전환 | 가능한 경우 inline style의 색상을 Tailwind 클래스로 전환 |
| Storybook 동기화 | .stories.tsx 파일에서도 구 토큰 참조가 있으면 함께 교체 |
| portal.css 토큰 보존 | portal.css에 있는 AI Portal 전용 토큰 (prompt-bg, avatar 등)은 유지 |
| 매핑 실패 보고 | 자동 매핑 불가 항목은 건너뛰고 결과 요약에 목록 출력 |

## 에러 처리

### Figma MCP 연결 실패
- PAT 토큰 만료 확인 안내
- claude mcp add 명령어 안내

### Storybook 미실행
- "Storybook이 포트 {config.storybookPort}에서 실행 중이어야 합니다" 안내
- 프로젝트 package.json의 storybook 관련 scripts를 확인하여 실행 (명령어가 변경될 수 있음)

### Playwright MCP 브라우저 충돌
- 기존 브라우저 세션 닫기 안내
- browser_close 후 재시도

### [MCP:ComponentSpec] 파싱 실패
- 어노테이션 형식 오류 시 사용자에게 원문 표시 후 확인 요청
- 폴백 모드로 전환 (variant property 기반)
