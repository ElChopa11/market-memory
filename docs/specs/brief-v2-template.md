# DONCAPO Market Intelligence — Telegram Report Template

Structure only. Every value below is a placeholder token in {CURLY_BRACES}.
No numbers, dates, or interpretations are invented — the bot fills these from
live data. If a data source is unavailable, the bot renders ⚪ and the literal
word `unavailable`, and does not omit the field.

## Legend (fixed, do not vary)

🟢  Confirmed / positive / live data
🟡  Developing / mixed / delayed data
🔴  Negative / stress / stale data
⚪  Missing / unavailable data
⚠️  Divergence
◇   Watch
✓   Confirmed
×   Invalidated

Rule: colour = data state, never a buy/sell recommendation.

## Message 1 — Executive

🧠 US CLOSE INTELLIGENCE
{DATE}

REGIME: {REGIME_LABEL}

Risk appetite  {RISK_APPETITE_ICON}
Liquidity      {LIQUIDITY_ICON}
Volatility     {VOLATILITY_ICON}
Rates          {RATES_ICON}
USD            {USD_ICON}
Crypto         {CRYPTO_ICON}

KEY TAKEAWAY
{3_SENTENCE_SUMMARY}

DATA HEALTH
{DATA_HEALTH_BAR} {DATA_HEALTH_PCT}%

## Message 2 — Market Dashboard

Asset      Last    Δ1D     Δ5D     Δ20D    Vol     Regime
S&P 500    {VAL}   {VAL}   {VAL}   {VAL}   {VAL}   {ICON}
Nasdaq     {VAL}   {VAL}   {VAL}   {VAL}   {VAL}   {ICON}
US 10Y     {VAL}   {VAL}   {VAL}   {VAL}   {VAL}   {ICON}
USD (DXY)  {VAL}   {VAL}   {VAL}   {VAL}   {VAL}   {ICON}
Oil        {VAL}   {VAL}   {VAL}   {VAL}   {VAL}   {ICON}
VIX        {VAL}   {VAL}   {VAL}   {VAL}   {VAL}   {ICON}
BTC        {VAL}   {VAL}   {VAL}   {VAL}   {VAL}   {ICON}
ETH        {VAL}   {VAL}   {VAL}   {VAL}   {VAL}   {ICON}

## Message 3 — Macro

MACRO TRANSMISSION
{DATE}

              Last      Δ1D     Δ5D     Δ20D    State
US 10Y        {VAL}     {VAL}   {VAL}   {VAL}   {ICON}
2s10s         {VAL}     {VAL}   {VAL}   {VAL}   {ICON}
DXY           {VAL}     {VAL}   {VAL}   {VAL}   {ICON}
Oil           {VAL}     {VAL}   {VAL}   {VAL}   {ICON}
Gold          {VAL}     {VAL}   {VAL}   {VAL}   {ICON}
Credit        {VAL}     {VAL}   {VAL}   {VAL}   {ICON}

TRANSMISSION CHAIN
Rates {RATES_DIR} → USD {USD_DIR} → Equities {EQ_DIR} → Risk {RISK_DIR}

DRIVER
{DOMINANT_DRIVER_OR_"indeterminate"}

## Message 4 — Crypto

CRYPTO TAPE
{DATE}

          Last      Δ1D     Δ5D     Δ20D    vs BTC   State
BTC       {VAL}     {VAL}   {VAL}   {VAL}   —        {ICON}
ETH       {VAL}     {VAL}   {VAL}   {VAL}   {VAL}    {ICON}
SOL       {VAL}     {VAL}   {VAL}   {VAL}   {VAL}    {ICON}
ZEC       {VAL}     {VAL}   {VAL}   {VAL}   {VAL}    {ICON}
XMR       {VAL}     {VAL}   {VAL}   {VAL}   {VAL}    {ICON}

BTC vs NDX correlation (20d): {VAL} {ICON}

CLUSTER LEADERSHIP
{LEADING_CLUSTER_OR_"none"}

## Message 5 — Positioning

BTC POSITIONING

PRICE        {VAL}     Δ1D {VAL}
OPEN INT     {VAL}     Δ1D {VAL}
FUNDING      {VAL}     z30d {VAL}  {BAR}
BASIS        {VAL}     z30d {VAL}  {BAR}
LIQUIDATIONS {VAL}     {BAR}
CB PREMIUM   {VAL}     z30d {VAL}

OI × PRICE STATE
{QUADRANT_LABEL}   {ICON}
  price↑ OI↑ = long build
  price↑ OI↓ = short cover
  price↓ OI↑ = short build
  price↓ OI↓ = long liquidation

ETH POSITIONING

PRICE        {VAL}     Δ1D {VAL}
OPEN INT     {VAL}     Δ1D {VAL}
FUNDING      {VAL}     z30d {VAL}  {BAR}
BASIS        {VAL}     z30d {VAL}  {BAR}
LIQUIDATIONS {VAL}     {BAR}
CB PREMIUM   {VAL}     z30d {VAL}

OI × PRICE STATE
{QUADRANT_LABEL}   {ICON}
  price↑ OI↑ = long build
  price↑ OI↓ = short cover
  price↓ OI↑ = short build
  price↓ OI↓ = long liquidation

POSITIONING CONFIDENCE
{CONFIDENCE_OR_"INSUFFICIENT HISTORY"}

## Message 6 — News

CATALYST RADAR — NEXT 24H
🇺🇸 MACRO      {BAR} {LEVEL}
🇺🇸 EQUITIES   {BAR} {LEVEL}
₿  CRYPTO     {BAR} {LEVEL}
🌍 EUROPE     {BAR} {LEVEL}
🌏 ASIA       {BAR} {LEVEL}

Dated events:
{EVENT_LIST_OR_"none scheduled"}

NEWS IMPACT MATRIX
Story     Asset     Direction  Magnitude  Confidence
{STORY}   {ASSET}   {DIR}      {MAG}      {CONF}

## Message 7 — Scenarios

BTC SCENARIO MAP
Condition       Market behaviour   Confirmation
Price↑ + OI↑    {LABEL}            {CONDITION}
Price↑ + OI↓    {LABEL}            {CONDITION}
Price↓ + OI↑    {LABEL}            {CONDITION}
Price↓ + OI↓    {LABEL}            {CONDITION}

INVALIDATION CONDITIONS
- {CONDITION_1}
- {CONDITION_2}
- {CONDITION_3}

## Message 8 — Audit

AUDIT

Data quality: {DATA_HEALTH_PCT}%
Freshest feed: {FRESHEST_FEED_NAME}
Major missing feeds: {MISSING_FEEDS_LIST}

Informational only.

## Notes for the bot

- Every panel above is a fixed layout — the bot must not invent narrative
  filler when a field has no data; render the ⚪ / unavailable state instead.
- "What Changed?" and "Anomaly Radar" panels are optional add-ons, not shown
  here, since they depend on prior-session snapshots the bot may not yet store.
  Add once history retention is confirmed.
- Confidence / precision scorecards should only populate once a defined
  signal-tracking methodology and historical log exist — otherwise omit rather
  than fabricate a percentage.
