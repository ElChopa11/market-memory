# Security model

Phase 1 documents the credential and environment model and implements **read-only public ingest**. No live keys, wallet material, or order-signing code ships in this repository.

## Separation of capital (Hyperliquid)

```text
Treasury (hardware wallet)
  └── never on any lab server, never in git, never in CI
Trading allocation (API / agent wallet)
  └── only the Execution service, only in the live environment
  └── withdraw disabled / limited where the platform allows
Read-only keys / public endpoints
  └── Ingest + Research + Briefing
```

Prefer an **API wallet / agent wallet** authorized to trade a sub-allocation. The cold treasury is not an API key and is not installed on research machines or VPS hosts.

Research workers **must not** import the live trading module (`hl_trade` / `mm_execution` signing surface when it exists) and **must not** receive trading credentials via env, vault, or files.

## Environments

| Env | Credentials present | Can submit orders | Risk config |
|---|---|---|---|
| `dev` | none / mocks | no | `config/risk/defaults.yaml` |
| `sim` | none | simulated | `config/risk/environments/sim.yaml` |
| `paper` | HL info / public only | paper ledger only | `config/risk/environments/paper.yaml` |
| `live` | API wallet key in a sealed secret store | yes, after Risk allow **and** Principal promotion | `config/risk/environments/live.yaml` (Principal-gated) |

`live_trading_enabled` is **false** in all committed configs. Enabling it is a Principal act, not an agent act.

## Rules

1. **No unrestricted private key for the treasury** in the lab.
2. Execution is a **separate deploy unit** with its own identity. Research cannot import live signing code.
3. Secrets via **env injection from a vault** (1Password / OS keychain / sealed files). `.env` is gitignored; `.env.example` has no credentials.
4. **Dual control for live:** Risk allow *and* a Principal promotion record for the thesis.
5. **Kill switch:** a Principal halt file (`config/halt.flag`, gitignored) or a signed CLI command. Execution must check it before every order. Presence of the flag means **no new orders**.
6. Logging: every signed action stores intent hash, risk decision id, request/response (redact secrets).
7. Australia ops: prefer an AU-region host for live execution when it exists; research can stay local.
8. ToS / lawful collection only.

## Kill switch

| Mechanism | Who | Effect |
|---|---|---|
| `config/halt.flag` present | Principal (or Coordinator acting under halt runbook) | Execution refuses new orders |
| `lab halt` (signed CLI; later phase) | Principal | Same; recorded in Market Memory |
| `live_trading_enabled: false` | Committed config | Entire live path is inert |

Phase 1: public Hyperliquid `/info` ingest only. The halt flag path and config gate exist; no execution loop is implemented. See [runbooks/halt.md](runbooks/halt.md). Ingest runbook: [runbooks/ingest.md](runbooks/ingest.md).

## Live risk config guard

`config/risk/environments/live.yaml` is Principal-owned.

- CODEOWNERS assigns the Principal.
- CI workflow `.github/workflows/risk-config-guard.yml` fails PRs that modify the file unless the `principal-review` label is present (bootstrap exception: first add while still hard-gated off).
- Autonomous Research/Skeptic/Briefing agents must not edit this file.

## Rotation and live later

When live exists: revoke API wallet → issue new → update vault → restart **execution only**. Test signing on testnet/paper before any mainnet key is installed. Runbook: [credential-rotation.md](runbooks/credential-rotation.md).

Promotion path: [promote-paper-to-live.md](runbooks/promote-paper-to-live.md).
