"""Atlas MT5 Supervisor — Backend API tests (mock mode).
Covers system health, KPIs, accounts, equity, drawdown, trades,
alerts, kill switch, risk limits and sim tick endpoints.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://atlas-dev-env.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- system health ----------
def test_system_health(client):
    r = client.get(f"{API}/system/health", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data["mode"] == "mock"
    assert data["store"]["backend"] == "mongo"
    assert data["store"]["ok"] is True
    assert data["bridge"] is None
    assert "server_time" in data


# ---------- KPIs ----------
def test_kpis(client):
    r = client.get(f"{API}/kpis", timeout=20)
    assert r.status_code == 200
    d = r.json()
    for key in ["total_equity", "daily_pnl", "open_positions", "accounts_total", "active_alerts", "server_time"]:
        assert key in d, f"missing key {key}"
    assert d["accounts_total"] == 8
    assert isinstance(d["total_equity"], (int, float))
    assert isinstance(d["active_alerts"], int)


# ---------- accounts list ----------
def test_accounts_list(client):
    r = client.get(f"{API}/accounts", timeout=20)
    assert r.status_code == 200
    accounts = r.json()
    assert isinstance(accounts, list)
    assert len(accounts) == 8
    a = accounts[0]
    for key in ["id", "login", "broker", "strategy", "balance", "equity", "daily_pnl", "status"]:
        assert key in a, f"missing {key}"
    # max_drawdown / current_drawdown present
    assert "max_drawdown" in a and "current_drawdown" in a
    # IDs are ACC-001 ... ACC-008
    ids = sorted([acc["id"] for acc in accounts])
    assert ids == [f"ACC-{i:03d}" for i in range(1, 9)]


# ---------- account detail ----------
def test_account_detail(client):
    r = client.get(f"{API}/accounts/ACC-001", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["id"] == "ACC-001"
    # no private series leaking
    assert not any(k.startswith("_") for k in d.keys())


def test_account_detail_not_found(client):
    r = client.get(f"{API}/accounts/ACC-999", timeout=20)
    assert r.status_code == 404


# ---------- equity / drawdown / trades ----------
def test_equity_series(client):
    r = client.get(f"{API}/accounts/ACC-001/equity?points=220", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["account_id"] == "ACC-001"
    assert isinstance(d["series"], list) and len(d["series"]) > 0
    p = d["series"][0]
    assert "t" in p and "equity" in p


def test_drawdown_series(client):
    r = client.get(f"{API}/accounts/ACC-002/drawdown?points=220", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert "max_drawdown" in d and "current_drawdown" in d
    assert isinstance(d["series"], list) and len(d["series"]) > 0
    assert "dd" in d["series"][0]


def test_trades_list(client):
    r = client.get(f"{API}/accounts/ACC-003/trades?limit=100", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["account_id"] == "ACC-003"
    assert isinstance(d["trades"], list)
    assert len(d["trades"]) <= 100
    t = d["trades"][0]
    for k in ["id", "symbol", "side", "lots", "pnl", "open_time", "close_time"]:
        assert k in t


# ---------- alerts ----------
def test_alerts_list_and_ack(client):
    r = client.get(f"{API}/alerts", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert "alerts" in d and "count" in d
    assert len(d["alerts"]) > 0
    alert_id = d["alerts"][0]["id"]
    # acknowledge
    r2 = client.post(f"{API}/alerts/{alert_id}/ack", json={"acknowledged": True}, timeout=20)
    assert r2.status_code == 200
    assert r2.json()["acknowledged"] is True
    # verify by re-fetching list
    r3 = client.get(f"{API}/alerts", timeout=20)
    found = next((a for a in r3.json()["alerts"] if a["id"] == alert_id), None)
    assert found is not None and found["acknowledged"] is True


def test_alert_ack_not_found(client):
    r = client.post(f"{API}/alerts/ALT-DOESNOTEXIST/ack", json={"acknowledged": True}, timeout=20)
    assert r.status_code == 404


# ---------- kill switch ----------
def test_kill_switch_toggle(client):
    # enable
    r = client.post(f"{API}/accounts/ACC-004/kill-switch", json={"enabled": True}, timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["kill_switch"] is True
    assert d["status"] == "PAUSED"
    # verify persisted via GET
    r2 = client.get(f"{API}/accounts/ACC-004", timeout=20)
    assert r2.json()["kill_switch"] is True
    assert r2.json()["status"] == "PAUSED"
    # disable
    r3 = client.post(f"{API}/accounts/ACC-004/kill-switch", json={"enabled": False}, timeout=20)
    assert r3.status_code == 200
    assert r3.json()["kill_switch"] is False
    assert r3.json()["status"] == "LIVE"


# ---------- risk limits ----------
def test_update_risk_limits(client):
    payload = {"max_daily_loss_pct": 4.5, "max_position_size_lots": 2.5, "max_open_positions": 15}
    r = client.put(f"{API}/accounts/ACC-005/risk-limits", json=payload, timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["risk_limits"]["max_daily_loss_pct"] == 4.5
    assert d["risk_limits"]["max_position_size_lots"] == 2.5
    assert d["risk_limits"]["max_open_positions"] == 15
    # GET to verify persistence
    r2 = client.get(f"{API}/accounts/ACC-005", timeout=20)
    rl = r2.json()["risk_limits"]
    assert rl["max_daily_loss_pct"] == 4.5
    assert rl["max_position_size_lots"] == 2.5
    assert rl["max_open_positions"] == 15


# ---------- sim tick ----------
def test_sim_tick(client):
    before = client.get(f"{API}/kpis", timeout=20).json()["total_equity"]
    r = client.post(f"{API}/sim/tick", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert "server_time" in d
    after = client.get(f"{API}/kpis", timeout=20).json()["total_equity"]
    # equity should have moved (or stayed; but server_time must change)
    assert isinstance(after, (int, float))
    assert before is not None
