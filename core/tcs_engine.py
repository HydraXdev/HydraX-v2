def score_tcs(signal_data):
    """
    TCS++ Engine - Multi-factor scoring system (0-100 points)
    Evaluates trade quality across multiple dimensions
    """
    score = 0
    breakdown = {}
    
    # 1. Market Structure Analysis (20 points max)
    structure_score = analyze_market_structure(signal_data)
    score += structure_score
    breakdown['structure'] = structure_score
    
    # 2. Timeframe Alignment (15 points max)
    tf_score = check_timeframe_alignment(signal_data)
    score += tf_score
    breakdown['timeframe_alignment'] = tf_score
    
    # 3. Momentum Assessment (15 points max)
    momentum_score = assess_momentum_strength(signal_data)
    score += momentum_score
    breakdown['momentum'] = momentum_score
    
    # 4. Volatility Analysis (10 points max)
    volatility_score = analyze_volatility_conditions(signal_data)
    score += volatility_score
    breakdown['volatility'] = volatility_score
    
    # 5. Session Weighting (10 points max)
    session_score = calculate_session_weight(signal_data)
    score += session_score
    breakdown['session'] = session_score
    
    # 6. Liquidity Analysis (10 points max)
    liquidity_score = detect_liquidity_patterns(signal_data)
    score += liquidity_score
    breakdown['liquidity'] = liquidity_score
    
    # 7. Risk/Reward Quality (10 points max)
    rr_score = evaluate_risk_reward(signal_data)
    score += rr_score
    breakdown['risk_reward'] = rr_score
    
    # 8. AI Sentiment Bonus (10 points max)
    ai_bonus = signal_data.get('ai_sentiment_bonus', 0)
    ai_bonus = min(ai_bonus, 10)  # Cap at 10 points
    score += ai_bonus
    breakdown['ai_sentiment'] = ai_bonus
    
    # Store breakdown in signal_data for transparency
    signal_data['tcs_breakdown'] = breakdown
    
    return min(score, 100)


def classify_trade(score, rr, signal_data=None):
    """
    Trade classification based on TCS++ score and risk/reward ratio
    Returns trade type and confidence level
    """
    # Extract additional factors if available
    momentum = signal_data.get('momentum_strength', 0) if signal_data else 0
    structure_quality = signal_data.get('structure_quality', 0) if signal_data else 0
    
    # Hammer trades - Elite setups (94+ TCS, 3.5+ RR)
    if score >= 94 and rr >= 3.5:
        if momentum > 0.8 and structure_quality > 0.9:
            return "hammer_elite"  # Top 1% of trades
        return "hammer"
    
    # Shadow Strike trades - High probability (84-93 TCS)
    elif 84 <= score < 94:
        if rr >= 3.0:
            return "shadow_strike_premium"
        return "shadow_strike"
    
    # Scalp trades - Quick opportunities (75-83 TCS)
    elif 75 <= score < 84:
        if signal_data and signal_data.get('session') in ['london', 'new_york']:
            return "scalp_session"  # Session-optimized scalp
        return "scalp"
    
    # Watchlist trades - Monitor but don't execute (65-74 TCS)
    elif 65 <= score < 75:
        return "watchlist"
    
    # No trade - Below threshold
    else:
        return "none"


# Component Analysis Functions

def analyze_market_structure(signal_data):
    """
    Analyze market structure quality (20 points max)
    Evaluates trend clarity, support/resistance levels, and pattern completion
    """
    score = 0
    
    # Check for clear trend structure
    if signal_data.get('trend_clarity', 0) > 0.7:
        score += 8
    elif signal_data.get('trend_clarity', 0) > 0.5:
        score += 6
    elif signal_data.get('trend_clarity', 0) > 0.3:
        score += 3
    
    # Support/Resistance quality
    sr_quality = signal_data.get('sr_quality', 0)
    if sr_quality > 0.8:
        score += 7
    elif sr_quality > 0.6:
        score += 5
    elif sr_quality > 0.4:
        score += 3
    
    # Pattern completion
    if signal_data.get('pattern_complete', False):
        score += 5
    elif signal_data.get('pattern_forming', False):
        score += 3
    
    # Store quality metric
    signal_data['structure_quality'] = score / 20.0
    
    return min(score, 20)


def check_timeframe_alignment(signal_data):
    """
    Check multi-timeframe alignment (15 points max)
    Higher alignment = stronger confluence
    """
    score = 0
    aligned_timeframes = 0
    
    # Check each timeframe
    timeframes = ['M15', 'H1', 'H4', 'D1']
    weights = [2, 4, 5, 4]  # Weight distribution
    
    for tf, weight in zip(timeframes, weights):
        if signal_data.get(f'{tf}_aligned', False):
            score += weight
            aligned_timeframes += 1
    
    # Bonus for perfect alignment
    if aligned_timeframes == 4:
        score = 15
    
    return min(score, 15)


def assess_momentum_strength(signal_data):
    """
    Assess momentum indicators (15 points max)
    RSI, MACD, and volume confirmation
    """
    score = 0
    
    # RSI momentum
    rsi = signal_data.get('rsi', 50)
    if 25 <= rsi <= 35 or 65 <= rsi <= 75:  # Strong momentum zones
        score += 5
    elif 35 < rsi <= 45 or 55 <= rsi < 65:  # Good momentum
        score += 3
    elif 45 < rsi < 55:  # Neutral zone
        score += 2
    
    # MACD alignment
    if signal_data.get('macd_aligned', False):
        score += 5
    elif signal_data.get('macd_divergence', False):
        score += 3  # Divergence can be powerful
    
    # Volume confirmation
    volume_ratio = signal_data.get('volume_ratio', 1.0)
    if volume_ratio > 1.5:
        score += 5
    elif volume_ratio > 1.2:
        score += 3
    elif volume_ratio > 1.0:
        score += 1
    
    # Store momentum strength
    signal_data['momentum_strength'] = score / 15.0
    
    return min(score, 15)


def analyze_volatility_conditions(signal_data):
    """
    Analyze volatility for optimal trading conditions (10 points max)
    """
    score = 0
    
    # ATR-based volatility check
    atr = signal_data.get('atr', 20)
    if 15 <= atr <= 50:  # Optimal volatility range
        score += 5
    elif 10 <= atr < 15 or 50 < atr <= 80:
        score += 3
    
    # Spread conditions
    spread_ratio = signal_data.get('spread_ratio', 1.0)
    if spread_ratio < 1.5:  # Good spread
        score += 3
    elif spread_ratio < 2.0:
        score += 1
    
    # Volatility consistency
    if signal_data.get('volatility_stable', True):
        score += 2
    
    return min(score, 10)


def calculate_session_weight(signal_data):
    """
    Weight based on trading session (10 points max)
    """
    session = signal_data.get('session', 'unknown')
    session_scores = {
        'london': 10,      # Prime session
        'new_york': 9,     # Strong session
        'overlap': 8,      # High volatility
        'tokyo': 6,        # Good for JPY pairs
        'sydney': 5,       # Lower activity
        'dead_zone': 2,    # Minimal activity
        'unknown': 0
    }
    
    return session_scores.get(session, 0)


def detect_liquidity_patterns(signal_data):
    """
    Detect liquidity grabs and institutional activity (10 points max)
    """
    score = 0
    
    # Liquidity grab detected
    if signal_data.get('liquidity_grab', False):
        score += 5
    
    # Stop hunt pattern
    if signal_data.get('stop_hunt_detected', False):
        score += 3
    
    # Institutional levels
    if signal_data.get('near_institutional_level', False):
        score += 2
    
    return min(score, 10)


def evaluate_risk_reward(signal_data):
    """
    Evaluate risk/reward quality (10 points max)
    """
    rr_ratio = signal_data.get('rr', 1.0)
    
    if rr_ratio >= 4.0:
        return 10
    elif rr_ratio >= 3.5:
        return 9
    elif rr_ratio >= 3.0:
        return 8
    elif rr_ratio >= 2.5:
        return 6
    elif rr_ratio >= 2.0:
        return 4
    elif rr_ratio >= 1.5:
        return 2
    else:
        return 0
