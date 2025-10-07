# /root/HydraX-v2/src/metasocket/symbols.py
ACTIVE_SYMBOLS = [
    # Majors (6)
    "EURUSD","GBPUSD","USDCHF","USDJPY","AUDUSD","NZDUSD",
    # Crosses (10)
    "EURJPY","GBPJPY","EURGBP","EURAUD","GBPCAD","AUDJPY","NZDJPY","CHFJPY","CADJPY","AUDCAD",
    # Additional (4)
    "USDCNH","AUDNZD","CADCHF","NZDCAD",
    # Metals (2)
    "XAUUSD","XAGUSD",
]
DISABLED_SYMBOLS = ["USDCAD"]
EXPECTED_ACTIVE_COUNT = 22