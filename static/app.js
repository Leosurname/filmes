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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url_original: link })
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
