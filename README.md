# API de Tarefas — Projeto de Cloud Security

API REST básica em **Python (FastAPI)** com banco **SQLite**, hospedada em uma **VM Linux na nuvem (Azure)** atrás de **Nginx**, com autenticação por **API Key**.

## Arquitetura

```
Cliente (navegador/curl)
        │  HTTP :80
        ▼
 [ NSG / Firewall Azure ]  → libera 22 (SSH) e 80 (HTTP)
        ▼
 VM Ubuntu 22.04 (Standard_B1s)
   ├─ Nginx (proxy reverso, :80)
   ├─ Uvicorn + FastAPI (127.0.0.1:8000, serviço systemd)
   └─ SQLite (/var/lib/api-tarefas/tarefas.db, no disco gerenciado)
```

## Endpoints

| Método | Rota             | Auth | Descrição            |
|--------|------------------|------|----------------------|
| GET    | `/`              | não  | Status do serviço    |
| GET    | `/saude`         | não  | Health check         |
| GET    | `/docs`          | não  | Swagger (OpenAPI)    |
| GET    | `/tarefas`       | sim  | Lista tarefas        |
| GET    | `/tarefas/{id}`  | sim  | Busca uma tarefa     |
| POST   | `/tarefas`       | sim  | Cria tarefa          |
| PUT    | `/tarefas/{id}`  | sim  | Atualiza tarefa      |
| DELETE | `/tarefas/{id}`  | sim  | Remove tarefa        |

Autenticação: cabeçalho `X-API-Key: <sua chave>`.

## Rodar localmente

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_KEY="minha-chave-local"
uvicorn app.main:app --reload
# abra http://127.0.0.1:8000/docs
```

Testes: `pytest -q`

## Exemplos de uso

```bash
curl http://<IP_PUBLICO>/saude

curl -X POST http://<IP_PUBLICO>/tarefas \
  -H "X-API-Key: <CHAVE>" -H "Content-Type: application/json" \
  -d '{"titulo":"Entregar projeto de cloud security"}'

curl -H "X-API-Key: <CHAVE>" http://<IP_PUBLICO>/tarefas
```

## Deploy na nuvem (resumo)

Passo a passo completo em [`docs/DEPLOY.md`](docs/DEPLOY.md). Em resumo:

1. Criar a VM Ubuntu 22.04 `Standard_B1s` no Azure e abrir a porta 80 no NSG.
2. Conectar por SSH.
3. Rodar `bash deploy/setup-vm.sh <URL_DO_REPO>`.
4. Acessar `http://<IP_PUBLICO>/docs`.

## Controles de segurança aplicados

- API Key comparada com `secrets.compare_digest` (evita timing attack).
- Chave fora do código: arquivo `/etc/api-tarefas.env` com permissão `600`.
- Consultas SQL parametrizadas (prevenção de SQL Injection).
- Validação de entrada com Pydantic (tamanho e tipo).
- Uvicorn escuta só em `127.0.0.1`; apenas o Nginx fica exposto.
- Firewall em duas camadas: NSG do Azure + `ufw` na VM.
- Banco de dados fora do repositório (`.gitignore`).

## Melhorias recomendadas (para produção)

HTTPS com Let's Encrypt/Certbot ou Azure Application Gateway, restringir o SSH ao seu IP, autenticação por chave SSH (sem senha), backup do arquivo SQLite (snapshot do disco), rate limiting e migração para um banco gerenciado.
