# Atlas / QUANT.SUPERVISE — Dashboard v4 Bug Report

Date: 2026-06-28  
Project: Atlas / QUANT.SUPERVISE  
Environment: Windows VPS / MT5 / Pepperstone Demo  
Dashboard URL: http://127.0.0.1:8001/?v=4  
MT5 Account: 62127915  

## Current Working Status

The following components are working:

- MT5 Bridge: CONNECTED
- Risk Engine: ACTIVE
- Account is visible
- Equity is visible
- Daily P&L is visible
- Alerts can be acknowledged with ACK ALL

- Dark Mimas — GBPJPY — H1 — Magic 10001
- Aurum Ra — XAUUSD — H1 — Magic 20001
- Pack Invest London Break Out — GBPUSD — H1 — Magic 40001
- RangeBreakout EA — EURUSD — H1 — Magic 50001

## Problems Found

### 1. Top Navigation Not Working

The dashboard top navigation buttons do not change view:

- OVERVIEW remains visible
- STRATEGIES does not open
- RISK does not open
- REPORTS does not open

Expected behavior:

Each tab should open its own functional dashboard section.

---

### 2. Alerts Panel Blocks Dashboard Functions

The Alerts panel stays over other dashboard areas and blocks visibility and interaction.

Problems:

- It overlays important UI areas
- It blocks access to other dashboard functions
- It makes the dashboard difficult to use, especially through Android RDP
- Even after ACK ALL, the panel remains visually obstructive
- It covers parts of the Risk Limits and System areas

Expected behavior:

The Alerts panel should be:

- closable, or
- collapsible, or
- positioned in a fixed area that does not block the dashboard

### 3. Risk Limits Inputs Are Not Usable

The Risk Limits section is not working correctly.

Problems found:

- Max Daily Loss (%) does not accept input
- Max Position Size (lots) does not accept decimal values like 0.01
- Max Position Size only allows 0 or 1
- If Max Position Size is set to 0, it may block or confuse position handling
- Max Open Positions can be changed to 4

Expected behavior:

Risk Limits must allow:

- Max Daily Loss (%) = 3
- Max Position Size (lots) = 0.01
- Max Open Positions = 4

These values are required because the trading system is designed for small accounts and 0.01 lot operation.

### 4. Missing Functional Strategies View

The dashboard does not show the active EAs clearly by Magic Number.

Expected Strategies view should show each active EA separately:

- Magic 10001 — Dark Mimas — GBPJPY — H1 — Active — Lot 0.01
- Magic 20001 — Aurum Ra — XAUUSD — H1 — Active — Lot 0.01
- Magic 40001 — Pack Invest London Break Out — GBPUSD — H1 — Active — Lot 0.01
- Magic 50001 — RangeBreakout EA — EURUSD — H1 — Active — Lot 0.01

The dashboard must allow the user to identify which EA is responsible for each position, result, alert, and risk event.

## Required Fix

This is not a new feature request.

These dashboard functions were part of the original Atlas / QUANT.SUPERVISE architecture and are required for the system to be usable.

Please fix the following as part of the existing delivery:

1. Make STRATEGIES, RISK and REPORTS tabs functional.
2. Fix the Alerts panel so it does not block the dashboard.
3. Fix Risk Limits inputs:
   - Max Daily Loss (%) must accept values like 3
   - Max Position Size (lots) must accept decimal values like 0.01
   - Max Open Positions must accept integer values like 4
4. Add a working Strategies view grouped by Magic Number.
5. Ensure the dashboard is usable on Windows VPS through Android RDP.

## Position

We are not requesting new paid development.

We are requesting correction of incomplete or defective dashboard functionality that belongs to the original Atlas architecture.
