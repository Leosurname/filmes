const listaEl = document.getElementById("lista-filmes");
const listaVaziaEl = document.getElementById("lista-vazia");
const abaBtns = document.querySelectorAll(".aba-btn");

const modal = document.getElementById("modal-confirmar");
const modalTitulo = document.getElementById("modal-titulo");
const modalCancelar = document.getElementById("modal-cancelar");
const modalConfirmarBtn = document.getElementById("modal-confirmar-btn");

let abaAtual = "quero_ver";
let filmeParaRemover = null;

async function carregarFilmes() {
  const resposta = await fetch(`/api/filmes?status=${encodeURIComponent(abaAtual)}`);
  const filmes = await resposta.json();
  renderizarFilmes(filmes);
}

function renderizarFilmes(filmes) {
  listaEl.innerHTML = "";
  listaVaziaEl.hidden = filmes.length > 0;

  for (const filme of filmes) {
    const li = document.createElement("li");
    li.className = "filme-card";

    const titulo = document.createElement("span");
    titulo.className = "filme-titulo";
    titulo.textContent = filme.titulo;

    const btnRemover = document.createElement("button");
    btnRemover.className = "btn btn-remover";
    btnRemover.textContent = "Remover";
    btnRemover.addEventListener("click", () => abrirConfirmacao(filme));

    li.appendChild(titulo);
    li.appendChild(btnRemover);
    listaEl.appendChild(li);
  }
}

function abrirConfirmacao(filme) {
  filmeParaRemover = filme;
  modalTitulo.textContent = filme.titulo;
  modal.hidden = false;
}

function fecharConfirmacao() {
  filmeParaRemover = null;
  modal.hidden = true;
}

async function confirmarRemocao() {
  if (!filmeParaRemover) return;
  const id = filmeParaRemover.id;
  fecharConfirmacao();

  const resposta = await fetch(`/api/filmes/${id}`, { method: "DELETE" });
  if (!resposta.ok) {
    alert("Nao foi possivel remover o filme. Tente novamente.");
    return;
  }
  await carregarFilmes();
}

modalCancelar.addEventListener("click", fecharConfirmacao);
modalConfirmarBtn.addEventListener("click", confirmarRemocao);
modal.addEventListener("click", (evento) => {
  if (evento.target === modal) fecharConfirmacao();
});

for (const btn of abaBtns) {
  btn.addEventListener("click", () => {
    abaAtual = btn.dataset.status;
    for (const b of abaBtns) b.classList.toggle("ativa", b === btn);
    carregarFilmes();
  });
}

abaBtns[0].classList.add("ativa");
carregarFilmes();
