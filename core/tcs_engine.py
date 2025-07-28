def score_tcs(signal_data):
    score = 0

    if detect_structure(signal_data):
        score += 20
    if check_tf_alignment(signal_data):
        score += 15
    if assess_momentum(signal_data):
        score += 15
    if check_volatility(signal_data):
        score += 10
    if session_weighting(signal_data):
        score += 10
    if detect_liquidity_grab(signal_data):
        score += 10
    if check_rr(signal_data):
        score += 10
    score += signal_data.get("ai_sentiment_bonus", 0)

    return min(score, 100)

def classify_trade(score, rr):
    if score >= 94 and rr >= 3.5:
        return "hammer"
    elif 84 <= score < 94:
        return "shadow_strike"
    elif score >= 75:
        return "scalp"
    else:
        return "none"
