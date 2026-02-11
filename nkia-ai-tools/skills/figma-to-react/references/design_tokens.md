# 디자인 토큰 관리 규칙

## tokens.json 경로

    shared/styles/tokens.json

파일이 없으면 빈 객체 `{}` 로 생성한다.

## 토큰 관리 방식: 증분(incremental)

전체 토큰을 미리 생성하지 않는다. 컴포넌트 변환 시마다 필요한 토큰만 추가한다.

### 절차

1. tokens.json 읽기
2. Figma MCP에서 추출한 RGBA를 HEX로 변환
3. 기존 토큰에서 동일 HEX 검색
   - 있으면: 기존 토큰 이름 재사용
   - 없으면: 시맨틱 이름으로 신규 토큰 생성
4. 사이즈, border-radius, font-weight 등도 동일 절차
5. tokens.json 업데이트 (신규 토큰만 추가, 기존 값 수정 금지)
6. 변경 사항을 결과 요약에 포함

## RGBA → HEX 변환

Figma MCP는 색상을 RGBA(0~1 범위)로 반환한다.

    변환: Math.round(value * 255).toString(16).padStart(2, '0')
    예시: { r: 0.114, g: 0.122, b: 0.125, a: 1 } → #1D1F20

- alpha가 1이 아닌 경우 8자리 HEX 사용 (#RRGGBBAA)
- alpha가 1이면 6자리 HEX 사용 (#RRGGBB)

## 토큰 네이밍 규칙

### 색상 토큰

    color.{tone}.{variant}: "#XXXXXX"
    color.{tone}.{variant}.hover: "#XXXXXX"
    color.{tone}.{variant}.active: "#XXXXXX"
    color.{tone}.{variant}.text: "#XXXXXX"
    color.{tone}.{variant}.border: "#XXXXXX"

예시:

    color.primary.filled: "#1D1F20"
    color.primary.filled.hover: "#3E4142"
    color.primary.filled.active: "#5C6061"
    color.primary.filled.text: "#FFFFFF"
    color.danger.filled: "#ED121D"
    color.danger.filled.hover: "#C70F18"

### 비활성 상태 토큰

    color.disabled.bg: "#F4F5F5"
    color.disabled.text: "#ABB2B5"
    color.disabled.border: "#EBEDED"

### 사이즈 토큰

    size.{component}.{size}.height: "{value}"
    size.{component}.{size}.paddingX: "{value}"
    size.{component}.{size}.paddingY: "{value}"
    size.{component}.{size}.fontSize: "{value}"
    size.{component}.{size}.lineHeight: "{value}"
    size.{component}.{size}.gap: "{value}"

예시:

    size.button.xl.height: "48px"
    size.button.xl.paddingX: "20px"
    size.button.xl.paddingY: "12px"

### 기타 토큰

    radius.{component}: "{value}"
    font.weight.{name}: "{value}"
    font.family.{name}: "{value}"

예시:

    radius.button: "4px"
    font.weight.normal: "400"
    font.family.default: "Spoqa Han Sans Neo, sans-serif"

## tokens.json 스키마

    {
      "color": {
        "primary": {
          "filled": "#1D1F20",
          "filled.hover": "#3E4142",
          "filled.active": "#5C6061",
          "filled.text": "#FFFFFF",
          "ghost": "transparent",
          "ghost.text": "#1D1F20",
          "ghost.border": "#3E4142",
          ...
        },
        "danger": { ... },
        "secondary": { ... },
        "disabled": {
          "bg": "#F4F5F5",
          "text": "#ABB2B5",
          "border": "#EBEDED"
        }
      },
      "size": {
        "button": {
          "xl": { "height": "48px", "paddingX": "20px", ... },
          "lg": { ... },
          "md": { ... },
          "sm": { ... }
        }
      },
      "radius": {
        "button": "4px"
      },
      "font": {
        "weight": { "normal": "400" },
        "family": { "default": "Spoqa Han Sans Neo, sans-serif" }
      }
    }

## 중복 검출 로직

토큰 생성 전 반드시 기존 토큰에서 동일 값을 검색한다.

### 검색 우선순위
1. 정확한 값 일치 (HEX 대소문자 무시)
2. 같은 카테고리 내에서 검색 (color → color, size → size)

### 재사용 예시
- Figma에서 추출한 배경색이 #F4F5F5인데, color.disabled.bg에 이미 #F4F5F5가 있으면 → 기존 토큰 재사용
- 새 컴포넌트의 border-radius가 4px인데, radius.button에 이미 4px가 있으면 → radius를 컴포넌트 공통으로 승격 검토

## 컴포넌트 코드에서 토큰 사용

### 금지: Tailwind 임의값 직접 사용

    // Bad — 토큰 추적 불가
    'bg-[#1D1F20] hover:bg-[#3E4142]'

### 권장: 토큰 참조 방식

현재는 tokens.json의 값을 참조하여 Tailwind 임의값으로 적용하되,
주석으로 토큰 이름을 명시한다.

    // 토큰: color.primary.filled, color.primary.filled.hover
    'bg-[#1D1F20] hover:bg-[#3E4142]'

향후 Tailwind CSS v4의 CSS 변수 테마와 통합하면
토큰을 CSS 변수로 전환할 수 있다.

    // 미래 목표
    'bg-[var(--color-primary-filled)] hover:bg-[var(--color-primary-filled-hover)]'

## 토큰 변경 보고 형식

결과 요약에 아래 형식으로 포함한다:

    ### 토큰 변경
    - 신규: {N}개
      - color.primary.filled: #1D1F20
      - color.primary.filled.hover: #3E4142
      - ...
    - 재사용: {N}개
      - color.disabled.bg (기존 값 #F4F5F5)
      - ...
