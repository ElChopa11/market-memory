# Morning brief row labels

The Telegram message does not repeat these labels. They do not change from one morning to the next. The Symbol column in the message is the proxy ticker that was quoted.

| Symbol in the message | Slot | Label |
|---|---|---|
| SPY | ES | SPY ETF (proxy for S&P 500; not ES futures) |
| QQQ | NQ | QQQ ETF (proxy for Nasdaq-100; not NQ futures) |
| US10Y | US10Y | US 10Y yield (FRED) |
| UUP | DXY | UUP ETF (USD proxy; not DX futures / DXY) |
| USO | CL | USO ETF (WTI oil proxy; not CL futures) |
| VIX | VIX | CBOE VIX (structurally unavailable without Cboe entitlement; not on the Polygon stocks plan) |
| BTC | BTC | HL BTC-USDC perp mid (not CoinGecko spot) |
| ETH | ETH | HL ETH-USDC perp mid (not CoinGecko spot) |

Funding in the message is the Hyperliquid hourly rate, annualised (`hourly × 24 × 365`), and only when it is off the interest baseline. That baseline is 0.01% per 8 hours (`0.0001`), paid each hour at one eighth: `0.0000125` per hour. A 6-decimal print within half of `1e-6` of that rate (`0.000012` and `0.000013`) is the baseline and is not a row. Open interest is rounded to a whole number. Basis is shown only beside the prior capture. A slot with no last, including VIX, is named on the `gaps:` line.
