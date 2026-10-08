#!/bin/bash
# Install everything `proof` needs. Idempotent: re-run it after `skills update`.
#
#   install.sh             core + narration (Kokoro)
#   install.sh --check     report what's installed and what's missing; changes nothing
#   install.sh --publish   also serve ~/dev/captures/public on the tailnet (tailscale serve, never funnel)
#   install.sh --screen    also install Cap (proof shot / proof clip; GUI screen recording)
#   install.sh --maestro   also install Maestro + JDK 21 (scripted iOS Simulator captures)
#   install.sh --all       all of the above
#   install.sh --no-narrate  skip Kokoro (proof then needs --no-narrate on every run)
#
# macOS on Apple Silicon only (Kokoro runs on MLX; terminal beats use SF Mono from Terminal.app).
set -eu

CHECK=0 NARRATE=1 PUBLISH=0 SCREEN=0 MAESTRO=0 CORE_MISSING=0
for a in "$@"; do
  case $a in
    --check) CHECK=1 ;;
    --no-narrate) NARRATE=0 ;;
    --publish) PUBLISH=1 ;;
    --screen) SCREEN=1 ;;
    --maestro) MAESTRO=1 ;;
    --all) PUBLISH=1 SCREEN=1 MAESTRO=1 ;;
    -h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

self=$(cd "$(dirname "$0")" && pwd -P)
BIN="$HOME/.local/bin"
TTS_TOOL="--python 3.12 mlx-audio==0.5.7 --with misaki[en]==0.9.4 --with pip"  # pip: misaki fetches spaCy's English model
export PATH="$BIN:/opt/homebrew/bin:$PATH" HF_HUB_DISABLE_TELEMETRY=1 DO_NOT_TRACK=1
missing=0

ok()   { printf '  \033[32mok\033[0m       %-22s %s\n' "$1" "${2:-}"; }
miss() { printf '  \033[33mmissing\033[0m  %-22s %s\n' "$1" "${2:-}"; missing=$((missing + 1)); }
step() { printf '\n\033[1m%s\033[0m\n' "$1"; }
do_() { [ $CHECK = 1 ] || "$@"; }

tailscale_bin() {
  command -v tailscale 2>/dev/null ||
    { for p in /usr/local/bin/tailscale /Applications/Tailscale.app/Contents/MacOS/Tailscale; do
        [ -x "$p" ] && { echo "$p"; return; }; done; }
}

step "Proof skills"
for sk in proof-write proof-capture proof-present; do
  [ -f "$(dirname "$self")/$sk/SKILL.md" ] && ok "$sk" ||
    miss "$sk" "npx skills add btn0s/agent-skills --skill $sk -g -y"
done

step "Host"
[ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ] && ok "macOS arm64" "$(sw_vers -productVersion)" ||
  { miss "macOS arm64" "proof needs macOS on Apple Silicon"; exit 1; }
[ -f /System/Applications/Utilities/Terminal.app/Contents/Resources/Fonts/SF-Mono-Regular.otf ] &&
  ok "SF Mono" || miss "SF Mono" "expected inside Terminal.app"

step "Core (proof run)"
if ! command -v uv >/dev/null; then
  if [ $CHECK = 1 ]; then miss uv "brew install uv"
  elif command -v brew >/dev/null; then brew install uv
  else curl -LsSf https://astral.sh/uv/install.sh | sh; fi
fi
command -v uv >/dev/null && ok uv "$(uv --version)" || CORE_MISSING=1
mkdir -p "$BIN"
do_ ln -sf "$self/proof/bin/proof" "$BIN/proof"
[ "$(readlink "$BIN/proof" 2>/dev/null)" = "$self/proof/bin/proof" ] && ok proof "$BIN/proof" ||
  { miss proof "run $0 (links $BIN/proof)"; CORE_MISSING=1; }
grep -qs '.local/bin' "$HOME/.zshrc" "$HOME/.zprofile" "$HOME/.zshenv" ||
  echo "  note     add to your shell profile: export PATH=\"\$HOME/.local/bin:\$PATH\""
if command -v uv >/dev/null; then  # resolves the script's own deps (pyte, pillow, pyyaml, imageio-ffmpeg)
  if [ $CHECK = 1 ] || uv run --quiet --script "$self/proof/proof.py" --help >/dev/null; then
    [ $CHECK = 1 ] || ok "proof deps" "pyte, pillow, pyyaml, bundled ffmpeg"
  else miss "proof deps" "uv run --script $self/proof/proof.py --help"; fi
fi

step "Narration (on by default)"
if [ $NARRATE = 1 ]; then
  tool_py="$(uv tool dir 2>/dev/null)/mlx-audio/bin/python"
  if [ ! -x "$tool_py" ]; then
    [ $CHECK = 1 ] && miss mlx-audio "uv tool install $TTS_TOOL" || uv tool install $TTS_TOOL
  fi
  if [ -x "$tool_py" ]; then
    ok mlx-audio "$("$tool_py" -c 'import importlib.metadata as m; print(m.version("mlx-audio"))')"
    [ "$tool_py" = "$HOME/.local/share/uv/tools/mlx-audio/bin/python" ] ||
      echo "  note     uv tools live elsewhere; export PROOF_TTS_PY=$tool_py"
    if ls "$HOME/.cache/huggingface/hub" 2>/dev/null | grep -q Kokoro-82M-bf16; then
      ok "Kokoro model" "cached"
    elif [ $CHECK = 1 ]; then miss "Kokoro model" "downloads ~350 MB on first use (install.sh warms it)"
    else  # first synthesis pulls the model and a spaCy English model; do it now, not mid-render
      tmp=$(mktemp -d)
      printf '[{"text":"Ready.","out":"%s/t.wav","voice":"af_heart","speed":1.0,"lang":"a"}]' "$tmp" > "$tmp/j.json"
      if "$tool_py" "$self/proof/tts_batch.py" "$tmp/j.json" >"$tmp/log" 2>&1; then ok "Kokoro model" "downloaded and tested"
      else miss "Kokoro model" "test synthesis failed:"; tail -3 "$tmp/log" | sed 's/^/           /'
        echo "           reinstall: uv tool install --force $TTS_TOOL"; fi
      rm -rf "$tmp"
    fi
  fi
else
  echo "  skipped  (run proof with --no-narrate, or set narrate: false in proof.config.yaml)"
fi

step "Publish to the tailnet (--publish)"
ts=$(tailscale_bin || true)
bucket="$HOME/dev/captures/public"
agent="$HOME/Library/LaunchAgents/dev.captures.serve.plist"
if [ -z "$ts" ]; then
  miss tailscale "install Tailscale and sign in; this script won't change your network"
else
  ok tailscale "$ts"
  if [ $PUBLISH = 1 ] && [ $CHECK = 0 ]; then
    mkdir -p "$bucket" "$HOME/Library/LaunchAgents"
    cat > "$agent" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>dev.captures.serve</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$self/scripts/serve_captures.py</string>
    <string>--dir</string><string>$bucket</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/captures-serve.log</string>
</dict>
</plist>
EOF
    launchctl bootout "gui/$(id -u)/dev.captures.serve" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$agent"
    sleep 1
    "$ts" serve status 2>/dev/null | grep -q /captures ||
      "$ts" serve --bg --set-path /captures http://127.0.0.1:8740 >/dev/null
  fi
  curl -fsS -o /dev/null http://127.0.0.1:8740/ 2>/dev/null && ok "captures server" "127.0.0.1:8740 -> $bucket" ||
    miss "captures server" "install.sh --publish"
  "$ts" serve status 2>/dev/null | grep -q /captures && ok "tailscale serve" "/captures (tailnet only)" ||
    miss "tailscale serve" "install.sh --publish (or use proof run --no-publish)"
fi

step "GitHub attachments (proof attach, --pr)"
if command -v gh >/dev/null; then
  gh attach --help >/dev/null 2>&1 && ok gh-attach "$(gh extension list 2>/dev/null | awk '/gh-attach/{print $3}')" ||
    { [ $CHECK = 0 ] && gh extension install sudosubin/gh-attach >/dev/null 2>&1 && ok gh-attach "installed" ||
      miss gh-attach "gh extension install sudosubin/gh-attach"; }
  echo "  note     gh-attach uploads with your browser's GitHub session; be signed in to github.com"
else
  miss gh "brew install gh && gh auth login"
fi

step "Screen recording (--screen: proof shot, proof clip)"
if [ ! -d /Applications/Cap.app ]; then
  [ $SCREEN = 1 ] && [ $CHECK = 0 ] && brew install --cask cap || miss Cap "install.sh --screen (brew install --cask cap)"
fi
if [ -d /Applications/Cap.app ]; then
  do_ mkdir -p "$HOME/.cap/bin"
  do_ ln -sf /Applications/Cap.app/Contents/MacOS/cap-cli "$HOME/.cap/bin/cap"
  [ -x "$HOME/.cap/bin/cap" ] && ok "cap CLI" "$("$HOME/.cap/bin/cap" --version 2>/dev/null)" || miss "cap CLI" "run $0 (links ~/.cap/bin/cap)"
  echo "  note     Screen Recording permission is granted by a person in System Settings, never by a script"
fi

step "Simulator captures (--maestro)"
if ! command -v maestro >/dev/null && [ ! -x "$HOME/.maestro/bin/maestro" ]; then
  if [ $MAESTRO = 1 ] && [ $CHECK = 0 ]; then
    brew list openjdk@21 >/dev/null 2>&1 || brew install openjdk@21
    curl -fsSL https://get.maestro.mobile.dev | bash
  else miss Maestro "install.sh --maestro"; fi
fi
if [ -x "$HOME/.maestro/bin/maestro" ] || command -v maestro >/dev/null; then
  ok Maestro "$HOME/.maestro/bin/maestro"
  echo "  note     run it with: JAVA_HOME=\$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home"
  echo "           MAESTRO_CLI_NO_ANALYTICS=1 MAESTRO_CLI_ANALYSIS_NOTIFICATION_DISABLED=true"
fi

step "Full edits (optional)"
tsrct="$HOME/Library/Application Support/Tesseract/bin/tsrct"
[ -x "$tsrct" ] && ok tsrct "$("$tsrct" --version 2>/dev/null | head -1)" ||
  miss tsrct "install the pinned CLI with the tesseract-video skill (references/installation.md)"

echo
if [ $CHECK = 1 ]; then echo "$missing missing (optional pieces count too)."; else echo "Done. Check anytime: $0 --check"; fi
exit $CORE_MISSING
