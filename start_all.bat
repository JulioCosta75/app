@echo off
REM ============================================================
REM  Atlas - MT5 Quant Supervisor
REM  start_all.bat - arranca Bridge + Backend e abre o Dashboard
REM  numa unica execucao (Windows Server 2022 / Windows 10-11).
REM
REM  Pre-requisitos:
REM    1. Python 3.10-3.12 no PATH (NAO 3.13)
REM    2. Node.js LTS + Yarn (apenas para o build do frontend)
REM    3. MetaTrader 5 aberto, conta logada, Algo Trading ON
REM    4. mt5-bridge\.env  e  backend\.env  preenchidos
REM       (ver .env.example em cada pasta)
REM
REM  Coloque este ficheiro na raiz do projeto (ex.: C:\Atlas\).
REM ============================================================
setlocal
cd /d "%~dp0"
set "ROOT=%~dp0"
set "BRIDGE_DIR=%ROOT%mt5-bridge"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"

echo ============================================================
echo   ATLAS - arranque de todos os servicos
echo ============================================================

REM ---- Verificar Python -------------------------------------
python --version >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH. Instale Python 3.10-3.12.
    pause & exit /b 1
)

REM ---- Verificar ficheiros .env -----------------------------
if not exist "%BRIDGE_DIR%\.env" (
    echo [ERRO] Falta %BRIDGE_DIR%\.env
    echo        Copie .env.example para .env e preencha as credenciais MT5.
    pause & exit /b 1
)
if not exist "%BACKEND_DIR%\.env" (
    echo [ERRO] Falta %BACKEND_DIR%\.env
    echo        Copie .env.example para .env e preencha MT5_BRIDGE_URL/TOKEN.
    pause & exit /b 1
)

REM ---- 1) MT5 BRIDGE (porta 8002) ---------------------------
echo.
echo [1/3] A arrancar MT5 Bridge (porta 8002) numa nova janela...
start "Atlas MT5 Bridge" cmd /k "cd /d "%BRIDGE_DIR%" && run.bat"

REM Dar tempo ao bridge para subir antes do backend
echo       a aguardar 8s pelo bridge...
timeout /t 8 /nobreak >nul

REM ---- 2) BACKEND (porta 8001) ------------------------------
echo [2/3] A preparar o Backend (porta 8001)...
if not exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
    echo       a criar virtualenv do backend...
    python -m venv "%BACKEND_DIR%\.venv" || (echo [ERRO] venv falhou & pause & exit /b 1)
    echo       a instalar dependencias do backend...
    "%BACKEND_DIR%\.venv\Scripts\python.exe" -m pip install --disable-pip-version-check ^
        fastapi==0.110.1 uvicorn==0.25.0 httpx pydantic python-dotenv "starlette<0.40" "anyio<5" ^
        || (echo [ERRO] pip install falhou & pause & exit /b 1)
)
if not exist "%ROOT%data" mkdir "%ROOT%data"

echo       a arrancar o Backend numa nova janela...
start "Atlas Backend" cmd /k "cd /d "%BACKEND_DIR%" && .venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8001"

REM ---- 3) DASHBOARD -----------------------------------------
echo [3/3] A aguardar 6s e abrir o Dashboard no browser...
timeout /t 6 /nobreak >nul

if not exist "%FRONTEND_DIR%\build\index.html" (
    echo.
    echo [AVISO] %FRONTEND_DIR%\build\index.html nao existe.
    echo         Corra uma vez:  cd frontend ^&^& yarn install ^&^& yarn build
    echo         (necessario SERVE_FRONTEND=true no backend\.env)
    echo.
)

start "" "http://127.0.0.1:8001/"

echo.
echo ============================================================
echo   Atlas a arrancar.
echo   Dashboard : http://127.0.0.1:8001/
echo   Health    : http://127.0.0.1:8001/api/system/health
echo   Bridge    : http://127.0.0.1:8002/health
echo ============================================================
echo   (As janelas "Atlas MT5 Bridge" e "Atlas Backend" ficam
echo    abertas com os logs em tempo real. Feche-as para parar.)
echo.
endlocal
