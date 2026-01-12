# AI 기반 MR 코드 리뷰 룰셋

본 문서는 Claude Code, Cursor 등 AI 도구가 Merge Request 코드 리뷰를 수행할 때 따라야 할 규칙을 정의합니다.

CodeRabbit 등 상용 도구 수준 이상의 체계적인 코드 리뷰를 목표로 합니다.

---

## 1. 리뷰 수행 순서

AI 코드 리뷰는 다음 순서로 진행합니다:

```
1. 브랜치명 검증
2. 커밋 메시지 검증
3. MR 메타데이터 검토
4. 코드 변경 사항 분석
5. 품질/보안/성능 검토
6. 리뷰 결과 작성
```

---

## 2. 브랜치명 검증

### 2.1 검증 규칙

**정규식 패턴:**
```regex
^(feature|bugfix|hotfix|refactor|docs|test|config)/PIMS-[0-9]+-[a-z0-9-]+$
```

**검증 항목:**

| 항목 | 규칙 | 예시 |
|------|------|------|
| Type Prefix | feature, bugfix, hotfix, refactor, docs, test, config 중 하나 | `feature/` |
| PIMS 번호 | `PIMS-` + 숫자 형식 필수 | `PIMS-114667` |
| 설명 | kebab-case, 소문자, 3-5단어 | `api-diff-notification` |

### 2.2 브랜치-작업 타입 일치 검증

| 브랜치 타입 | 허용되는 작업 |
|-------------|--------------|
| feature | 새로운 기능 추가 |
| bugfix | 버그 수정 |
| hotfix | 긴급 운영 이슈 수정 |
| refactor | 리팩토링, 성능 개선 |
| docs | 문서 작업만 |
| test | 테스트 코드만 |
| config | 설정 파일만 |

### 2.3 리뷰 코멘트 예시

```markdown
## 브랜치명 검증

**브랜치:** `feature/PIMS-114667-api-diff-slack-notification`

| 항목 | 상태 | 비고 |
|------|------|------|
| Type Prefix | ✅ | feature |
| PIMS 번호 | ✅ | PIMS-114667 |
| 네이밍 규칙 | ✅ | kebab-case 준수 |
| 타입-작업 일치 | ✅ | 새 기능 추가 작업 |
```

---

## 3. 커밋 메시지 검증

### 3.1 검증 규칙

**정규식 패턴:**
```regex
^#[0-9]+ (Feat|Fix|Refactor|Cleanup|Wip|Revert|Style|Merge|Docs|Config|Dependency|Test) : .+$
```

**검증 항목:**

| 항목 | 규칙 | 예시 |
|------|------|------|
| PIMS 번호 | `#` + 숫자 형식 | `#114667` |
| Type | 허용된 타입 키워드 | `Feat` |
| 구분자 | ` : ` (공백 포함 콜론) | ` : ` |
| 내용 | 한글/영문, 명확한 설명 | `API 변경 감지 시스템 구축` |

### 3.2 Type Keyword 검증

| Type | 용도 | 변경 범위 |
|------|------|----------|
| Feat | 새로운 기능 추가 | 신규 파일/메서드 추가 |
| Fix | 오류 수정 | 버그 수정 코드 |
| Refactor | 리팩토링/성능 개선 | 기존 코드 구조 변경 |
| Cleanup | 불필요한 코드 정리 | 파일/코드 삭제 |
| Wip | 진행 중 작업 | 임시 커밋 (MR 시 지양) |
| Style | 코드 스타일 수정 | 포맷팅, 공백 등 |
| Docs | 문서 변경 | .md 파일 등 |
| Config | 설정 파일 변경 | 빌드/배포 설정 |
| Test | 테스트 코드 | *Test.java, *Spec.java |

### 3.3 브랜치-커밋 PIMS 일치 검증

```
브랜치: feature/PIMS-114667-api-diff-notification
커밋: #114667 Feat : API 변경 감지 시스템 구축
      ^^^^^^^^
      동일한 PIMS 번호 사용 필수
```

### 3.4 리뷰 코멘트 예시

```markdown
## 커밋 메시지 검증

**총 커밋 수:** 3개

| 커밋 | PIMS | Type | 상태 | 비고 |
|------|------|------|------|------|
| `#114667 Feat : API 변경 감지 시스템 구축` | ✅ | ✅ Feat | ✅ | - |
| `#114667 Fix : Slack 웹훅 URL 수정` | ✅ | ✅ Fix | ✅ | - |
| `update readme` | ❌ | ❌ | ❌ | PIMS 번호, Type 누락 |

⚠️ **수정 필요:** 3번째 커밋 메시지가 규칙을 준수하지 않습니다.
```

---

## 4. MR 메타데이터 검토

### 4.1 필수 항목 체크리스트

| 항목 | 필수 | 검증 내용 |
|------|------|----------|
| Title | ✅ | PIMS 번호 포함, 명확한 설명 |
| Description | ✅ | 기능 상세 설명 작성 |
| Part (FE/BE) | ✅ | 해당 파트 선택 |
| Target Branch | ✅ | develop (master 아님) |
| 연관 백로그 | 권장 | `#이슈번호` 형식 |
| 테스트 코드 | ✅ | 체크 여부 확인 |
| 정적 분석 | ✅ | 체크 여부 확인 |

### 4.2 변경 규모 검증

| 변경 라인 | 상태 | 권고 |
|----------|------|------|
| 1-200 | ✅ 적정 | - |
| 201-500 | ⚠️ 주의 | 분할 검토 권장 |
| 500+ | ❌ 과다 | MR 분할 필요 |

---

## 5. 코드 리뷰 체크리스트

### 5.1 코드 품질

#### 클린 코드 원칙
- [ ] **단일 책임 원칙 (SRP)** - 클래스/메서드가 하나의 책임만 가지는가?
- [ ] **메서드 길이** - 20줄 이하인가? 복잡한 경우 분리 필요
- [ ] **중복 코드** - DRY 원칙 준수, 기존 유틸리티 활용
- [ ] **네이밍** - 의미 있는 변수/메서드명 사용
- [ ] **매직 넘버** - 상수로 정의되어 있는가?

#### Java/Spring 특화
- [ ] **Optional 사용** - null 대신 Optional 활용
- [ ] **Stream API** - 적절한 활용, 과도한 체이닝 지양
- [ ] **Lombok** - 적절한 어노테이션 사용 (@Getter, @Builder 등)
- [ ] **의존성 주입** - 생성자 주입 사용 (@RequiredArgsConstructor)
- [ ] **불변성** - final 키워드 적절히 사용

### 5.2 보안 검토 (OWASP Top 10)

| 취약점 | 검토 항목 |
|--------|----------|
| Injection | SQL, NoSQL, Command, LDAP 인젝션 방지 |
| Broken Auth | 인증/세션 관리 적절성 |
| Sensitive Data | 민감 정보 노출 여부 (로그, 응답) |
| XXE | XML 외부 엔티티 처리 |
| Broken Access | 권한 검증 누락 |
| Security Misconfig | 보안 설정 오류 |
| XSS | 입력값 이스케이프 처리 |
| Deserialization | 안전하지 않은 역직렬화 |
| Known Vuln | 취약한 라이브러리 사용 |
| Logging | 로깅/모니터링 부족 |

**검토 코드 패턴:**
```java
// ❌ SQL Injection 취약
String query = "SELECT * FROM users WHERE id = " + userId;

// ✅ PreparedStatement 사용
@Query("SELECT u FROM User u WHERE u.id = :id")
User findById(@Param("id") Long id);

// ❌ 민감 정보 로깅
log.info("User password: {}", password);

// ✅ 민감 정보 마스킹
log.info("User login attempt: {}", maskEmail(email));
```

### 5.3 성능 검토

| 항목 | 검토 내용 |
|------|----------|
| N+1 Query | JPA 연관관계 로딩 전략 확인 |
| Index | 쿼리 대상 컬럼 인덱스 존재 |
| Pagination | 대량 데이터 페이징 처리 |
| Caching | 반복 조회 데이터 캐싱 |
| Async | 비동기 처리 적절성 |
| Connection Pool | 연결 풀 크기 적정성 |

**검토 코드 패턴:**
```java
// ❌ N+1 문제
@OneToMany(fetch = FetchType.LAZY)
private List<Order> orders;  // 루프에서 각각 쿼리 발생

// ✅ Fetch Join 사용
@Query("SELECT u FROM User u JOIN FETCH u.orders")
List<User> findAllWithOrders();

// ❌ 전체 조회
List<Entity> findAll();  // 데이터 증가 시 OOM

// ✅ 페이징 적용
Page<Entity> findAll(Pageable pageable);
```

### 5.4 테스트 코드 검토

| 항목 | 검토 내용 |
|------|----------|
| 테스트 존재 | 신규/변경 코드에 대한 테스트 존재 |
| 테스트 커버리지 | 주요 로직 80% 이상 커버 |
| 테스트 품질 | 의미 있는 검증 (assert) 포함 |
| Edge Case | 경계값, 예외 케이스 테스트 |
| Mock 적절성 | 외부 의존성 적절히 모킹 |

**테스트 네이밍 규칙:**
```java
// 패턴: {테스트대상}_{시나리오}_{예상결과}
@Test
void searchTraces_WithValidRequest_ReturnsTraceList() { }

@Test
void searchTraces_WithInvalidTimeRange_ThrowsException() { }
```

### 5.5 에러 처리

- [ ] **예외 처리** - 적절한 예외 타입 사용
- [ ] **에러 메시지** - 사용자 친화적 메시지
- [ ] **로깅** - 에러 상황 적절히 로깅
- [ ] **Fallback** - 장애 시 대체 로직 존재

```java
// ❌ 포괄적 예외 처리
catch (Exception e) {
    log.error("Error", e);
}

// ✅ 구체적 예외 처리
catch (ResourceNotFoundException e) {
    log.warn("Resource not found: {}", e.getResourceId());
    throw new ApiException(ErrorCode.NOT_FOUND, e.getMessage());
}
```

### 5.6 API 문서화

- [ ] **Controller @Tag** - API 그룹 설명
- [ ] **@Operation** - 메서드별 summary, description
- [ ] **@ApiResponse** - 응답 코드별 설명
- [ ] **DTO @Schema** - 필드별 설명, example

---

## 6. 리뷰 결과 작성 형식

### 6.1 전체 요약

```markdown
# MR 코드 리뷰 결과

## 요약

| 항목 | 결과 |
|------|------|
| 브랜치명 | ✅ Pass |
| 커밋 메시지 | ⚠️ 1건 수정 필요 |
| 코드 품질 | ✅ Pass |
| 보안 | ✅ Pass |
| 성능 | ⚠️ 개선 권장 |
| 테스트 | ❌ 테스트 추가 필요 |

**전체 판정:** ⚠️ 수정 후 승인 권장
```

### 6.2 상세 코멘트 형식

```markdown
### 📁 파일: `TraceQueryController.java`

#### Line 45-50: 🔴 Critical - N+1 Query 문제

**현재 코드:**
```java
traces.forEach(trace -> {
    trace.getSpans().size();  // N+1 발생
});
```

**문제점:**
- 각 trace마다 개별 쿼리 발생
- 100개 trace 조회 시 101개 쿼리 실행

**권장 수정:**
```java
@Query("SELECT t FROM Trace t JOIN FETCH t.spans WHERE t.id IN :ids")
List<Trace> findByIdsWithSpans(@Param("ids") List<Long> ids);
```

---

#### Line 78: 🟡 Warning - 하드코딩된 값

**현재 코드:**
```java
if (size > 100) {
    throw new IllegalArgumentException("Size exceeded");
}
```

**권장 수정:**
```java
private static final int MAX_PAGE_SIZE = 100;

if (size > MAX_PAGE_SIZE) {
    throw new IllegalArgumentException("Page size cannot exceed " + MAX_PAGE_SIZE);
}
```
```

### 6.3 심각도 레벨

| 레벨 | 아이콘 | 의미 | 조치 |
|------|--------|------|------|
| Critical | 🔴 | 버그, 보안 취약점 | 반드시 수정 |
| Warning | 🟡 | 개선 권장 사항 | 수정 권장 |
| Info | 🔵 | 제안, 스타일 | 선택적 수정 |
| Praise | 🟢 | 좋은 코드 | 칭찬/참고 |
