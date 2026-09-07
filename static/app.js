const selectDuracao = document.getElementById("filtro-duracao");
const lista = document.getElementById("lista-filmes");
const aviso = document.getElementById("aviso-duracao-desconhecida");

function textoDuracao(duracaoMin) {
  return duracaoMin != null ? `${duracaoMin} min` : "duracao desconhecida";
}

async function carregarFilmes() {
  const duracao = selectDuracao.value;
  const params = new URLSearchParams();
  if (duracao) {
    params.set("duracao", duracao);
  }

  const resposta = await fetch(`/api/filmes?${params.toString()}`);
  const dados = await resposta.json();

  lista.innerHTML = "";
  for (const filme of dados.filmes) {
    const desconhecida = filme.duracao_min == null;
    const item = document.createElement("li");
    item.className = "filme-card";
    item.innerHTML = `
      <strong>${filme.titulo}</strong>
      <span class="duracao${desconhecida ? " duracao-desconhecida" : ""}">
        ${textoDuracao(filme.duracao_min)}
      </span>
    `;
    lista.appendChild(item);
  }

  if (duracao && dados.filmes_duracao_desconhecida > 0) {
    aviso.hidden = false;
    aviso.textContent =
      `Mostrando tambem ${dados.filmes_duracao_desconhecida} filme(s) ` +
      "com duracao desconhecida, que nao foram escondidos pelo filtro.";
  } else {
    aviso.hidden = true;
  }
}

selectDuracao.addEventListener("change", carregarFilmes);
carregarFilmes();
