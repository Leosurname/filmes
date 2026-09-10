// Quem esta usando o aparelho. A API precisa saber de quem e a sugestao.
// Isto e provisorio: a tela de login e o armazenamento definitivo sao as
// issues #26 e #30, e o contrato final da identificacao e a #31.
function nomeDaPessoa() {
  var nome = "";
  try {
    nome = window.localStorage.getItem("filmes:pessoa") || "";
  } catch (e) {
    nome = "";
  }
  if (!nome) {
    nome = (window.prompt("Qual e o seu nome?") || "").trim();
    if (nome) {
      try {
        window.localStorage.setItem("filmes:pessoa", nome);
      } catch (e) {
        // Armazenamento bloqueado: segue so nesta visita.
      }
    }
  }
  return nome;
}

(function () {
  "use strict";

  var form = document.getElementById("form-filme");
  var input = document.getElementById("link-filme");
  var botao = document.getElementById("botao-enviar");
  var mensagem = document.getElementById("mensagem");

  function mostrarMensagem(texto, tipo) {
    mensagem.textContent = texto;
    mensagem.className = "mensagem " + tipo;
    mensagem.hidden = false;
  }

  function limparMensagem() {
    mensagem.hidden = true;
    mensagem.textContent = "";
    mensagem.className = "mensagem";
  }

  function definirCarregando(carregando) {
    botao.disabled = carregando;
    botao.querySelector(".botao-texto").textContent = carregando
      ? "Enviando..."
      : "Adicionar filme";
  }

  form.addEventListener("submit", function (evento) {
    evento.preventDefault();

    var link = input.value.trim();
    if (!link) {
      mostrarMensagem("Cole o link do filme antes de enviar.", "erro");
      return;
    }

    limparMensagem();
    definirCarregando(true);

    fetch("/api/filmes", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Pessoa-Nome": nomeDaPessoa()
      },
      body: JSON.stringify({ url: link })
    })
      .then(function (resposta) {
        if (!resposta.ok) {
          return resposta
            .json()
            .catch(function () {
              return {};
            })
            .then(function (dados) {
              throw new Error(
                (dados && dados.detail) ||
                  "Nao foi possivel adicionar o filme. Tente de novo."
              );
            });
        }
        return resposta.json().catch(function () {
          return {};
        });
      })
      .then(function () {
        input.value = "";
        mostrarMensagem("Filme adicionado a lista!", "sucesso");
        document.dispatchEvent(new CustomEvent("filmes:atualizar"));
      })
      .catch(function (erro) {
        mostrarMensagem(
          erro && erro.message
            ? erro.message
            : "Nao foi possivel adicionar o filme. Tente de novo.",
          "erro"
        );
      })
      .finally(function () {
        definirCarregando(false);
        input.focus();
      });
  });
})();

// --- Lista de filmes em cards ---------------------------------------------

// Busca a lista de filmes na API e desenha os cards na tela.
// Issue #6 — Mostrar a lista de filmes em cards.

const GRID = document.getElementById("filmes-grid");
const MENSAGEM = document.getElementById("filmes-mensagem");

function mostrarMensagemLista(texto) {
  if (!MENSAGEM) return;
  if (!texto) {
    MENSAGEM.hidden = true;
    MENSAGEM.textContent = "";
    return;
  }
  MENSAGEM.hidden = false;
  MENSAGEM.textContent = texto;
}

// Devolve o valor se ele existir e não for uma string vazia; senão null.
// Evita que campos ausentes apareçam como "undefined" ou "null" no card.
function valorOuNulo(valor) {
  if (valor === undefined || valor === null) return null;
  if (typeof valor === "string" && valor.trim() === "") return null;
  return valor;
}

function textoOuVazio(valor, sufixo = "") {
  const v = valorOuNulo(valor);
  return v === null ? "" : `${v}${sufixo}`;
}

function formatarDuracao(minutos) {
  const v = valorOuNulo(minutos);
  if (v === null) return "";
  const min = Number(v);
  if (Number.isNaN(min) || min <= 0) return "";
  const horas = Math.floor(min / 60);
  const resto = min % 60;
  if (horas === 0) return `${resto} min`;
  if (resto === 0) return `${horas}h`;
  return `${horas}h${String(resto).padStart(2, "0")}`;
}

function formatarGeneros(generos) {
  const v = valorOuNulo(generos);
  if (v === null) return "";
  if (Array.isArray(v)) return v.filter(Boolean).join(", ");
  return String(v);
}

// O nome de quem sugeriu pode vir em formatos diferentes dependendo de como
// o back-end monta a resposta (campo direto ou objeto pessoa aninhado).
function nomeSugeriu(filme) {
  const candidatos = [
    filme.pessoa_nome,
    filme.sugerido_por,
    filme.pessoa && filme.pessoa.nome,
  ];
  for (const c of candidatos) {
    const v = valorOuNulo(c);
    if (v !== null) return String(v);
  }
  return "";
}

function criarSpan(texto, className) {
  const span = document.createElement("span");
  if (className) span.className = className;
  span.textContent = texto;
  return span;
}

function criarCard(filme) {
  const card = document.createElement("article");
  card.className = "filme-card";

  const posterUrl = valorOuNulo(filme.poster_url);
  if (posterUrl) {
    const img = document.createElement("img");
    img.className = "filme-card__poster";
    img.src = posterUrl;
    img.alt = valorOuNulo(filme.titulo) ? `Pôster de ${filme.titulo}` : "Pôster do filme";
    img.loading = "lazy";
    // Se a imagem falhar ao carregar, troca por um espaço reservado em vez
    // de quebrar o layout do card.
    img.addEventListener("error", () => {
      const placeholder = document.createElement("div");
      placeholder.className = "filme-card__poster filme-card__poster--vazio";
      placeholder.textContent = "Sem pôster";
      img.replaceWith(placeholder);
    });
    card.appendChild(img);
  } else {
    const placeholder = document.createElement("div");
    placeholder.className = "filme-card__poster filme-card__poster--vazio";
    placeholder.textContent = "Sem pôster";
    card.appendChild(placeholder);
  }

  const corpo = document.createElement("div");
  corpo.className = "filme-card__corpo";

  const titulo = document.createElement("h3");
  titulo.className = "filme-card__titulo";
  titulo.textContent = valorOuNulo(filme.titulo) || "Título não informado";
  corpo.appendChild(titulo);

  const metaPartes = [
    textoOuVazio(filme.ano),
    formatarDuracao(filme.duracao_min),
    textoOuVazio(filme.classificacao),
  ].filter((parte) => parte !== "");

  if (metaPartes.length > 0) {
    const meta = document.createElement("div");
    meta.className = "filme-card__meta";
    metaPartes.forEach((parte) => meta.appendChild(criarSpan(parte)));
    corpo.appendChild(meta);
  }

  const generosTexto = formatarGeneros(filme.generos);
  if (generosTexto) {
    const generos = document.createElement("div");
    generos.className = "filme-card__generos";
    generos.textContent = generosTexto;
    corpo.appendChild(generos);
  }

  const rodape = document.createElement("div");
  rodape.className = "filme-card__rodape";

  const nota = valorOuNulo(filme.nota_imdb);
  if (nota !== null) {
    rodape.appendChild(criarSpan(`IMDb ${nota}`, "filme-card__nota"));
  } else {
    rodape.appendChild(criarSpan("", "filme-card__nota"));
  }

  const sugeriu = nomeSugeriu(filme);
  rodape.appendChild(criarSpan(sugeriu ? `sugerido por ${sugeriu}` : ""));

  corpo.appendChild(rodape);
  card.appendChild(corpo);

  return card;
}

// --- Filtros ---------------------------------------------------------------
//
// Cada filtro e uma funcao que recebe o filme e devolve true/false. Todos os
// filtros ativos sao aplicados juntos, entao eles se combinam. Filme com o
// dado ausente (duracao, nota, genero...) nunca some calado: ele passa pelo
// filtro e a tela avisa quantos estao nessa situacao.

const FILTROS = [];
let semDadoNoUltimoFiltro = 0;

function registrarFiltro(fn) {
  FILTROS.push(fn);
}

function valorDoSelect(id) {
  const el = document.getElementById(id);
  return el ? el.value : "";
}

function dentroDaFaixa(duracao, faixa) {
  if (faixa === "curto") return duracao <= 90;
  if (faixa === "medio") return duracao > 90 && duracao <= 120;
  if (faixa === "longo") return duracao > 120;
  return true;
}

registrarFiltro(function filtroDuracao(filme) {
  const faixa = valorDoSelect("filtro-duracao");
  if (!faixa) return true;
  if (filme.duracao_min == null) {
    semDadoNoUltimoFiltro += 1;
    return true;
  }
  return dentroDaFaixa(filme.duracao_min, faixa);
});

function filtrarLista(filmes) {
  semDadoNoUltimoFiltro = 0;
  return filmes.filter((filme) => FILTROS.every((fn) => fn(filme)));
}

function avisarSobreDadosAusentes() {
  const aviso = document.getElementById("aviso-filtro");
  if (!aviso) return;
  if (semDadoNoUltimoFiltro > 0) {
    aviso.textContent =
      `Mostrando também ${semDadoNoUltimoFiltro} filme(s) sem essa informação, ` +
      "que não foram escondidos pelo filtro.";
    aviso.hidden = false;
  } else {
    aviso.hidden = true;
  }
}

// --- Ordenacao da lista ----------------------------------------------------

// Filme sem nota ou sem duracao vai sempre para o fim, nunca para o comeco.
function ordenarLista(filmes, criterio) {
  const lista = [...filmes];
  const porCampoCrescente = (campo) => (a, b) => {
    const va = a[campo];
    const vb = b[campo];
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    return va - vb;
  };

  switch (criterio) {
    case "nota":
      lista.sort((a, b) => {
        const na = a.nota_imdb;
        const nb = b.nota_imdb;
        if (na == null && nb == null) return 0;
        if (na == null) return 1;
        if (nb == null) return -1;
        return nb - na;
      });
      break;
    case "duracao":
      lista.sort(porCampoCrescente("duracao_min"));
      break;
    case "recente":
    default:
      lista.sort((a, b) => new Date(b.data_sugestao) - new Date(a.data_sugestao));
      break;
  }
  return lista;
}

function criterioAtual() {
  const select = document.getElementById("ordenacao");
  return select ? select.value : "recente";
}

async function carregarFilmes() {
  mostrarMensagemLista("Carregando filmes...");
  try {
    const resposta = await fetch("/api/filmes");
    if (!resposta.ok) {
      throw new Error(`Falha ao buscar filmes (status ${resposta.status})`);
    }
    const filmes = await resposta.json();

    GRID.innerHTML = "";

    if (!Array.isArray(filmes) || filmes.length === 0) {
      mostrarMensagemLista("Nenhum filme na lista ainda.");
      return;
    }

    mostrarMensagemLista(null);
    const fragmento = document.createDocumentFragment();
    const visiveis = ordenarLista(filtrarLista(filmes), criterioAtual());
    avisarSobreDadosAusentes();

    if (visiveis.length === 0) {
      mostrarMensagemLista("Nenhum filme com esses filtros.");
      return;
    }

    visiveis.forEach((filme) => fragmento.appendChild(criarCard(filme)));
    GRID.appendChild(fragmento);
  } catch (erro) {
    console.error("Erro ao carregar filmes:", erro);
    mostrarMensagemLista("Não foi possível carregar os filmes agora.");
  }
}

// Permite que outras partes da página (ex.: o formulário de adicionar filme)
// disparem uma atualização da lista sem recarregar a página inteira.
document.addEventListener("filmes:atualizar", carregarFilmes);

document.addEventListener("DOMContentLoaded", () => {
  ["ordenacao", "filtro-duracao"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("change", carregarFilmes);
    }
  });
  carregarFilmes();
});

// Exposto para reuso/testes manuais.
window.carregarFilmes = carregarFilmes;
