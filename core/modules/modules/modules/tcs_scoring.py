# tcs_scoring.py
# Trade Confidence Score engine (0–100)

def calculate_tcs(trade_context):
    """
    Returns a TCS (Trade Confidence Score) from 0 to 100
    based on provided confluence factors in trade_context.
    """
    print("Calculating TCS...")
    return 75  # Placeholder confidence score

if __name__ == "__main__":
    sample = {"rsi": 30, "engulfing": True, "session": "NY"}
    score = calculate_tcs(sample)
    print(f"TCS Score: {score}")
