# 디자인 토큰 관리 규칙

## 토큰 소스 (CRITICAL)

토큰 시스템은 두 개의 CSS 파일로 구성된다:

| 파일 | 경로 (config) | 관리 방식 | 설명 |
|------|--------------|-----------|------|
| tokens.css | `config.tokensCssPath` | **자동 생성** (`npm run build:tokens`) | DTCG 멀티파일 토큰 소스에서 빌드. light/dark/contrast 3테마 |
| portal.css | `config.portalCssPath` | **수동 관리** | Figma에 없는 AI Portal 전용 토큰 |

참조용 소스:

| 경로 (config) | 설명 |
|--------------|------|
| `config.tokenSourceDir` | DTCG 멀티파일 토큰 원본 (tokens/ 디렉토리, 7개 파일) |

### tokens.css 수정 금지 원칙

tokens.css는 `npm run build:tokens`로 자동 생성되므로:

    ❌ 스킬이 tokens.css를 직접 수정하는 것은 절대 금지
    ❌ tokens.css에 새 변수를 수동 추가
    ✅ 새 토큰이 필요하면 portal.css에 추가
    ✅ portal.css 추가 시 기존 portal.css의 네이밍 패턴 준수
    ✅ portal.css에 추가할 때도 @theme { } 블록 내에 정의 (Tailwind 유틸리티 자동 생성)

## 토큰 매칭 절차 (5단계)

### 1단계: CSS 파싱 → CSS 변수 맵 구성

tokens.css와 portal.css를 파싱하여 CSS 변수명 → HEX 값 테이블을 구성한다.

    파싱 절차:
    1. tokens.css 전체 읽기
    2. @theme { } 블록에서 --변수명: 값; 패턴 추출
    3. [data-theme="dark"] { } 블록에서 다크 모드 오버라이드 추출
    4. [data-theme="contrast"] { } 블록에서 고대비 모드 오버라이드 추출
    5. portal.css @theme { } 블록 파싱 → 맵에 병합
    6. 결과: { 변수명: { light: 값, dark: 값, contrast: 값 } } 형태의 맵

### 2단계: Figma RGBA → HEX 변환

Figma MCP는 색상을 RGBA(0~1 범위)로 반환한다.

    변환: Math.round(value * 255).toString(16).padStart(2, '0')
    예시: { r: 0.114, g: 0.122, b: 0.125, a: 1 } → #1D1F20

- alpha가 1이 아닌 경우 8자리 HEX 사용 (#RRGGBBAA)
- alpha가 1이면 6자리 HEX 사용 (#RRGGBB)

### 3단계: 시맨틱 토큰 우선 매칭

HEX 값으로 tokens.css에서 검색한다. 정확 일치 우선.

    검색 범위 (시맨틱 카테고리 우선):
    background, layer, field, border, text, icon, link,
    feedback, interactive, focus, overlay

### 4단계: 컴포넌트 전용 토큰 매칭

시맨틱 매칭 실패 시 컴포넌트 전용 토큰에서 검색한다.

    검색 범위:
    chip, tag, badge, toggle, tooltip, notification,
    codeblock, prompt-input, chatting-bubble

### 5단계: 미매칭 토큰 처리

매칭 실패 시 portal.css에 신규 CSS 변수를 추가한다.

    portal.css 추가 규칙:
    - @theme { } 블록 내에 정의
    - 기존 portal.css의 네이밍 패턴 준수
    - 주석으로 용도를 명시

## 토큰 우선순위 (5단계)

동일 HEX 값이 여러 CSS 변수에 매핑될 때의 선택 우선순위:

| 우선순위 | 카테고리 | 예시 | 이유 |
|---------|---------|------|------|
| 1 | Theme 시맨틱 색상 | `--color-text-primary`, `--color-layer-01` | 테마 전환 시 자동 변경 |
| 2 | Component 전용 색상 | `--color-codeblock-bg`, `--color-chatting-bubble-bg` | 컴포넌트 의도 명확 |
| 3 | portal.css 수동 토큰 | `--color-prompt-bg` | Figma에 없는 AI Portal 전용 |
| 4 | Brand 색상 | `--color-brand-500` | 브랜드 의미 보존 |
| 5 (지양) | Core 팔레트 | `--color-gray-cool-900` | 테마 전환 시 변하지 않음 |

## CSS 변수 → Tailwind 유틸리티 직접 출력 규칙

매칭된 CSS 변수를 Tailwind 유틸리티 클래스로 직접 출력한다.
HEX 임의값 + 주석 방식은 폐기한다.

### 색상 유틸리티 변환

| CSS 변수 패턴 | Tailwind 접두사 | 예시 |
|--------------|----------------|------|
| `--color-background-*` | `bg-background-*` | `bg-background-default` |
| `--color-layer-*` | `bg-layer-*` | `bg-layer-01` |
| `--color-field-*` | `bg-field-*` | `bg-field-01` |
| `--color-border-*` | `border-border-*` | `border-border-default` |
| `--color-text-*` | `text-text-*` | `text-text-primary` |
| `--color-link-*` | `text-link-*` | `text-link-primary` |
| `--color-icon-*` | `text-icon-*` | `text-icon-primary` |
| `--color-feedback-*` | `bg-feedback-*` 또는 `text-feedback-*` | `bg-feedback-error` |
| `--color-interactive-*` | `bg-interactive-*` | `bg-interactive-primary` |
| `--color-focus-*` | `outline-focus-*` | `outline-focus-default` |
| `--color-overlay-*` | `bg-overlay-*` | `bg-overlay-modal` |
| `--color-chip-*` | `bg-chip-*` / `text-chip-*` / `border-chip-*` | 속성에 따라 결정 |
| `--color-toggle-*` | `bg-toggle-*` | `bg-toggle-track-on` |
| `--color-tooltip-*` | `bg-tooltip-*` / `text-tooltip-*` | 속성에 따라 결정 |
| `--color-codeblock-*` | `bg-codeblock-*` / `text-codeblock-*` | 속성에 따라 결정 |
| `--color-prompt-input-*` | `bg-prompt-input-*` | `bg-prompt-input-bg` |
| `--color-chatting-bubble-*` | `bg-chatting-bubble-*` | `bg-chatting-bubble-bg` |

> **참고**: `--color-text-*`와 `--text-*`는 다른 네임스페이스. `text-text-primary`는 color 유틸리티, `text-body`는 font-size 유틸리티.

### 타이포그래피 유틸리티 변환

| CSS 변수 패턴 | Tailwind 접두사 | 예시 |
|--------------|----------------|------|
| `--text-*` | `text-*` (font-size) | `text-body` |

### 사이즈/레이아웃 유틸리티 변환

| CSS 변수 패턴 | Tailwind 접두사 | 예시 |
|--------------|----------------|------|
| `--spacing-*` | `p-*`, `m-*`, `gap-*` | `p-4` (= 16px) |
| `--radius-*` | `rounded-*` | `rounded-md` |
| `--shadow-*` | `shadow-*` | `shadow-md` |

### 컴포넌트 사이즈 토큰 (var() 참조)

| CSS 변수 패턴 | Tailwind 사용법 | 예시 |
|--------------|----------------|------|
| `--comp-height-*` | `h-[var(--comp-height-*)]` | `h-[var(--comp-height-md)]` |
| `--comp-padding-x-*` | `px-[var(--comp-padding-x-*)]` | `px-[var(--comp-padding-x-md)]` |
| `--comp-padding-y-*` | `py-[var(--comp-padding-y-*)]` | `py-[var(--comp-padding-y-md)]` |
| `--comp-gap-*` | `gap-[var(--comp-gap-*)]` | `gap-[var(--comp-gap-md)]` |
| `--comp-icon-size-*` | `w-[var(--comp-icon-size-*)]` | `w-[var(--comp-icon-size-md)]` |
| `--comp-radius-*` | `rounded-[var(--comp-radius-*)]` | `rounded-[var(--comp-radius-wrapper)]` |

### 출력 비교 (기존 → 변경 후)

| 용도 | 기존 스킬 출력 | 변경 후 스킬 출력 |
|------|--------------|--------------------|
| 배경색 | `bg-[#FFFFFF] /* color.layer.01 */` | `bg-layer-01` |
| 텍스트색 | `text-[#101213] /* color.text.primary */` | `text-text-primary` |
| 보더색 | `border-[#E8ECEF] /* color.border.default */` | `border-border-default` |
| 호버 배경 | `hover:bg-[#F3F5F7]` | `hover:bg-layer-01-hover` |
| 타이포그래피 | `text-[14px] leading-[20px]` | `text-body` |
| 타이포+웨이트 | `text-[14px] leading-[20px] font-medium` | `text-body font-medium` |
| 간격 | `gap-[8px] p-[16px]` | `gap-2 p-4` |
| 라운딩 | `rounded-[8px]` | `rounded-md` |
| 컴포넌트 높이 | `h-[28px]` | `h-[var(--comp-height-md)]` |
| 컴포넌트 패딩 | `px-[8px] py-[4px]` | `px-[var(--comp-padding-x-md)] py-[var(--comp-padding-y-md)]` |

## 정적 매핑 테이블 (구 → 신 토큰)

토큰 마이그레이션 모드(`-m`)에서 사용하는 구 → 신 토큰 매핑 테이블.
접두사 규칙: 구/신 모두 Tailwind 접두사(`bg-`/`text-`/`border-`/`hover:bg-` 등)는 유지하고, 토큰 이름 부분만 교체한다.

### 배경/레이어 토큰

| 구 토큰 이름 부분 | 신 토큰 이름 부분 | 접두사 예시 |
|----------------|-----------------|-----------:|
| `fill-standard-default` | `layer-01` | `bg-` |
| `fill-standard-hover` | `layer-01-hover` | `bg-` / `hover:bg-` |
| `fill-standard-active` | `layer-01-active` | `bg-` / `active:bg-` |
| `fill-inverse-default` | `interactive-primary` | `bg-` |
| `fill-inverse-hover` | `interactive-primary-hover` | `bg-` / `hover:bg-` |
| `fill-inverse-active` | `interactive-primary-active` | `bg-` / `active:bg-` |
| `fill-tertiary-default` | `layer-02` | `bg-` |
| `fill-disable-default` | `interactive-disabled` | `bg-` |
| `fill-transparent-hover` | `interactive-tertiary-hover` | `hover:bg-` |

### 텍스트 토큰

| 구 토큰 이름 부분 | 신 토큰 이름 부분 | 접두사 예시 |
|----------------|-----------------|-----------:|
| `text-standard-default` | `text-primary` | `text-` |
| `text-secondary-default` | `text-secondary` | `text-` |
| `text-tertiary-default` | `text-tertiary` | `text-` |
| `text-inverse-default` | `text-on-color` | `text-` |
| `text-disable-default` | `text-disabled` | `text-` |
| `text-accent-default` | `text-brand` | `text-` |
| `text-accent-active` | `text-brand-active` | `text-` |
| `text-success-default` | `text-success` | `text-` |

### 보더 토큰

| 구 토큰 이름 부분 | 신 토큰 이름 부분 | 접두사 예시 |
|----------------|-----------------|-----------:|
| `line-standard-default` | `border-default` | `border-` |
| `line-disable-default` | `border-disabled` | `border-` |

### 포커스/아웃라인 토큰

| 구 토큰 이름 부분 | 신 토큰 이름 부분 | 접두사 예시 |
|----------------|-----------------|-----------:|
| `brand-default` (outline) | `focus-default` | `outline-` / `focus-visible:outline-` |

### portal.css → tokens.css 매핑 (제거 대상)

portal.css에서 제거하고 tokens.css 신 토큰으로 교체해야 하는 항목:

| portal.css 토큰 | tokens.css 대응 토큰 | 컴포넌트 코드 변경 |
|-----------------|---------------------|--------------------|
| `--color-button-danger-default` | `--color-interactive-danger-strong-default` | `bg-button-danger-default` → `bg-interactive-danger-strong-default` |
| `--color-button-danger-hover` | `--color-interactive-danger-strong-hover` | `bg-button-danger-hover` → `bg-interactive-danger-strong-hover` |
| `--color-button-danger-ghost-hover` | `--color-interactive-danger-weak-hover` | `bg-button-danger-ghost-hover` → `bg-interactive-danger-weak-hover` |
| `--color-button-danger-ghost-active` | `--color-interactive-danger-weak-active` | `bg-button-danger-ghost-active` → `bg-interactive-danger-weak-active` |
| `--color-text-accent-default` | `--color-text-brand` | `text-text-accent-default` → `text-text-brand` |
| `--color-text-accent-active` | `--color-text-brand-active` | `text-text-accent-active` → `text-text-brand-active` |
| `--color-button-link-default` | `--color-link-primary` | `text-button-link-default` → `text-link-primary` |
| `--color-button-link-hover` | `--color-link-primary-hover` | `text-button-link-hover` → `text-link-primary-hover` |
| `--color-button-link-active` | `--color-link-primary-active` | `text-button-link-active` → `text-link-primary-active` |

### CSS 변수 참조 매핑 (index.css 등)

| 구 CSS 변수 참조 | 신 CSS 변수 | 용도 |
|------------------|------------|------|
| `var(--color-text-standard-default)` | `var(--color-text-primary)` | .nds-markdown 본문 |
| `var(--color-fill-standard-active)` | `var(--color-layer-01-active)` | .nds-markdown code 배경 |
| `var(--color-fill-standard-default)` | `var(--color-layer-01)` | .nds-markdown pre, table 배경 |
| `var(--color-fill-standard-hover)` | `var(--color-layer-01-hover)` | .nds-markdown th 배경 |
| `var(--color-line-standard-default)` | `var(--color-border-default)` | .nds-markdown blockquote, table 보더 |
| `var(--color-text-secondary-default)` | `var(--color-text-secondary)` | .nds-markdown blockquote 텍스트 |
| `var(--color-brand-default)` | `var(--color-link-primary)` | .nds-markdown a 링크 |
| `var(--color-brand-hover)` | `var(--color-link-primary-hover)` | .nds-markdown a:hover |

### 치환 예시

    bg-fill-standard-default              → bg-layer-01
    hover:bg-fill-standard-hover          → hover:bg-layer-01-hover
    text-text-standard-default            → text-text-primary
    text-text-inverse-default             → text-text-on-color
    border-line-standard-default          → border-border-default
    focus-visible:outline-brand-default   → focus-visible:outline-focus-default
    text-h-2                              → text-heading (Figma 확인 후 결정)

### brand-default 분기 처리

`brand-default`는 컨텍스트에 따라 다르게 매핑된다.
스킬은 Tailwind 접두사를 보고 컨텍스트를 판별한다.

| 사용 컨텍스트 | 구 클래스 | 신 클래스 |
|--------------|----------|----------|
| 텍스트 (링크) | `text-brand-default` | `text-link-primary` |
| 텍스트 (강조) | `text-brand-default` | `text-text-brand` |
| 배경 (버튼) | `bg-brand-default` | `bg-interactive-primary` |
| 포커스 링 | `outline-brand-default` | `outline-focus-default` |

## 타이포그래피 매칭 규칙

Figma에서 추출한 fontSize/lineHeight/letterSpacing 조합을 tokens.css의 `--text-*` 숏핸드로 매핑한다.

### 일반 타이포그래피

| fontSize | lineHeight | letterSpacing | Tailwind 클래스 |
|----------|-----------|--------------|-----------------|
| 11px | 16px | 0.01em | `text-caption` |
| 12px | 18px | 0.01em | `text-helper` |
| 14px | 20px | 0em | `text-body` |
| 16px | 24px | 0em | `text-body-reading` 또는 `text-subtitle` |
| 20px | 28px | -0.01em | `text-title` |
| 28px | 36px | -0.02em | `text-heading` |
| 36px | 44px | -0.025em | `text-display` |
| 48px | 56px | -0.03em | `text-hero` |

### 컴포넌트 사이즈별 폰트

| fontSize | lineHeight | Tailwind 클래스 |
|----------|-----------|-----------------|
| 11px | 16px | `text-comp-xs` |
| 12px | 18px | `text-comp-sm` |
| 14px | 20px | `text-comp-md` |
| 16px | 24px | `text-comp-lg` |
| 20px | 28px | `text-comp-xl` |

### fontWeight 유틸리티 조합

fontWeight은 별도 유틸리티로 조합한다:

| Figma fontWeight | Tailwind 클래스 |
|-----------------|-----------------|
| Regular (400) | (기본값, 생략) |
| Medium (500) | `font-medium` |
| SemiBold (600) | `font-semibold` |
| Bold (700) | `font-bold` |

## 금지 패턴

    ❌ bg-[#HEX] — 하드코딩 색상 임의값
    ❌ 구 토큰명 사용 — fill-standard-*, text-standard-*, line-standard-*, text-accent-*, fill-inverse-* 등
    ❌ Core 팔레트 직접 참조 — bg-gray-cool-500 등 (다크 모드에서 색상이 안 바뀜)

    ✅ Tailwind 유틸리티 클래스 — bg-layer-01, text-text-primary 등
    ✅ CSS 변수 임의값 — bg-[var(--color-*)] (유틸리티가 없는 경우 허용)
    ✅ 컴포넌트 사이즈 토큰 var() 참조 — h-[var(--comp-height-md)]

## 토큰 변경 보고 형식

결과 요약에 아래 형식으로 포함한다:

    ### 토큰 변경
    - 매칭: {N}개
      - bg-layer-01 (--color-layer-01: #ffffff)
      - text-text-primary (--color-text-primary: #101213)
      - ...
    - 미매칭 → portal.css 추가: {N}개
      - --color-{name}: #HEX (용도: ...)
      - ...
    - 구 토큰 교체: {N}개 (마이그레이션 모드)
      - bg-fill-standard-default → bg-layer-01
      - text-text-standard-default → text-text-primary
      - ...
