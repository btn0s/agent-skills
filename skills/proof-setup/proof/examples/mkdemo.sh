#!/bin/sh
# Build a tiny repo with a real bug on main and its fix on a branch.
set -eu
R=$HOME/dev/proof-demo
rm -rf "$R" && mkdir -p "$R" && cd "$R"
git init -q -b main
git config user.name "proof demo"; git config user.email "proof-demo@devbox.local"
cat > slugkit.py <<'PY'
"""Turn titles into URL slugs."""
import re
import sys


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return text.strip("-")


if __name__ == "__main__":
    for line in sys.stdin.read().splitlines():
        print(f"{line:<26} -> {slugify(line)}")
PY
cat > test_slugkit.py <<'PY'
import unittest

from slugkit import slugify


class SlugifyTest(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_spaces(self):
        self.assertEqual(slugify("  many   spaces  "), "many-spaces")

    def test_accents(self):
        self.assertEqual(slugify("Crème Brûlée"), "creme-brulee")

    def test_mixed(self):
        self.assertEqual(slugify("Déjà Vu, 2026"), "deja-vu-2026")
PY
printf 'Crème Brûlée\nDéjà Vu, 2026\nSão Paulo Café\nHello, World!\n' > titles.txt
git add -A && git commit -qm "slugkit: initial slugify"
git switch -qc fix/slugify-accents
python3 - <<'PY'
p = "slugkit.py"
s = open(p).read()
s = s.replace("import re\nimport sys\n", "import re\nimport sys\nimport unicodedata\n")
s = s.replace('    text = re.sub(', '    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()\n    text = re.sub(')
open(p, "w").write(s)
PY
git commit -qam "slugify: fold accented letters to ASCII instead of dropping them"
git switch -q main
git log --oneline --all
