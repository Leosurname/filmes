const form = document.getElementById("form-novo-filme");
const input = document.getElementById("input-url");
const mensagem = document.getElementById("mensagem");
const lista = document.getElementById("lista-filmes");

function mostrarMensagem(texto, tipo = "aviso") {
  mensagem.textContent = texto;
  mensagem.hidden = false;
  mensagem.className = tipo === "erro" ? "erro" : "";
}

function esconderMensagem() {
  mensagem.hidden = true;
}

async function carregarFilmes() {
  try {
    const resposta = await fetch("/api/filmes");
    if (!resposta.ok) {
      throw new Error("Falha ao carregar a lista.");
    }
    const filmes = await resposta.json();
    renderizarLista(filmes);
  } catch (erro) {
    // A página nunca deve travar por causa de um erro de rede.
    mostrarMensagem(
      "Não foi possível carregar a lista agora. Tente recarregar a página.",
      "erro"
    );
  }
}

function renderizarLista(filmes) {
  lista.innerHTML = "";
  for (const filme of filmes) {
    lista.appendChild(criarCard(filme));
  }
}

function criarCard(filme) {
  const li = document.createElement("li");
  li.className = "card";

  const titulo = document.createElement("strong");
  titulo.textContent = filme.titulo || "(sem título ainda)";
  li.appendChild(titulo);

  const url = document.createElement("div");
  url.className = "url";
  url.textContent = filme.url_original;
  li.appendChild(url);

  if (filme.metadados_incompletos) {
    const aviso = document.createElement("div");
    aviso.className = "aviso";
    aviso.textContent =
      filme.aviso_metadados ||
      "Não foi possível buscar os dados desse filme. Complete manualmente abaixo.";
    li.appendChild(aviso);
    li.appendChild(criarFormularioCompletar(filme));
  }

  return li;
}

function criarFormularioCompletar(filme) {
  const form = document.createElement("form");
  form.className = "completar";

  const campos = [
    { nome: "titulo", label: "Título" },
    { nome: "ano", label: "Ano" },
    { nome: "duracao_min", label: "Duração (min)" },
    { nome: "generos", label: "Gêneros" },
    { nome: "classificacao", label: "Classificação" },
  ];

  for (const campo of campos) {
    const input = document.createElement("input");
    input.name = campo.nome;
    input.placeholder = campo.label;
    form.appendChild(input);
  }

  const botao = document.createElement("button");
  botao.type = "submit";
  botao.textContent = "Salvar dados";
  form.appendChild(botao);

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(form).entries());
    const payload = {};
    for (const [chave, valor] of Object.entries(dados)) {
      if (valor.trim() === "") continue;
      payload[chave] = ["ano", "duracao_min"].includes(chave)
        ? Number(valor)
        : valor;
    }

    try {
      const resposta = await fetch(`/api/filmes/${filme.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resposta.ok) {
        throw new Error("Falha ao salvar.");
      }
      esconderMensagem();
      await carregarFilmes();
    } catch (erro) {
      mostrarMensagem("Não foi possível salvar os dados agora. Tente de novo.", "erro");
    }
  });

  return form;
}

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const url = input.value.trim();
  if (!url) return;

  try {
    const resposta = await fetch("/api/filmes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      mostrarMensagem(
        erro.detail || "Não foi possível salvar esse link.",
        "erro"
      );
      return;
    }

    const filme = await resposta.json();
    input.value = "";

    if (filme.metadados_incompletos) {
      mostrarMensagem(
        filme.aviso_metadados ||
          "O filme foi salvo, mas não encontramos os dados automaticamente."
      );
    } else {
      esconderMensagem();
    }

    await carregarFilmes();
  } catch (erro) {
    // API fora do ar ou sem rede: a página continua funcionando.
    mostrarMensagem(
      "Não foi possível falar com o servidor agora. Tente novamente em instantes.",
      "erro"
    );
  }
});

carregarFilmes();
