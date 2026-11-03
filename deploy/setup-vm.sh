#!/usr/bin/env bash
# Deploy na VM Ubuntu 22.04 (Azure). Rode como usuario com sudo: bash deploy/setup-vm.sh <URL_DO_REPO_GIT>
set -euo pipefail

REPO_URL="${1:?Informe a URL do repositorio Git}"
APP_DIR=/opt/api-tarefas-cloud

sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip nginx git ufw

sudo git clone "$REPO_URL" "$APP_DIR" || (cd "$APP_DIR" && sudo git pull)
sudo chown -R "$USER":"$USER" "$APP_DIR"

cd "$APP_DIR"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Gera uma chave de API aleatoria e guarda fora do repositorio
if [ ! -f /etc/api-tarefas.env ]; then
  KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
  printf 'API_KEY=%s\nDB_PATH=/var/lib/api-tarefas/tarefas.db\n' "$KEY" | sudo tee /etc/api-tarefas.env >/dev/null
  sudo chmod 600 /etc/api-tarefas.env
  echo "Sua API_KEY (guarde): $KEY"
fi

sudo mkdir -p /var/lib/api-tarefas
sudo chown "$USER":"$USER" /var/lib/api-tarefas

sudo cp deploy/api-tarefas.service /etc/systemd/system/
sudo cp deploy/nginx-api-tarefas.conf /etc/nginx/sites-available/api-tarefas
sudo ln -sf /etc/nginx/sites-available/api-tarefas /etc/nginx/sites-enabled/api-tarefas
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable --now api-tarefas
sudo nginx -t && sudo systemctl restart nginx

# Firewall do sistema operacional (alem do NSG do Azure)
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx HTTP'
sudo ufw --force enable

echo "Pronto. Teste: curl http://localhost/saude"
