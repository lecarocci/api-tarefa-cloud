import importlib
import os

import pytest
from fastapi.testclient import TestClient

CHAVE = "chave-de-teste"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "teste.db"))
    monkeypatch.setenv("API_KEY", CHAVE)
    from app import main
    importlib.reload(main)
    with TestClient(main.app) as c:
        yield c


H = {"X-API-Key": CHAVE}


def test_saude_publica(client):
    assert client.get("/saude").json() == {"status": "saudavel"}


def test_sem_chave_retorna_401(client):
    assert client.get("/tarefas").status_code == 401


def test_chave_errada_retorna_401(client):
    assert client.get("/tarefas", headers={"X-API-Key": "errada"}).status_code == 401


def test_crud_completo(client):
    r = client.post("/tarefas", json={"titulo": "Estudar cloud"}, headers=H)
    assert r.status_code == 201
    tid = r.json()["id"]

    assert len(client.get("/tarefas", headers=H).json()) == 1

    r = client.put(f"/tarefas/{tid}", json={"titulo": "Estudar cloud", "concluida": True}, headers=H)
    assert r.json()["concluida"] is True

    assert client.delete(f"/tarefas/{tid}", headers=H).status_code == 204
    assert client.get(f"/tarefas/{tid}", headers=H).status_code == 404


def test_sql_injection_tratado_como_texto(client):
    payload = "x'); DROP TABLE tarefas;--"
    assert client.post("/tarefas", json={"titulo": payload}, headers=H).status_code == 201
    itens = client.get("/tarefas", headers=H).json()
    assert itens[0]["titulo"] == payload


def test_validacao_titulo_vazio(client):
    assert client.post("/tarefas", json={"titulo": ""}, headers=H).status_code == 422
