# External Integrations

**Analysis Date:** 2026-05-11

## APIs & External Services

**Market data:**
- Yahoo Finance - SPX (^GSPC), VIX (^VIX), WTI crude oil futures (CL=F)
  - SDK/Client: `yfinance`
  - Auth: none required for public historical data

**Macro data:**
- No external FRED or premium data used for current SPX thesis pivot

## Data Storage

**Files:**
- CSV files in `data/processed/`
  - `data/processed/spx_data.csv`
  - `data/processed/train.csv`
  - `data/processed/test.csv`

**Model/artifacts:**
- Output figures saved to `figures/`
- No database or external file storage service used

## Authentication & Identity

**Auth Provider:**
- None

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- Standard output in CLI scripts
- No logging framework configured

## CI/CD & Deployment

**Hosting:**
- None

**CI Pipeline:**
- Not detected in repository

## Environment Configuration

**Required env vars:**
- None currently required for thesis SPX data

**Secrets location:**
- Not used

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-05-11*

---
LINKS:AUTO
