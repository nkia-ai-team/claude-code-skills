# 장애 시나리오 패턴 카탈로그

`testbed-generate-scenarios` 스킬이 새 시나리오를 만들 때 후보로 제시하는 카드 모음.
각 카드는 1 패턴 = 1 마크다운 = `script-template.md` 가 인스턴스로 변환할 수 있는 템플릿.

## 카드 형식 (필수)

```markdown
# Pattern: <name>
## Summary (한 줄)
## 트리거 메커니즘
## propagation (root → user-visible)
## 적합한 도메인
## bash 스크립트 골격
## expected_alarms (기본값)
## cleanup 안전성 + 부작용
```

## 현재 카드

| 파일 | 패턴 | 발화 알람 카테고리 | 적합 도메인 |
|---|---|---|---|
| [db-lock-contention.md](db-lock-contention.md) | DB row/table lock | DPM lock wait / APM response time / SMS process CPU | 트랜잭션 도메인 (e-commerce, banking) |
| [external-api-timeout.md](external-api-timeout.md) | 외부 의존성 무응답 | APM error rate / APM cascade timeout / DPM transaction time | 외부 PG/3rd-party API 호출 도메인 |
| [db-cpu-throttle.md](db-cpu-throttle.md) | DB CPU 제한 | APM 평균 응답시간 / KCM Pod CPU throttling | DB 의존도 높은 도메인 |
| [traffic-flood.md](traffic-flood.md) | 동시성 폭주 | APM thread pool / DPM connection / DPM lock count | 모든 웹 서비스 |
| [template-generic.md](template-generic.md) | 신규 패턴 작성 가이드 | (사용자 정의) | — |

## 새 패턴 추가 절차

1. `template-generic.md` 복사하여 새 카드 생성
2. 각 섹션 채우기 (Summary 한 줄 / 트리거 / propagation / 적합 도메인 / bash 골격 / expected_alarms / cleanup 부작용)
3. 본 README 의 표에 행 추가
4. (선택) `testbed-generate-scenarios/references/pattern-to-script.md` 에 변환 룰 보강
