#!/usr/bin/env bash
# Publica a pasta static/ no GitHub Pages, pela branch gh-pages.
#
# A branch gh-pages contém SÓ os arquivos da página — nada do código do
# servidor. Ela é montada do zero a cada publicação, num worktree separado, para
# não haver sobra de publicação anterior.
#
# O ideal seria um workflow do GitHub Actions publicando sozinho a cada push.
# Isso exige o escopo `workflow` no token do gh:
#
#     gh auth refresh -s workflow

set -euo pipefail

cd "$(dirname "$0")/.."
raiz="$(pwd)"

if [ -n "$(git status --porcelain)" ]; then
  echo "Há alterações não commitadas. Commit antes de publicar." >&2
  exit 1
fi

arvore="$(mktemp -d)"
rm -rf "$arvore"

if git ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
  git fetch -q origin gh-pages
  git worktree add -q "$arvore" -B gh-pages origin/gh-pages
else
  git worktree add -q --detach "$arvore"
  git -C "$arvore" checkout -q --orphan gh-pages
fi

# Limpa tudo que estiver lá, para não sobrar arquivo de publicação anterior.
git -C "$arvore" rm -rq --ignore-unmatch -- . 2>/dev/null || true
find "$arvore" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

cp "$raiz"/static/index.html "$raiz"/static/style.css "$raiz"/static/app.js "$raiz"/static/config.js "$arvore/"
# Impede o GitHub Pages de processar os arquivos como Jekyll.
touch "$arvore/.nojekyll"

git -C "$arvore" add -A
if git -C "$arvore" diff --cached --quiet; then
  echo "Nada mudou na página."
else
  git -C "$arvore" commit -q -m "Publicar página a partir de static/"
  git -C "$arvore" push -q origin gh-pages
  echo "Página publicada."
fi

git worktree remove --force "$arvore"
