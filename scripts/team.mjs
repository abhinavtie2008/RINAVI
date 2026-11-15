#!/usr/bin/env node
// Team coordination for the multi-agent workflow.
//
// GitHub Issues are the task board and labels are the state machine, so every
// agent (Freebuff, Qoder, OpenCode) reads the same queue without talking to the
// others directly.
//
//   node scripts/team.mjs board
//   node scripts/team.mjs next --agent freebuff
//   node scripts/team.mjs claim 42 --agent freebuff
//   node scripts/team.mjs handoff 42 --to qoder --note "backend done, needs UI"
//   node scripts/team.mjs review
//
// Needs GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN in the environment.

import { execSync, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { join } from 'node:path'

const API = 'https://api.github.com'

function token() {
  const value = process.env.GITHUB_PERSONAL_ACCESS_TOKEN || process.env.GITHUB_TOKEN
  if (!value) throw new Error('team: set GITHUB_PERSONAL_ACCESS_TOKEN (or GITHUB_TOKEN) first')
  return value
}

function repoSlug() {
  if (process.env.GITHUB_REPOSITORY) return process.env.GITHUB_REPOSITORY
  const url = execSync('git remote get-url origin', { encoding: 'utf8' }).trim()
  const match = url.match(/github\.com[:/]([^/]+)\/([^/]+?)(?:\.git)?$/)
  if (!match) throw new Error(`team: cannot parse origin url: ${url}`)
  return `${match[1]}/${match[2]}`
}

async function api(path, init = {}) {
  const response = await fetch(`${API}/repos/${repoSlug()}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token()}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'rinavi-team',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
  })
  if (response.status === 204 || response.status === 404) return null
  const body = await response.json()
  if (!response.ok) throw new Error(`team: ${response.status} ${path}: ${body.message || ''}`)
  return body
}

const label = (item, prefix) =>
  item.labels.map((l) => l.name).find((n) => n.startsWith(`${prefix}:`))?.slice(prefix.length + 1) || '-'

const status = (item) => label(item, 'status')

async function addLabels(number, labels) {
  await api(`/issues/${number}/labels`, { method: 'POST', body: JSON.stringify({ labels }) })
}

async function removeLabel(number, name) {
  await api(`/issues/${number}/labels/${encodeURIComponent(name)}`, { method: 'DELETE' })
}

// The labels POST endpoint appends, so an issue handed from qoder to freebuff
// would keep both owner labels and `label()` could report the stale one.
async function assignOwner(number, issue, agent) {
  const stale = issue.labels
    .map((l) => l.name)
    .filter((name) => name.startsWith('agent:') && name !== `agent:${agent}`)
  // DELETE on the collection removes every label, so each stale owner goes one
  // at a time; status:* and model:* have to survive a reassignment.
  for (const name of stale) await removeLabel(number, name)
  await addLabels(number, [`agent:${agent}`])
}

async function comment(number, body) {
  await api(`/issues/${number}/comments`, { method: 'POST', body: JSON.stringify({ body }) })
}

async function openIssues() {
  const items = await api('/issues?state=open&per_page=100')
  return items.filter((i) => !i.pull_request)
}

async function openPulls() {
  return api('/pulls?state=open&per_page=100')
}

function pad(value, width) {
  return String(value).padEnd(width)
}

async function board() {
  const [issues, pulls] = await Promise.all([openIssues(), openPulls()])

  console.log(`Issues (${issues.length}${issues.length === 100 ? ', page limit reached' : ''})`)
  if (!issues.length) console.log('  none queued')
  for (const issue of issues) {
    console.log(
      `  #${pad(issue.number, 4)} ${pad(status(issue), 16)} ${pad(label(issue, 'agent'), 16)} ` +
        `${pad(label(issue, 'model'), 16)} ${issue.title}`,
    )
  }

  console.log(`\nPull requests (${pulls.length})`)
  if (!pulls.length) console.log('  none open')
  for (const pull of pulls) {
    console.log(
      `  #${pad(pull.number, 4)} ${pad(status(pull), 16)} ${pad(pull.head.ref, 28)} ` +
        `${pull.draft ? 'draft' : 'ready'}  ${pull.title}`,
    )
  }
}

async function next(agent) {
  if (!agent) throw new Error('team: next needs --agent <name>')
  const issues = await openIssues()
  const ready = issues
    .filter((i) => status(i) === 'queued')
    .filter((i) => {
      const owner = label(i, 'agent')
      return owner === '-' || owner === agent
    })
    .sort((a, b) => a.number - b.number)

  if (!ready.length) {
    console.log(`No queued issue for ${agent}.`)
    return
  }

  const issue = ready[0]
  console.log(`#${issue.number} ${issue.title}`)
  console.log(`tier: ${label(issue, 'model')}   labels: ${issue.labels.map((l) => l.name).join(', ')}`)
  console.log(`owner: ${label(issue, 'agent')}`)
  console.log(`\n${(issue.body || '(no body)').trim().slice(0, 1200)}`)
  const type = (/^(feat|fix|chore|docs|refactor|test|ci)(\(|:|!)/.exec(issue.title) || [])[1] || 'fix'
  const slug = issue.title
    .toLowerCase()
    .replace(/^[a-z]+(\([^)]*\))?!?:\s*/, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 40)
  console.log(`\nclaim it:   node scripts/team.mjs claim ${issue.number} --agent ${agent}`)
  console.log(`branch:     git fetch origin && git checkout -b ${type}/${slug} origin/main`)
  console.log(`delegate:   node scripts/team.mjs dispatch ${issue.number} --agent opencode`)
}

// Each agent works in its own checkout; the tier decides the model when an
// override exists, otherwise the agent's configured default stands.
const WORKTREES = { freebuff: '.', qoder: '../rinavi-qoder', opencode: '../rinavi-opencode' }

async function dispatch(number, agent = 'opencode', run = false) {
  if (!number) throw new Error('team: dispatch needs <number> [--agent opencode] [--run]')
  const issue = await api(`/issues/${number}`)
  if (!issue) throw new Error(`team: no issue #${number} in ${repoSlug()}`)

  const tier = label(issue, 'model')
  const dir = WORKTREES[agent]
  if (!dir) throw new Error(`team: unknown agent ${agent}; expected ${Object.keys(WORKTREES).join(', ')}`)

  const prompt = [
    `You are ${agent} working the RINAVI task queue. Read AGENTS.md first.`,
    '',
    `Issue #${number}: ${issue.title}`,
    '',
    (issue.body || '(no body)').trim(),
    '',
    `Before you start: claim this issue with \`node scripts/team.mjs claim ${number} --agent ${agent}\` unless it is already yours. Branch from origin/main, commit in small checkpoints, and open one pull request that says \`Closes #${number}\` and carries a \`Model:\` line naming the model you ran. Run scripts/check.sh before opening it. Hand the issue back with \`node scripts/team.mjs handoff\` if it needs a different agent.`,
  ].join('\n')

  const envModel = process.env[`RINAVI_MODEL_${(tier === '-' ? 'standard' : tier).toUpperCase()}`]
  // OpenCode 2 has no --dir: the worktree is the working directory, and
  // --standalone keeps a scripted run off the desktop app's own server.
  const server = process.env.OPENCODE_SERVER
  const args = ['run', server ? '--server' : '--standalone']
  if (server) args.push(server)
  args.push('--auto', '--archived')
  if (envModel) args.push('--model', envModel)
  args.push(prompt)

  console.log(`tier ${tier} · agent ${agent} · worktree ${dir}`)
  console.log(`model ${envModel || `(unset: opencode's own default for ${tier})`}`)

  if (!run) {
    console.log(`\ncd ${dir} && opencode ${args.map((a) => (/\s/.test(a) ? JSON.stringify(a) : a)).join(' ')}`)
    console.log('\nDry run. Add --run to start it.')
    return
  }

  // The npm shim is not spawnable on Windows, so prefer the real executable.
  const windowsBin = process.env.APPDATA
    ? join(process.env.APPDATA, 'npm/node_modules/@opencode/cli/bin/opencode.exe')
    : null
  const bin = process.env.OPENCODE_BIN || (windowsBin && existsSync(windowsBin) ? windowsBin : 'opencode')

  // A worktree that is behind main sends the agent down a stale path.
  try {
    execSync('git fetch -q origin && git merge -q --ff-only origin/main', { cwd: dir, stdio: 'ignore' })
  } catch {
    console.log(`warning: could not fast-forward ${dir} to origin/main`)
  }

  // stdin must be closed: without a TTY the CLI blocks forever waiting on it.
  const result = spawnSync(bin, args, { stdio: ['ignore', 'inherit', 'inherit'], cwd: dir })
  if (result.error) throw result.error
  if (result.status !== 0) throw new Error(`team: opencode exited with ${result.status}`)
}

async function claim(number, agent) {
  if (!number || !agent) throw new Error('team: claim needs <number> --agent <name>')
  const issue = await api(`/issues/${number}`)
  if (!issue) throw new Error(`team: no issue #${number} in ${repoSlug()}`)
  const owner = label(issue, 'agent')
  if (owner !== '-' && owner !== agent && status(issue) === 'in-progress') {
    throw new Error(`team: #${number} is already claimed by ${owner}`)
  }
  await assignOwner(number, issue, agent)
  await addLabels(number, ['status:in-progress'])
  if (status(issue) === 'queued') await removeLabel(number, 'status:queued')
  await comment(number, `Claimed by **${agent}**. Branch from \`origin/main\`; comment here if it turns out to need a different owner.`)
  console.log(`claimed #${number} as ${agent}`)
}

async function handoff(number, to, note) {
  if (!number || !to) throw new Error('team: handoff needs <number> --to <agent> [--note "..."]')
  const issue = await api(`/issues/${number}`)
  if (!issue) throw new Error(`team: no issue #${number} in ${repoSlug()}`)
  await assignOwner(number, issue, to)
  await addLabels(number, ['status:queued'])
  if (status(issue) === 'in-progress') await removeLabel(number, 'status:in-progress')
  await comment(
    number,
    `Handing off to **${to}**.${note ? `\n\n${note}` : ''}\n\nNext step: claim it, branch from \`origin/main\`, and open one PR that says \`Closes #${number}\`.`,
  )
  console.log(`#${number} handed to ${to}`)
}

async function review() {
  const pulls = await openPulls()
  const candidates = pulls.filter((p) => status(p) === 'review')
  if (!candidates.length) {
    console.log('No pull request is waiting for review.')
    return
  }
  for (const pull of candidates) {
    const comments = await api(`/issues/${pull.number}/comments?per_page=100`)
    const ai = (comments || []).find((c) => (c.body || '').includes('<!-- rinavi-ai-review -->'))
    const verdict = ai ? ((ai.body.match(/### Overall assessment\s*\n+([^\n]+)/) || [])[1] || 'posted') : 'not posted yet'
    const model = ((pull.body || '').match(/\*\*Model:\*\*\s*`?([^`\n]+)`?/) || [])[1] || 'not stated'
    console.log(
      `#${pull.number} ${pull.title}\n  branch ${pull.head.ref} · ${pull.draft ? 'draft' : 'ready'} · ` +
        `model: ${model.trim()}\n  AI review: ${verdict}\n  ${pull.html_url}`,
    )
  }
}

function flag(args, name) {
  const i = args.indexOf(`--${name}`)
  return i === -1 ? undefined : args[i + 1]
}

const [command, ...rest] = process.argv.slice(2)

try {
  switch (command) {
    case 'board':
      await board()
      break
    case 'next':
      await next(flag(rest, 'agent'))
      break
    case 'claim':
      await claim(Number(rest[0]), flag(rest, 'agent'))
      break
    case 'handoff':
      await handoff(Number(rest[0]), flag(rest, 'to'), flag(rest, 'note'))
      break
    case 'review':
      await review()
      break
    case 'dispatch':
      await dispatch(Number(rest[0]), flag(rest, 'agent') || 'opencode', rest.includes('--run'))
      break
    default:
      console.log('usage: node scripts/team.mjs <board|next|claim|handoff|review|dispatch> [args]')
      process.exit(command ? 1 : 0)
  }
} catch (error) {
  console.error(error.message)
  process.exit(1)
}
