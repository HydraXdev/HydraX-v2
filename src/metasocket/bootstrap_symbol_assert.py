# /root/HydraX-v2/src/metasocket/bootstrap_symbol_assert.py
from symbols import ACTIVE_SYMBOLS, DISABLED_SYMBOLS, EXPECTED_ACTIVE_COUNT


def assert_symbols():
    active = list(dict.fromkeys(ACTIVE_SYMBOLS))
    assert len(active) == EXPECTED_ACTIVE_COUNT, f"{len(active)} != {EXPECTED_ACTIVE_COUNT}"
    assert "XAGUSD" in active and "XAUUSD" in active, "Metals must be active"
    assert "USDCAD" not in active, "USDCAD must remain disabled"


if __name__ == "__main__":
    assert_symbols()
    print(f"✅ Symbols OK: {len(ACTIVE_SYMBOLS)} active")
