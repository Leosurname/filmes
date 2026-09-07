// Lista os filmes já assistidos, mostra a nota do IMDb junto da nota da
// família (sem confundir as duas) e permite dar/trocar a nota da família e
// ordenar a lista por ela. Issue #19.

const lista = document.getElementById("lista");
const selectOrdenar = document.getElementById("ordenar");
const template = document.getElementById("template-card");

async function carregarFilmes() {
  const ordenar = selectOrdenar.value;
  const params = new URLSearchParams({ status: "assistido" });
  if (ordenar) params.set("ordenar", ordenar);

  const resposta = await fetch(`/api/filmes?${params.toString()}`);
  const filmes = await resposta.json();
  renderizar(filmes);
}

function formatarNota(nota) {
  if (nota === null || nota === undefined) return "—";
  return Number(nota).toFixed(1);
}

function renderizar(filmes) {
  lista.innerHTML = "";

  for (const filme of filmes) {
    const node = template.content.cloneNode(true);

    const poster = node.querySelector(".poster");
    poster.src = filme.poster_url || "";
    poster.alt = filme.titulo || "Pôster do filme";

    node.querySelector(".titulo").textContent = filme.titulo || "(sem título)";
    node.querySelector(".ano").textContent = filme.ano || "";

    const valorImdb = node.querySelector(".valor-imdb");
    valorImdb.textContent = formatarNota(filme.nota_imdb);
    valorImdb.classList.toggle("vazio", filme.nota_imdb == null);

    const valorFamilia = node.querySelector(".valor-familia");
    valorFamilia.textContent = formatarNota(filme.nota_familia);
    valorFamilia.classList.toggle("vazio", filme.nota_familia == null);

    const form = node.querySelector(".form-nota-familia");
    const input = form.querySelector(".input-nota-familia");
    if (filme.nota_familia != null) input.value = filme.nota_familia;

    form.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      await salvarNotaFamilia(filme.id, input.value);
      carregarFilmes();
    });

    lista.appendChild(node);
  }
}

async function salvarNotaFamilia(filmeId, nota) {
  const resposta = await fetch(`/api/filmes/${filmeId}/nota-familia`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nota_familia: Number(nota) }),
  });

  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => ({}));
    alert(erro.detail || "Não deu para salvar a nota da família.");
  }
}

selectOrdenar.addEventListener("change", carregarFilmes);

carregarFilmes();
