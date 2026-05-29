#!/usr/bin/env node
/**
 * PIMS2(Redmine) REST helper — library + CLI.
 *
 * 인증: API Key 우선, 없으면 Basic Auth fallback.
 * 자격증명 출처 우선순위 (lib/credentials.mjs 참고):
 *   1. 환경변수 (REDMINE_API_KEY / REDMINE_USER / REDMINE_PASS)
 *   2. ~/.config/tc-runner-linear/credentials.json 의 pims.api_key / user / pass
 *   3. 없으면 호출 시 에러 → 최초 setup 인터뷰 필요
 *
 * 환경변수
 *   REDMINE_URL        기본 http://pims2.nkia.co.kr
 *   PIMS_PROJECT_ID    기본 494 (Polestar 10 (Lucida)) — NKIA 팀 공통
 *   PIMS_TRACKER_ID    기본 17  (테스트케이스) — NKIA 팀 공통
 *   PIMS_CATEGORY_ID   create 시 카테고리 (옵션)
 *   PIMS_FIXED_VERSION_ID  create 시 마일스톤 (옵션, NKIA 공통 2096=테스트자동화)
 *
 * CLI
 *   node redmine.mjs get <issueId>
 *   node redmine.mjs create [--project=<pid>] [--tracker=<tid>] [--category=<cid>] [--version=<vid>] --subject="..." <textFile>
 *   node redmine.mjs append-desc <issueId> <textFile>
 *   node redmine.mjs set-desc <issueId> <textFile>
 *   node redmine.mjs note <issueId> <textFile> [img...]
 */
import { readFile } from 'node:fs/promises'
import { basename } from 'node:path'
import { pathToFileURL } from 'node:url'
import { loadCredentials, resolveValue } from './lib/credentials.mjs'

const creds = (await loadCredentials()) || {}

const BASE = (
    resolveValue(creds, 'REDMINE_URL', ['pims', 'base_url'], 'http://pims2.nkia.co.kr')
).replace(/\/$/, '')
const API_KEY = resolveValue(creds, 'REDMINE_API_KEY', ['pims', 'api_key'])
const USER = resolveValue(creds, 'REDMINE_USER', ['pims', 'user'])
const PASS = resolveValue(creds, 'REDMINE_PASS', ['pims', 'pass'])

const headers = (extra = {}) => {
    if (API_KEY) return { 'X-Redmine-API-Key': API_KEY, ...extra }
    if (USER && PASS) {
        return {
            Authorization: 'Basic ' + Buffer.from(`${USER}:${PASS}`).toString('base64'),
            ...extra,
        }
    }
    throw new Error(
        'PIMS 자격증명 없음. 환경변수 REDMINE_API_KEY 설정 또는\n' +
            '  node scripts/lib/credentials.mjs save <json> 로 자격증명 저장 필요.\n' +
            '  (스킬 최초 사용 시 SKILL.md Step 0 setup 흐름 참조.)',
    )
}

function contentType(name) {
    const ext = name.toLowerCase().split('.').pop()
    return (
        {
            png: 'image/png',
            jpg: 'image/jpeg',
            jpeg: 'image/jpeg',
            gif: 'image/gif',
            webp: 'image/webp',
        }[ext] || 'application/octet-stream'
    )
}

export async function getIssue(id) {
    const url = `${BASE}/issues/${id}.json?include=journals,children,attachments`
    const r = await fetch(url, { headers: headers() })
    if (!r.ok) throw new Error(`getIssue ${id} -> ${r.status} ${await r.text()}`)
    return (await r.json()).issue
}

export async function createIssue({ projectId, trackerId, categoryId, fixedVersionId, subject, description }) {
    if (!projectId) throw new Error('createIssue: projectId required')
    if (!subject) throw new Error('createIssue: subject required')
    const issue = {
        project_id: Number(projectId),
        tracker_id: Number(trackerId || 17),
        subject,
        description: description || '',
    }
    if (categoryId) issue.category_id = Number(categoryId)
    if (fixedVersionId) issue.fixed_version_id = Number(fixedVersionId)
    const r = await fetch(`${BASE}/issues.json`, {
        method: 'POST',
        headers: headers({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ issue }),
    })
    if (!r.ok) throw new Error(`createIssue -> ${r.status} ${await r.text()}`)
    return (await r.json()).issue
}

export async function setDescription(id, description) {
    const r = await fetch(`${BASE}/issues/${id}.json`, {
        method: 'PUT',
        headers: headers({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ issue: { description } }),
    })
    if (!r.ok) throw new Error(`setDescription ${id} -> ${r.status} ${await r.text()}`)
}

export async function appendDescription(id, text) {
    const issue = await getIssue(id)
    const cur = issue.description || ''
    const sep = cur.trim() ? '\n\n' : ''
    await setDescription(id, cur + sep + text)
}

export async function uploadFile(filePath) {
    const data = await readFile(filePath)
    const name = basename(filePath)
    const r = await fetch(`${BASE}/uploads.json?filename=${encodeURIComponent(name)}`, {
        method: 'POST',
        headers: headers({ 'Content-Type': 'application/octet-stream' }),
        body: data,
    })
    if (!r.ok) throw new Error(`uploadFile ${name} -> ${r.status} ${await r.text()}`)
    const token = (await r.json()).upload.token
    return { token, filename: name, content_type: contentType(name) }
}

export async function addNote(id, notes, uploads = []) {
    const body = { issue: { notes } }
    if (uploads.length) body.issue.uploads = uploads
    const r = await fetch(`${BASE}/issues/${id}.json`, {
        method: 'PUT',
        headers: headers({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(`addNote ${id} -> ${r.status} ${await r.text()}`)
}

function parseFlags(argv) {
    const flags = {}
    const rest = []
    for (const a of argv) {
        const m = a.match(/^--([^=]+)=(.*)$/)
        if (m) flags[m[1]] = m[2]
        else rest.push(a)
    }
    return { flags, rest }
}

// ---- CLI ----
const isMain = import.meta.url === pathToFileURL(process.argv[1] || '').href
if (isMain) {
    const [cmd, ...rawArgs] = process.argv.slice(2)
    const { flags, rest: args } = parseFlags(rawArgs)
    const main = async () => {
        switch (cmd) {
            case 'get': {
                if (!args[0]) throw new Error('usage: get <issueId>')
                console.log(JSON.stringify(await getIssue(args[0]), null, 2))
                break
            }
            case 'create': {
                const projectId =
                    flags.project ||
                    resolveValue(creds, 'PIMS_PROJECT_ID', ['pims', 'project_id'], 494)
                const trackerId =
                    flags.tracker ||
                    resolveValue(creds, 'PIMS_TRACKER_ID', ['pims', 'tracker_id'], 17)
                const categoryId =
                    flags.category || resolveValue(creds, 'PIMS_CATEGORY_ID', ['pims', 'category_id'])
                const fixedVersionId =
                    flags.version ||
                    resolveValue(creds, 'PIMS_FIXED_VERSION_ID', ['pims', 'fixed_version_id'])
                const subject = flags.subject
                const file = args[0]
                if (!subject) throw new Error('usage: create --subject="..." <textFile>  (project/tracker 는 기본값 사용)')
                if (!file) throw new Error('<textFile> required')
                const description = await readFile(file, 'utf8')
                const issue = await createIssue({ projectId, trackerId, categoryId, fixedVersionId, subject, description })
                console.log(`CREATED: ${issue.id}`)
                console.log(`URL: ${BASE}/issues/${issue.id}`)
                break
            }
            case 'append-desc': {
                const [id, file] = args
                if (!id || !file) throw new Error('usage: append-desc <issueId> <textFile>')
                await appendDescription(id, await readFile(file, 'utf8'))
                console.log(`OK: appended TC to description of #${id}`)
                break
            }
            case 'set-desc': {
                const [id, file] = args
                if (!id || !file) throw new Error('usage: set-desc <issueId> <textFile>')
                await setDescription(id, await readFile(file, 'utf8'))
                console.log(`OK: replaced description of #${id}`)
                break
            }
            case 'note': {
                const [id, noteFile, ...shots] = args
                if (!id || !noteFile) throw new Error('usage: note <issueId> <textFile> [img...]')
                const uploads = []
                for (const s of shots) uploads.push(await uploadFile(s))
                await addNote(id, await readFile(noteFile, 'utf8'), uploads)
                console.log(`OK: added note to #${id} with ${uploads.length} attachment(s)`)
                break
            }
            default:
                console.error('commands: get | create | append-desc | set-desc | note')
                process.exit(1)
        }
    }
    main().catch((e) => {
        console.error('ERROR:', e.message)
        process.exit(1)
    })
}
