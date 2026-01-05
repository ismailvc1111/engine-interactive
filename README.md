# Engine Interactive Trading Bot

This repository contains a lightweight, event-driven trading engine with martingale-style strategies (CDM, WDM, ZRM, IZRM), a paper-trading broker, and a simple backtest runner.

## Layout

```
trading_bot/
├── main.py              # Backtest demo entry point
├── requirements.txt     # Python dependencies
├── config.py            # Configuration schemas (dataclasses + enums)
├── core/                # Engine, events, shared models, helpers
├── broker/              # Broker interfaces + paper broker
└── strategies/          # Strategy implementations
```

## Quickstart

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r trading_bot/requirements.txt
   ```
2. Run the sample backtest:
   ```bash
   python -m trading_bot.main
   ```

The sample generates synthetic sine-wave ticks for SPY and prints basic per-cycle metrics. The engine is deterministic and auditable—strategy logic is fully encapsulated and shares a single paper broker for both backtests and future live adapters.
