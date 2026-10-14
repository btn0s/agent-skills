#!/usr/bin/env node
import { readFile, writeFile, mkdir, readdir, cp } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const skill = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const blacksiteUrl = 'https://github.com/btn0s/blacksite.git'
const alsUrl = 'https://github.com/btn0s/als-web.git'
const systems = {
  operator: { name: 'Operator', description: 'ALS first and third person controller', dependencies: [] },
  arsenal: { name: 'Arsenal', description: 'Deterministic weapon simulation', dependencies: [] },
  warden: { name: 'Warden', description: 'Squad AI and decision systems', dependencies: [] },
  rupture: { name: 'Rupture', description: 'Destruction simulation and effects', dependencies: [] },
}
const profiles = {
  tpp: { name: 'Third person', description: 'ALS character, native shoulder camera, walking arena', included: [], optional: Object.keys(systems), unavailable: [] },
  fpp: { name: 'First and third person', description: 'ALS body, first person view, Operator and Arsenal', included: ['operator', 'arsenal'], optional: ['warden', 'rupture'], unavailable: [] },
  blank: { name: 'Blank', description: 'Minimal R3F scene ready for selected systems', included: [], optional: Object.keys(systems), unavailable: [] },
}
function parse(argv) {
  const result = { command: argv[0] === 'catalog' ? 'catalog' : 'scaffold', json: argv.includes('--json'), gate: argv.includes('--gate') }
  const args = result.command === 'catalog' ? argv.slice(1) : argv
  for (let i = 0; i < args.length; i++) {
    const arg = args[i]
    if (['--json', '--gate'].includes(arg)) continue
    if (!['--profile', '--name', '--dir', '--systems', '--blacksite-ref'].includes(arg) || !args[i + 1]) throw new Error(`Unknown or incomplete option: ${arg}`)
    result[arg.slice(2)] = args[++i]
  }
  return result
}
function emit(json, step, status, message) {
  const line = JSON.stringify({ step, status, message })
  if (json) process.stdout.write(`${line}\n`)
  else process.stderr.write(`${step}: ${message}\n`)
}
function run(command, args, cwd) {
  const windows = process.platform === 'win32'
  const executable = windows && ['pnpm', 'npm'].includes(command) ? `${command}.cmd` : command
  const result = spawnSync(executable, args, { cwd, encoding: 'utf8', shell: windows && executable.endsWith('.cmd'), maxBuffer: 32 * 1024 * 1024 })
  if (result.error || result.status !== 0) throw new Error(`${command} ${args.join(' ')} failed: ${(result.stderr || result.stdout || result.error?.message || '').trim().slice(-3000)}`)
  return result.stdout.trim()
}
async function json(file) { return JSON.parse(await readFile(file, 'utf8')) }
function slug(name) { return name.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'game' }
async function npmRange(name) {
  const version = run('npm', ['view', name, 'version'], process.cwd()).split('\n').at(-1)
  if (!/^\d+\.\d+\.\d+/.test(version)) throw new Error(`No published version for ${name}`)
  return `^${version}`
}
async function submodule(root, url, target, ref) {
  const full = path.join(root, target)
  const modules = existsSync(path.join(root, '.gitmodules')) ? await readFile(path.join(root, '.gitmodules'), 'utf8') : ''
  if (!modules.includes(`path = ${target}`)) {
    if (existsSync(full)) throw new Error(`${target} exists but is not a registered Git submodule`)
    run('git', ['submodule', 'add', url, target], root)
  }
  run('git', ['submodule', 'update', '--init', '--recursive', '--', target], root)
  if (!existsSync(path.join(full, '.git'))) throw new Error(`${target} could not be initialized`)
  if (ref) {
    run('git', ['fetch', 'origin', ref], full)
    run('git', ['checkout', '--detach', 'FETCH_HEAD'], full)
    run('git', ['submodule', 'update', '--init', '--recursive'], full)
  }
}
async function packageClosure(blacksite, requested) {
  const names = new Map()
  for (const folder of await readdir(path.join(blacksite, 'packages'))) {
    const file = path.join(blacksite, 'packages', folder, 'package.json')
    if (existsSync(file)) names.set((await json(file)).name, folder)
  }
  const selected = new Set()
  async function visit(name) {
    if (selected.has(name)) return
    const folder = names.get(name)
    if (!folder) throw new Error(`Blacksite package unavailable: ${name}`)
    selected.add(name)
    const manifest = await json(path.join(blacksite, 'packages', folder, 'package.json'))
    for (const dep of Object.keys({ ...manifest.dependencies, ...manifest.peerDependencies })) if (dep.startsWith('@blacksite/')) await visit(dep)
  }
  for (const id of requested) await visit(`@blacksite/${id}`)
  return [...selected].map(name => `vendor/blacksite/packages/${names.get(name)}`).sort()
}
async function main() {
  const options = parse(process.argv.slice(2))
  if (options.command === 'catalog') {
    const catalog = {
      profiles: Object.entries(profiles).map(([id, profile]) => ({ id, ...profile, thumbnail: `assets/thumbnails/${id}.svg` })),
      systems: Object.entries(systems).map(([id, system]) => ({ id, ...system, thumbnail: `assets/thumbnails/${id}.svg`, profiles: Object.fromEntries(Object.entries(profiles).map(([profile, data]) => [profile, data.included.includes(id) ? 'included' : data.unavailable.includes(id) ? 'unavailable' : 'optional'])) })),
    }
    process.stdout.write(`${JSON.stringify(catalog)}\n`)
    return
  }
  const profile = options.profile
  if (!profiles[profile]) throw new Error('Choose --profile tpp|fpp|blank')
  if (!options.name || !options.name.trim()) throw new Error('--name is required')
  if (!options.dir || !path.isAbsolute(options.dir)) throw new Error('--dir must be absolute')
  const requested = new Set(profiles[profile].included)
  for (const id of (options.systems || '').split(',').filter(Boolean)) {
    if (!systems[id]) throw new Error(`Unknown system: ${id}`)
    requested.add(id)
  }
  const root = path.resolve(options.dir)
  const config = { profile, name: options.name, systems: [...requested].sort(), blacksiteRef: options['blacksite-ref'] || null }
  const marker = path.join(root, '.web-game-stack.json')
  const complete = path.join(root, '.web-game-stack-complete')
  if (existsSync(root)) {
    const entries = await readdir(root)
    if (entries.length && !existsSync(marker)) throw new Error(`Refusing nonempty directory without scaffold marker: ${root}`)
    if (existsSync(marker) && JSON.stringify(await json(marker)) !== JSON.stringify(config)) throw new Error('Existing scaffold options differ; use a new directory')
  }
  if (existsSync(complete)) {
    if (options.gate) {
      emit(options.json, 'gate', 'start', 'Running lint, typecheck, and build')
      run('pnpm', ['check'], root)
      emit(options.json, 'gate', 'done', 'Gate passed')
    }
    process.stdout.write(`${JSON.stringify({ result: 'ok', dir: root, devCommand: 'pnpm dev', port: 5173 })}\n`)
    return
  }
  emit(options.json, 'directory', 'start', root)
  await mkdir(root, { recursive: true })
  await writeFile(marker, `${JSON.stringify(config, null, 2)}\n`)
  if (!existsSync(path.join(root, '.git'))) run('git', ['init'], root)
  emit(options.json, 'directory', 'done', 'Initialized Git repository')
  emit(options.json, 'submodules', 'start', 'Adding Blacksite and ALS')
  await submodule(root, blacksiteUrl, 'vendor/blacksite', options['blacksite-ref'])
  await submodule(root, alsUrl, 'vendor/als-web')
  emit(options.json, 'submodules', 'done', 'Submodules initialized')
  const closure = await packageClosure(path.join(root, 'vendor/blacksite'), [...requested])
  const workspace = ['packages:', ...closure.map(item => `  - '${item}'`), "  - 'vendor/als-web'", 'allowBuilds:', '  esbuild: true', 'minimumReleaseAge: 0', ''].join('\n')
  await writeFile(path.join(root, 'pnpm-workspace.yaml'), workspace)
  const dependencyNames = ['react', 'react-dom', 'three', '@react-three/fiber', '@react-three/rapier']
  const devNames = ['typescript', 'vite', '@vitejs/plugin-react', 'oxlint', '@types/react', '@types/react-dom', '@types/three']
  const dependencies = { 'als-ue5-r3f': 'workspace:*' }
  for (const id of requested) dependencies[`@blacksite/${id}`] = 'workspace:*'
  for (const name of dependencyNames) dependencies[name] = await npmRange(name)
  const devDependencies = {}
  for (const name of devNames) devDependencies[name] = await npmRange(name)
  const manifest = { name: slug(options.name), private: true, type: 'module', scripts: { dev: 'vite', lint: 'oxlint .', typecheck: 'tsc --noEmit', build: 'vite build', check: 'pnpm lint && pnpm typecheck && pnpm build' }, dependencies, devDependencies }
  await writeFile(path.join(root, 'package.json'), `${JSON.stringify(manifest, null, 2)}\n`)
  await writeFile(path.join(root, 'pnpm-workspace.yaml'), `${workspace}overrides:\n  three: '${dependencies.three}'\n  '@types/three': '${devDependencies['@types/three']}'\n`)
  const source = path.join(skill, 'assets', 'starters', profile)
  await cp(source, root, { recursive: true, force: true })
  await mkdir(path.join(root, 'lint'), { recursive: true })
  await cp(path.join(skill, 'assets', 'lint', 'game.mjs'), path.join(root, 'lint', 'game.mjs'), { recursive: true, force: true })
  await cp(path.join(skill, 'assets', 'lint', '.oxlintrc.json'), path.join(root, '.oxlintrc.json'), { force: true })
  await cp(path.join(skill, 'assets', 'monorepo', 'tsconfig.json'), path.join(root, 'tsconfig.json'), { force: true })
  await cp(path.join(skill, 'assets', 'monorepo', 'vite.config.mjs'), path.join(root, 'vite.config.mjs'), { force: true })
  await cp(path.join(skill, 'assets', 'monorepo', '.gitignore'), path.join(root, '.gitignore'), { force: true })
  await writeFile(path.join(root, 'index.html'), `<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${options.name.replaceAll('&', '&amp;').replaceAll('<', '&lt;')}</title></head><body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>\n`)
  emit(options.json, 'files', 'done', `Copied ${profile} starter and ${closure.length} Blacksite workspace packages`)
  emit(options.json, 'install', 'start', 'Running pnpm install')
  run('pnpm', ['install'], root)
  emit(options.json, 'install', 'done', 'Dependencies installed')
  if (options.gate) {
    emit(options.json, 'gate', 'start', 'Running lint, typecheck, and build')
    run('pnpm', ['check'], root)
    emit(options.json, 'gate', 'done', 'Gate passed')
  }
  await writeFile(complete, 'complete\n')
  const final = { result: 'ok', dir: root, devCommand: 'pnpm dev', port: 5173 }
  process.stdout.write(`${JSON.stringify(final)}\n`)
}
try { await main() } catch (error) {
  const json = process.argv.includes('--json')
  emit(json, 'scaffold', 'fail', error instanceof Error ? error.message : String(error))
  process.exitCode = 1
}
