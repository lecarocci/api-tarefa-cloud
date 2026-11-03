# Guia de deploy — Azure VM + Nginx + systemd

> Pré-requisito: conta Azure (a conta de estudante ou a gratuita servem) e este repositório publicado no GitHub.

## 1. Publicar o código no GitHub

```bash
cd api-tarefas-cloud
git init
git add .
git commit -m "API de tarefas com FastAPI e SQLite"
git branch -M main
git remote add origin https://github.com/<SEU_USUARIO>/api-tarefas-cloud.git
git push -u origin main
```

Crie antes o repositório vazio (público) em https://github.com/new.

## 2. Criar a VM no portal Azure

1. **Máquinas virtuais → Criar → Máquina virtual do Azure**.
2. Grupo de recursos: `rg-api-tarefas`. Nome: `vm-api-tarefas`. Região: **Brazil South** (ou a mais próxima/barata).
3. Imagem: **Ubuntu Server 22.04 LTS**.
4. Tamanho (SKU): **Standard_B1s** (1 vCPU, 1 GiB RAM, série B burstable). Confira a disponibilidade e o preço na sua região.
5. Autenticação: **Chave pública SSH** (baixe o `.pem`).
6. Regras de entrada: marque **SSH (22)** e **HTTP (80)**.
7. Disco: **Standard SSD** (disco do SO padrão).
8. **Revisar + criar → Criar**. Anote o **IP público**.

Equivalente em linha de comando (Azure CLI):

```bash
az group create -n rg-api-tarefas -l brazilsouth
az vm create -g rg-api-tarefas -n vm-api-tarefas \
  --image Ubuntu2204 --size Standard_B1s \
  --admin-username azureuser --generate-ssh-keys \
  --public-ip-sku Standard
az vm open-port -g rg-api-tarefas -n vm-api-tarefas --port 80 --priority 1010
```

## 3. Conectar e instalar

```bash
chmod 400 chave.pem
ssh -i chave.pem azureuser@<IP_PUBLICO>

git clone https://github.com/<SEU_USUARIO>/api-tarefas-cloud.git
cd api-tarefas-cloud
bash deploy/setup-vm.sh https://github.com/<SEU_USUARIO>/api-tarefas-cloud.git
```

O script imprime a `API_KEY` gerada. **Guarde-a**.

## 4. Validar

```bash
curl http://<IP_PUBLICO>/saude
# {"status":"saudavel"}
```

No navegador: `http://<IP_PUBLICO>/docs`. Clique em **Authorize**, cole a chave e teste as rotas.

## 5. Prints para o relatório

- Portal Azure: página de visão geral da VM (nome, SKU, IP, SO).
- Navegador em `http://<IP_PUBLICO>/docs` com as rotas.
- Resposta de uma chamada autenticada (200) e outra sem chave (401).
- Terminal com `systemctl status api-tarefas`.
- Página do repositório no GitHub.

## 6. Custos e limpeza

Ao terminar, apague os recursos para não gerar cobrança:

```bash
az group delete -n rg-api-tarefas --yes --no-wait
```

## Solução de problemas

| Sintoma | Verificação |
|---------|-------------|
| Site não abre | Porta 80 liberada no NSG? `sudo ufw status` |
| 502 Bad Gateway | `sudo systemctl status api-tarefas` e `journalctl -u api-tarefas -n 50` |
| 500 "API_KEY nao configurada" | Conferir `/etc/api-tarefas.env` e reiniciar o serviço |
