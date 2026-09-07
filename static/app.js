const selectClassificacao = document.getElementById("filtro-classificacao");
const listaFilmes = document.getElementById("lista-filmes");

async function carregarOpcoesDeClassificacao() {
  const resposta = await fetch("/api/classificacoes");
  const opcoes = await resposta.json();
  for (const opcao of opcoes) {
    const item = document.createElement("option");
    item.value = opcao.valor;
    item.textContent = `Ate ${opcao.rotulo}`;
    selectClassificacao.appendChild(item);
  }
}

async function carregarFilmes() {
  const classificacaoMax = selectClassificacao.value;
  const url = classificacaoMax
    ? `/api/filmes?classificacao_max=${encodeURIComponent(classificacaoMax)}`
    : "/api/filmes";

  const resposta = await fetch(url);
  const filmes = await resposta.json();

  listaFilmes.innerHTML = "";
  for (const filme of filmes) {
    const item = document.createElement("li");

    const titulo = document.createElement("span");
    titulo.textContent = `${filme.titulo} (${filme.ano ?? "?"})`;

    const classificacao = document.createElement("span");
    classificacao.textContent = filme.classificacao_rotulo;
    classificacao.className = "classificacao";
    if (filme.classificacao === null) {
      classificacao.classList.add("nao-informada");
    }

    item.appendChild(titulo);
    item.appendChild(classificacao);
    listaFilmes.appendChild(item);
  }
}

selectClassificacao.addEventListener("change", carregarFilmes);

carregarOpcoesDeClassificacao().then(carregarFilmes);
