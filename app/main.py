"""API de Tarefas - projeto de Cloud Security.

FastAPI + SQLite. Rotas de escrita/leitura protegidas por API Key
enviada no cabecalho X-API-Key. A chave vem da variavel de ambiente
API_KEY (nunca fica no codigo).
"""
import os
import secrets
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

DB_PATH = os.getenv("DB_PATH", "tarefas.db")
API_KEY = os.getenv("API_KEY", "")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    iniciar_banco()
    yield


app = FastAPI(
    title="API de Tarefas - Cloud Security",
    description="API basica com SQLite hospedada em VM na nuvem.",
    version="1.0.0",
    lifespan=lifespan,
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verificar_chave(chave: Optional[str] = Security(api_key_header)) -> None:
    if not API_KEY:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "API_KEY nao configurada no servidor",
        )
    # compare_digest evita ataques de temporizacao (timing attack)
    if not chave or not secrets.compare_digest(chave, API_KEY):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chave de API invalida")


@contextmanager
def conexao():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def iniciar_banco() -> None:
    with conexao() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS tarefas (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo     TEXT    NOT NULL,
                descricao  TEXT,
                concluida  INTEGER NOT NULL DEFAULT 0,
                criada_em  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


class TarefaIn(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=120)
    descricao: Optional[str] = Field(None, max_length=500)
    concluida: bool = False


class TarefaOut(TarefaIn):
    id: int
    criada_em: str


def linha_para_tarefa(row: sqlite3.Row) -> TarefaOut:
    return TarefaOut(
        id=row["id"],
        titulo=row["titulo"],
        descricao=row["descricao"],
        concluida=bool(row["concluida"]),
        criada_em=row["criada_em"],
    )


@app.get("/", tags=["status"])
def raiz():
    return {"status": "ok", "servico": "API de Tarefas", "docs": "/docs"}


@app.get("/saude", tags=["status"])
def saude():
    return {"status": "saudavel"}


@app.get("/tarefas", response_model=List[TarefaOut], tags=["tarefas"],
         dependencies=[Depends(verificar_chave)])
def listar():
    with conexao() as con:
        rows = con.execute("SELECT * FROM tarefas ORDER BY id").fetchall()
    return [linha_para_tarefa(r) for r in rows]


@app.get("/tarefas/{tarefa_id}", response_model=TarefaOut, tags=["tarefas"],
         dependencies=[Depends(verificar_chave)])
def obter(tarefa_id: int):
    with conexao() as con:
        row = con.execute("SELECT * FROM tarefas WHERE id = ?", (tarefa_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Tarefa nao encontrada")
    return linha_para_tarefa(row)


@app.post("/tarefas", response_model=TarefaOut, status_code=201, tags=["tarefas"],
          dependencies=[Depends(verificar_chave)])
def criar(t: TarefaIn):
    # Consulta parametrizada (?) previne SQL Injection
    with conexao() as con:
        cur = con.execute(
            "INSERT INTO tarefas (titulo, descricao, concluida) VALUES (?, ?, ?)",
            (t.titulo, t.descricao, int(t.concluida)),
        )
        row = con.execute("SELECT * FROM tarefas WHERE id = ?", (cur.lastrowid,)).fetchone()
    return linha_para_tarefa(row)


@app.put("/tarefas/{tarefa_id}", response_model=TarefaOut, tags=["tarefas"],
         dependencies=[Depends(verificar_chave)])
def atualizar(tarefa_id: int, t: TarefaIn):
    with conexao() as con:
        cur = con.execute(
            "UPDATE tarefas SET titulo=?, descricao=?, concluida=? WHERE id=?",
            (t.titulo, t.descricao, int(t.concluida), tarefa_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Tarefa nao encontrada")
        row = con.execute("SELECT * FROM tarefas WHERE id = ?", (tarefa_id,)).fetchone()
    return linha_para_tarefa(row)


@app.delete("/tarefas/{tarefa_id}", status_code=204, tags=["tarefas"],
            dependencies=[Depends(verificar_chave)])
def remover(tarefa_id: int):
    with conexao() as con:
        cur = con.execute("DELETE FROM tarefas WHERE id = ?", (tarefa_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Tarefa nao encontrada")
