#!/usr/bin/env node
/**
 * tc-runner-linear 자격증명 저장소.
 *
 * 저장 위치: $XDG_CONFIG_HOME/tc-runner-linear/credentials.json
 *           (기본 ~/.config/tc-runner-linear/credentials.json, chmod 600)
 *
 * OMC 영역(.omc/) 무관 — OMC 비사용자도 동일하게 동작.
 *
 * 자격증명 우선순위: 환경변수 → credentials.json → (없음 → 호출자가 인터뷰 트리거)
 *
 * 형식:
 * {
 *   "pims": {
 *     "api_key": "...",
 *     "user": "...",     // API key fallback 용
 *     "pass": "...",
 *     "project_id": 494,
 *     "tracker_id": 17,
 *     "fixed_version_id": 2096
 *   },
 *   "polestar10": {
 *     "base_url": "https://192.168.230.104/",
 *     "user": "...",
 *     "pass": "...",
 *     "org": "MyOrganization"
 *   },
 *   "lucida_ui_dir": "/home/<user>/dev/lucida-ui"
 * }
 *
 * CLI:
 *   node credentials.mjs path        저장 위치 출력
 *   node credentials.mjs check       자격증명 충분 여부 (exit 0=OK, 1=인터뷰 필요)
 *   node credentials.mjs show        저장값 (비밀번호/API key 마스킹)
 *   node credentials.mjs save <file> JSON 파일 내용을 credentials.json 으로 저장 (chmod 600)
 *   node credentials.mjs reset       파일 삭제
 *
 * API (호출 측):
 *   import { loadCredentials, resolveValue, hasMinimum } from './lib/credentials.mjs'
 *   const creds = loadCredentials() || {}
 *   const apiKey = resolveValue(creds, 'REDMINE_API_KEY', ['pims','api_key'])
 */
import { readFile, writeFile, mkdir, chmod, stat, unlink } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { homedir } from 'node:os'
import { pathToFileURL } from 'node:url'

const CONFIG_HOME = process.env.XDG_CONFIG_HOME || join(homedir(), '.config')
const CRED_DIR = join(CONFIG_HOME, 'tc-runner-linear')
const CRED_PATH = join(CRED_DIR, 'credentials.json')

export function credentialsPath() {
    return CRED_PATH
}

export async function loadCredentials() {
    try {
        const raw = await readFile(CRED_PATH, 'utf8')
        return JSON.parse(raw)
    } catch (e) {
        if (e.code === 'ENOENT') return null
        throw e
    }
}

export async function saveCredentials(obj) {
    await mkdir(CRED_DIR, { recursive: true })
    await writeFile(CRED_PATH, JSON.stringify(obj, null, 2) + '\n')
    await chmod(CRED_PATH, 0o600)
}

/**
 * env > creds[path[0]][path[1]]... > defaultValue 순으로 해결.
 *   resolveValue(creds, 'REDMINE_API_KEY', ['pims','api_key'])
 *   resolveValue(creds, 'TC_USER', ['polestar10','user'], 'sjbang')
 */
export function resolveValue(creds, envKey, path, defaultValue) {
    const envVal = process.env[envKey]
    if (envVal !== undefined && envVal !== '') return envVal
    if (creds) {
        let cur = creds
        for (const k of path) {
            if (cur == null) break
            cur = cur[k]
        }
        if (cur !== undefined && cur !== null && cur !== '') return cur
    }
    return defaultValue
}

/**
 * 자격증명 충분 여부:
 *   - PIMS: api_key 또는 (user + pass)
 *   - Polestar10: user + pass
 *   - lucida_ui_dir
 * 환경변수가 채워주는 항목도 인정.
 */
export function hasMinimum(creds) {
    creds = creds || {}
    const get = (envKey, path) => resolveValue(creds, envKey, path)
    const pimsOk = get('REDMINE_API_KEY', ['pims', 'api_key']) ||
        (get('REDMINE_USER', ['pims', 'user']) && get('REDMINE_PASS', ['pims', 'pass']))
    const polestarOk =
        get('TC_USER', ['polestar10', 'user']) && get('TC_PASS', ['polestar10', 'pass'])
    const lucidaOk = get('LUCIDA_UI_DIR', ['lucida_ui_dir'])
    return Boolean(pimsOk && polestarOk && lucidaOk)
}

function mask(v) {
    if (v == null) return null
    const s = String(v)
    if (s.length <= 4) return '****'
    return s.slice(0, 3) + '****' + s.slice(-2)
}

function maskCreds(c) {
    if (!c) return null
    const out = JSON.parse(JSON.stringify(c))
    if (out.pims) {
        if (out.pims.api_key) out.pims.api_key = mask(out.pims.api_key)
        if (out.pims.pass) out.pims.pass = mask(out.pims.pass)
    }
    if (out.polestar10) {
        if (out.polestar10.pass) out.polestar10.pass = mask(out.polestar10.pass)
    }
    return out
}

// ---- CLI ----
const isMain = import.meta.url === pathToFileURL(process.argv[1] || '').href
if (isMain) {
    const [cmd, ...args] = process.argv.slice(2)
    const main = async () => {
        switch (cmd) {
            case 'path':
                console.log(CRED_PATH)
                break
            case 'check': {
                const creds = await loadCredentials()
                if (hasMinimum(creds)) {
                    console.log('OK')
                    process.exit(0)
                } else {
                    console.log('SETUP_NEEDED')
                    process.exit(1)
                }
                break
            }
            case 'show': {
                const creds = await loadCredentials()
                if (!creds) {
                    console.log('(없음 — node credentials.mjs save <file> 로 저장 필요)')
                    process.exit(1)
                }
                console.log(JSON.stringify(maskCreds(creds), null, 2))
                console.log(`\n저장 위치: ${CRED_PATH}`)
                break
            }
            case 'save': {
                const file = args[0]
                if (!file) throw new Error('usage: save <JSON file>')
                const raw = await readFile(file, 'utf8')
                const obj = JSON.parse(raw)
                await saveCredentials(obj)
                const s = await stat(CRED_PATH)
                console.log(`OK: ${CRED_PATH} (mode=${(s.mode & 0o777).toString(8)})`)
                break
            }
            case 'reset': {
                try {
                    await unlink(CRED_PATH)
                    console.log(`OK: removed ${CRED_PATH}`)
                } catch (e) {
                    if (e.code === 'ENOENT') console.log('(없음 — 이미 삭제됨)')
                    else throw e
                }
                break
            }
            default:
                console.error('commands: path | check | show | save <file> | reset')
                process.exit(1)
        }
    }
    main().catch((e) => {
        console.error('ERROR:', e.message)
        process.exit(1)
    })
}
