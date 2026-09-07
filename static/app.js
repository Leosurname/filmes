(() => {
  const listaQueroVer = document.getElementById("lista-quero-ver");
  const listaAssistidos = document.getElementById("lista-assistidos");
  const vazioQueroVer = document.getElementById("vazio-quero-ver");
  const vazioAssistidos = document.getElementById("vazio-assistidos");
  const toast = document.getElementById("toast");

  let toastTimeoutId = null;

  async function carregarFilmes() {
    const [queroVer, assistidos] = await Promise.all([
      buscarFilmes("quero_ver"),
      buscarFilmes("assistido"),
    ]);

    renderizarLista(listaQueroVer, vazioQueroVer, queroVer, criarCardQueroVer);
    renderizarLista(listaAssistidos, vazioAssistidos, assistidos, criarCardAssistido);
  }

  async function buscarFilmes(status) {
    const resposta = await fetch(`/api/filmes?status=${encodeURIComponent(status)}`);
    if (!resposta.ok) {
      throw new Error(`Falha ao buscar filmes (${status}): ${resposta.status}`);
    }
    return resposta.json();
  }

  function renderizarLista(container, mensagemVazia, filmes, criarCard) {
    container.innerHTML = "";
    if (filmes.length === 0) {
      mensagemVazia.hidden = false;
      return;
    }
    mensagemVazia.hidden = true;
    for (const filme of filmes) {
      container.appendChild(criarCard(filme));
    }
  }

  function criarCardQueroVer(filme) {
    const card = document.createElement("article");
    card.className = "card-filme";
    card.dataset.id = filme.id;

    card.innerHTML = `
      <h3>${escapeHtml(filme.titulo)}</h3>
      <p class="meta">${metaFilme(filme)}</p>
      <button type="button" class="botao-assistido">Marcar como assistido</button>
    `;

    card.querySelector(".botao-assistido").addEventListener("click", () => {
      marcarComoAssistido(filme);
    });

    return card;
  }

  function criarCardAssistido(filme) {
    const card = document.createElement("article");
    card.className = "card-filme";
    card.dataset.id = filme.id;

    card.innerHTML = `
      <h3>${escapeHtml(filme.titulo)}</h3>
      <p class="meta">${metaFilme(filme)}</p>
      <p class="data-assistido">Assistido em ${formatarData(filme.data_assistido)}</p>
      <button type="button" class="botao-desfazer">Desfazer</button>
    `;

    card.querySelector(".botao-desfazer").addEventListener("click", () => {
      voltarParaQueroVer(filme.id);
    });

    return card;
  }

  async function marcarComoAssistido(filme) {
    try {
      await atualizarStatus(filme.id, "assistido");
      await carregarFilmes();
      mostrarToast(`"${filme.titulo}" marcado como assistido.`, async () => {
        await voltarParaQueroVer(filme.id);
      });
    } catch (erro) {
      console.error(erro);
      alert("Não foi possível marcar o filme como assistido. Tente novamente.");
    }
  }

  async function voltarParaQueroVer(filmeId) {
    try {
      await atualizarStatus(filmeId, "quero_ver");
      esconderToast();
      await carregarFilmes();
    } catch (erro) {
      console.error(erro);
      alert("Não foi possível desfazer. Tente novamente.");
    }
  }

  async function atualizarStatus(filmeId, status) {
    const resposta = await fetch(`/api/filmes/${filmeId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!resposta.ok) {
      throw new Error(`Falha ao atualizar status: ${resposta.status}`);
    }
    return resposta.json();
  }

  function mostrarToast(mensagem, aoDesfazer) {
    clearTimeout(toastTimeoutId);
    toast.innerHTML = "";

    const texto = document.createElement("span");
    texto.textContent = mensagem;

    const botao = document.createElement("button");
    botao.type = "button";
    botao.textContent = "Desfazer";
    botao.addEventListener("click", aoDesfazer);

    toast.appendChild(texto);
    toast.appendChild(botao);
    toast.hidden = false;

    toastTimeoutId = setTimeout(esconderToast, 6000);
  }

  function esconderToast() {
    clearTimeout(toastTimeoutId);
    toast.hidden = true;
  }

  function metaFilme(filme) {
    const partes = [];
    if (filme.ano) partes.push(filme.ano);
    if (filme.duracao_min) partes.push(`${filme.duracao_min} min`);
    if (filme.generos) partes.push(filme.generos);
    return partes.join(" · ") || "Sem detalhes adicionais";
  }

  function formatarData(isoString) {
    if (!isoString) return "data desconhecida";
    const data = new Date(isoString);
    if (Number.isNaN(data.getTime())) return "data desconhecida";
    return data.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  function escapeHtml(texto) {
    const div = document.createElement("div");
    div.textContent = texto ?? "";
    return div.innerHTML;
  }

  document.addEventListener("DOMContentLoaded", carregarFilmes);
})();
