/**
 * Playwright 기반 TC 실행 베이스.
 *
 * lucida-ui 의 @playwright/test(chromium 포함)를 절대경로 동적 import 로 재사용하므로
 * 이 스크립트는 어디서 실행해도 동작한다(별도 npm install 불필요).
 *
 * 자격증명 출처 우선순위 (lib/credentials.mjs):
 *   1. 환경변수 (LUCIDA_UI_DIR / TC_USER / TC_PASS / TC_ORG / TC_BASE_URL)
 *   2. ~/.config/tc-runner-linear/credentials.json (polestar10.user / pass / org / base_url, lucida_ui_dir)
 *   3. NKIA 공통 기본값 (base_url, org)
 *
 * 환경변수
 *   LUCIDA_UI_DIR  playwright 가 설치된 lucida-ui 경로 (자격증명 또는 환경변수 필수)
 *   TC_BASE_URL    테스트 서버 (NKIA 공통 기본 https://192.168.230.104/)
 *   TC_USER/TC_PASS  로그인 계정 (자격증명 또는 환경변수 필수)
 *   TC_ORG         조직 선택 (NKIA 공통 기본 MyOrganization)
 *   TC_OUT_DIR     스크린샷/결과 출력 폴더 (기본 ../../runs/latest)
 *   TC_HEADLESS    'false' 로 주면 브라우저 창을 띄움(디버깅용)
 *
 * 사용 예 (generated 스펙에서):
 *   import { startRun } from '../lib/tc-runner.mjs'
 *   const run = await startRun({ tc: 'SMS-01-02-01-001' })
 *   await run.login()
 *   await run.step('1. 서버목록 메뉴 클릭', async (page) => {
 *     await page.getByText('서버목록', { exact: true }).click()
 *   })
 *   await run.finish()
 */
import { fileURLToPath, pathToFileURL } from 'node:url'
import { dirname, join } from 'node:path'
import { mkdir, writeFile } from 'node:fs/promises'
import { loadCredentials, resolveValue } from './credentials.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const creds = (await loadCredentials()) || {}

const LUCIDA_UI_DIR = resolveValue(creds, 'LUCIDA_UI_DIR', ['lucida_ui_dir'])
if (!LUCIDA_UI_DIR) {
    throw new Error(
        'LUCIDA_UI_DIR 미설정. 환경변수 LUCIDA_UI_DIR 또는\n' +
            '  ~/.config/tc-runner-linear/credentials.json 의 lucida_ui_dir 필요.\n' +
            '  (스킬 최초 사용 시 SKILL.md Step 0 setup 흐름 참조.)',
    )
}

const pwUrl = pathToFileURL(
    join(LUCIDA_UI_DIR, 'node_modules', '@playwright', 'test', 'index.mjs'),
).href
const { chromium } = await import(pwUrl)

const slug = (s) =>
    String(s)
        .replace(/[^\w가-힣]+/g, '_')
        .replace(/^_+|_+$/g, '')
        .slice(0, 48) || 'step'

export async function startRun(opts = {}) {
    // resolveValue: env(TC_BASE_URL 등) → creds.polestar10.* → default 순으로 해결.
    // creds 와 resolveValue 는 라인 32 의 `./credentials.mjs` import 로 가져옴.
    const baseUrl =
        opts.baseUrl ||
        resolveValue(creds, 'TC_BASE_URL', ['polestar10', 'base_url'], 'https://192.168.230.104/')
    const user = opts.user || resolveValue(creds, 'TC_USER', ['polestar10', 'user'])
    const pass = opts.pass || resolveValue(creds, 'TC_PASS', ['polestar10', 'pass'])
    if (!user || !pass) {
        throw new Error(
            'Polestar10 자격증명 없음. 환경변수 TC_USER/TC_PASS 또는\n' +
                '  ~/.config/tc-runner-linear/credentials.json 의 polestar10.user/pass 필요.',
        )
    }
    // 계정에 조직이 여러 개면 로그인 후 조직 선택 화면이 뜬다.
    // org 지정 시 해당 이름의 조직, 미지정 시 기본 'MyOrganization' 선택.
    const org = opts.org || resolveValue(creds, 'TC_ORG', ['polestar10', 'org'], 'MyOrganization')
    const outDir =
        opts.outDir || process.env.TC_OUT_DIR || join(__dirname, '..', '..', 'runs', 'latest')
    const headless = opts.headless ?? process.env.TC_HEADLESS !== 'false'

    await mkdir(outDir, { recursive: true })

    const browser = await chromium.launch({ headless })
    const context = await browser.newContext({
        ignoreHTTPSErrors: true, // self-signed cert
        viewport: { width: 1600, height: 900 },
        locale: 'ko-KR',
    })
    const page = await context.newPage()

    const results = {
        tc: opts.tc || null,
        baseUrl,
        user,
        startedAt: new Date().toISOString(),
        login: null,
        steps: [],
    }
    let n = 0

    async function shot(label) {
        const file = join(outDir, `${String(++n).padStart(2, '0')}-${slug(label)}.png`)
        try {
            await page.screenshot({ path: file })
        } catch (e) {
            return null
        }
        return file
    }

    /**
     * 로그인. 단계:
     *   1) #loginId/#password 입력 후 Enter
     *   2) 조직 선택 화면이 뜨면 org(또는 첫 번째) 조직 선택
     *   3) /login 을 벗어나면 성공
     * 2차 인증 등 추가 화면이 있으면 ok=false 로 떨어지며 login.png 로 확인 가능.
     */
    async function login() {
        await page.goto(baseUrl, { waitUntil: 'domcontentloaded' })
        await page.waitForSelector('#loginId', { timeout: 30000 })
        await page.fill('#loginId', user)
        await page.fill('#password', pass)
        await page.locator('#password').press('Enter')

        // 로그인 폼 사라짐 대기
        await page
            .waitForSelector('#loginId', { state: 'detached', timeout: 30000 })
            .catch(() => {})

        // 조직 선택 화면 처리
        const orgBox = '.login-body-org-content-body-list-box'
        const hasOrg = await page
            .waitForSelector(orgBox, { timeout: 5000 })
            .then(() => true)
            .catch(() => false)
        if (hasOrg) {
            let target
            if (org) {
                target = page.locator(orgBox).filter({ hasText: org }).first()
            } else {
                target = page.locator(orgBox).first()
            }
            const picked = await target
                .locator('.login-body-org-content-body-list-title')
                .innerText()
                .catch(() => org || '(first)')
            results.org = picked
            await target.click()
        }

        // 앱 진입(=/login 이탈) 대기
        await page
            .waitForFunction(() => !location.pathname.startsWith('/login'), null, {
                timeout: 30000,
            })
            .catch(() => {})
        await page.waitForLoadState('networkidle').catch(() => {})

        const screenshot = await shot('login')
        const url = page.url()
        const ok = !url.includes('/login') && !(await page.locator('#loginId').count())
        results.login = { ok, url, org: results.org || null, screenshot }
        if (!ok) {
            console.warn(
                '[WARN] 로그인이 완료되지 않았습니다(2차 인증/조직 선택/실패 가능). login.png 확인.',
            )
        }
        return results.login
    }

    /**
     * 한 절차 실행 + 스크린샷 + Pass/Fail 기록.
     * fn 안에서 예외가 나면 fail, 예상결과 검증은 fn 내부에서 expect/assert 로 수행.
     */
    async function step(name, fn) {
        const rec = { name, status: 'pass', error: null, screenshot: null }
        try {
            if (fn) await fn(page)
        } catch (e) {
            rec.status = 'fail'
            rec.error = String((e && e.message) || e).split('\n')[0]
        }
        rec.screenshot = await shot(name)
        results.steps.push(rec)
        console.log(`[${rec.status.toUpperCase()}] ${name}${rec.error ? ' :: ' + rec.error : ''}`)
        return rec
    }

    async function finish() {
        results.finishedAt = new Date().toISOString()
        results.summary = {
            total: results.steps.length,
            pass: results.steps.filter((s) => s.status === 'pass').length,
            fail: results.steps.filter((s) => s.status === 'fail').length,
        }
        results.outDir = outDir
        await writeFile(join(outDir, 'results.json'), JSON.stringify(results, null, 2))
        await browser.close()
        console.log(
            `\n== ${results.tc || 'TC'}: ${results.summary.pass}/${results.summary.total} pass, ${results.summary.fail} fail ==`,
        )
        console.log(`results: ${join(outDir, 'results.json')}`)
        return results
    }

    return { browser, context, page, results, outDir, shot, login, step, finish }
}
