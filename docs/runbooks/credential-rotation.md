# Credential rotation (runbook)

## Scope

API / agent wallet used by Execution in live. **Treasury / hardware wallet is never on a lab host** and is not rotated by this runbook.

## Never stored in git

Private keys, mnemonic phrases, API wallet secrets, vault tokens, `.env` files.

## Rotate live API wallet (when live exists)

1. Halt new orders (`config/halt.flag`).
2. Revoke the old API / agent wallet on Hyperliquid.
3. Issue a new API / agent wallet authorized only for the trading sub-allocation; withdraw disabled / limited if the platform allows.
4. Update the sealed vault (1Password / OS keychain). Do not paste into chat, tickets, or git.
5. Restart **execution only**. Do not restart research workers with the new secret in their environment.
6. Confirm research/briefing/ingest still have no trading env vars.
7. Paper/testnet signing check before mainnet key is considered good.
8. Remove halt when Principal is ready.
9. Record rotation (timestamp, who, last-4 of public address only).

## If a secret may have leaked

Treat as incident: halt, revoke, rotate, audit git history and logs for the material, assume compromise of that API wallet.
