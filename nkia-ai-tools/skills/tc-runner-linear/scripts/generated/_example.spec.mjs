/**
 * 생성 스펙 예시 — Claude 가 Linear 이슈마다 이 형태로 새 파일을 만든다.
 *   파일명 규칙: <LinearID>-<tcId>.spec.mjs
 *     예: NKIAAI-498-sms-01-02-001.spec.mjs
 *         NKIAAI-498-positive.spec.mjs / NKIAAI-498-negative.spec.mjs
 *   실행:       node scripts/generated/<파일명>
 *
 * 핵심 규칙
 *   - step() 의 이름은 TC '테스트절차'의 번호/문구와 1:1로 맞춘다.
 *   - 예상결과 검증은 step 콜백 안에서 expect/단언으로 수행 → 실패 시 자동 Fail.
 *   - 셀렉터는 ./lucida-ui 소스(remotes/<모듈>)에서 확인한 실제 값 사용.
 */
import { startRun } from '../lib/tc-runner.mjs'

const run = await startRun({ tc: 'SMS-01-02-01-001' })

// expect 가 필요하면 동일 경로의 playwright 에서 가져온다.
// import { expect } from '<LUCIDA_UI_DIR>/node_modules/@playwright/test/index.mjs'
// (간단한 경우 page.locator(...).waitFor() / count() 로 충분)

await run.login()
if (!run.results.login.ok) {
    // 조직 선택 등 후속 화면 처리 예시 (필요 시 주석 해제·수정)
    // await run.page.getByText('MyOrganization').click()
    // await run.page.getByRole('button', { name: '로그인' }).click()
}

await run.step('1. 사이드바 확장 버튼 클릭', async (page) => {
    await page.locator('.st-first-menu-left-button-area').click()
})

await run.step('2. 서버관리 > 서버목록 메뉴 클릭', async (page) => {
    await page.getByText('서버목록', { exact: true }).click()
})

await run.step('3. AG Grid 렌더링 및 행 1개 이상 확인', async (page) => {
    await page.locator('div.ag-root').waitFor({ state: 'visible', timeout: 15000 })
    const rows = await page.locator('.ag-center-cols-container .ag-row').count()
    if (rows < 1) throw new Error('그리드 행이 0건')
})

await run.finish()
