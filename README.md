# Filmes da Família

Lista única de filmes para a casa. Veja o funcionamento completo em `plan.md`.

> O passo a passo completo de instalação (dependências, `.env`, etc.) é
> assunto da issue #23. Esta seção cobre só o que a issue #22 pede: deixar o
> servidor acessível pela rede de casa.

## Rodando na rede de casa

O servidor sobe aceitando conexões de qualquer aparelho da mesma rede Wi-Fi
(celular, tablet, notebook) — não só da máquina onde ele roda.

### Subir o servidor

```bash
./scripts/iniciar-servidor.sh
```

O script sempre entra na pasta do projeto antes de rodar (não importa de onde
foi chamado), garante que o servidor escuta em `0.0.0.0` — em vez de
`127.0.0.1`, que só aceitaria conexões da própria máquina — e imprime o
endereço de acesso ao iniciar.

Por baixo, ele equivale a:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Endereço de acesso pelo celular

1. Descubra o IP da máquina que vai rodar o servidor, na rede local:
   ```bash
   ipconfig getifaddr en0   # Wi-Fi, na maioria dos Macs
   ```
2. No celular (conectado à **mesma rede Wi-Fi**), abra:
   ```
   http://SEU-IP-LOCAL:8000
   ```
   Por exemplo: `http://192.168.3.152:8000`.

O IP pode mudar se o roteador reatribuir o endereço; se isso acontecer,
rode o comando do passo 1 de novo.

**Isso não expõe o serviço na internet** — só funciona para aparelhos dentro
da rede Wi-Fi de casa. Nada de redirecionamento de porta no roteador nem
túneis públicos.

Se o macOS bloquear conexões de entrada (Firewall em
*Ajustes do Sistema → Rede → Firewall*), autorize o Python/uvicorn quando o
sistema perguntar, ou libere a porta 8000 manualmente.

### Banco de dados

O banco é o arquivo `filmes.db`, na raiz do projeto (fora do Git, veja
`.gitignore`). Por ser um arquivo comum em disco — não algo em memória nem em
pasta temporária — ele **sobrevive sozinho a reinícios do servidor**: parar e
subir o processo de novo não apaga nem reseta os dados. O único cuidado é
sempre rodar o servidor a partir da mesma pasta do projeto, o que o
`scripts/iniciar-servidor.sh` já garante.

### Ligar sozinho quando o computador liga?

**Decisão: por enquanto, não.** O servidor sobe manualmente
(`./scripts/iniciar-servidor.sh`), porque o sistema ainda está em construção
(fases F1 a F5 do `plan.md` seguem pendentes) e faz mais sentido controlar
quando ele está no ar enquanto isso.

Para quem já quiser deixá-lo sempre ligado, existe um modelo pronto de
LaunchAgent do macOS em `scripts/exemplo.com.filmes.servidor.plist`. Para
ativar:

```bash
cp scripts/exemplo.com.filmes.servidor.plist ~/Library/LaunchAgents/com.filmes.servidor.plist
# edite o arquivo copiado e troque SEU_USUARIO pelo caminho real do projeto
launchctl load ~/Library/LaunchAgents/com.filmes.servidor.plist
```

Para desligar o autostart:

```bash
launchctl unload ~/Library/LaunchAgents/com.filmes.servidor.plist
```

Essa decisão pode ser revista quando as fases F1–F5 estiverem prontas.
