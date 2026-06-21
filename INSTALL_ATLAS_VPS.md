# Atlas — MT5 Quant Supervisor
## Guia de Instalação no VPS (Windows Server 2022) — Desenvolvimento & Testes

> Cenário confirmado: **VPS Windows Server 2022**, acesso por **RDP**, terminal **MetaTrader 5** na mesma máquina, apenas **código-fonte** do repositório `JulioCosta75/Mt5`. Objetivo: instalar e validar todos os componentes (incl. ponte MT5) para o laboratório **Dark Mimas**. **Sem produção** nesta fase.

---

## 0. Arquitetura (resumo)

```
                 ┌──────────────── VPS Windows Server 2022 ────────────────┐
                 │                                                          │
  Browser  ──►   │  Frontend (React build)                                  │
  http://...8001 │        ▲                                                 │
                 │        │ servido pelo backend (SERVE_FRONTEND=true)      │
                 │  Backend FastAPI  (porta 8001)                           │
                 │        │  MT5_BRIDGE_URL=http://127.0.0.1:8002           │
                 │        ▼  HTTP + Bearer token                            │
                 │  MT5 Bridge FastAPI (porta 8002)  ◄── lib MetaTrader5    │
                 │        │  IPC                                            │
                 │        ▼                                                 │
                 │  Terminal MetaTrader 5 (aberto + conta logada)          │
                 └──────────────────────────────────────────────────────────┘
```

**Vantagem do vosso cenário:** como backend, bridge e MT5 correm **todos no mesmo VPS Windows**, o backend liga ao bridge por `http://127.0.0.1:8002`. **Não é preciso túnel** (Cloudflare/ngrok/Tailscale) — esses só seriam necessários se o backend corresse num host Linux separado.

---

## 1. Estado do repositório — está organizado para instalar?

**Sim, está funcionalmente completo e bem organizado.** Estrutura relevante:

| Pasta | Papel | Onde corre |
|---|---|---|
| `backend/` | API FastAPI + dados mock + cliente MT5 | Windows (porta 8001) |
| `frontend/` | Dashboard React 19 (craco) | build estático servido pelo backend |
| `mt5-bridge/` | Ponte Windows para o terminal MT5 (`MetaTrader5`) | Windows (porta 8002) |
| `installer/` | Kit Inno Setup para gerar `Atlas_Setup.exe` (opcional) | máquina de build |
| `memory/PRD.md` | Documento de produto / decisões de arquitetura | — |

**3 observações de organização (não bloqueantes):**
1. O `README.md` na raiz é apenas o *placeholder* default (`# Here are your Instructions`) — não guia a instalação. O conteúdo útil está em `mt5-bridge/README.md` e `installer/README.md`. (Este ficheiro resolve isso.)
2. `frontend/build/` está no `.gitignore` — terá de correr `yarn build` no VPS (precisa de Node.js).
3. Os ficheiros `.env` **não** estão no repositório (corretamente ignorados) — terá de os criar (secções 4 e 5).

---

## 2. Pré-requisitos a instalar no VPS

| Software | Versão | Porquê | Nota |
|---|---|---|---|
| **Python** | **3.10, 3.11 ou 3.12** | backend + bridge | **NÃO usar 3.13** — `MetaTrader5` ainda não é estável nessa versão. Marcar "Add Python to PATH" no instalador. |
| **Node.js LTS + Yarn** | LTS (20.x) | compilar o frontend React | `npm install -g yarn` após instalar Node |
| **Git** (opcional) | qualquer | clonar o repo no VPS | em alternativa, RDP file-transfer do ZIP |
| **MetaTrader 5** | do seu broker | fonte dos dados | terminal **aberto**, conta **logada**, **Algo Trading ON** |

> **Não é preciso MongoDB.** No Windows usamos `ATLAS_STORE=sqlite` (zero dependências de base de dados externa).

**Ativar Algo Trading no MT5:** `Tools → Options → Expert Advisors → ☑ Allow algorithmic trading`.

---

## 3. Obter o código no VPS

Via RDP, abra o **PowerShell** e:

```powershell
cd C:\
git clone https://github.com/JulioCosta75/Mt5.git C:\Atlas
cd C:\Atlas
```
(Ou copie o ZIP do repositório por RDP e extraia para `C:\Atlas`.)

---

## 4. Instalar e arrancar a **Ponte MT5** (porta 8002)

```powershell
cd C:\Atlas\mt5-bridge
copy .env.example .env
notepad .env
```

Edite o `.env` com as credenciais **reais** da conta que o terminal MT5 tem logada:

```ini
MT5_LOGIN=12345678
MT5_PASSWORD=a_sua_password
MT5_SERVER=NomeDoServidor-Live
# MT5_TERMINAL_PATH=C:\Program Files\SeuBroker MT5\terminal64.exe   (só se tiver várias instalações)

# Gere um token aleatório (guarde-o, será usado pelo backend):
#   python -c "import secrets;print(secrets.token_urlsafe(32))"
BRIDGE_TOKEN=COLE_AQUI_O_TOKEN_GERADO

BRIDGE_HOST=127.0.0.1
BRIDGE_PORT=8002
SNAPSHOT_INTERVAL_SECONDS=10
```

> **Dica de segurança (dev):** use `BRIDGE_HOST=127.0.0.1` para o bridge só aceitar ligações locais (o backend está na mesma máquina). O `.env.example` traz `0.0.0.0` — restrinja a loopback nesta fase.

Arranque o bridge (cria venv + instala dependências automaticamente):

```powershell
.\run.bat
```

Deixe esta janela aberta. O bridge fica a correr em `http://127.0.0.1:8002`.

---

## 5. Instalar e arrancar o **Backend** (porta 8001)

Numa **nova** janela PowerShell:

```powershell
cd C:\Atlas\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> **Importante:** o `backend/requirements.txt` completo é pesado (inclui `emergentintegrations`, `litellm`, `boto3`, `motor`…) e é desenhado para o pod Linux da Emergent. Para correr no Windows em modo SQLite **basta o conjunto mínimo** (o backend só importa `motor` se `ATLAS_STORE=mongo`):

```powershell
pip install fastapi==0.110.1 uvicorn==0.25.0 httpx pydantic python-dotenv "starlette<0.40" "anyio<5"
```

Crie o ficheiro `C:\Atlas\backend\.env`:

```ini
ATLAS_STORE=sqlite
ATLAS_SQLITE_PATH=C:\Atlas\data\atlas.db

# Ativa modo MT5 REAL apontando para o bridge local:
MT5_BRIDGE_URL=http://127.0.0.1:8002
MT5_BRIDGE_TOKEN=O_MESMO_TOKEN_DO_BRIDGE

# Servir o dashboard React a partir do backend:
SERVE_FRONTEND=true
FRONTEND_BUILD=C:\Atlas\frontend\build

CORS_ORIGINS=*
```

Crie a pasta de dados e arranque o backend:

```powershell
mkdir C:\Atlas\data -Force
python -m uvicorn server:app --host 127.0.0.1 --port 8001
```

> **Modo mock primeiro (opcional):** se quiser validar o dashboard *antes* de ligar ao MT5, comente/remova as linhas `MT5_BRIDGE_URL` e `MT5_BRIDGE_TOKEN`. O backend arranca em **modo mock** (8 contas simuladas) e o dashboard funciona na mesma. Volte a adicioná-las para ativar dados reais.

---

## 6. Compilar o **Frontend** (uma vez)

Numa nova janela PowerShell:

```powershell
cd C:\Atlas\frontend
copy .env.example .env 2>$null   # se não existir, crie manualmente (ver abaixo)
yarn install
yarn build
```

Conteúdo do `C:\Atlas\frontend\.env` (para o build apontar ao backend local):

```ini
REACT_APP_BACKEND_URL=http://127.0.0.1:8001
WDS_SOCKET_PORT=0
```

O `yarn build` gera `C:\Atlas\frontend\build\` — é exatamente a pasta que o backend serve (`FRONTEND_BUILD` na secção 5).

> Em alternativa, para **desenvolvimento com hot-reload**: `yarn start` arranca o React em `http://localhost:3000` e fala com o backend via `REACT_APP_BACKEND_URL`. Nesse caso não precisa de `SERVE_FRONTEND` no backend.

---

## 7. Validar que a instalação ficou OK (component-by-component)

Execute por ordem. Tudo deve responder localmente.

### 7.1 Ponte MT5
```powershell
curl http://127.0.0.1:8002/health
```
Esperado (conta logada e Algo Trading ON):
```json
{"status":"ok","terminal_connected":true,"account_logged_in":true,
 "trade_allowed":true,"login":12345678,"server":"...","last_error":null}
```
Endpoint autenticado:
```powershell
$T="O_SEU_BRIDGE_TOKEN"
curl -H "Authorization: Bearer $T" http://127.0.0.1:8002/account
```
Swagger interativo: `http://127.0.0.1:8002/docs`

### 7.2 Backend
```powershell
curl http://127.0.0.1:8001/api/system/health
```
Esperado em modo real: `"mode":"mt5"` e `"store":{"backend":"sqlite","ok":true}`.
(Se vir `"mode":"mock"`, o `.env` não foi lido ou `MT5_BRIDGE_URL` não está definido.)

Ligação backend↔bridge:
```powershell
curl http://127.0.0.1:8001/api/bridge/health
curl http://127.0.0.1:8001/api/kpis
curl http://127.0.0.1:8001/api/accounts
```

### 7.3 Frontend / Dashboard
Abra no browser do VPS:
- Dashboard: `http://127.0.0.1:8001/`
- Página de diagnóstico: `http://127.0.0.1:8001/healthcheck`

✅ Instalação validada quando: bridge `terminal_connected:true`, backend `mode:mt5`, `/api/bridge/health` OK e o dashboard mostra a conta MT5 real.

---

## 7-B. Arranque rápido com `start_all.bat` (recomendado)

Depois de criados os dois `.env` (`mt5-bridge\.env` e `backend\.env`) e feito o `yarn build` do frontend uma vez, pode arrancar **tudo numa só execução** a partir da raiz do projeto:

```powershell
cd C:\Atlas
.\start_all.bat
```

O script:
1. Verifica Python e a presença dos dois `.env`.
2. Arranca a **Ponte MT5** (porta 8002) numa janela própria (via `run.bat`).
3. Cria o venv do **Backend** (1ª vez), instala dependências mínimas e arranca o uvicorn (porta 8001).
4. Abre o **Dashboard** em `http://127.0.0.1:8001/`.

As janelas "Atlas MT5 Bridge" e "Atlas Backend" ficam abertas com os logs ao vivo — feche-as para parar os serviços. (Para auto-arranque sem janelas, use os serviços NSSM da secção 8.)

---

## 8. (Opcional) Transformar em serviços Windows (auto-arranque)

Para os processos não dependerem de janelas RDP abertas, registe-os como serviços com **NSSM** (`https://nssm.cc`):

```powershell
# Exemplo (ajuste caminhos do python.exe de cada venv):
nssm install AtlasBridge  "C:\Atlas\mt5-bridge\.venv\Scripts\python.exe" "C:\Atlas\mt5-bridge\bridge_server.py"
nssm set     AtlasBridge  AppDirectory "C:\Atlas\mt5-bridge"

nssm install AtlasBackend "C:\Atlas\backend\.venv\Scripts\python.exe" "-m" "uvicorn" "server:app" "--host" "127.0.0.1" "--port" "8001"
nssm set     AtlasBackend AppDirectory "C:\Atlas\backend"
nssm set     AtlasBackend DependOnService AtlasBridge

net start AtlasBridge
net start AtlasBackend
```

O repositório já traz scripts equivalentes prontos em `installer/scripts/install_services.bat` e `start_atlas.bat`.

---

## 9. (Alternativa) Instalador `Atlas_Setup.exe` (1-clique)

O repo inclui um kit completo em `installer/` que produz um instalador único com Python 3.11 embebido + NSSM + serviços + wizard Tkinter. **Para esta fase de dev/testes não é necessário** (a via manual das secções 4–7 é mais rápida e transparente). Se quiser gerá-lo mais tarde, precisa numa **máquina de build Windows**: Inno Setup 6, Python 3.11 full, Node+yarn, PyInstaller — depois corre `installer\build.bat` → `dist\Atlas_Setup.exe`. Detalhes em `installer/README.md`.

---

## 10. Configuração inicial recomendada (pós-instalação)

1. **Manter tudo em loopback (127.0.0.1)** nesta fase — não exponha 8001/8002 à internet enquanto estiver em testes.
2. **`ATLAS_STORE=sqlite`** — evita instalar MongoDB no Windows.
3. **Token do bridge forte e único** (`secrets.token_urlsafe(32)`); o mesmo valor em `mt5-bridge/.env` e `backend/.env`.
4. **Backup da pasta `data\`** — contém os snapshots de equity (SQLite). É o estado que vale a pena preservar.
5. **MT5 sempre aberto + logado + Algo Trading ON** — se fechar o terminal, o bridge fica offline (o `/health` reporta).
6. **Logs:** redirecione stdout/stderr dos serviços (NSSM faz isto) para `C:\Atlas\logs\` para diagnóstico.
7. **Multi-conta (futuro Dark Mimas):** correr N bridges em portas distintas (8002, 8003, …), cada um com `MT5_LOGIN` e `BRIDGE_TOKEN` próprios, e no backend usar `MT5_BRIDGE_URLS=` + `MT5_BRIDGE_TOKENS=` (listas separadas por vírgula).

---

## 11. Resolução de problemas (mais comuns)

| Sintoma | Causa provável | Solução |
|---|---|---|
| `/health` → `terminal_connected:false` | Terminal MT5 fechado | Abra o MT5 e faça login |
| Bridge `MT5 error [-10027]` | Algo Trading desativado | `Tools → Options → Expert Advisors → Allow algorithmic trading` |
| Bridge `MT5 error [-10004]` | login/password/servidor errados | Reveja `mt5-bridge\.env` |
| `initialize failed` | DLL do terminal não encontrada | Defina `MT5_TERMINAL_PATH` para o `terminal64.exe` correto |
| Backend `mode:mock` (esperava mt5) | `.env` não lido ou `MT5_BRIDGE_URL` em falta | Confirme `backend\.env` e reinicie o backend |
| Backend erro a importar `motor` | `ATLAS_STORE` ≠ sqlite | Garanta `ATLAS_STORE=sqlite` no `.env` |
| `pip install MetaTrader5` falha | Python 3.13 | Use Python 3.10–3.12 |
| Dashboard em branco | `frontend/build` em falta ou `FRONTEND_BUILD` errado | Corra `yarn build` e confirme o caminho |

---

### Resumo dos portos
- **8001** — Backend + Dashboard (`http://127.0.0.1:8001`)
- **8002** — Ponte MT5 (`http://127.0.0.1:8002`)
