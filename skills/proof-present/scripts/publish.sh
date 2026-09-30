#!/bin/sh
# Publish a finished capture to the tailnet-only captures bucket and print its URL.
#   publish.sh <file> [slug]   ->   https://<host>.ts.net/captures/<date>-<slug>/<file>
set -eu
[ $# -ge 1 ] && [ -f "$1" ] || { echo "usage: publish.sh <file> [slug]" >&2; exit 2; }
file=$1
name=$(basename "$file")
slug=${2:-$(basename "${name%.*}" | tr '[:upper:] _' '[:lower:]--')}
bucket="$HOME/dev/captures/public"
dest="$bucket/$(date +%Y-%m-%d)-$slug"
mkdir -p "$dest"
cp "$file" "$dest/$name"

TS=$(command -v tailscale || { [ -x /usr/local/bin/tailscale ] && echo /usr/local/bin/tailscale; } || echo /Applications/Tailscale.app/Contents/MacOS/Tailscale)
host=$("$TS" status --json | /usr/bin/python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')
# Self-heal: file server and serve mount (both are idempotent).
curl -fsS -o /dev/null http://127.0.0.1:8740/ 2>/dev/null ||
  launchctl kickstart -k "gui/$(id -u)/dev.captures.serve" >/dev/null 2>&1 || true
"$TS" serve status 2>/dev/null | grep -q '/captures' ||
  "$TS" serve --bg --set-path /captures http://127.0.0.1:8740 >/dev/null

url="https://$host/captures/$(basename "$dest")/$(/usr/bin/python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$name")"
code=$(curl -s -o /dev/null -w '%{http_code}' -r 0-0 "http://127.0.0.1:8740/$(basename "$dest")/$name" || true)
[ "$code" = 206 ] || echo "warning: local server returned $code for the published file" >&2
echo "$url"
