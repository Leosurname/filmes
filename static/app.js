// Ordenação da lista de filmes (issue #14).
//
// O projeto ainda não tem back-end nem filtros (fases anteriores do plan.md
// seguem em aberto), então este arquivo traz uma lista de exemplo só para
// demonstrar e testar a ordenação de forma isolada. Quando os filtros das
// issues #11, #12 e #13 existirem, eles devem atualizar `filmesAtuais` antes
// de chamar `aplicarOrdenacao()` — a ordenação sempre atua sobre a lista que
// já está na tela (filtrada ou não), então continua funcionando com filtros
// ligados sem precisar de nenhuma mudança aqui.

const FILMES_EXEMPLO = [
  { id: 1, titulo: "Filme A", data_sugestao: "2026-09-01", nota_imdb: 7.2, duracao_min: 118 },
  { id: 2, titulo: "Filme B (sem nota)", data_sugestao: "2026-09-05", nota_imdb: null, duracao_min: 95 },
  { id: 3, titulo: "Filme C", data_sugestao: "2026-08-20", nota_imdb: 8.9, duracao_min: 142 },
  { id: 4, titulo: "Filme D (sem duração)", data_sugestao: "2026-09-03", nota_imdb: 6.1, duracao_min: null },
  { id: 5, titulo: "Filme E", data_sugestao: "2026-09-06", nota_imdb: 8.9, duracao_min: 80 },
  { id: 6, titulo: "Filme F (sem nota e sem duração)", data_sugestao: "2026-08-28", nota_imdb: null, duracao_min: null },
];

/**
 * Ordena uma lista de filmes por um critério.
 *
 * Critérios aceitos:
 *  - "recente": mais recente primeiro (por data_sugestao)
 *  - "nota": maior nota do IMDb primeiro
 *  - "duracao": menor duração primeiro
 *
 * Em "nota" e "duracao", filme sem o valor (null/undefined) vai para o fim
 * da lista, nunca para o começo. Não modifica o array recebido.
 */
function ordenarLista(filmes, criterio) {
  const lista = [...filmes];

  switch (criterio) {
    case "recente":
      lista.sort((a, b) => new Date(b.data_sugestao) - new Date(a.data_sugestao));
      break;

    case "nota":
      lista.sort((a, b) => {
        const notaA = a.nota_imdb;
        const notaB = b.nota_imdb;
        if (notaA == null && notaB == null) return 0;
        if (notaA == null) return 1;
        if (notaB == null) return -1;
        return notaB - notaA;
      });
      break;

    case "duracao":
      lista.sort((a, b) => {
        const duracaoA = a.duracao_min;
        const duracaoB = b.duracao_min;
        if (duracaoA == null && duracaoB == null) return 0;
        if (duracaoA == null) return 1;
        if (duracaoB == null) return -1;
        return duracaoA - duracaoB;
      });
      break;

    default:
      break;
  }

  return lista;
}

// Estado da lista "atual" (o que estaria na tela depois de aplicar os
// filtros). Enquanto não existem filtros, é só a lista de exemplo inteira.
let filmesAtuais = FILMES_EXEMPLO;

function renderLista(filmes) {
  const container = document.getElementById("lista");
  if (!container) return;

  container.innerHTML = "";
  for (const filme of filmes) {
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <h3>${filme.titulo}</h3>
      <p>Sugerido em: ${filme.data_sugestao}</p>
      <p>Nota IMDb: ${filme.nota_imdb ?? "—"}</p>
      <p>Duração: ${filme.duracao_min != null ? filme.duracao_min + " min" : "—"}</p>
    `;
    container.appendChild(card);
  }
}

function aplicarOrdenacao() {
  const select = document.getElementById("ordenacao");
  const criterio = select ? select.value : "recente";
  renderLista(ordenarLista(filmesAtuais, criterio));
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("ordenacao");
    if (select) select.addEventListener("change", aplicarOrdenacao);
    aplicarOrdenacao();
  });
}

// Exporta a função pura para poder testar sem navegador (ex.: node).
if (typeof module !== "undefined" && module.exports) {
  module.exports = { ordenarLista, FILMES_EXEMPLO };
}
