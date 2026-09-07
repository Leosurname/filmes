// Issue #16 — Mostrar onde assistir no card e filtrar por serviço
//
// O back-end que busca "onde assistir" na TMDB (issue #15) e o endpoint de
// listagem de filmes (issue #4) ainda não existem. Para não invadir o escopo
// dessas issues, este arquivo usa uma lista de exemplo (FILMES_EXEMPLO) com o
// mesmo formato do campo `provedores` descrito no plan.md. Quando o endpoint
// real existir, basta trocar `carregarFilmes()` para buscar em `/api/filmes`
// — o resto (renderizar cards e filtrar) já funciona com o mesmo formato.

const SERVICOS = ["Netflix", "Apple TV", "Prime Video", "Disney+", "HBO Max"];
const NAO_DISPONIVEL = "Não disponível";

// Dados de exemplo só para demonstrar a funcionalidade desta issue.
const FILMES_EXEMPLO = [
  { id: 1, titulo: "Um Sonho de Liberdade", provedores: ["Netflix", "Prime Video"] },
  { id: 2, titulo: "O Poderoso Chefão", provedores: ["Prime Video"] },
  { id: 3, titulo: "Divertida Mente", provedores: ["Disney+"] },
  { id: 4, titulo: "Duna", provedores: ["HBO Max", "Apple TV"] },
  { id: 5, titulo: "Cidade de Deus", provedores: [] },
  { id: 6, titulo: "Interestelar", provedores: ["Prime Video", "Apple TV", "Netflix"] },
  { id: 7, titulo: "Vingadores: Ultimato", provedores: ["Disney+"] },
  { id: 8, titulo: "Filme sem informação de streaming" },
];

let filtrosAtivos = new Set();

function carregarFilmes() {
  // Placeholder até a API de listagem (issue #4) existir.
  return FILMES_EXEMPLO;
}

function servicosDoFilme(filme) {
  return Array.isArray(filme.provedores) ? filme.provedores : [];
}

function renderizarFiltros() {
  const container = document.getElementById("lista-filtros");
  container.innerHTML = "";

  SERVICOS.forEach((servico) => {
    const id = `filtro-${servico.replace(/\s+/g, "-").toLowerCase()}`;
    const label = document.createElement("label");
    label.className = "filtro-item";
    label.setAttribute("for", id);

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = id;
    checkbox.value = servico;
    checkbox.checked = filtrosAtivos.has(servico);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        filtrosAtivos.add(servico);
      } else {
        filtrosAtivos.delete(servico);
      }
      renderizarFilmes();
    });

    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(servico));
    container.appendChild(label);
  });
}

function filmeCombinaComFiltro(filme) {
  if (filtrosAtivos.size === 0) return true;
  const servicos = servicosDoFilme(filme);
  return servicos.some((servico) => filtrosAtivos.has(servico));
}

function criarBadgeServico(servico) {
  const span = document.createElement("span");
  span.className = "badge-servico";
  span.textContent = servico;
  return span;
}

function criarBadgeIndisponivel() {
  const span = document.createElement("span");
  span.className = "badge-servico badge-indisponivel";
  span.textContent = NAO_DISPONIVEL;
  return span;
}

function criarCard(filme) {
  const card = document.createElement("article");
  card.className = "card-filme";

  const titulo = document.createElement("h3");
  titulo.textContent = filme.titulo;
  card.appendChild(titulo);

  const servicosContainer = document.createElement("div");
  servicosContainer.className = "servicos";

  const servicos = servicosDoFilme(filme);
  if (servicos.length === 0) {
    servicosContainer.appendChild(criarBadgeIndisponivel());
  } else {
    servicos.forEach((servico) => {
      servicosContainer.appendChild(criarBadgeServico(servico));
    });
  }

  card.appendChild(servicosContainer);
  return card;
}

function renderizarFilmes() {
  const container = document.getElementById("lista-filmes");
  container.innerHTML = "";

  const filmes = carregarFilmes().filter(filmeCombinaComFiltro);

  if (filmes.length === 0) {
    const vazio = document.createElement("p");
    vazio.className = "sem-resultado";
    vazio.textContent = "Nenhum filme disponível nos serviços selecionados.";
    container.appendChild(vazio);
    return;
  }

  filmes.forEach((filme) => {
    container.appendChild(criarCard(filme));
  });
}

function limparFiltros() {
  filtrosAtivos.clear();
  renderizarFiltros();
  renderizarFilmes();
}

document.getElementById("limpar-filtros").addEventListener("click", limparFiltros);

renderizarFiltros();
renderizarFilmes();
