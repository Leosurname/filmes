const formNome = document.getElementById("form-nome");
const formFilme = document.getElementById("form-filme");
const inputNome = document.getElementById("nome");
const inputUrl = document.getElementById("url");
const aviso = document.getElementById("aviso");
const listaFilmes = document.getElementById("lista-filmes");

function nomeSalvo() {
  return localStorage.getItem("nome");
}

function mostrarFormFilme() {
  formNome.hidden = true;
  formFilme.hidden = false;
}

if (nomeSalvo()) {
  mostrarFormFilme();
}

formNome.addEventListener("submit", (evento) => {
  evento.preventDefault();
  const nome = inputNome.value.trim();
  if (!nome) return;
  localStorage.setItem("nome", nome);
  mostrarFormFilme();
});

function formatarData(isoString) {
  const data = new Date(isoString);
  return data.toLocaleString("pt-BR");
}

function esconderAviso() {
  aviso.hidden = true;
  aviso.textContent = "";
}

function mostrarAvisoDuplicado(detalhe) {
  const filme = detalhe.filme;
  aviso.textContent =
    `Esse filme já está na lista! Foi sugerido por ${filme.sugerido_por} ` +
    `em ${formatarData(filme.data_sugestao)}.`;
  aviso.hidden = false;
}

async function carregarLista() {
  const resposta = await fetch("/api/filmes");
  const filmes = await resposta.json();
  listaFilmes.innerHTML = "";
  for (const filme of filmes) {
    const item = document.createElement("li");
    item.textContent =
      `${filme.imdb_id} — sugerido por ${filme.sugerido_por} em ${formatarData(filme.data_sugestao)}`;
    listaFilmes.appendChild(item);
  }
}

formFilme.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  esconderAviso();

  const url = inputUrl.value.trim();
  const nome = nomeSalvo();

  const resposta = await fetch("/api/filmes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, nome }),
  });

  if (resposta.status === 409) {
    const corpo = await resposta.json();
    mostrarAvisoDuplicado(corpo.detail);
    return;
  }

  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}));
    aviso.textContent = corpo.detail || "Não foi possível adicionar o filme.";
    aviso.hidden = false;
    return;
  }

  inputUrl.value = "";
  await carregarLista();
});

carregarLista();
