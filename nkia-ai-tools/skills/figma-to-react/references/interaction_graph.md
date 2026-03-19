# Interaction Graph 추출 (Step 1.6)

## 개요

Figma REST API에서 `interactions` 필드를 추출하여 3종류의 인터랙션 그래프를 생성한다.
이 그래프는 이후 Step에서 컴포넌트 state 설계, 이벤트 핸들러 연결, 라우팅 스캐폴딩에 활용된다.

MCP 도구는 interactions 데이터를 의도적으로 생략하므로 REST API 직접 호출이 필수.

### 실행 조건

- **항상 실행**: 컴포넌트 단위든 화면 수준이든 interactions 추출을 시도한다
- interactions가 0개인 경우: 경고 출력 후 건너뛰기 (파이프라인 블로커 아님)

## 1.6-1. REST API 호출

Figma REST API로 대상 노드의 interactions 필드를 추출한다.

    GET https://api.figma.com/v1/files/{fileKey}/nodes?ids={nodeId}&depth=10
    Header: X-Figma-Token: {FIGMA_ACCESS_TOKEN}

depth=10으로 호출하여 중첩된 인스턴스 내부의 인터랙션까지 수집.

    주의사항:
    - 환경변수 FIGMA_ACCESS_TOKEN 사용 (PAT)
    - depth가 클수록 응답이 커지므로, 노드 단위로 호출 (페이지 전체 금지)
    - 응답에서 interactions 필드만 파싱 (전체 구조 데이터는 MCP에서 이미 추출)
    - null children 방어 코드 필수 (실험에서 발견)

## 1.6-2. Interaction 파싱 및 분류

응답의 모든 노드를 재귀 탐색하여 `interactions` 배열이 있는 노드를 수집한다.
수집된 인터랙션을 아래 4가지 그래프로 분류한다.

### A. State Machine (CHANGE_TO)

같은 컴포넌트의 variant를 전환하는 인터랙션.
컴포넌트 내부 상태 설계의 근거가 된다.

    추출 형식:
    | 소스 노드 | 트리거 | 대상 variant | transition |
    |-----------|--------|-------------|------------|
    | Log (collapsed=true) | ON_CLICK | collapsed=false | SMART_ANIMATE |
    | thinkingAccordion (default) | ON_HOVER | hover | DISSOLVE |
    | theme=lightMode | ON_CLICK | theme=darkMode | SMART_ANIMATE |

    중복 제거:
    - 동일 컴포넌트 인스턴스가 여러 번 나오면 (예: menuItem 14개) 대표 1개만 남긴다
    - 키: (소스 노드명, 트리거, 대상 노드명)

    destination nodeId resolve:
    - CHANGE_TO의 destinationId는 같은 컴포넌트 셋 내의 다른 variant를 가리킴
    - 응답 데이터에서 destinationId의 노드명을 조회하여 variant 값을 추출
    - 조회 실패 시: destinationId만 기록 (이후 수동 확인)

    코드 활용:
    - ON_HOVER → CSS :hover pseudo-class (React state 불필요)
    - ON_CLICK + CHANGE_TO → useState 토글 (collapsed, expanded, active 등)
    - AFTER_TIMEOUT + CHANGE_TO → useEffect + setTimeout (로딩 애니메이션 등)

### B. Navigation Map (NAVIGATE)

다른 화면/프레임으로 이동하는 인터랙션.
라우팅 구조와 onClick → navigate 핸들러의 근거가 된다.

    추출 형식:
    | 소스 노드 | 소스 화면 | 트리거 | 대상 화면 (nodeId) | 대상 화면명 | transition |
    |-----------|----------|--------|-------------------|-----------|------------|
    | "도구" 버튼 | 메인화면 | ON_CLICK | 4154:19904 | 도구화면 | SMART_ANIMATE |
    | "뒤로" 버튼 | 도구화면 | ON_CLICK | 2101:46330 | 메인화면 | DISSOLVE |

    destination resolve:
    - NAVIGATE의 destinationId는 다른 프레임(화면)을 가리킴
    - 파일 내에서 해당 nodeId의 프레임명을 조회
    - 같은 페이지 내에 있으면 바로 resolve 가능
    - 다른 페이지에 있으면: 추가 API 호출로 resolve 또는 "미확인" 표시

    코드 활용:
    - React Router navigate() 호출 또는 상태 기반 뷰 전환
    - 소스 노드의 onClick에 navigation 핸들러 연결

### C. Overlay Map (OVERLAY + CLOSE)

모달, 팝오버, 툴팁 등 오버레이 표시/닫기 인터랙션.

    추출 형식:
    | 소스 노드 | 트리거 | 오버레이 대상 (nodeId) | 오버레이 명 | 동작 |
    |-----------|--------|---------------------|-----------|------|
    | sider/category | ON_HOVER | 3127:10625 | tooltip | OPEN |
    | close 버튼 | ON_CLICK | — | — | CLOSE |

    코드 활용:
    - Headless UI Dialog/Popover/Menu 컴포넌트
    - useState(isOpen) + trigger 요소의 onClick/onHover

### D. Variable Mode (SET_VARIABLE_MODE)

Figma 변수 모드 변경 (테마, 다크모드 등).

    추출 형식:
    | 소스 노드 | 트리거 | 변수 | 모드 변경 |
    |-----------|--------|------|----------|
    | theme-button | ON_CLICK | theme | light → dark |

    코드 활용:
    - Context Provider 기반 테마 전환
    - CSS class 토글 (dark: prefix)

## 1.6-3. Interaction Graph 출력

파싱 결과를 구조화된 형식으로 출력한다.

    ## Interaction Graph: {컴포넌트/화면명}

    ### A. State Machine ({N}개)
    | # | 컴포넌트 | 트리거 | 상태 전환 | 코드 유형 |
    |---|---------|--------|----------|----------|
    | 1 | Log | ON_CLICK | collapsed=true → false | useState |
    | 2 | thinkingAccordion | ON_HOVER | default → hover | CSS :hover |
    | 3 | theme-button | ON_CLICK | lightMode ↔ darkMode | Context |
    | 4 | loadingGradient | AFTER_TIMEOUT | action=start → end | useEffect |

    ### B. Navigation Map ({N}개)
    | # | 소스 | 트리거 | 대상 화면 | 상태 |
    |---|------|--------|----------|------|
    | 1 | "도구" 버튼 | ON_CLICK | 도구화면 (4154:19904) | 확인됨 |
    | 2 | "뒤로" 버튼 | ON_CLICK | 메인화면 (2101:46330) | 추론 |

    ### C. Overlay Map ({N}개)
    | # | 소스 | 트리거 | 오버레이 | 동작 |
    |---|------|--------|---------|------|
    | 1 | sider/category | ON_HOVER | tooltip (3127:10625) | OPEN |
    | 2 | close 버튼 | ON_CLICK | — | CLOSE |

    ### D. Variable Mode ({N}개)
    | # | 소스 | 변수 | 변경 |
    |---|------|------|------|
    | 1 | theme-button | theme | light ↔ dark |

    ### 신뢰도
    - 프로토타입 연결 기반: {N}개 (확인됨)
    - 구조 추론 기반: {N}개 (Step 8.5에서 사용자 확인 필요)
    - 데이터 없음 (인터랙션 0개): Step 건너뜀

## 1.6-4. 프로토타입 미연결 시 추론 전략

디자이너가 프로토타입 연결을 걸지 않은 경우 (interactions 0개 또는 극소수),
디자인 구조에서 인터랙션을 추론한다.

    추론 소스:
    1. Figma variant property 이름 — isFocused, isCollapsed, isExpanded 등
       → State Machine 추론
    2. 노드 naming convention — "close-button", "back-button", "menu-trigger" 등
       → Navigation/Overlay 추론
    3. MCP 데이터의 컴포넌트 구조 — Button 안에 navigate 관련 텍스트가 있으면
       → Navigation 추론
    4. Step 1.5 기획 스펙 — [IF-xx] 인터랙션 플로우가 있으면
       → 기획 기반 인터랙션 추론

    추론 결과의 신뢰도 표시:
    - 확인됨 (confirmed): 프로토타입 연결이 실제로 존재
    - 추론 (inferred): 구조/네이밍에서 추론, Step 8.5에서 사용자 확인 필요
    - 기획 기반 (spec-based): 기획 스펙 [IF-xx]에서 파생, Step 8.5에서 사용자 확인 필요

    추론을 하지 않는 경우:
    - 명확한 근거 없이 임의로 인터랙션을 만들지 않는다
    - 추론 불가능한 항목은 "미확인"으로 남기고 Step 8.5에서 사용자에게 질문

## 1.6-5. Main Component 조회 및 Dev Comment 추출

### 목적

INSTANCE 노드의 원본 Main Component를 찾아 다음을 추출한다:
- 프로토타입 인터랙션 (interactions) — Main Component에만 달려 있고, 인스턴스에는 복사되지 않음
- Dev 코멘트 — 디자이너/개발자가 Main Component에 남긴 구현 의도, 동작 설명

### 실행 시점

**컴포넌트 URL 직접 입력 시:**
- 입력된 URL이 이미 Main Component(COMPONENT 또는 COMPONENT_SET)를 가리키므로
  해당 노드에서 interactions + dev 코멘트를 바로 추출

**화면 URL 입력 시:**
- 화면 내 INSTANCE 노드를 탐색하여 Code Connect가 없는 컴포넌트를 식별
- 각 INSTANCE의 componentId로 Main Component를 resolve
- Main Component의 interactions + dev 코멘트를 추출
- 이 정보를 해당 컴포넌트 빌드(Step 6, 6.5)에서 활용

### 1.6-5-a. Main Component Resolution

Figma REST API 응답에서 INSTANCE 노드의 `componentId` 필드를 사용한다.

    절차:
    1. 화면 REST API 응답에서 INSTANCE 노드 목록 추출
    2. Code Connect가 있는 인스턴스는 건너뛰기 (이미 매핑됨)
    3. Code Connect가 없는 인스턴스의 componentId 수집
    4. Main Component 조회:
       GET /v1/files/{fileKey}/nodes?ids={componentId}&depth=2
       Header: X-Figma-Token: {FIGMA_ACCESS_TOKEN}
    5. 응답에서 interactions + 구조 데이터 추출

    중복 호출 방지:
    - 같은 componentId를 가진 인스턴스가 여러 개면 (예: menuItem 14개)
      Main Component 조회는 1번만 수행
    - componentId 기준으로 deduplicate하여 API 호출 최소화

    componentId가 다른 파일에 있는 경우 (팀 라이브러리):
    - 응답의 componentId로 조회 실패 시, 컴포넌트가 외부 라이브러리에 있음
    - 이 경우 "외부 라이브러리 컴포넌트"로 표기, 별도 조회하지 않음
    - 단, 디자인 시스템 파일의 fileKey가 config에 있으면 해당 파일에서 조회 시도

### 1.6-5-b. Dev Comment 추출

Main Component에 달린 Figma 코멘트를 추출한다.

    API 호출:
    GET /v1/files/{fileKey}/comments
    Header: X-Figma-Token: {FIGMA_ACCESS_TOKEN}

    응답 필터링:
    - client_meta.node_id가 대상 Main Component의 nodeId와 일치하는 코멘트 추출
    - Main Component의 하위 노드(variant 각각)에 달린 코멘트도 포함
    - resolved(해결됨) 상태인 코멘트는 제외 (이미 반영된 것)

    추출 형식:
    | # | 작성자 | 대상 노드 | 내용 | 유형 |
    |---|--------|----------|------|------|
    | 1 | designer | Button/primary/hover | "hover 시 배경 opacity 0.9" | 인터랙션 |
    | 2 | dev | Input/focused | "focus 시 ring-2 primary" | 스타일 |
    | 3 | designer | Tooltip | "300ms delay 후 표시" | 동작 |

    코멘트 유형 분류:
    - 인터랙션 관련: hover, click, focus, toggle 등 → Step 6.5 인터랙션 연결에 활용
    - 스타일 관련: 색상, 크기, 간격 등 → Step 6 컴포넌트 생성에 활용
    - 동작 관련: 딜레이, 애니메이션, 조건 등 → Step 6.5 인터랙션 연결에 활용
    - 기타: 결과 요약에 "Dev 코멘트 참고 사항"으로 기록

    Comments API 최적화:
    - 파일의 전체 코멘트를 가져오므로, 대상 nodeId 목록으로 필터링
    - 파일 당 1회만 호출하고 결과를 캐시 (같은 파일에서 여러 컴포넌트 조회 시)

### 1.6-5-c. Interaction Graph 출력에 통합

Main Component에서 추출한 interactions와 dev 코멘트를 Interaction Graph 출력(1.6-3)에 통합한다.

    Interaction Graph 출력에 추가 섹션:

    ### E. Main Component 정보 ({N}개 컴포넌트)
    | # | 컴포넌트 | Main Component ID | interactions | dev 코멘트 |
    |---|---------|-------------------|-------------|-----------|
    | 1 | Button | 4701:91201 | 3개 (hover, click, focus) | 2개 |
    | 2 | Input | 4263:64060 | 1개 (focus) | 1개 |
    | 3 | Tooltip | 5102:33001 | 0개 | 1개 ("300ms delay") |

    ### F. Dev 코멘트 요약
    | # | 컴포넌트 | 코멘트 내용 | 코드 반영 방식 |
    |---|---------|-----------|--------------|
    | 1 | Button | "hover 시 배경 opacity 0.9" | hover:opacity-90 |
    | 2 | Tooltip | "300ms delay 후 표시" | setTimeout(300) |

## 1.6-6. 기획 스펙(Step 1.5)과의 통합

Step 1.5에서 추출한 인터랙션 플로우([IF-xx])와 Interaction Graph(1.6-2)를 교차 대조한다.
Main Component에서 추출한 interactions/dev 코멘트(1.6-5)도 교차 대조에 포함한다.

    교차 대조 매트릭스:
    | 상태 | 의미 | 처리 |
    |------|------|------|
    | 기획 ✅ + Graph ✅ | 기획과 프로토타입 모두 있음 | 가장 신뢰도 높음, 바로 구현 |
    | 기획 ✅ + Graph ❌ | 기획에만 있고 프로토타입 미연결 | 기획 기반 구현, Step 8.5에서 확인 |
    | 기획 ❌ + Graph ✅ | 프로토타입에만 있고 기획서 미기술 | 구현하되, 기획 누락인지 확인 |
    | 기획 ❌ + Graph ❌ | 둘 다 없음 | 추론 시도, 추론 불가 시 건너뛰기 |

## 알려진 한계

### Figma REST API interactions의 한계

| 한계 | 영향 | 대안 |
|------|------|------|
| 데이터 흐름 없음 | "어떤 값을 다음 화면에 넘기는지" 알 수 없음 | 기획 스펙에서 보강 |
| 비즈니스 로직 없음 | "권한에 따라 다른 화면" 같은 조건 분기 없음 | 기획 스펙에서 보강 |
| 프로토타입 미연결 시 데이터 없음 | NAVIGATE/OVERLAY가 0개 | 구조 추론 + Step 8.5 사용자 대화 |
| 컴포넌트 셋 내부 interactions만 | 팀 라이브러리 컴포넌트의 내부 interactions는 안 나올 수 있음 | 컴포넌트 URL로 별도 호출 |
| depth 10 응답 크기 | 복잡한 화면은 응답이 수 MB | 필요 시 depth를 줄이고 하위 노드를 별도 호출 |

### 디자이너 의존성

| 항목 | 의존도 | 비고 |
|------|--------|------|
| 프로토타입 연결 | 높음 | 연결이 없으면 NAVIGATE/OVERLAY 추출 불가 |
| variant naming | 중간 | isFocused, isCollapsed 같은 시맨틱 이름이어야 추론 가능 |
| 기획 스펙 | 낮음 | 있으면 좋지만 없어도 동작 |
