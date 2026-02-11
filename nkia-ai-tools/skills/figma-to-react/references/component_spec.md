# MCP:ComponentSpec 어노테이션 규칙

디자이너가 Figma 컴포넌트에 [MCP:ComponentSpec] 어노테이션을 추가하면,
이 스펙이 Figma variant property보다 우선한다.

## 어노테이션 형식

Figma 컴포넌트의 Description 또는 별도 텍스트 레이어에 아래 형식으로 작성:

    [MCP:ComponentSpec]

    State(interaction)
    - default | hover | focus | active
    - user interaction에 의해 자동 전이
    - code prop으로 제어하지 않음
    - visual spec only

    Prop
    - disabled: boolean
    - tone: default | error | success

    Rule
    - disabled=true 일 경우 모든 interaction state 무시
    - tone는 state와 조합 가능

    Priority
    disabled > tone > state

## 섹션별 파싱 규칙

### State(interaction)
- 인터랙션 기반 시각 상태 (hover, focus, active 등)
- **React prop으로 생성하지 않는다**
- **Storybook args로 노출하지 않는다**
- CSS pseudo-class로만 구현 (hover:, focus:, active:)
- Storybook에서는 Docs 또는 pseudo-state 애드온으로 시연

### Prop
- 이 섹션에 정의된 항목만 React 컴포넌트 props로 생성
- Figma variant property에 있더라도 Prop 섹션에 없으면 무시
- 타입 표기: boolean, string enum (| 구분), number

### Rule
- prop 간 충돌 해소 규칙
- 무효 조합 방지 (예: disabled=true이면 interaction state 무시)
- 컴포넌트 내부 로직으로 구현

### Priority
- prop 적용 우선순위
- 왼쪽이 우선 (disabled > tone > state)
- disabled가 true이면 tone 스타일도 무시하고 disabled 스타일 적용

## 어노테이션 유무에 따른 동작

### 어노테이션 있음
1. Prop 섹션의 항목만 React props로 생성
2. State(interaction) 항목은 CSS pseudo로만 처리
3. Rule과 Priority로 내부 로직 구성
4. Figma variant property 중 어노테이션에 없는 것은 무시

### 어노테이션 없음 (폴백)
1. Figma variant property를 분석하여 props 추론
2. state 관련 property(default, hover, pressed, focused)는 CSS pseudo로 처리
3. **사용자에게 구현 범위 확인** (과잉 생성 방지)
4. contentType 등 prop 값이 있더라도 실제 디자인 존재 여부 확인 필요

## 예시: Button 컴포넌트

### 어노테이션

    [MCP:ComponentSpec]

    State(interaction)
    - default | hover | focus | active

    Prop
    - disabled: boolean
    - tone: primary | secondary | danger
    - variant: filled | ghost | outline | text | link
    - size: xl | lg | md | sm

    Rule
    - disabled=true 일 경우 모든 interaction state 무시
    - tone×variant 유효 조합: primary/filled, primary/ghost, primary/link,
      danger/filled, secondary/outline, secondary/ghost, secondary/text
    - 유효하지 않은 조합은 primary/filled로 폴백

    Priority
    disabled > tone + variant > size > state

### 생성 결과

    interface NdsButtonProps {
        tone?: 'primary' | 'secondary' | 'danger'
        variant?: 'filled' | 'ghost' | 'outline' | 'text' | 'link'
        size?: 'xl' | 'lg' | 'md' | 'sm'
        disabled?: boolean
        // hover, focus, active는 props에 없음
    }

### Storybook args

    argTypes: {
        tone: { control: 'select', options: ['primary', 'secondary', 'danger'] },
        variant: { control: 'select', options: ['filled', 'ghost', 'outline', 'text', 'link'] },
        size: { control: 'select', options: ['xl', 'lg', 'md', 'sm'] },
        disabled: { control: 'boolean' },
        // hover, focus, active는 args에 없음
    }
