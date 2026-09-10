// --- Identificacao guardada no aparelho ------------------------------------
//
// Depois de entrar uma vez, o aparelho guarda quem e a pessoa e nao pergunta
// mais. O que fica guardado e o id e o nome, no armazenamento local do proprio
// site: nao e cookie, entao nao vai junto nos pedidos nem serve para rastrear
// ninguem fora daqui.
//
// Nao existe prazo de validade. Fechar a aba, fechar o navegador ou reiniciar o
// celular nao apagam nada. So some se a pessoa limpar os dados do navegador,
// que e o caso tratado na issue #33.
//
// Quando o armazenamento esta bloqueado (aba anonima em alguns navegadores,
// configuracao restritiva), nada disso funciona. Nesse caso a pagina avisa em
// vez de quebrar, e a identificacao vale so enquanto a aba estiver aberta.

const CHAVE_PESSOA = "filmes:pessoa";

// Guarda a pessoa desta visita quando o armazenamento nao esta disponivel.
let pessoaSoNestaVisita = null;
let armazenamentoBloqueado = false;

function armazenamentoDisponivel() {
  try {
    const teste = "filmes:teste";
    window.localStorage.setItem(teste, "1");
    window.localStorage.removeItem(teste);
    return true;
  } catch (e) {
    return false;
  }
}

function pessoaValida(pessoa) {
  return Boolean(pessoa) && typeof pessoa.id === "number" && Boolean(pessoa.nome);
}

function pessoaGuardada() {
  if (pessoaSoNestaVisita) return pessoaSoNestaVisita;
  try {
    const bruto = window.localStorage.getItem(CHAVE_PESSOA);
    if (!bruto) return null;
    const pessoa = JSON.parse(bruto);
    // Guardado corrompido ou de uma versao antiga: trata como se nao houvesse.
    return pessoaValida(pessoa) ? pessoa : null;
  } catch (e) {
    return null;
  }
}

function guardarPessoa(pessoa) {
  pessoaSoNestaVisita = pessoa;
  try {
    window.localStorage.setItem(CHAVE_PESSOA, JSON.stringify(pessoa));
    armazenamentoBloqueado = false;
  } catch (e) {
    armazenamentoBloqueado = true;
  }
}

function esquecerPessoa() {
  pessoaSoNestaVisita = null;
  try {
    window.localStorage.removeItem(CHAVE_PESSOA);
  } catch (e) {
    // Nada a fazer: ja nao havia o que apagar.
  }
}

function avisarSeArmazenamentoBloqueado() {
  const aviso = document.getElementById("aviso-armazenamento");
  if (!aviso) return;
  const bloqueado = armazenamentoBloqueado || !armazenamentoDisponivel();
  if (bloqueado) {
    aviso.textContent =
      "Este navegador não está deixando guardar dados, então vamos perguntar " +
      "o seu nome de novo na próxima visita.";
    aviso.hidden = false;
  } else {
    aviso.hidden = true;
  }
}

async function entrarComNome(nome) {
  const resposta = await fetch("/api/entrar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome })
  });
  if (!resposta.ok) {
    throw new Error("Não foi possível entrar.");
  }
  const pessoa = await resposta.json();
  guardarPessoa(pessoa);
  avisarSeArmazenamentoBloqueado();
  return pessoa;
}

// Cabecalhos de identificacao para os pedidos que criam ou alteram algo.
function cabecalhosDeIdentificacao() {
  const pessoa = pessoaGuardada();
  return pessoa ? { "X-Pessoa-Id": String(pessoa.id) } : {};
}

// Se a API recusar a identificacao (401), o aparelho esqueceu ou a pessoa foi
// removida do banco. Em vez de deixar a pessoa presa num erro, voltamos para a
// tela de entrada: digitar o mesmo nome recupera a mesma pessoa e o historico.
function tratarIdentificacaoRecusada(resposta) {
  if (resposta && resposta.status === 401) {
    esquecerPessoa();
    mostrarTelaEntrada();
    return true;
  }
  return false;
}

// --- Tela de entrada -------------------------------------------------------
//
// Na primeira visita a pessoa digita o proprio nome e entra. Nao existe lista
// de nomes da casa para escolher: cada um digita o seu. Da segunda visita em
// diante a pergunta nao aparece mais, porque o aparelho ja sabe quem e (#30).

function mostrarTelaEntrada() {
  const entrada = document.getElementById("tela-entrada");
  const pagina = document.getElementById("pagina");
  if (entrada) entrada.hidden = false;
  if (pagina) pagina.hidden = true;
  const campo = document.getElementById("nome-pessoa");
  if (campo) campo.focus();
}

function mostrarLista(pessoa) {
  const entrada = document.getElementById("tela-entrada");
  const pagina = document.getElementById("pagina");
  if (entrada) entrada.hidden = true;
  if (pagina) pagina.hidden = false;

  const nome = document.getElementById("nome-de-quem-usa");
  if (nome) nome.textContent = pessoa.nome;

  avisarSeArmazenamentoBloqueado();
  document.dispatchEvent(new CustomEvent("filmes:atualizar"));
}

function ligarFormularioDeEntrada() {
  const form = document.getElementById("form-entrada");
  if (!form) return;

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const campo = document.getElementById("nome-pessoa");
    const erro = document.getElementById("erro-entrada");
    const nome = (campo ? campo.value : "").trim();

    if (erro) erro.hidden = true;
    if (!nome) {
      if (erro) {
        erro.textContent = "Digite o seu nome para entrar.";
        erro.hidden = false;
      }
      return;
    }

    try {
      const pessoa = await entrarComNome(nome);
      mostrarLista(pessoa);
    } catch (e) {
      if (erro) {
        erro.textContent = "Não foi possível entrar agora. Tente de novo.";
        erro.hidden = false;
      }
    }
  });
}

// Quem digitou o nome errado na primeira visita ficaria preso a ele, porque a
// tela de entrada nao volta a aparecer. Esta correcao renomeia a pessoa que ja
// existe: os filmes dela continuam com ela, e a tela de entrada nao reaparece.
async function corrigirNome() {
  const pessoa = pessoaGuardada();
  if (!pessoa) return;

  const novo = (window.prompt("Como o seu nome deve aparecer?", pessoa.nome) || "").trim();
  if (!novo || novo === pessoa.nome) return;

  try {
    const resposta = await fetch("/api/pessoa", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...cabecalhosDeIdentificacao()
      },
      body: JSON.stringify({ nome: novo })
    });

    if (resposta.status === 409) {
      const dados = await resposta.json().catch(() => ({}));
      window.alert(dados.detail || "Esse nome já é de outra pessoa da casa.");
      return;
    }
    if (tratarIdentificacaoRecusada(resposta)) return;
    if (!resposta.ok) throw new Error("falhou");

    const atualizada = await resposta.json();
    guardarPessoa(atualizada);
    const rotulo = document.getElementById("nome-de-quem-usa");
    if (rotulo) rotulo.textContent = atualizada.nome;
    document.dispatchEvent(new CustomEvent("filmes:atualizar"));
  } catch (e) {
    window.alert("Não foi possível corrigir o nome agora.");
  }
}

function ligarCorrecaoDeNome() {
  const botao = document.getElementById("botao-corrigir-nome");
  if (botao) botao.addEventListener("click", corrigirNome);
}

function iniciarSessao() {
  ligarFormularioDeEntrada();
  ligarCorrecaoDeNome();
  const pessoa = pessoaGuardada();
  if (pessoa) {
    mostrarLista(pessoa);
  } else {
    mostrarTelaEntrada();
  }
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
        ...cabecalhosDeIdentificacao()
      },
      body: JSON.stringify({ url: link })
    })
      .then(function (resposta) {
        if (typeof tratarIdentificacaoRecusada === "function" && tratarIdentificacaoRecusada(resposta)) {
          throw new Error("Entre com o seu nome de novo.");
        }
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

function textoServicos(filme) {
  const nomes = provedoresDoFilme(filme);
  return nomes.length ? nomes.join(", ") : "Não disponível nos serviços conhecidos";
}

// A nota da familia e a do IMDb aparecem separadas e rotuladas, para nao
// virarem um numero solto que ninguem sabe de onde veio.
function textoNotas(filme) {
  const partes = [];
  if (filme.nota_imdb != null) partes.push(`IMDb ${filme.nota_imdb}`);
  if (filme.nota_familia != null) partes.push(`Família ${filme.nota_familia}`);
  return partes.join(" · ");
}

// Apagar pede confirmacao: nao da para perder um filme com um clique so.
async function removerFilme(filme) {
  const nome = filme.titulo || "esse filme";
  if (!window.confirm(`Tirar ${nome} da lista? Isso não dá para desfazer.`)) {
    return;
  }
  try {
    const resposta = await fetch(`/api/filmes/${filme.id}`, { method: "DELETE" });
    if (!resposta.ok && resposta.status !== 204) {
      throw new Error(`status ${resposta.status}`);
    }
    document.dispatchEvent(new CustomEvent("filmes:atualizar"));
  } catch (erro) {
    console.error("Erro ao remover filme:", erro);
    mostrarMensagemLista("Não foi possível remover o filme agora.");
  }
}

function criarBotaoRemover(filme) {
  const botao = document.createElement("button");
  botao.type = "button";
  botao.className = "botao-remover";
  botao.textContent = "Tirar da lista";
  botao.addEventListener("click", () => removerFilme(filme));
  return botao;
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
    textoNotas(filme),
    `Sugerido por ${nomeDeQuemSugeriu(filme)}${
      filme.data_sugestao ? ` em ${filme.data_sugestao}` : ""
    }`,
    textoServicos(filme),
    // Na visão de assistidos, a data de quando foi assistido entra no card.
    filme.status === "assistido" && filme.data_assistido
      ? `Assistido em ${filme.data_assistido}`
      : "",
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

// Ordenacao extra: pela nota que a familia deu.
function ordenarPorNotaFamilia(lista) {
  return [...lista].sort((a, b) => {
    const na = a.nota_familia;
    const nb = b.nota_familia;
    if (na == null && nb == null) return 0;
    if (na == null) return 1;
    if (nb == null) return -1;
    return nb - na;
  });
}

// Duas visoes: "quero ver" (padrao) e "ja assistimos". Os filtros valem nas
// duas, porque a visao entra como mais um filtro na mesma camada.
function visaoAtual() {
  const marcado = document.querySelector('input[name="visao"]:checked');
  return marcado ? marcado.value : "quero_ver";
}

registrarFiltro(function filtroVisao(filme) {
  return (filme.status || "quero_ver") === visaoAtual();
});

registrarFiltro(function filtroDuracao(filme) {
  const faixa = valorDoSelect("filtro-duracao");
  if (!faixa) return true;
  if (filme.duracao_min == null) {
    semDadoNoUltimoFiltro += 1;
    return true;
  }
  return dentroDaFaixa(filme.duracao_min, faixa);
});

function generosDoFilme(filme) {
  if (!filme.generos) return [];
  return String(filme.generos)
    .split(",")
    .map((g) => g.trim())
    .filter(Boolean);
}

registrarFiltro(function filtroTema(filme) {
  const tema = valorDoSelect("filtro-tema");
  if (!tema) return true;
  const generos = generosDoFilme(filme);
  if (generos.length === 0) {
    semDadoNoUltimoFiltro += 1;
    return true;
  }
  // Filme com varios generos aparece em todos eles.
  return generos.some((g) => g.toLowerCase() === tema.toLowerCase());
});

// A lista de temas vem dos filmes que existem no banco: nao adianta oferecer
// um genero que ninguem sugeriu.
function preencherTemas(filmes) {
  const select = document.getElementById("filtro-tema");
  if (!select) return;
  const atual = select.value;
  const temas = new Set();
  filmes.forEach((filme) => generosDoFilme(filme).forEach((g) => temas.add(g)));

  select.innerHTML = "";
  const vazio = document.createElement("option");
  vazio.value = "";
  vazio.textContent = "Qualquer tema";
  select.appendChild(vazio);

  [...temas].sort((a, b) => a.localeCompare(b, "pt-BR")).forEach((tema) => {
    const opcao = document.createElement("option");
    opcao.value = tema;
    opcao.textContent = tema;
    select.appendChild(opcao);
  });

  if (atual && temas.has(atual)) {
    select.value = atual;
  }
}

// Ordem das classificacoes, da mais leve para a mais pesada. Comparar como
// texto daria errado: "10" viria depois de "12".
const ORDEM_CLASSIFICACAO = ["L", "10", "12", "14", "16", "18"];

registrarFiltro(function filtroClassificacao(filme) {
  const teto = valorDoSelect("filtro-classificacao");
  if (!teto) return true;
  const valor = filme.classificacao;
  const indice = ORDEM_CLASSIFICACAO.indexOf(valor);
  if (!valor || indice === -1) {
    semDadoNoUltimoFiltro += 1;
    return true;
  }
  // "ate 12 anos" traz tudo que e igual ou mais leve.
  return indice <= ORDEM_CLASSIFICACAO.indexOf(teto);
});

// O campo `provedores` chega como texto JSON com tres listas: assinatura,
// aluguel e compra. Para filtrar e exibir, interessa o conjunto de nomes.
function provedoresDoFilme(filme) {
  const bruto = filme.provedores;
  if (!bruto) return [];
  let dados = bruto;
  if (typeof bruto === "string") {
    try {
      dados = JSON.parse(bruto);
    } catch (e) {
      return [];
    }
  }
  if (Array.isArray(dados)) return dados.filter(Boolean);
  if (typeof dados !== "object") return [];

  const nomes = new Set();
  ["assinatura", "aluguel", "compra"].forEach((categoria) => {
    (dados[categoria] || []).forEach((nome) => nome && nomes.add(nome));
  });
  return [...nomes];
}

registrarFiltro(function filtroServico(filme) {
  const servico = valorDoSelect("filtro-servico");
  if (!servico) return true;
  const nomes = provedoresDoFilme(filme);
  if (nomes.length === 0) {
    semDadoNoUltimoFiltro += 1;
    return true;
  }
  return nomes.some((n) => n.toLowerCase() === servico.toLowerCase());
});

function preencherServicos(filmes) {
  const select = document.getElementById("filtro-servico");
  if (!select) return;
  const atual = select.value;
  const servicos = new Set();
  filmes.forEach((filme) => provedoresDoFilme(filme).forEach((n) => servicos.add(n)));

  select.innerHTML = "";
  const vazio = document.createElement("option");
  vazio.value = "";
  vazio.textContent = "Qualquer serviço";
  select.appendChild(vazio);
  [...servicos].sort((a, b) => a.localeCompare(b, "pt-BR")).forEach((nome) => {
    const o = document.createElement("option");
    o.value = nome;
    o.textContent = nome;
    select.appendChild(o);
  });
  if (atual && servicos.has(atual)) select.value = atual;
}

function nomeDeQuemSugeriu(filme) {
  // Filme antigo, sem pessoa vinculada, nao pode quebrar a tela.
  return filme.sugerido_por || "alguém da casa";
}

registrarFiltro(function filtroPessoa(filme) {
  const escolha = valorDoSelect("filtro-pessoa");
  if (!escolha) return true;
  if (escolha === "__minhas__") {
    const eu = pessoaGuardada();
    return Boolean(eu) && filme.pessoa_id === eu.id;
  }
  return nomeDeQuemSugeriu(filme) === escolha;
});

function preencherPessoas(filmes) {
  const select = document.getElementById("filtro-pessoa");
  if (!select) return;
  const atual = select.value;
  const nomes = new Set();
  filmes.forEach((filme) => {
    if (filme.sugerido_por) nomes.add(filme.sugerido_por);
  });

  select.innerHTML = "";
  const todos = document.createElement("option");
  todos.value = "";
  todos.textContent = "Qualquer pessoa";
  select.appendChild(todos);

  const minhas = document.createElement("option");
  minhas.value = "__minhas__";
  minhas.textContent = "Só as minhas";
  select.appendChild(minhas);

  [...nomes].sort((a, b) => a.localeCompare(b, "pt-BR")).forEach((nome) => {
    const o = document.createElement("option");
    o.value = nome;
    o.textContent = nome;
    select.appendChild(o);
  });

  const valores = ["", "__minhas__", ...nomes];
  if (atual && valores.includes(atual)) select.value = atual;
}

registrarFiltro(function filtroNotaMinima(filme) {
  const minima = parseFloat(valorDoSelect("filtro-nota"));
  if (!minima) return true;
  if (filme.nota_imdb == null) {
    // Filme sem nota conhecida nao some calado: passa e a tela avisa.
    semDadoNoUltimoFiltro += 1;
    return true;
  }
  return filme.nota_imdb >= minima;
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
    preencherTemas(filmes);
    preencherServicos(filmes);
    preencherPessoas(filmes);
    const visiveis = ordenarLista(filtrarLista(filmes), criterioAtual());
    avisarSobreDadosAusentes();

    if (visiveis.length === 0) {
      mostrarMensagemLista(
        visaoAtual() === "assistido"
          ? "Nenhum filme assistido ainda."
          : "Nenhum filme com esses filtros."
      );
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
  document.querySelectorAll('input[name="visao"]').forEach((el) => {
    el.addEventListener("change", carregarFilmes);
  });
  iniciarSessao();
  ["ordenacao", "filtro-duracao", "filtro-tema", "filtro-classificacao", "filtro-servico", "filtro-pessoa", "filtro-nota"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("change", carregarFilmes);
    }
  });
  carregarFilmes();
});

// Exposto para reuso/testes manuais.
window.carregarFilmes = carregarFilmes;
