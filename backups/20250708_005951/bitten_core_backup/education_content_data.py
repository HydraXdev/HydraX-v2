"""
Educational Content Data for HydraX Trading Platform
Real-world, practical content for trader education
"""

from typing import Dict, List, Any
from datetime import datetime

# Quiz Questions Database
QUIZ_QUESTIONS = {
    "risk_management": [
        {
            "id": "rm_001",
            "question": "You have $10,000 in your account. What's the maximum you should risk on a single trade according to the 2% rule?",
            "options": ["$100", "$200", "$500", "$1,000"],
            "correct": 1,
            "explanation": "The 2% rule suggests risking no more than 2% of your account on any single trade. $10,000 × 0.02 = $200"
        },
        {
            "id": "rm_002",
            "question": "Your stop loss is 50 pips away and you want to risk $100. If 1 pip = $1 per micro lot, how many micro lots should you trade?",
            "options": ["1 micro lot", "2 micro lots", "5 micro lots", "10 micro lots"],
            "correct": 1,
            "explanation": "Risk per pip = $100 ÷ 50 pips = $2 per pip. Since 1 micro lot = $1 per pip, you need 2 micro lots."
        },
        {
            "id": "rm_003",
            "question": "What's the purpose of a trailing stop loss?",
            "options": [
                "To guarantee profits",
                "To lock in profits while allowing for further gains",
                "To increase leverage",
                "To avoid margin calls"
            ],
            "correct": 1,
            "explanation": "A trailing stop follows the price up but stays fixed when price moves down, protecting profits while allowing upside."
        },
        {
            "id": "rm_004",
            "question": "You're on a 5-trade losing streak. What should you do?",
            "options": [
                "Double your position size to recover losses",
                "Switch to a different strategy immediately",
                "Take a break and review your trades",
                "Add more money to your account"
            ],
            "correct": 2,
            "explanation": "After consecutive losses, it's crucial to pause, analyze what went wrong, and ensure you're following your plan."
        },
        {
            "id": "rm_005",
            "question": "What's the Risk/Reward ratio if you risk $50 to potentially make $150?",
            "options": ["1:1", "1:2", "1:3", "3:1"],
            "correct": 2,
            "explanation": "Risk/Reward = Potential Profit ÷ Risk = $150 ÷ $50 = 3, written as 1:3"
        },
        {
            "id": "rm_006",
            "question": "Your account dropped from $5,000 to $2,500. What percentage gain do you need to break even?",
            "options": ["50%", "75%", "100%", "125%"],
            "correct": 2,
            "explanation": "You lost 50% ($2,500). To go from $2,500 back to $5,000, you need a 100% gain ($2,500 × 2 = $5,000)."
        },
        {
            "id": "rm_007",
            "question": "Which position sizing method adjusts trade size based on market volatility?",
            "options": [
                "Fixed lot sizing",
                "Percentage risk sizing",
                "ATR-based sizing",
                "Martingale sizing"
            ],
            "correct": 2,
            "explanation": "ATR (Average True Range) based sizing adjusts position size according to market volatility."
        },
        {
            "id": "rm_008",
            "question": "What's the main risk of using high leverage?",
            "options": [
                "Lower potential profits",
                "Higher broker fees",
                "Faster account depletion on losses",
                "Slower order execution"
            ],
            "correct": 2,
            "explanation": "High leverage amplifies both gains and losses, potentially wiping out your account quickly on adverse moves."
        },
        {
            "id": "rm_009",
            "question": "You want to trade 3 positions. How should you allocate your 2% total risk?",
            "options": [
                "2% on each trade",
                "0.67% on each trade",
                "1% on the best setup, 0.5% on the others",
                "Risk depends on the setups"
            ],
            "correct": 1,
            "explanation": "To maintain 2% total risk across 3 trades: 2% ÷ 3 = 0.67% per trade."
        },
        {
            "id": "rm_010",
            "question": "What's a margin call?",
            "options": [
                "When your broker calls about a trading opportunity",
                "When your account equity falls below required margin",
                "When you need to add indicators to your chart",
                "When a trade hits take profit"
            ],
            "correct": 1,
            "explanation": "A margin call occurs when your account equity falls below the broker's required margin level."
        }
    ],
    
    "technical_analysis": [
        {
            "id": "ta_001",
            "question": "What does a 'Golden Cross' indicate?",
            "options": [
                "50 MA crossing below 200 MA",
                "50 MA crossing above 200 MA",
                "Price crossing above 50 MA",
                "RSI crossing above 70"
            ],
            "correct": 1,
            "explanation": "A Golden Cross occurs when the 50-day MA crosses above the 200-day MA, often signaling a bullish trend."
        },
        {
            "id": "ta_002",
            "question": "An RSI reading of 75 typically indicates:",
            "options": ["Oversold", "Neutral", "Overbought", "Strong downtrend"],
            "correct": 2,
            "explanation": "RSI above 70 indicates overbought conditions, suggesting the asset may be due for a pullback."
        },
        {
            "id": "ta_003",
            "question": "What pattern looks like a 'W' and often signals a reversal?",
            "options": [
                "Head and Shoulders",
                "Double Bottom",
                "Rising Wedge",
                "Bear Flag"
            ],
            "correct": 1,
            "explanation": "A Double Bottom forms a 'W' shape and typically signals a bullish reversal after a downtrend."
        },
        {
            "id": "ta_004",
            "question": "In a strong uptrend, where do prices typically find support?",
            "options": [
                "Previous resistance levels",
                "Moving averages",
                "Round numbers",
                "All of the above"
            ],
            "correct": 3,
            "explanation": "In uptrends, prices often bounce off moving averages, previous resistance turned support, and psychological round numbers."
        },
        {
            "id": "ta_005",
            "question": "What does increasing volume on a breakout suggest?",
            "options": [
                "The breakout is likely false",
                "The breakout has strong conviction",
                "Traders are uncertain",
                "A reversal is coming"
            ],
            "correct": 1,
            "explanation": "High volume on a breakout confirms strong participation and increases the probability of follow-through."
        },
        {
            "id": "ta_006",
            "question": "A Doji candlestick indicates:",
            "options": [
                "Strong buying pressure",
                "Strong selling pressure",
                "Indecision in the market",
                "Trend continuation"
            ],
            "correct": 2,
            "explanation": "A Doji has nearly equal open and close prices, showing indecision between buyers and sellers."
        },
        {
            "id": "ta_007",
            "question": "What's the key characteristic of a Bull Flag pattern?",
            "options": [
                "Sharp move down, followed by consolidation",
                "Sharp move up, followed by slight downward consolidation",
                "Horizontal price movement",
                "V-shaped recovery"
            ],
            "correct": 1,
            "explanation": "A Bull Flag shows a strong upward move (the pole) followed by a slight downward consolidation (the flag)."
        },
        {
            "id": "ta_008",
            "question": "MACD histogram turning positive indicates:",
            "options": [
                "MACD line crossed below signal line",
                "MACD line crossed above signal line",
                "Price is oversold",
                "Volume is increasing"
            ],
            "correct": 1,
            "explanation": "The MACD histogram turns positive when the MACD line crosses above the signal line, indicating bullish momentum."
        },
        {
            "id": "ta_009",
            "question": "What does a 'pin bar' or 'hammer' candlestick suggest at a support level?",
            "options": [
                "Continuation of downtrend",
                "Potential bullish reversal",
                "Sideways movement ahead",
                "Increased volatility"
            ],
            "correct": 1,
            "explanation": "A pin bar with a long lower wick at support shows buyers stepped in, suggesting potential reversal."
        },
        {
            "id": "ta_010",
            "question": "Fibonacci retracement levels are based on:",
            "options": [
                "Moving average calculations",
                "Mathematical ratios from the Fibonacci sequence",
                "Previous day's high and low",
                "Trading volume"
            ],
            "correct": 1,
            "explanation": "Fibonacci retracements use ratios (23.6%, 38.2%, 61.8%) derived from the Fibonacci sequence."
        }
    ],
    
    "market_psychology": [
        {
            "id": "mp_001",
            "question": "What emotion typically drives traders to hold losing positions too long?",
            "options": ["Greed", "Fear", "Hope", "Confidence"],
            "correct": 2,
            "explanation": "Hope that the trade will turn around prevents traders from cutting losses at predetermined levels."
        },
        {
            "id": "mp_002",
            "question": "FOMO stands for:",
            "options": [
                "Fear Of Missing Out",
                "First Order Market Open",
                "Forex Order Management Option",
                "Financial Options Market Order"
            ],
            "correct": 0,
            "explanation": "FOMO (Fear Of Missing Out) causes traders to chase moves and enter trades at poor prices."
        },
        {
            "id": "mp_003",
            "question": "What's 'revenge trading'?",
            "options": [
                "Trading against a specific broker",
                "Copying another trader's positions",
                "Aggressive trading to recover losses",
                "Trading during high volatility"
            ],
            "correct": 2,
            "explanation": "Revenge trading is emotionally-driven aggressive trading attempting to quickly recover losses, often leading to bigger losses."
        },
        {
            "id": "mp_004",
            "question": "The 'herd mentality' in trading refers to:",
            "options": [
                "Using multiple indicators",
                "Following what everyone else is doing",
                "Trading in groups",
                "Diversifying positions"
            ],
            "correct": 1,
            "explanation": "Herd mentality is following the crowd without independent analysis, often leading to buying tops and selling bottoms."
        },
        {
            "id": "mp_005",
            "question": "What typically happens to trading volume during fear-driven selloffs?",
            "options": [
                "Volume decreases significantly",
                "Volume remains constant",
                "Volume spikes dramatically",
                "Volume becomes erratic"
            ],
            "correct": 2,
            "explanation": "Fear-driven selloffs see dramatic volume spikes as panicked traders rush to exit positions."
        },
        {
            "id": "mp_006",
            "question": "Confirmation bias in trading means:",
            "options": [
                "Waiting for trade confirmation",
                "Only seeing information that supports your view",
                "Confirming orders before execution",
                "Using multiple timeframes"
            ],
            "correct": 1,
            "explanation": "Confirmation bias leads traders to focus only on information supporting their position while ignoring contrary evidence."
        },
        {
            "id": "mp_007",
            "question": "What's the psychology behind support and resistance levels?",
            "options": [
                "Random price points",
                "Broker manipulation",
                "Collective memory of traders",
                "Computer algorithms"
            ],
            "correct": 2,
            "explanation": "Support and resistance work because many traders remember and react to previous important price levels."
        },
        {
            "id": "mp_008",
            "question": "Why do most traders fail to follow their stop losses?",
            "options": [
                "Stops are set too tight",
                "Emotional attachment to being right",
                "Market manipulation",
                "Technical issues"
            ],
            "correct": 1,
            "explanation": "Emotional attachment and the need to be right override logical risk management decisions."
        },
        {
            "id": "mp_009",
            "question": "The 'disposition effect' describes traders tendency to:",
            "options": [
                "Trade too frequently",
                "Sell winners too early and hold losers too long",
                "Avoid trading during news",
                "Use too much leverage"
            ],
            "correct": 1,
            "explanation": "The disposition effect is the tendency to sell profitable positions too quickly while holding losing positions hoping for recovery."
        },
        {
            "id": "mp_010",
            "question": "What's the best way to combat emotional trading?",
            "options": [
                "Trade smaller positions",
                "Use more indicators",
                "Have a written trading plan",
                "Trade only major pairs"
            ],
            "correct": 2,
            "explanation": "A written trading plan with clear rules helps override emotional decisions during market action."
        }
    ],
    
    "trading_strategies": [
        {
            "id": "ts_001",
            "question": "In trend following, when should you typically enter a trade?",
            "options": [
                "At the start of a new trend",
                "During pullbacks in an established trend",
                "When the trend reverses",
                "At resistance levels"
            ],
            "correct": 1,
            "explanation": "Trend followers typically enter during pullbacks to get better risk/reward within established trends."
        },
        {
            "id": "ts_002",
            "question": "What's the main advantage of scalping?",
            "options": [
                "Large profit per trade",
                "Less time in the market means less risk",
                "Requires less capital",
                "Works in all market conditions"
            ],
            "correct": 1,
            "explanation": "Scalping's quick in-and-out approach reduces exposure to unexpected market moves."
        },
        {
            "id": "ts_003",
            "question": "A breakout trader would most likely enter when:",
            "options": [
                "Price bounces off support",
                "Price breaks above resistance with volume",
                "RSI shows oversold",
                "During low volatility"
            ],
            "correct": 1,
            "explanation": "Breakout traders enter when price breaks key levels with strong volume confirmation."
        },
        {
            "id": "ts_004",
            "question": "What's the key principle of mean reversion trading?",
            "options": [
                "Trends always continue",
                "Prices tend to return to average levels",
                "Volume predicts direction",
                "News drives all moves"
            ],
            "correct": 1,
            "explanation": "Mean reversion assumes prices that move too far from average will eventually return to normal levels."
        },
        {
            "id": "ts_005",
            "question": "Position trading typically involves:",
            "options": [
                "Holding trades for minutes",
                "Holding trades for hours",
                "Holding trades for days",
                "Holding trades for weeks to months"
            ],
            "correct": 3,
            "explanation": "Position traders hold trades for extended periods, focusing on major trends rather than short-term fluctuations."
        },
        {
            "id": "ts_006",
            "question": "What's a 'confluence' in trading?",
            "options": [
                "When price moves quickly",
                "Multiple indicators pointing to the same conclusion",
                "Trading multiple assets",
                "High trading volume"
            ],
            "correct": 1,
            "explanation": "Confluence occurs when multiple technical factors align, strengthening the trade signal."
        },
        {
            "id": "ts_007",
            "question": "The best time to trade a ranging market is:",
            "options": [
                "Never trade ranges",
                "Buy at support, sell at resistance",
                "Only trade breakouts",
                "During high volatility"
            ],
            "correct": 1,
            "explanation": "Range trading profits from predictable bounces between established support and resistance levels."
        },
        {
            "id": "ts_008",
            "question": "What's the primary goal of a hedging strategy?",
            "options": [
                "Maximize profits",
                "Reduce or offset risk",
                "Increase leverage",
                "Time the market"
            ],
            "correct": 1,
            "explanation": "Hedging aims to reduce risk by taking offsetting positions, protecting against adverse moves."
        },
        {
            "id": "ts_009",
            "question": "Grid trading works best in:",
            "options": [
                "Strong trending markets",
                "Ranging/sideways markets",
                "News events",
                "Low liquidity"
            ],
            "correct": 1,
            "explanation": "Grid trading places orders at regular intervals and profits from oscillating prices in ranging markets."
        },
        {
            "id": "ts_010",
            "question": "What's the '3-touch rule' for trendlines?",
            "options": [
                "Draw lines with 3 indicators",
                "Wait for 3 candles to close",
                "Trendline is confirmed after 3 price touches",
                "Take profit after 3% gain"
            ],
            "correct": 2,
            "explanation": "A trendline becomes more reliable after price has touched and respected it at least 3 times."
        }
    ],
    
    "platform_usage": [
        {
            "id": "pu_001",
            "question": "What's the purpose of a demo account?",
            "options": [
                "To make real profits",
                "To practice without risking real money",
                "To get better spreads",
                "To avoid regulations"
            ],
            "correct": 1,
            "explanation": "Demo accounts let you practice strategies and learn the platform using virtual money."
        },
        {
            "id": "pu_002",
            "question": "What should you check before placing a trade on any platform?",
            "options": [
                "Only the entry price",
                "Lot size, stop loss, and take profit",
                "Just the chart",
                "Account balance only"
            ],
            "correct": 1,
            "explanation": "Always verify your lot size, stop loss, and take profit before executing to avoid costly mistakes."
        },
        {
            "id": "pu_003",
            "question": "What's a pending order?",
            "options": [
                "An order waiting for broker approval",
                "An order that executes at a future price level",
                "A cancelled order",
                "A market order"
            ],
            "correct": 1,
            "explanation": "Pending orders execute automatically when price reaches your specified level."
        },
        {
            "id": "pu_004",
            "question": "One-click trading means:",
            "options": [
                "Trades need one confirmation",
                "Trades execute instantly without confirmation",
                "You can only place one trade",
                "Trading with one indicator"
            ],
            "correct": 1,
            "explanation": "One-click trading executes trades instantly without confirmation dialogs - use with caution!"
        },
        {
            "id": "pu_005",
            "question": "What's the 'spread' shown on trading platforms?",
            "options": [
                "Broker's commission",
                "Difference between bid and ask price",
                "Daily price range",
                "Volatility indicator"
            ],
            "correct": 1,
            "explanation": "The spread is the difference between bid (sell) and ask (buy) prices, representing the cost to enter a trade."
        },
        {
            "id": "pu_006",
            "question": "Why is it important to use a VPS for automated trading?",
            "options": [
                "Better charts",
                "24/7 uptime and low latency",
                "Free trading signals",
                "Lower spreads"
            ],
            "correct": 1,
            "explanation": "VPS ensures your trading bots run 24/7 with stable internet and low latency to broker servers."
        },
        {
            "id": "pu_007",
            "question": "What does 'slippage' mean in order execution?",
            "options": [
                "Order was cancelled",
                "Execution price differs from requested price",
                "Platform error",
                "Slow internet"
            ],
            "correct": 1,
            "explanation": "Slippage occurs when your order fills at a different price than requested, common during high volatility."
        },
        {
            "id": "pu_008",
            "question": "The 'equity' shown on your platform represents:",
            "options": [
                "Your deposited amount",
                "Balance plus/minus open positions",
                "Available margin",
                "Profit this month"
            ],
            "correct": 1,
            "explanation": "Equity is your balance plus or minus any floating profit/loss from open positions."
        },
        {
            "id": "pu_009",
            "question": "What's a trailing stop in platform terms?",
            "options": [
                "A stop that moves with profitable positions",
                "A delayed stop loss",
                "Multiple stop losses",
                "A pending order type"
            ],
            "correct": 0,
            "explanation": "Trailing stops automatically move to lock in profits as your position moves favorably."
        },
        {
            "id": "pu_010",
            "question": "Why should you regularly check your platform's economic calendar?",
            "options": [
                "To see holidays",
                "To prepare for high-impact news events",
                "To check spread changes",
                "To see other traders' positions"
            ],
            "correct": 1,
            "explanation": "Economic calendars show upcoming news events that can cause significant market volatility."
        }
    ]
}

# Mission Scenarios Database
MISSIONS = {
    "story_missions": [
        {
            "id": "story_001",
            "title": "The Rookie's First Trade",
            "narrative": "Fresh out of training, you've just funded your first real account with $1,000. Your mentor calls: 'I see a perfect setup forming on EUR/USD. This is your moment.'",
            "objectives": [
                "Analyze the EUR/USD chart for the setup",
                "Calculate proper position size using 2% risk rule",
                "Place your first trade with stop loss and take profit",
                "Manage the trade as it develops"
            ],
            "success_criteria": {
                "risk_managed": True,
                "stop_loss_set": True,
                "position_sized_correctly": True
            },
            "rewards": {
                "xp": 100,
                "unlock": "Risk Management Badge"
            }
        },
        {
            "id": "story_002",
            "title": "The London Breakout",
            "narrative": "It's 3 AM New York time. London markets just opened and GBP/USD is coiling in a tight range. Your algorithm detects a potential breakout forming. Time to put your breakout strategy to the test.",
            "objectives": [
                "Identify the range boundaries",
                "Set breakout entry orders",
                "Calculate stop distance based on ATR",
                "Manage the breakout trade"
            ],
            "success_criteria": {
                "breakout_identified": True,
                "proper_entry_timing": True,
                "risk_reward_minimum": 2
            },
            "rewards": {
                "xp": 150,
                "unlock": "Breakout Trader Achievement"
            }
        },
        {
            "id": "story_003",
            "title": "The NFP Nightmare",
            "narrative": "It's the first Friday of the month. Non-Farm Payrolls are about to be released. You have three open positions. The market is holding its breath...",
            "objectives": [
                "Decide whether to close positions before news",
                "If keeping positions, adjust stops for volatility",
                "React appropriately to the news spike",
                "Protect your capital during high volatility"
            ],
            "success_criteria": {
                "capital_preserved": True,
                "decisions_documented": True,
                "no_panic_trades": True
            },
            "rewards": {
                "xp": 200,
                "unlock": "News Survivor Badge"
            }
        },
        {
            "id": "story_004",
            "title": "The Trend Rider",
            "narrative": "Gold has been in a strong uptrend for weeks. Your analysis shows a perfect pullback to the 50-day moving average. But markets are nervous about upcoming Fed announcements...",
            "objectives": [
                "Confirm the trend is still valid",
                "Time your entry on the pullback",
                "Set a trailing stop to ride the trend",
                "Scale out of the position at key levels"
            ],
            "success_criteria": {
                "trend_analysis_correct": True,
                "entry_at_support": True,
                "profit_protected": True
            },
            "rewards": {
                "xp": 175,
                "unlock": "Trend Master Certificate"
            }
        },
        {
            "id": "story_005",
            "title": "The Reversal Recognition",
            "narrative": "USD/JPY has been falling for days. Now you spot a potential double bottom forming at a major support level. Volume is picking up. Is this the reversal?",
            "objectives": [
                "Identify the double bottom pattern",
                "Wait for pattern confirmation",
                "Enter with proper risk management",
                "Set realistic profit targets"
            ],
            "success_criteria": {
                "pattern_identified": True,
                "confirmation_waited": True,
                "risk_reward_achieved": True
            },
            "rewards": {
                "xp": 225,
                "unlock": "Pattern Recognition Pro"
            }
        }
    ],
    
    "survival_scenarios": [
        {
            "id": "survival_001",
            "title": "Flash Crash Survival",
            "scenario": "The Swiss National Bank just removed the EUR/CHF peg. The market is in freefall. You have open positions.",
            "objectives": [
                "Assess your exposure immediately",
                "Close positions if possible",
                "Document lessons learned",
                "Survive with account intact"
            ],
            "market_conditions": {
                "volatility": "extreme",
                "liquidity": "very_low",
                "spreads": "widened_10x"
            },
            "success_metrics": {
                "max_drawdown": 20,
                "decisions_made": ["close_all", "hedge", "wait"],
                "time_to_react": 300  # seconds
            }
        },
        {
            "id": "survival_002",
            "title": "The Margin Call Crisis",
            "scenario": "Overleveraged positions are moving against you. Account equity dropping fast. Margin call imminent.",
            "objectives": [
                "Calculate time until margin call",
                "Decide which positions to close",
                "Preserve remaining capital",
                "Learn from the experience"
            ],
            "market_conditions": {
                "positions": 5,
                "average_loss": -8,
                "margin_level": 130
            },
            "success_metrics": {
                "avoided_margin_call": True,
                "capital_preserved_percent": 50,
                "lesson_documented": True
            }
        },
        {
            "id": "survival_003",
            "title": "Weekend Gap Disaster",
            "scenario": "Major news broke over the weekend. Markets open with massive gaps. Your positions are deep underwater.",
            "objectives": [
                "Assess the damage calmly",
                "Decide whether to hold or close",
                "Implement damage control",
                "Adjust future weekend risk"
            ],
            "market_conditions": {
                "gap_size": "200_pips",
                "positions_affected": 3,
                "account_impact": -15
            },
            "success_metrics": {
                "panic_avoided": True,
                "logical_decisions": True,
                "future_plan_created": True
            }
        },
        {
            "id": "survival_004",
            "title": "The Correlation Crisis",
            "scenario": "You thought you were diversified, but all your positions are moving against you. Hidden correlations revealed.",
            "objectives": [
                "Identify the correlation issue",
                "Reduce correlated exposure",
                "Rebalance portfolio",
                "Implement correlation checks"
            ],
            "market_conditions": {
                "correlated_pairs": 4,
                "correlation_coefficient": 0.9,
                "portfolio_loss": -12
            },
            "success_metrics": {
                "correlation_reduced": True,
                "portfolio_balanced": True,
                "system_improved": True
            }
        },
        {
            "id": "survival_005",
            "title": "Black Swan Event",
            "scenario": "Unexpected geopolitical event. All majors in freefall. Safe havens spiking. Chaos in markets.",
            "objectives": [
                "Stay calm amid chaos",
                "Protect capital first",
                "Look for opportunity in chaos",
                "Document the experience"
            ],
            "market_conditions": {
                "vix_spike": 300,
                "major_moves": "500+_pips",
                "liquidity": "sporadic"
            },
            "success_metrics": {
                "account_survived": True,
                "opportunities_found": True,
                "experience_gained": True
            }
        }
    ],
    
    "hunt_missions": [
        {
            "id": "hunt_001",
            "title": "Bull Flag Hunter",
            "description": "Find and trade 3 bull flag patterns across any instruments",
            "objectives": [
                "Identify valid bull flag patterns",
                "Confirm with volume analysis",
                "Execute trades with proper R:R",
                "Document pattern performance"
            ],
            "requirements": {
                "patterns_found": 3,
                "min_risk_reward": 2,
                "win_rate_target": 60
            }
        },
        {
            "id": "hunt_002",
            "title": "Support Resistance Sniper",
            "description": "Identify and trade from major support/resistance levels",
            "objectives": [
                "Map out key S/R levels",
                "Wait for price action confirmation",
                "Trade the bounces or breaks",
                "Track level reliability"
            ],
            "requirements": {
                "levels_identified": 5,
                "trades_executed": 3,
                "confirmation_required": True
            }
        },
        {
            "id": "hunt_003",
            "title": "Divergence Detective",
            "description": "Hunt for RSI/MACD divergences across multiple timeframes",
            "objectives": [
                "Spot divergence formations",
                "Confirm with price action",
                "Time entries precisely",
                "Measure divergence reliability"
            ],
            "requirements": {
                "divergences_found": 4,
                "timeframes_used": ["H1", "H4", "D1"],
                "success_rate_target": 65
            }
        },
        {
            "id": "hunt_004",
            "title": "Volatility Vampire",
            "description": "Profit from high volatility events and expansions",
            "objectives": [
                "Identify volatility expansion setups",
                "Use ATR for position sizing",
                "Trade the volatility wisely",
                "Protect against whipsaws"
            ],
            "requirements": {
                "volatility_events": 3,
                "atr_multiplier_used": True,
                "profitable_trades": 2
            }
        },
        {
            "id": "hunt_005",
            "title": "Fibonacci Finder",
            "description": "Master the art of Fibonacci retracements and extensions",
            "objectives": [
                "Draw accurate Fib levels",
                "Trade from key Fib zones",
                "Combine with other confluence",
                "Track Fib level accuracy"
            ],
            "requirements": {
                "fib_setups_found": 5,
                "key_levels": ["38.2", "61.8", "161.8"],
                "confluence_required": True
            }
        }
    ],
    
    "daily_challenges": [
        {
            "id": "daily_001",
            "title": "Paper Trade Perfect",
            "description": "Execute 5 paper trades with perfect risk management",
            "time_limit": "24_hours",
            "requirements": {
                "trades": 5,
                "all_stops_set": True,
                "risk_per_trade_max": 2,
                "documentation_required": True
            }
        },
        {
            "id": "daily_002",
            "title": "Patience Pays",
            "description": "Wait for A+ setup without forcing trades",
            "time_limit": "market_session",
            "requirements": {
                "forced_trades": 0,
                "setup_quality": "A+",
                "patience_score": 90
            }
        },
        {
            "id": "daily_003",
            "title": "Multi-Timeframe Master",
            "description": "Analyze one pair across 5 timeframes before trading",
            "time_limit": "24_hours",
            "requirements": {
                "timeframes_analyzed": 5,
                "confluence_found": True,
                "analysis_documented": True
            }
        },
        {
            "id": "daily_004",
            "title": "News Ninja",
            "description": "Trade successfully around a high-impact news event",
            "time_limit": "news_window",
            "requirements": {
                "news_awareness": True,
                "position_managed": True,
                "volatility_handled": True
            }
        },
        {
            "id": "daily_005",
            "title": "Discipline Day",
            "description": "Follow your trading plan exactly - no deviations",
            "time_limit": "24_hours",
            "requirements": {
                "plan_followed": 100,
                "emotional_trades": 0,
                "rules_broken": 0
            }
        }
    ]
}

# Achievements Database
ACHIEVEMENTS = {
    "beginner": [
        {
            "id": "ach_001",
            "name": "First Steps",
            "description": "Complete your first trade with proper risk management",
            "requirements": {
                "trades_completed": 1,
                "stop_loss_used": True,
                "risk_percentage_max": 2
            },
            "reward": {"xp": 50, "badge": "rookie_trader"}
        },
        {
            "id": "ach_002",
            "name": "Risk Guardian",
            "description": "Complete 10 trades without exceeding 2% risk",
            "requirements": {
                "trades_completed": 10,
                "max_risk_exceeded": 0,
                "consecutive": True
            },
            "reward": {"xp": 100, "badge": "risk_guardian"}
        },
        {
            "id": "ach_003",
            "name": "Chart Reader",
            "description": "Correctly identify 20 chart patterns",
            "requirements": {
                "patterns_identified": 20,
                "accuracy_minimum": 80
            },
            "reward": {"xp": 150, "badge": "pattern_spotter"}
        },
        {
            "id": "ach_004",
            "name": "Steady Hands",
            "description": "Avoid overtrading for 5 consecutive days",
            "requirements": {
                "days": 5,
                "max_trades_per_day": 3,
                "consecutive": True
            },
            "reward": {"xp": 100, "badge": "disciplined_trader"}
        },
        {
            "id": "ach_005",
            "name": "Knowledge Seeker",
            "description": "Complete all beginner education modules",
            "requirements": {
                "modules_completed": ["risk", "basics", "psychology"],
                "quiz_scores_minimum": 70
            },
            "reward": {"xp": 200, "unlock": "intermediate_content"}
        }
    ],
    
    "intermediate": [
        {
            "id": "ach_006",
            "name": "Profit Protector",
            "description": "Successfully use trailing stops on 10 winning trades",
            "requirements": {
                "trailing_stops_used": 10,
                "profitable_exits": 10,
                "profit_protected_minimum": 50
            },
            "reward": {"xp": 250, "badge": "profit_protector"}
        },
        {
            "id": "ach_007",
            "name": "Strategy Master",
            "description": "Achieve 60% win rate over 50 trades using one strategy",
            "requirements": {
                "trades_completed": 50,
                "win_rate_minimum": 60,
                "single_strategy": True
            },
            "reward": {"xp": 500, "badge": "strategy_master"}
        },
        {
            "id": "ach_008",
            "name": "Market Timer",
            "description": "Successfully trade 3 different market sessions",
            "requirements": {
                "sessions_traded": ["london", "new_york", "asian"],
                "profitable_sessions": 2
            },
            "reward": {"xp": 300, "badge": "global_trader"}
        },
        {
            "id": "ach_009",
            "name": "Comeback Kid",
            "description": "Recover from a 10% drawdown using proper risk management",
            "requirements": {
                "drawdown_experienced": 10,
                "recovery_achieved": True,
                "revenge_trading": False
            },
            "reward": {"xp": 400, "badge": "resilient_trader"}
        },
        {
            "id": "ach_010",
            "name": "Confluence Hunter",
            "description": "Execute 20 trades with 3+ confluence factors",
            "requirements": {
                "trades_with_confluence": 20,
                "minimum_factors": 3,
                "win_rate_boost": True
            },
            "reward": {"xp": 350, "badge": "confluence_master"}
        }
    ],
    
    "advanced": [
        {
            "id": "ach_011",
            "name": "Risk Adjusted Returns",
            "description": "Achieve Sharpe ratio > 2 over 100 trades",
            "requirements": {
                "trades_completed": 100,
                "sharpe_ratio_minimum": 2,
                "consistent_risk": True
            },
            "reward": {"xp": 1000, "badge": "elite_trader"}
        },
        {
            "id": "ach_012",
            "name": "Multi-Strategy Maven",
            "description": "Profitably employ 3 different strategies",
            "requirements": {
                "strategies_used": 3,
                "profitable_each": True,
                "trades_per_strategy_min": 30
            },
            "reward": {"xp": 750, "badge": "versatile_trader"}
        },
        {
            "id": "ach_013",
            "name": "Mentor Material",
            "description": "Help 10 other traders improve their performance",
            "requirements": {
                "traders_mentored": 10,
                "positive_feedback": 8,
                "improvement_shown": True
            },
            "reward": {"xp": 800, "badge": "mentor", "unlock": "teaching_tools"}
        },
        {
            "id": "ach_014",
            "name": "Market Survivor",
            "description": "Trade profitably through a major market crisis",
            "requirements": {
                "crisis_periods_survived": 1,
                "capital_preserved": True,
                "opportunities_captured": True
            },
            "reward": {"xp": 1500, "badge": "crisis_veteran"}
        },
        {
            "id": "ach_015",
            "name": "Consistency King",
            "description": "Achieve 12 consecutive profitable months",
            "requirements": {
                "profitable_months": 12,
                "consecutive": True,
                "max_monthly_drawdown": 10
            },
            "reward": {"xp": 2000, "badge": "consistency_crown"}
        }
    ]
}

# Video Content Metadata
VIDEO_CONTENT = {
    "beginner_series": [
        {
            "id": "vid_001",
            "title": "Trading Basics: What Moves Markets?",
            "duration": "15:23",
            "instructor": "Marcus Chen",
            "topics": ["supply_demand", "market_participants", "liquidity"],
            "url": "placeholder_url_001"
        },
        {
            "id": "vid_002",
            "title": "Risk Management: The 2% Rule Explained",
            "duration": "12:45",
            "instructor": "Sarah Williams",
            "topics": ["position_sizing", "stop_loss", "risk_reward"],
            "url": "placeholder_url_002"
        },
        {
            "id": "vid_003",
            "title": "Chart Patterns Every Trader Must Know",
            "duration": "22:10",
            "instructor": "Alex Rodriguez",
            "topics": ["double_tops", "flags", "triangles", "head_shoulders"],
            "url": "placeholder_url_003"
        },
        {
            "id": "vid_004",
            "title": "Platform Tutorial: Your First Trade",
            "duration": "18:30",
            "instructor": "Platform Team",
            "topics": ["interface", "order_types", "execution"],
            "url": "placeholder_url_004"
        },
        {
            "id": "vid_005",
            "title": "Psychology: Why 90% of Traders Fail",
            "duration": "25:15",
            "instructor": "Dr. James Mitchell",
            "topics": ["emotions", "discipline", "common_mistakes"],
            "url": "placeholder_url_005"
        }
    ],
    
    "intermediate_series": [
        {
            "id": "vid_006",
            "title": "Advanced Patterns: Harmonics and Fibonacci",
            "duration": "28:40",
            "instructor": "Elena Volkov",
            "topics": ["gartley", "butterfly", "fib_confluence"],
            "url": "placeholder_url_006"
        },
        {
            "id": "vid_007",
            "title": "Multi-Timeframe Analysis Masterclass",
            "duration": "35:20",
            "instructor": "Marcus Chen",
            "topics": ["top_down_analysis", "timeframe_confluence", "entry_timing"],
            "url": "placeholder_url_007"
        },
        {
            "id": "vid_008",
            "title": "Volume Profile: The Hidden Edge",
            "duration": "30:15",
            "instructor": "David Park",
            "topics": ["volume_analysis", "poc", "value_areas"],
            "url": "placeholder_url_008"
        },
        {
            "id": "vid_009",
            "title": "Building Your Trading Plan",
            "duration": "40:00",
            "instructor": "Sarah Williams",
            "topics": ["strategy_development", "backtesting", "rules"],
            "url": "placeholder_url_009"
        },
        {
            "id": "vid_010",
            "title": "Correlation Trading Strategies",
            "duration": "32:45",
            "instructor": "Alex Rodriguez",
            "topics": ["currency_correlations", "hedging", "pair_trading"],
            "url": "placeholder_url_010"
        }
    ],
    
    "advanced_series": [
        {
            "id": "vid_011",
            "title": "Algorithmic Trading Fundamentals",
            "duration": "45:30",
            "instructor": "Dr. Robert Kim",
            "topics": ["algo_basics", "backtesting", "optimization"],
            "url": "placeholder_url_011"
        },
        {
            "id": "vid_012",
            "title": "Market Microstructure for Traders",
            "duration": "38:20",
            "instructor": "Elena Volkov",
            "topics": ["order_flow", "market_makers", "liquidity_pools"],
            "url": "placeholder_url_012"
        },
        {
            "id": "vid_013",
            "title": "Options Strategies for Forex Traders",
            "duration": "42:15",
            "instructor": "Michael Thompson",
            "topics": ["fx_options", "hedging", "volatility_trading"],
            "url": "placeholder_url_013"
        },
        {
            "id": "vid_014",
            "title": "Portfolio Management and Diversification",
            "duration": "36:40",
            "instructor": "Dr. Lisa Chang",
            "topics": ["portfolio_theory", "risk_metrics", "optimization"],
            "url": "placeholder_url_014"
        },
        {
            "id": "vid_015",
            "title": "Trading Psychology: Peak Performance",
            "duration": "50:00",
            "instructor": "Dr. James Mitchell",
            "topics": ["flow_state", "routine", "stress_management"],
            "url": "placeholder_url_015"
        }
    ]
}

# Study Group Topics
STUDY_GROUPS = {
    "beginner_groups": [
        {
            "id": "sg_001",
            "name": "Risk Management Rookies",
            "focus": "Master the fundamentals of risk management",
            "curriculum": [
                "Week 1: Position sizing basics",
                "Week 2: Stop loss strategies",
                "Week 3: Risk/Reward ratios",
                "Week 4: Portfolio risk management"
            ],
            "max_members": 20,
            "duration_weeks": 4
        },
        {
            "id": "sg_002",
            "name": "Chart Pattern Hunters",
            "focus": "Learn to identify and trade classic patterns",
            "curriculum": [
                "Week 1: Reversal patterns",
                "Week 2: Continuation patterns",
                "Week 3: Pattern trading rules",
                "Week 4: Live pattern hunting"
            ],
            "max_members": 15,
            "duration_weeks": 4
        },
        {
            "id": "sg_003",
            "name": "Platform Masters",
            "focus": "Master every feature of HydraX platform",
            "curriculum": [
                "Week 1: Basic navigation and tools",
                "Week 2: Advanced charting",
                "Week 3: Automation features",
                "Week 4: Custom indicators"
            ],
            "max_members": 25,
            "duration_weeks": 4
        }
    ],
    
    "intermediate_groups": [
        {
            "id": "sg_004",
            "name": "Strategy Builders",
            "focus": "Develop and test your own trading strategies",
            "curriculum": [
                "Week 1: Strategy components",
                "Week 2: Backtesting methods",
                "Week 3: Optimization techniques",
                "Week 4: Forward testing",
                "Week 5: Performance analysis",
                "Week 6: Strategy presentation"
            ],
            "max_members": 12,
            "duration_weeks": 6
        },
        {
            "id": "sg_005",
            "name": "Psychology Warriors",
            "focus": "Master the mental game of trading",
            "curriculum": [
                "Week 1: Identifying emotional triggers",
                "Week 2: Building discipline",
                "Week 3: Handling losses",
                "Week 4: Performance psychology",
                "Week 5: Creating routines",
                "Week 6: Maintaining consistency"
            ],
            "max_members": 10,
            "duration_weeks": 6
        },
        {
            "id": "sg_006",
            "name": "News Trading Ninjas",
            "focus": "Trade high-impact news events effectively",
            "curriculum": [
                "Week 1: Economic calendar mastery",
                "Week 2: Pre-news positioning",
                "Week 3: News spike trading",
                "Week 4: Post-news trends",
                "Week 5: Risk management for news"
            ],
            "max_members": 15,
            "duration_weeks": 5
        }
    ],
    
    "advanced_groups": [
        {
            "id": "sg_007",
            "name": "Algo Trading Lab",
            "focus": "Build and deploy trading algorithms",
            "curriculum": [
                "Week 1: Algorithm design principles",
                "Week 2: Coding trading logic",
                "Week 3: Backtesting frameworks",
                "Week 4: Risk management systems",
                "Week 5: Live deployment",
                "Week 6: Performance monitoring",
                "Week 7: Algorithm optimization",
                "Week 8: Portfolio of strategies"
            ],
            "max_members": 8,
            "duration_weeks": 8
        },
        {
            "id": "sg_008",
            "name": "Market Makers Mastermind",
            "focus": "Understand and trade like institutions",
            "curriculum": [
                "Week 1: Market microstructure",
                "Week 2: Order flow analysis",
                "Week 3: Liquidity provision",
                "Week 4: Institutional strategies",
                "Week 5: Dark pools and hidden orders",
                "Week 6: Advanced execution"
            ],
            "max_members": 10,
            "duration_weeks": 6
        },
        {
            "id": "sg_009",
            "name": "Portfolio Management Pro",
            "focus": "Professional-level portfolio management",
            "curriculum": [
                "Week 1: Modern portfolio theory",
                "Week 2: Risk metrics (Sharpe, Sortino)",
                "Week 3: Correlation management",
                "Week 4: Dynamic allocation",
                "Week 5: Drawdown control",
                "Week 6: Performance attribution",
                "Week 7: Client reporting",
                "Week 8: Scaling strategies"
            ],
            "max_members": 12,
            "duration_weeks": 8
        }
    ]
}

# Mentor Profiles
MENTORS = {
    "technical_specialists": [
        {
            "id": "mentor_001",
            "name": "Marcus Chen",
            "specialization": "Price Action & Market Structure",
            "experience_years": 12,
            "background": "Former institutional trader, specialized in forex majors",
            "teaching_style": "Practical, example-heavy approach focusing on real market conditions",
            "availability": "Mon-Wed, 9AM-5PM EST",
            "rating": 4.8,
            "students_mentored": 245
        },
        {
            "id": "mentor_002",
            "name": "Elena Volkov",
            "specialization": "Harmonic Patterns & Advanced Fibonacci",
            "experience_years": 15,
            "background": "Hedge fund analyst, pattern recognition expert",
            "teaching_style": "Detailed, mathematical approach with emphasis on precision",
            "availability": "Tue-Thu, 2PM-10PM EST",
            "rating": 4.9,
            "students_mentored": 189
        },
        {
            "id": "mentor_003",
            "name": "David Park",
            "specialization": "Volume Profile & Order Flow",
            "experience_years": 10,
            "background": "Market maker at major bank, liquidity specialist",
            "teaching_style": "Data-driven, focuses on reading institutional activity",
            "availability": "Mon-Fri, 6AM-2PM EST",
            "rating": 4.7,
            "students_mentored": 156
        }
    ],
    
    "strategy_specialists": [
        {
            "id": "mentor_004",
            "name": "Sarah Williams",
            "specialization": "Swing Trading & Position Management",
            "experience_years": 14,
            "background": "Independent trader, author of 'The Patient Trader'",
            "teaching_style": "Structured approach emphasizing patience and planning",
            "availability": "Wed-Fri, 10AM-6PM EST",
            "rating": 4.9,
            "students_mentored": 312
        },
        {
            "id": "mentor_005",
            "name": "Alex Rodriguez",
            "specialization": "Scalping & Day Trading Systems",
            "experience_years": 8,
            "background": "Prop firm trader, high-frequency specialist",
            "teaching_style": "Fast-paced, focuses on quick decision making and execution",
            "availability": "Mon-Thu, 7AM-3PM EST",
            "rating": 4.6,
            "students_mentored": 198
        },
        {
            "id": "mentor_006",
            "name": "Michael Thompson",
            "specialization": "Options Strategies for Spot Traders",
            "experience_years": 18,
            "background": "Options market maker, volatility expert",
            "teaching_style": "Complex concepts made simple, risk-focused approach",
            "availability": "Tue-Thu, 1PM-9PM EST",
            "rating": 4.8,
            "students_mentored": 167
        }
    ],
    
    "psychology_specialists": [
        {
            "id": "mentor_007",
            "name": "Dr. James Mitchell",
            "specialization": "Trading Psychology & Performance Coaching",
            "experience_years": 20,
            "background": "Clinical psychologist, works with pro athletes and traders",
            "teaching_style": "Cognitive behavioral approach, practical exercises",
            "availability": "Mon-Wed-Fri, 11AM-7PM EST",
            "rating": 5.0,
            "students_mentored": 423
        },
        {
            "id": "mentor_008",
            "name": "Dr. Lisa Chang",
            "specialization": "Risk Psychology & Decision Making",
            "experience_years": 16,
            "background": "Behavioral finance researcher, trading coach",
            "teaching_style": "Evidence-based methods, focuses on bias recognition",
            "availability": "Tue-Thu, 12PM-8PM EST",
            "rating": 4.9,
            "students_mentored": 287
        }
    ],
    
    "algorithmic_specialists": [
        {
            "id": "mentor_009",
            "name": "Dr. Robert Kim",
            "specialization": "Algorithmic Trading & System Development",
            "experience_years": 13,
            "background": "Quant developer at top hedge fund, PhD in Computer Science",
            "teaching_style": "Code-first approach, emphasis on robust system design",
            "availability": "Mon-Wed, 3PM-11PM EST",
            "rating": 4.7,
            "students_mentored": 134
        },
        {
            "id": "mentor_010",
            "name": "Natasha Petrov",
            "specialization": "Machine Learning for Trading",
            "experience_years": 9,
            "background": "AI researcher turned systematic trader",
            "teaching_style": "Project-based learning, cutting-edge techniques",
            "availability": "Thu-Sat, 10AM-6PM EST",
            "rating": 4.8,
            "students_mentored": 98
        }
    ]
}

# Gamification Rewards
REWARDS = {
    "xp_levels": {
        "novice": {"min": 0, "max": 999, "perks": ["Basic badges", "Forum access"]},
        "apprentice": {"min": 1000, "max": 4999, "perks": ["Custom avatar", "Priority support"]},
        "journeyman": {"min": 5000, "max": 9999, "perks": ["Advanced tools", "Group creation"]},
        "expert": {"min": 10000, "max": 19999, "perks": ["Mentor access", "Beta features"]},
        "master": {"min": 20000, "max": 49999, "perks": ["Private events", "Strategy sharing"]},
        "grandmaster": {"min": 50000, "max": None, "perks": ["Hall of fame", "Lifetime perks"]}
    },
    
    "badges": {
        "risk_manager": "Completed 50 trades with perfect risk management",
        "pattern_master": "Identified 100 patterns with 80%+ accuracy",
        "discipline_demon": "30 days of following trading plan perfectly",
        "comeback_king": "Recovered from 3 significant drawdowns",
        "mentor_material": "Helped 25 other traders improve",
        "algo_wizard": "Deployed 5 profitable algorithms",
        "psychology_warrior": "Completed all psychology challenges",
        "consistency_crown": "12 months of profitable trading"
    },
    
    "unlockables": {
        "advanced_indicators": "Unlock at Expert level",
        "custom_strategies": "Complete Strategy Builder course",
        "mentor_sessions": "Achieve Master level",
        "algorithm_builder": "Complete Algo Trading Lab",
        "private_groups": "Mentor 10 traders successfully"
    }
}

# Educational Paths
LEARNING_PATHS = {
    "beginner_path": {
        "name": "Trading Foundations",
        "duration_weeks": 8,
        "modules": [
            "Market Basics",
            "Platform Mastery",
            "Risk Management 101",
            "Basic Chart Patterns",
            "Psychology Fundamentals",
            "First Strategy Development",
            "Paper Trading Practice",
            "Going Live Safely"
        ]
    },
    
    "technical_path": {
        "name": "Technical Analysis Mastery",
        "duration_weeks": 12,
        "modules": [
            "Advanced Charting",
            "Indicator Deep Dive",
            "Pattern Recognition Pro",
            "Multi-Timeframe Analysis",
            "Volume and Order Flow",
            "Fibonacci Mastery",
            "Harmonic Patterns",
            "Technical Strategy Building"
        ]
    },
    
    "systematic_path": {
        "name": "Systematic Trading",
        "duration_weeks": 16,
        "modules": [
            "Strategy Development",
            "Backtesting Fundamentals",
            "Statistical Analysis",
            "Risk Metrics",
            "Portfolio Construction",
            "Algorithm Basics",
            "Automation Tools",
            "Performance Analysis"
        ]
    },
    
    "professional_path": {
        "name": "Professional Trader",
        "duration_weeks": 24,
        "modules": [
            "Institutional Methods",
            "Advanced Risk Management",
            "Portfolio Theory",
            "Market Microstructure",
            "Algorithmic Trading",
            "Psychology Mastery",
            "Business of Trading",
            "Scaling Strategies"
        ]
    }
}

def get_quiz_by_category(category: str) -> List[Dict[str, Any]]:
    """Get quiz questions by category"""
    return QUIZ_QUESTIONS.get(category, [])

def get_mission_by_type(mission_type: str) -> List[Dict[str, Any]]:
    """Get missions by type"""
    return MISSIONS.get(mission_type, [])

def get_achievements_by_level(level: str) -> List[Dict[str, Any]]:
    """Get achievements by difficulty level"""
    return ACHIEVEMENTS.get(level, [])

def get_mentors_by_specialization(specialization: str) -> List[Dict[str, Any]]:
    """Get mentors by their specialization"""
    return MENTORS.get(specialization, [])

def get_study_groups_by_level(level: str) -> List[Dict[str, Any]]:
    """Get study groups by level"""
    return STUDY_GROUPS.get(f"{level}_groups", [])

def get_videos_by_series(series: str) -> List[Dict[str, Any]]:
    """Get videos by series type"""
    return VIDEO_CONTENT.get(f"{series}_series", [])