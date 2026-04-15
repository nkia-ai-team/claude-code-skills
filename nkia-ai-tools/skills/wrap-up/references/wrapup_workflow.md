# Wrap-up Workflow 상세

## 1. 타겟 브랜치 판별 (브랜치 정리용)

머지 후 어느 브랜치로 전환할지 결정합니다.

### 판별 원리

wrap-up 시점에는 HEAD가 방금 머지된 feature 브랜치입니다. 이 HEAD가 **실제로 어느 base에서 분기됐는지**를 원격 후보 브랜치와의 커밋 거리로 찾습니다. `<cand>..HEAD`(HEAD에 있으나 후보에 없는 커밋 수)가 가장 작은 후보가 실제 base입니다.

kickoff가 `develop-10.2.4_3`에서 feature를 뽑았다고 가정:

| 후보 | `<cand>..HEAD` | 판정 |
|------|----------------|------|
| `origin/develop-10.2.4_3` | N (feature 커밋 수) | **최솟값 — 실제 base** |
| `origin/develop-10.2.4_2` | N + (2→3 델타) | 이전 버전 |
| `origin/develop` | N + (누적) | 상위 base |
| `origin/main` | 훨씬 더 큼 | 최상위 |

submit 스킬과 동일한 알고리즘이며, 레포 이름 테이블은 사용하지 않습니다.

### 판별 + 브랜치 정리 스크립트

    git fetch origin --quiet

    # 후보 base: 버전 브랜치 (-chat 변형 포함) + 전통 fallback
    candidates=$(git for-each-ref --format='%(refname:short)' refs/remotes/origin/ \
      | grep -E '^origin/(develop-10\.[0-9]+\.[0-9]+_[0-9]+(-chat)?|develop|main|master)$')

    if [ -z "$candidates" ]; then
      echo "WARN: 후보 base 브랜치를 찾지 못했습니다. fallback으로 develop 또는 main 사용." >&2
      TARGET_BRANCH=$(git ls-remote --heads origin develop main 2>/dev/null \
        | awk '{print $2}' | sed 's|refs/heads/||' | head -1)
    else
      # HEAD의 고유 커밋 수가 가장 적은 후보 = 실제 base
      best_base=""
      best_ahead=999999999
      for cand in $candidates; do
        ahead=$(git rev-list --count "$cand..HEAD" 2>/dev/null) || continue
        if [ "$ahead" -lt "$best_ahead" ]; then
          best_ahead=$ahead
          best_base=$cand
        fi
      done
      TARGET_BRANCH="${best_base#origin/}"
    fi

    echo "Auto-detected target: $TARGET_BRANCH (ahead: $best_ahead)"

    # 타겟 브랜치로 전환
    git checkout "$TARGET_BRANCH"

    # 최신화
    git pull origin "$TARGET_BRANCH"

    # 원격 정리
    git remote prune origin

    # 머지된 로컬 브랜치 삭제 (현재 브랜치 + 보호 브랜치 제외, 정확한 이름 매칭)
    git branch --merged | grep -v '^\*' \
      | grep -v -x -E '  (main|master|develop|develop-ui|develop-ui-chat|develop-sandbox|release.*|develop-10\.[0-9]+\.[0-9]+_[0-9]+(-chat)?)' \
      | xargs -r git branch -d

### 보호 브랜치 regex 설명

정확한 이름 매칭(`-x`)으로 아래 브랜치만 보호합니다:

| 패턴 | 목적 |
|------|------|
| `main`, `master` | 최상위 default 브랜치 |
| `develop` | 전통 dev 브랜치 |
| `develop-ui`, `develop-ui-chat`, `develop-sandbox` | 레거시 base (지금은 안 쓰지만 잔존 가능성 대비) |
| `release.*` | 릴리스 브랜치 |
| `develop-10\.[0-9]+\.[0-9]+_[0-9]+(-chat)?` | **kickoff가 매 사이클 뽑는 현재/과거 버전 base** — 실수로 삭제 방지 |

UI feature 브랜치(`develop-10.2.4_3-chat-auditTrail` 등)는 위 regex와 `$` 매칭이 안 되므로 정상적으로 삭제 대상이 됩니다.

### 엣지 케이스

| 케이스 | 동작 |
|--------|------|
| 후보 목록이 비어있음 | fallback으로 `origin/develop` 또는 `main` 사용 |
| 모든 `rev-list` 실패 (shallow clone 등) | `best_base`가 비어있으면 사용자에게 에러 안내 |
| 여러 후보에서 `ahead` 동률 | 먼저 순회된 후보 선택 (`for-each-ref` 사전식 정렬이므로 결정적) |
| HEAD가 base와 동일 (이미 checkout됨) | `ahead=0` 후보 선택, 정상 동작 |

---

## 2. 현재 레포 범위 판별

하나의 이슈에 여러 레포(AI, AP, UI)의 AC가 섞여 있을 수 있습니다.
**현재 레포에 해당하는 AC만 증빙을 수집·업데이트하고, 다른 레포의 AC는 건드리지 않습니다.**

### 현재 레포 확인

    git remote get-url origin
    # → lucida-chat-ai / lucida-chat-ap / lucida-ui 등

### AC 항목 필터링 기준

각 AC 항목이 현재 레포에 해당하는지 판별합니다:

| 판별 방법 | 우선순위 | 예시 |
|-----------|---------|------|
| AC 텍스트에 레포/시스템 명시 | 1순위 | "AP toolCalls DB 저장" → AP 레포 |
| AC의 MR 링크가 현재 레포 | 2순위 | `→ 결과물: AP MR !20` → AP 레포 |
| AC의 변경 대상이 현재 레포 코드 | 3순위 | "writer 전파" + 현재 레포 diff에 해당 코드 존재 |
| 판별 불가 | — | 건드리지 않음 (다른 레포에서 처리) |

### 레포 키워드 매핑

| 키워드 | 레포 |
|--------|------|
| `AI`, `모델`, `LLM`, `추론`, `reasoning`, `streaming`, `writer`, `emitter` | lucida-chat-ai |
| `AP`, `API`, `DB`, `저장`, `백엔드`, `서버`, `Spring`, `toolCalls` | lucida-chat-ap |
| `UI`, `프론트`, `화면`, `컴포넌트`, `스크린샷`, `표시`, `SSE`, `프롬프트` | lucida-ui |

**주의:** 키워드 매핑은 보조 수단입니다. AC 텍스트에 레포가 명시되어 있으면 그것을 우선합니다.

### 공통 AC 처리

"코드 리뷰 완료", "전체 흐름 정상 동작" 같은 공통 AC는:
- **코드 리뷰 완료:** 현재 레포의 MR 링크만 리소스에 추가 (다른 레포 MR은 건드리지 않음)
- **전체 흐름 테스트:** 모든 레포 배포 후 수집해야 하므로, 마지막 레포에서 wrap-up 시 수집하거나 수동 업로드 대상으로 안내

---

## 3. 증빙 자가 점검

evidence 스킬로 증빙 등록 후, 이슈를 다시 읽어서 미흡한 증빙을 식별하고 보강합니다.

### 점검 프로세스

1. `mcp__plugin_linear_linear__get_issue`로 이슈 재조회
2. AC 항목별 증빙 텍스트 파싱
3. 아래 기준으로 미흡 판정
4. 미흡 항목 재수집 → description 업데이트

### 미흡 판정 기준

| 증빙 유형 | 미흡 판정 | 보강 방법 |
|-----------|----------|----------|
| 테스트 결과 | 요약만 있고 실제 출력 없음 | 테스트 재실행하여 전체 출력 수집 |
| 테스트 결과 | "테스트 통과" 같은 한 줄 텍스트만 있음 | verbose 모드로 재실행 |
| 코드 변경 | "구현 완료" 텍스트만 있음 | git diff --stat + 주요 변경 요약 수집 |
| 코드 변경 | diff --stat만 있고 주요 변경 요약 없음 | 주요 변경 요약 추가 |
| 데이터 경로 | 경로만 있고 건수/샘플 없음 | ls + wc + head 실행 |
| 메트릭 결과 | 수치만 있고 산출 근거 없음 | 평가 스크립트 재실행 |
| API 응답 | 상태코드만 있음 | curl 재실행하여 전체 응답 수집 |
| CI/CD 로그 | URL만 있고 결과 요약 없음 | gh run view 또는 glab ci view로 결과 수집 |

### 미흡 판정 NOT — 충분한 경우

다음은 보강 불필요:
- 요약 한 줄 + 실제 출력이 모두 있는 경우
- PR/MR 링크가 이슈 리소스에 첨부된 경우
- 스크린샷/동영상이 업로드되고 AC에 매핑된 경우
- 문서 URL이 첨부된 경우

---

## 4. 검증 실패 분기

validator 스킬 실행 후 결과에 따른 분기입니다.

### 분기 판정

검증 코멘트에서 실패 항목의 유형을 분류합니다:

| 지적사항 유형 | 판단 기준 | 행동 |
|-------------|----------|------|
| 증빙 미흡 | "증빙 내용 부족", "형식 불일치", "증빙 누락" | 자동 보강 → 재검증 |
| 문서 미반영 | "문서 내용 불일치", "업데이트 미반영" | Confluence 문서 자동 수정 → 재검증 |
| 코드 문제 | "MR diff에서 ~", "구현 누락", "코드 리뷰 ~" | 사용자 안내 → 스킬 종료 |
| 스크린샷 누락 | "이미지 미첨부", "스크린샷 없음" | 사용자에게 업로드 요청 → 업로드 후 매핑 → 재검증 |
| MR 누락 | "MR 링크 없음", "코드 리뷰 미수행" | 사용자 안내 → 스킬 종료 |

### 자동 보강 프로세스

1. 실패 항목에서 미흡 유형 파악
2. Section 3의 보강 방법에 따라 증빙 재수집
3. `mcp__plugin_linear_linear__save_issue`로 description 업데이트
4. validator 스킬 워크플로우 재실행

### 수동 업로드 후 매핑 프로세스

1. 사용자가 Linear 이슈에 스크린샷/동영상 업로드 후 알림
2. `mcp__plugin_linear_linear__get_issue`로 이슈 재조회
3. `mcp__plugin_linear_linear__extract_images`로 업로드된 이미지 확인
4. 각 이미지 내용을 열람하여 AC 항목과 매칭:
   - 이미지 내용 (UI 화면, 로그, 터미널 등) 분석
   - AC 항목의 요구사항과 비교
   - 가장 적절한 AC 항목에 매핑
5. description에 증빙 텍스트 업데이트:

       - [x] 동작 확인 → 결과물: 스크린샷 4장
             ↳ Kafka 로그, 감사 이력 목록, 감사 이력 상세, 채팅 UI

6. 매핑 결과를 사용자에게 보여주고 다음 단계 진행

### 검증 루프 제한

- 최대 3회까지 자동 보강 → 재검증
- 3회 초과 시:

      === 검증 자동 보강 한도 초과 ===

      3회 보강을 시도했지만 아직 미통과 항목이 있습니다.

      미통과 항목:
      - AC #2: 테스트 결과 — 실제 출력이 AC 요건과 불일치

      직접 확인하고 증빙을 보완해주세요.
      보완 후 /wrap-up을 다시 실행하면 됩니다.

      ===========================
