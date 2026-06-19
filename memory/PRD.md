# Atlas — MT5 Quant Supervisor (QUANT.SUPERVISE)

## Original Problem Statement
User (Portuguese) shared public repo github.com/JulioCosta75/Mt5 and asked for help installing "Atlas" on a VPS for development/testing (NOT production). Then asked to run the dashboard in this Emergent workspace in MOCK mode to validate the UI before installing on the VPS.

## VPS context (confirmed by user)
- Windows Server 2022, RDP access
- MetaTrader 5 available on the same machine
- Only source code available (no compiled installer)
- Goal: install Atlas, validate all components incl. MT5 bridge, prepare infra for the "Dark Mimas" lab

## Architecture
- backend/  FastAPI (port 8001). ATLAS_STORE=mongo(default)|sqlite. MT5_MODE on when MT5_BRIDGE_URL set; else mock (8 fake accounts).
- frontend/ React 19 (craco) dashboard. Uses REACT_APP_BACKEND_URL.
- mt5-bridge/ Windows-only (lib MetaTrader5, port 8002). Needs MT5 terminal open + Algo Trading ON.
- installer/ Inno Setup kit -> Atlas_Setup.exe (embedded python + NSSM services). Optional.

## What's been done in this workspace
- 2026-06-19: Imported Atlas backend + frontend source from repo (preserved platform .env files).
- 2026-06-19: Installed frontend deps (yarn). Backend running mock mode (store mongo OK, 8 accounts).
- 2026-06-19: Created /app/INSTALL_ATLAS_VPS.md — full PT install+validation guide for Windows Server 2022.
- 2026-06-19: E2E testing PASSED 100% (backend 13/13 pytest; all UI flows). Report: /app/test_reports/iteration_1.json. Suite: /app/backend/tests/test_atlas_api.py.

## Known MVP limitations (expected, not bugs)
- Nav tabs Strategies/Risk/Reports/Audit are decorative placeholders (no onClick). Only Overview functional.
- System panel indicators are hardcoded in mock mode.
- Mock state is in-memory (resets on backend restart).

## Next actions
- P0: Install on Windows Server 2022 per INSTALL_ATLAS_VPS.md; run bridge (8002) + backend (8001, ATLAS_STORE=sqlite); set MT5_BRIDGE_URL=http://127.0.0.1:8002 + token to activate mode:mt5; validate /api/bridge/health.
- P1: Tighten CORS before any public exposure. Wire System panel to /api/bridge/health in real mode.
- P1: Multi-account (Dark Mimas) -> N bridges (8002,8003...) + MT5_BRIDGE_URLS/MT5_BRIDGE_TOKENS.
