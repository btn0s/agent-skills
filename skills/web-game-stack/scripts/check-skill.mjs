#!/usr/bin/env node
import { readFile, readdir, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const required = ['SKILL.md', 'agents/openai.yaml', 'scripts/scaffold.mjs', 'assets/lint/game.mjs', 'assets/lint/.oxlintrc.json', 'assets/loading/warmup.mjs', 'assets/monorepo/tsconfig.json', 'assets/monorepo/pnpm-workspace.yaml', 'assets/deploy/Dockerfile', 'assets/deploy/worker.ts', ...['tpp', 'fpp', 'blank'].map(p => `assets/starters/${p}/src/main.tsx`), ...['profiles', 'state-effect-xstate-koota', 'netcode-colyseus', 'controller-intent', 'als-integration', 'rendering-physics', 'ui-and-input', 'assets-pipeline', 'loading-warmup', 'vfx-audio', 'deploy', 'gate-and-conventions', 'pins-and-exceptions', 'update-procedure'].map(n => `references/${n}.md`)]
const errors = []
for (const file of required) {
  try { await stat(path.join(root, file)) } catch { errors.push(`Missing ${file}`) }
}
async function walk(dir) {
  const found = []
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name)
    if (entry.isDirectory()) found.push(...await walk(file))
    else found.push(file)
  }
  return found
}
for (const file of await walk(root)) {
  const relative = path.relative(root, file)
  const content = await readFile(file, 'utf8')
  if (!relative.endsWith('pins-and-exceptions.md')) {
    const versions = content.match(/(?<![\d.])\d+\.\d+\.\d+(?:-[a-zA-Z0-9.]+)?/g) || []
    for (const version of versions.filter(version => version !== '0.0.0')) errors.push(`Exact version in ${relative}: ${version}`)
  }
  if (file.endsWith('package.json')) {
    const data = JSON.parse(content)
    for (const value of Object.values({ ...data.dependencies, ...data.devDependencies, ...data.peerDependencies })) if (/^\d+\.\d+\.\d+/.test(value)) errors.push(`Exact dependency in ${relative}: ${value}`)
  }
  if (/^assets\/starters\/.+\/(?:package\.json|pnpm-lock\.yaml)$/.test(relative)) errors.push(`Starter should use generated latest ranges: ${relative}`)
}
const skill = await readFile(path.join(root, 'SKILL.md'), 'utf8')
if (!skill.startsWith('---\nname: web-game-stack\n')) errors.push('Invalid SKILL.md frontmatter')
if (!/Last verified: \d{4}-\d{2}-\d{2}/.test(skill)) errors.push('Missing Last verified date')
if (errors.length) { for (const error of errors) process.stderr.write(`${error}\n`); process.exitCode = 1 }
else process.stdout.write('web-game-stack structure and dependency policy: pass\n')
