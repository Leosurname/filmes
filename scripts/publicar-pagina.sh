#!/usr/bin/env bash
# Publica a pasta static/ no GitHub Pages, pela branch gh-pages.
#
# O ideal seria um workflow do GitHub Actions publicando sozinho a cada push.
# Isso exige o escopo `workflow` no token do gh:
#
#     gh auth refresh -s workflow
#
# Enquanto isso não for feito, este script faz o mesmo trabalho na mão.

set -euo pipefail

cd "$(dirname "$0")/.."

if [ -n "$(git status --porcelain)" ]; then
  echo "Há alterações não commitadas. Commit antes de publicar." >&2
  exit 1
fi

origem="$(git rev-parse --abbrev-ref HEAD)"
temporaria="$(mktemp -d)"

cp static/*.html static/*.css static/*.js "$temporaria/"
# Impede o GitHub Pages de processar os arquivos como Jekyll.
touch "$temporaria/.nojekyll"

git checkout -q gh-pages 2>/dev/null || git checkout -q --orphan gh-pages
git rm -rq . 2>/dev/null || true
cp -R "$temporaria"/. .
rm -rf "$temporaria"

git add -A
if git diff --cached --quiet; then
  echo "Nada mudou na página."
else
  git commit -q -m "Publicar página a partir de static/"
  git push -q origin gh-pages
  echo "Página publicada."
fi

git checkout -q "$origem"
