const botoesVisao = document.querySelectorAll(".visao-btn");
const listaEl = document.getElementById("lista-filmes");
const vazioEl = document.getElementById("vazio");
const filtroGenero = document.getElementById("filtro-genero");
const filtroDuracao = document.getElementById("filtro-duracao");

let statusAtual = "quero_ver";

function ativarBotao(status) {
  botoesVisao.forEach((botao) => {
    botao.classList.toggle("ativo", botao.dataset.status === status);
  });
}

async function carregarGeneros() {
  const resposta = await fetch("/api/generos");
  const generos = await resposta.json();
  generos.forEach((genero) => {
    const opcao = document.createElement("option");
    opcao.value = genero;
    opcao.textContent = genero;
    filtroGenero.appendChild(opcao);
  });
}

function montarUrl() {
  const params = new URLSearchParams({ status: statusAtual });
  if (filtroGenero.value) params.set("genero", filtroGenero.value);
  if (filtroDuracao.value) params.set("duracao_max", filtroDuracao.value);
  return `/api/filmes?${params.toString()}`;
}

function criarCard(filme) {
  const item = document.createElement("li");
  item.className = "card";

  const assistidoInfo =
    filme.status === "assistido"
      ? `<div class="assistido-info">
           Assistido em ${formatarData(filme.data_assistido)}<br />
           Nota da família: ${formatarNota(filme.nota_familia)}
         </div>`
      : "";

  item.innerHTML = `
    <h2>${filme.titulo} (${filme.ano ?? "?"})</h2>
    <p class="meta">${filme.generos ?? ""} · ${filme.duracao_min ?? "?"} min · Classificação: ${filme.classificacao ?? "?"}</p>
    <p class="meta">Nota IMDb: ${filme.nota_imdb ?? "-"}</p>
    ${assistidoInfo}
  `;

  return item;
}

function formatarData(data) {
  if (!data) return "-";
  const [ano, mes, dia] = data.split("-");
  return `${dia}/${mes}/${ano}`;
}

function formatarNota(nota) {
  return nota === null || nota === undefined ? "-" : nota;
}

async function carregarFilmes() {
  const resposta = await fetch(montarUrl());
  const filmes = await resposta.json();

  listaEl.innerHTML = "";
  vazioEl.hidden = filmes.length > 0;

  filmes.forEach((filme) => listaEl.appendChild(criarCard(filme)));
}

botoesVisao.forEach((botao) => {
  botao.addEventListener("click", () => {
    statusAtual = botao.dataset.status;
    ativarBotao(statusAtual);
    carregarFilmes();
  });
});

filtroGenero.addEventListener("change", carregarFilmes);
filtroDuracao.addEventListener("change", carregarFilmes);

carregarGeneros();
carregarFilmes();
