# Code Connect 워크플로우

Figma Code Connect를 활용하여 컴포넌트 매핑을 등록하고,
화면 수준 생성 시 토큰 사용량과 속도를 개선하는 워크플로우.

## 핵심 개념

Code Connect는 이미 만들어진 React 컴포넌트를 Figma 디자인 컴포넌트와 연결하는 매핑 도구다.
연결된 컴포넌트는 Figma MCP Server가 CodeConnectSnippet으로 축약하여 제공한다.

    [연결 전] Figma MCP 응답
    - FRAME "Button"
      - layoutMode, padding, fills, strokes...
      - FRAME "Content" → TEXT "Label" → fontSize, fontWeight...
      - variant properties 전체...
      → 컴포넌트 하나에 수십~수백 노드

    [연결 후] Figma MCP 응답
    <CodeConnectSnippet>
      import: import { NdsButton } from '{config.componentPath}'
      snippet: <NdsButton tone="primary" variant="filled" size="lg">Label</NdsButton>
      instructions: "tone, variant, size props 사용"
    </CodeConnectSnippet>
      → 수십 토큰으로 축약

## 전제 조건

- Figma Organization 또는 Enterprise 플랜 + Dev/Full seat
- @figma/code-connect 패키지 설치
- Figma Personal Access Token (PAT) 설정

## 설치

    npm i @figma/code-connect

## 두 가지 진입점

### A. 컴포넌트 단위 생성 (기존 방식)

사용자가 개별 컴포넌트 URL을 직접 지정하여 실행.
기존 pipeline_workflow.md Step 1~8 + Step 9(시각적 비교 루프) + Step 10(매핑 등록).

    /figma-to-react https://www.figma.com/design/{fileKey}?node-id={컴포넌트-노드-id}

### B. 화면 수준 생성 (Top-down 자동 발견)

사용자가 화면(프레임) URL을 주면 시스템이 자동으로:
1. 화면 내 모든 컴포넌트 인스턴스를 발견
2. 연결 여부를 분류
3. 미연결 컴포넌트를 자동 빌드 + 등록
4. 화면을 조립

사용자가 수백 개의 컴포넌트를 일일이 찾아서 실행할 필요 없다.

    /figma-to-react https://www.figma.com/design/{fileKey}?node-id={화면-노드-id}

---

## 화면 수준 생성 워크플로우 (Top-down)

### Step 1: 화면 MCP 데이터 추출

화면 프레임의 node-id로 MCP 조회.
응답에서 두 종류의 데이터가 섞여 온다:

    [연결된 컴포넌트] → CodeConnectSnippet (축약)
    - import 경로와 props가 바로 제공됨
    - 내부 구조 파싱 불필요

    [미연결 요소] → 원시 노드 트리 (상세)
    - 아직 등록하지 않은 컴포넌트 인스턴스
    - 레이아웃 프레임 (flex, grid 구조)
    - 텍스트, 이미지 등 화면 고유 요소

### Step 2: 컴포넌트 인벤토리 생성

MCP 응답을 분석하여 화면에 사용된 모든 컴포넌트를 목록화한다.

    ## 컴포넌트 인벤토리: 로그인 화면

    | # | 컴포넌트명 | Figma 노드 | 사용 횟수 | 상태 |
    |---|-----------|-----------|----------|------|
    | 1 | Button    | 1234-5678 | 2        | ✅ 연결됨 (CodeConnectSnippet) |
    | 2 | Input     | 2345-6789 | 2        | ❌ 미연결 |
    | 3 | Checkbox  | 3456-7890 | 1        | ❌ 미연결 |
    | 4 | Icon      | 4567-8901 | 3        | ❌ 미연결 (단순) |

### Step 3: 사용자 확인

인벤토리를 사용자에게 보여주고 확인한다:

    "이 화면에 컴포넌트 {N}종이 사용되었습니다.
    - 연결됨: {N}종 (바로 사용 가능)
    - 미연결: {N}종 (빌드 필요)
    - 단순 요소: {N}종 (인라인 처리 예정)

    미연결 컴포넌트를 자동 빌드하고 Code Connect에 등록할까요?"

사용자가 승인하면 Step 4로 진행.
특정 컴포넌트를 제외하거나 순서를 조정할 수 있다.

### Step 4: 미연결 컴포넌트 자동 빌드

미연결 컴포넌트를 **리프(leaf) 컴포넌트부터 상위로** 순차 빌드한다.

#### 빌드 순서 (Bottom-up)

중첩 구조가 있으면 안쪽 컴포넌트부터 먼저 빌드한다:

    예: Card 안에 Button과 Badge가 있는 경우

    1단계: Icon (리프)     → 빌드 + Code Connect 등록
    2단계: Badge (리프)    → 빌드 + Code Connect 등록
    3단계: Button (Icon 포함) → 빌드 + Code Connect 등록
    4단계: Card (Button, Badge 포함) → 빌드 + Code Connect 등록

#### 각 컴포넌트 빌드 절차

미연결 컴포넌트 하나당 기존 파이프라인 Step 1~10을 실행한다:

    1. 해당 컴포넌트의 Figma 노드 데이터 추출
    2. 어노테이션 파싱
    3. 기존 컴포넌트 탐색 (이미 로컬에 있으면 재사용)
    4. 아이콘/에셋 다운로드
    5. 디자인 토큰 매칭/생성
    6. React 컴포넌트 생성
    7. Storybook 스토리 생성
    8. Playwright E2E 테스트
    9. 시각적 비교 루프 (Storybook ↔ Figma)
    10. Code Connect 매핑 등록 (.figma.tsx + publish)

단, 단순 컴포넌트(아이콘, 디바이더 등)는 Storybook/테스트/시각적 비교를 생략하고
코드 + Code Connect 매핑만 생성한다.

#### 빌드 대상 판단

| 유형 | 판단 기준 | 처리 |
|------|----------|------|
| 공통 컴포넌트 | Figma 컴포넌트 라이브러리 소속 | 풀 파이프라인 (빌드 + 테스트 + 등록) |
| 단순 요소 | variant 없음, 노드 5개 이하 | 코드만 생성 (테스트 생략) |
| 레이아웃 프레임 | 컴포넌트 아님, 구조만 있음 | 등록 안 함, 화면 조립 시 Tailwind로 처리 |
| 이미지/일러스트 | 비구조적 요소 | 플레이스홀더 또는 asset으로 처리 |

### Step 5: 화면 조립

모든 컴포넌트가 준비되면 화면을 조립한다.

    // 모든 import는 Code Connect에서 제공된 경로 사용
    import { NdsButton } from '{config.componentPath}'
    import { NdsInput } from '{config.componentPath}'
    import { NdsCheckbox } from '{config.componentPath}'

    // 레이아웃만 새로 작성
    export function LoginPage() {
        return (
            <div className="flex flex-col gap-6 p-8 max-w-md mx-auto">
                <h1 className="text-2xl font-bold">로그인</h1>
                <NdsInput label="이메일" type="email" />
                <NdsInput label="비밀번호" type="password" />
                <NdsCheckbox label="자동 로그인" />
                <NdsButton tone="primary" variant="filled" size="lg">
                    로그인
                </NdsButton>
            </div>
        )
    }

### Step 6: 결과 요약

    ## 화면 변환 결과: 로그인 페이지

    ### 컴포넌트 인벤토리
    | 컴포넌트 | 상태 | 처리 |
    |---------|------|------|
    | Button  | 기존 연결 | CodeConnectSnippet 사용 |
    | Input   | 신규 빌드 | 생성 + 등록 완료 |
    | Checkbox | 신규 빌드 | 생성 + 등록 완료 |

    ### 생성 파일
    | 파일 | 용도 |
    |------|------|
    | NdsInput.tsx | 컴포넌트 |
    | NdsInput.figma.tsx | Code Connect 매핑 |
    | NdsCheckbox.tsx | 컴포넌트 |
    | NdsCheckbox.figma.tsx | Code Connect 매핑 |
    | LoginPage.tsx | 화면 |

    ### 토큰 변경
    - 신규: {N}개
    - 재사용: {N}개

---

## 중첩 컴포넌트 처리

### 문제

Card 안에 Button이 있고, Button 안에 Icon이 있는 경우:

    Card
    ├── CardHeader
    │   └── Badge
    ├── CardBody
    │   └── Text
    └── CardFooter
        ├── Button (← Icon 포함)
        └── Button

이 구조에서 Card, Badge, Button, Icon 각각 .figma.tsx가 필요하다.

### figma.instance()로 중첩 참조

부모 컴포넌트가 자식 컴포넌트를 참조할 때 figma.instance()를 사용한다.
자식이 Code Connect에 등록되어 있으면 부모의 스니펫에 자식 스니펫이 자동 합성된다.

    // NdsButton.figma.tsx — 부모
    figma.connect(NdsButton, 'https://...', {
        props: {
            label: figma.string('Label'),
            icon: figma.instance('Icon'),  // 자식 컴포넌트 참조
        },
        example: ({ label, icon }) => (
            <NdsButton icon={icon}>{label}</NdsButton>
        ),
    })

    // NdsIcon.figma.tsx — 자식 (별도 파일)
    figma.connect(NdsIcon, 'https://...', {
        props: {
            name: figma.enum('IconName', {
                Heart: 'heart',
                Star: 'star',
            }),
        },
        example: ({ name }) => <NdsIcon name={name} />,
    })

결과: Figma에서 Button + Heart Icon을 보면 MCP가 아래를 제공:

    <NdsButton icon={<NdsIcon name="heart" />}>Label</NdsButton>

### figma.children()으로 자식 목록 참조

자식이 여러 개 반복되는 경우 (탭, 리스트 아이템 등):

    // NdsTabs.figma.tsx
    figma.connect(NdsTabs, 'https://...', {
        props: {
            tabs: figma.children('Tab'),  // "Tab" 이름의 자식 인스턴스 전체
        },
        example: ({ tabs }) => <NdsTabs>{tabs}</NdsTabs>,
    })

와일드카드도 지원: figma.children('Tab*')로 Tab1, Tab2 등을 매칭.

### 빌드 순서가 중요한 이유

figma.instance()가 참조하는 자식 컴포넌트가 아직 등록되지 않았으면
부모의 CodeConnectSnippet에서 자식 부분이 원시 노드로 풀려나온다.
그래서 **리프부터 등록**해야 부모가 자식의 스니펫을 올바르게 합성한다.

---

## .figma.tsx 매핑 파일 작성 규칙

### 파일 위치

컴포넌트 파일과 동일 디렉토리에 .figma.tsx 확장자로 생성:

    {config.componentPath}/
    ├── {Prefix}Button.tsx           # 컴포넌트
    ├── {Prefix}Button.figma.tsx     # Code Connect 매핑
    └── index.ts

### figma.connect() 기본 구조

    import figma from '@figma/code-connect/react'
    import { NdsButton } from './NdsButton'

    figma.connect(NdsButton, 'https://www.figma.com/design/{fileKey}?node-id={nodeId}', {
        props: {
            tone: figma.enum('Tone', {
                Primary: 'primary',
                Secondary: 'secondary',
                Danger: 'danger',
            }),
            variant: figma.enum('Variant', {
                Filled: 'filled',
                Ghost: 'ghost',
                Outline: 'outline',
            }),
            size: figma.enum('Size', {
                XL: 'xl',
                LG: 'lg',
                MD: 'md',
                SM: 'sm',
            }),
            disabled: figma.boolean('Disabled'),
            label: figma.string('Label'),
        },
        example: ({ tone, variant, size, disabled, label }) => (
            <NdsButton tone={tone} variant={variant} size={size} disabled={disabled}>
                {label}
            </NdsButton>
        ),
    })

### 프로퍼티 매핑 헬퍼

| Figma 프로퍼티 타입 | Code Connect 헬퍼 | 용도 |
|---------------------|-------------------|------|
| Variant (enum) | figma.enum() | tone, variant, size 등 선택지 |
| Boolean | figma.boolean() | disabled, loading 등 토글 |
| Text | figma.string() | label, placeholder 등 텍스트 |
| Instance swap | figma.instance() | 아이콘 등 중첩 컴포넌트 |
| Instance children | figma.children() | 탭, 리스트 아이템 등 자식 |

### Variant Restriction

하나의 Figma 컴포넌트가 코드에서 여러 컴포넌트로 분리된 경우,
variant 조건으로 각각 매핑한다:

    // IconButton은 contentType이 iconOnly일 때만
    figma.connect(NdsIconButton, 'https://...', {
        variant: { ContentType: 'iconOnly' },
        props: { ... },
        example: ({ icon }) => <NdsIconButton>{icon}</NdsIconButton>,
    })

    // 일반 Button은 나머지
    figma.connect(NdsButton, 'https://...', {
        variant: { ContentType: 'text' },
        props: { ... },
        example: ({ label }) => <NdsButton>{label}</NdsButton>,
    })

### MCP Instructions 추가

Code Connect에 AI 에이전트용 사용 지침을 추가할 수 있다.
이 지침은 CodeConnectSnippet의 instructions 필드에 포함된다:

    figma.connect(NdsButton, 'https://...', {
        props: { ... },
        example: ({ ... }) => ...,
        links: [
            { name: 'Storybook', url: 'http://localhost:{config.storybookPort}/?path=/story/{component}' },
        ],
    })

Figma UI에서는 "Add instructions for MCP" 기능으로도 추가 가능:
- 컴포넌트별 접근성 요구사항
- 특수 사용 패턴 (예: "NdsButton은 form submit에만 type='submit' 사용")
- 금지 사항 (예: "tone='danger'는 삭제 액션에만 사용할 것")

### Publish

프로젝트 package.json의 figma 관련 scripts를 확인하여 실행한다.
명령어는 변경될 수 있으므로 하드코딩하지 않고, 실행 전 package.json을 읽어 확인할 것.

성공 시 Figma Dev Mode에서 해당 컴포넌트 선택 시 코드 스니펫이 표시된다.
MCP Server에서도 CodeConnectSnippet으로 제공된다.

### 관리 명령어

프로젝트 package.json scripts에 figma 관련 명령어(parse, publish, unpublish 등)가 정의되어 있다.
실행 전 반드시 package.json을 읽어 최신 명령어를 확인할 것.

---

## 기대 효과

### 토큰 절감

    컴포넌트 1개의 원시 노드: ~500~2000 토큰
    CodeConnectSnippet:       ~50~100 토큰
    → 컴포넌트당 약 10~20배 축소

    화면에 컴포넌트 10개 사용 시:
    연결 전: 5,000~20,000 토큰 (컴포넌트만)
    연결 후:   500~1,000 토큰 (컴포넌트만)
    + 레이아웃 노드는 동일

### 속도 개선

- LLM 컨텍스트 감소 → 추론 시간 단축
- 코드베이스 탐색 (Step 3) 생략 가능 → 도구 호출 감소
- 정확한 import/props 제공 → 재시도 감소

### 정확도 향상

- 실제 컴포넌트 인터페이스가 보장됨 (props 오타, 누락 방지)
- 디자이너가 의도한 컴포넌트와 코드가 1:1 매칭
- AI가 임의로 새 컴포넌트를 만들지 않음

### 누적 효과

화면을 만들수록 등록된 컴포넌트가 쌓인다.
n번째 화면은 1번째 화면보다 훨씬 빠르고 저렴하다:

    1번째 화면: 컴포넌트 10종 전부 빌드 + 등록 → 느림
    2번째 화면: 7종 이미 등록, 3종만 빌드 → 빠름
    5번째 화면: 9종 이미 등록, 1종만 빌드 → 매우 빠름
    10번째 화면: 전부 등록됨, 레이아웃만 생성 → 거의 즉시

---

## 매핑 등록 기준

모든 컴포넌트를 등록할 필요는 없다. 아래 기준으로 우선순위를 정한다:

### 반드시 등록

- 디자인 시스템 공통 컴포넌트 (Button, Input, Select, Checkbox, Radio 등)
- 3회 이상 재사용되는 컴포넌트
- 내부 구조가 복잡한 컴포넌트 (노드가 많아 토큰 절감 효과가 큰 것)

### 선택 등록

- 특정 화면에서만 사용되는 컴포넌트
- 구조가 단순한 컴포넌트 (아이콘, 디바이더 등)

### 등록 불필요

- 일회성 레이아웃
- 컨텐츠 영역 (텍스트, 이미지 배치)

---

## 주의사항

- Code Connect 파일은 실행되지 않는다. 문자열로 취급되어 스니펫만 제공한다.
- 삼항 연산자 등 조건 로직은 그대로 텍스트로 렌더링된다 (실행 안 됨).
- 루프로 figma.connect()를 동적 생성할 수 없다.
- 중첩 인스턴스는 각각 별도로 connect 해야 한다 (리프부터 등록).
- Figma 컴포넌트의 노드 URL이 변경되면 매핑이 깨진다 (Figma에서 컴포넌트 재구성 시 주의).
- figma.config.json에 include/exclude 경로를 설정하여 publish 범위를 관리한다.
