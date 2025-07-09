# BITTEN Stealth Protocol — Modular Cloaking Layer

## Functions:
- entry_delay(): Adds 1–12s delay
- lot_size_jitter(): Adjusts lot ±3–7%
- tp_sl_offset(): ±1–3 pip shift on TP/SL
- ghost_skip(): Skips ~1 in 6 trades
- vol_cap(): Caps active trades per asset
- execution_shuffle(): Randomizes queue

All actions are logged to /logs/stealth_log.txt
