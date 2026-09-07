const temasAtivos = new Set();

async function carregarTemas() {
  const resp = await fetch("/api/generos");
  const temas = await resp.json();
  const container = document.getElementById("filtro-temas");
  container.innerHTML = "";

  if (temas.length === 0) {
    container.innerHTML = "<p class=\"vazio\">Ainda nao ha temas cadastrados.</p>";
    return;
  }

  temas.forEach((tema) => {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "tag";
    botao.textContent = tema;
    botao.dataset.tema = tema;
    botao.addEventListener("click", () => {
      if (temasAtivos.has(tema)) {
        temasAtivos.delete(tema);
        botao.classList.remove("ativo");
      } else {
        temasAtivos.add(tema);
        botao.classList.add("ativo");
      }
      carregarFilmes();
    });
    container.appendChild(botao);
  });
}

async function carregarFilmes() {
  const params = new URLSearchParams();
  temasAtivos.forEach((tema) => params.append("genero", tema));

  const resp = await fetch(`/api/filmes?${params.toString()}`);
  const filmes = await resp.json();

  const lista = document.getElementById("lista-filmes");
  const vazio = document.getElementById("vazio");
  lista.innerHTML = "";

  if (filmes.length === 0) {
    vazio.hidden = false;
    return;
  }
  vazio.hidden = true;

  filmes.forEach((filme) => {
    const li = document.createElement("li");
    li.className = "filme-card";
    li.innerHTML = `
      <h3>${filme.titulo}</h3>
      <p class="generos">${filme.generos.join(", ")}</p>
    `;
    lista.appendChild(li);
  });
}

carregarTemas();
carregarFilmes();
