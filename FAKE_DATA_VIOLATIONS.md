# FAKE DATA VIOLATION REPORT
Generated: 2025-07-28 04:11:23.948139
Total files with violations: 137

## apex_vs_venom_real_comparison.py
Violations: 8
- Line 117: `price_change = (trend_strength + micro_trend + np.random.uniform(-1, 1) * 0.5) *...`
- Line 120: `if np.random.random() < 0.002:...`
- Line 121: `price_change += np.random.choice([-1, 1]) * np.random.uniform(1.0, 3.0) * daily_...`
- Line 124: `open_price = base_price + (np.random.uniform(-0.3, 0.3) * daily_vol)...`
- Line 127: `range_size = daily_vol * np.random.uniform(0.3, 1.2)...`
- Line 128: `high_price = max(open_price, close_price) + range_size * np.random.random()...`
- Line 129: `low_price = min(open_price, close_price) - range_size * np.random.random()...`
- Line 131: `volume = int(np.random.randint(400, 1200) * session_multiplier)...`

## INTEL_CENTER_EASTER_EGGS.py
Violations: 1
- Line 193: `return random.choice(eggs)...`

## venom_2024_h2_backtest.py
Violations: 19
- Line 218: `if random.random() < news_probability:...`
- Line 223: `return np.random.choice(regimes, p=weights)...`
- Line 232: `base_technical = random.uniform(60, 88)  # More conservative for real market...`
- Line 346: `is_full_win = random.random() < win_probability...`
- Line 349: `base_slippage = random.uniform(0.2, 0.6)...`
- Line 351: `base_slippage += random.uniform(0.2, 0.5)  # Higher volatility = more slippage...`
- Line 417: `slippage = random.uniform(0.1, 0.4)...`
- Line 427: `if random.random() < partial_probability:...`
- Line 429: `partial_pips = random.uniform(0, target_pips * 0.7)...`
- Line 437: `slippage = random.uniform(0.2, 0.8)...`
- Line 490: `direction = random.choice(['BUY', 'SELL'])...`
- Line 494: `stop_pips = random.randint(10, 15)...`
- Line 497: `stop_pips = random.randint(15, 20)...`
- Line 537: `spread = random.uniform(spread_min, spread_min + (spread_max - spread_min) * 0.6...`
- Line 539: `spread = random.uniform(spread_min + (spread_max - spread_min) * 0.4, spread_max...`
- Line 544: `base_volume = random.randint(800, 1500)...`
- Line 579: `return random.random() < final_prob...`
- Line 638: `pairs_to_scan = primary_pairs + random.sample(secondary_pairs, k=min(4, len(seco...`
- Line 640: `pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(5, 8))...`

## test_connect_enhancements.py
Violations: 1
- Line 240: `• Balance: ${mock_account_info.get('balance', 0):,.2f}...`

## independent_validation_analysis.py
Violations: 14
- Line 92: `backtest_wins = sum(1 for s in backtest_signals if random.random() < s.get('expe...`
- Line 109: `real_wins = sum(1 for s in adjusted_signals if random.random() < s['adjusted_win...`
- Line 148: `market_condition = random.choice(['normal_market', 'news_events', 'thin_liquidit...`
- Line 159: `if random.random() < self.real_world.data_issues['missed_ticks']:...`
- Line 163: `if random.random() < 0.1:  # 10% of trades face broker issues...`
- Line 167: `if signal.get('trade_type') == 'SNIPER' and random.random() < 0.05:...`
- Line 171: `if random.random() < 0.2:  # 20% of trades affected by emotions...`
- Line 175: `if random.random() < 0.05:  # 5% chance of correlation breakdown...`
- Line 182: `if adjusted_prob < 0.4 or random.random() < 0.05:  # 5% signal dropout...`
- Line 301: `'symbol': random.choice(['EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'XAUUSD']),...`
- Line 302: `'trade_type': random.choice(['RAID', 'SNIPER']),...`
- Line 303: `'expected_win_probability': random.uniform(0.70, 0.85),...`
- Line 304: `'pip_target': random.randint(10, 40),...`
- Line 305: `'confidence_score': random.randint(70, 90)...`

## 🚨 CRITICAL: apex_venom_v7_unfiltered.py
Violations: 4
- Line 436: `def generate_realistic_market_data(self, pair: str, timestamp: datetime) -> Dict...`
- Line 437: `"""PERMANENTLY DISABLED - NO FAKE DATA ALLOWED"""...`
- Line 438: `raise RuntimeError(f"FAKE DATA GENERATION FORBIDDEN! Use get_real_mt5_data() for...`
- Line 485: `slippage = 0.2  # Fixed reasonable slippage - NO FAKE DATA...`

## test_fake_data_disabled.py
Violations: 10
- Line 3: `Test that fake data generation is completely disabled...`
- Line 12: `print("🧪 TESTING FAKE DATA IS DISABLED")...`
- Line 19: `print("\n❌ TEST 1: Calling generate_realistic_market_data()...")...`
- Line 21: `fake_data = venom.generate_realistic_market_data("EURUSD", datetime.now())...`
- Line 21: `fake_data = venom.generate_realistic_market_data("EURUSD", datetime.now())...`
- Line 22: `print("❌ FAILED - Fake data was generated!")...`
- Line 23: `print(f"Data: {fake_data}")...`
- Line 31: `print("  market_data = self.generate_realistic_market_data(pair, timestamp)")...`
- Line 42: `if hasattr(venom_timer, 'generate_realistic_market_data'):...`
- Line 54: `print("🎯 FAKE DATA GENERATION IS PERMANENTLY DISABLED!")...`

## apex_genius_optimizer.py
Violations: 16
- Line 184: `if random.random() < 0.05:  # 5% chance of news event...`
- Line 190: `return np.random.choice(regimes, p=weights)...`
- Line 200: `base_technical = random.uniform(60, 95)...`
- Line 359: `return random.random() < final_prob...`
- Line 388: `market_data = self.generate_realistic_market_data(pair, timestamp)...`
- Line 411: `direction = random.choice(['BUY', 'SELL'])...`
- Line 414: `stop_pips = random.randint(10, 15)...`
- Line 417: `stop_pips = random.randint(15, 20)...`
- Line 438: `def generate_realistic_market_data(self, pair: str, timestamp: datetime) -> Dict...`
- Line 462: `spread = random.uniform(spread_min, spread_min + (spread_max - spread_min) * 0.6...`
- Line 464: `spread = random.uniform(spread_min + (spread_max - spread_min) * 0.4, spread_max...`
- Line 467: `base_volume = random.randint(1000, 2000)...`
- Line 497: `is_win = random.random() < signal['win_probability']...`
- Line 500: `slippage = random.uniform(0.1, 0.3) if signal['quality'] in ['gold', 'platinum']...`
- Line 564: `pairs_to_scan = primary_pairs + random.sample(secondary_pairs, k=min(3, len(seco...`
- Line 566: `pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(4, 8))...`

## final_volume_test.py
Violations: 3
- Line 38: `daily_target = random.randint(30, 50)...`
- Line 44: `symbol = random.choice(engine.trading_pairs)...`
- Line 71: `total_wins = sum(1 for s in all_signals if random.random() < s.expected_win_prob...`

## last_6_months_backtest.py
Violations: 19
- Line 77: `volatility = random.uniform(12, 22)...`
- Line 78: `trend_strength = random.uniform(0.6, 0.8)...`
- Line 79: `liquidity = random.uniform(0.8, 1.0)...`
- Line 80: `news_impact = random.uniform(0.2, 0.5)...`
- Line 85: `volatility = random.uniform(20, 35)...`
- Line 86: `trend_strength = random.uniform(0.4, 0.7)...`
- Line 87: `liquidity = random.uniform(0.6, 0.9)...`
- Line 88: `news_impact = random.uniform(0.6, 0.9)...`
- Line 93: `volatility = random.uniform(10, 20)...`
- Line 94: `trend_strength = random.uniform(0.3, 0.5)...`
- Line 95: `liquidity = random.uniform(0.7, 0.95)...`
- Line 96: `news_impact = random.uniform(0.3, 0.6)...`
- Line 101: `volatility = random.uniform(8, 18)...`
- Line 102: `trend_strength = random.uniform(0.5, 0.7)...`
- Line 103: `liquidity = random.uniform(0.6, 0.8)  # Lower summer liquidity...`
- Line 104: `news_impact = random.uniform(0.2, 0.5)...`
- Line 196: `if random.random() < generation_prob:...`
- Line 198: `symbol = random.choice(self.engine.trading_pairs)...`
- Line 303: `is_win = random.random() < signal.expected_win_probability...`

## apex_real_data_validator.py
Violations: 1
- Line 534: `Previous Fake Data Results: 76.2% win rate (INVALID)...`

## apex_venom_v7_with_smart_timer_original.py
Violations: 3
- Line 359: `market_data = self.generate_realistic_market_data(pair, timestamp)...`
- Line 463: `pairs_to_scan = primary_pairs + random.sample(secondary_pairs, k=min(3, len(seco...`
- Line 465: `pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(4, 8))...`

## ema_rsi_atr_engine_backtest.py
Violations: 9
- Line 114: `noise = np.random.uniform(-1, 1) * 0.6...`
- Line 119: `if np.random.random() < 0.003:...`
- Line 120: `price_change += np.random.choice([-1, 1]) * np.random.uniform(1.5, 4.0) * daily_...`
- Line 122: `open_price = base_price + (np.random.uniform(-0.2, 0.2) * daily_vol)...`
- Line 125: `range_size = daily_vol * np.random.uniform(0.5, 1.5)...`
- Line 126: `high_price = max(open_price, close_price) + range_size * np.random.random()...`
- Line 127: `low_price = min(open_price, close_price) - range_size * np.random.random()...`
- Line 129: `volume = int(np.random.randint(500, 1800) * session_multiplier)...`
- Line 193: `rrr_type = np.random.choice(["1:2", "1:3"], p=[self.config['rrr_distribution']["...`

## apex_calibrated_flow_engine.py
Violations: 5
- Line 222: `if random.random() < generation_prob:...`
- Line 223: `symbol = random.choice(self.engine.trading_pairs)...`
- Line 281: `wins = sum(1 for s in daily_signals if random.random() < s.expected_win_probabil...`
- Line 310: `total_wins = sum(1 for s in signals if random.random() < s.expected_win_probabil...`
- Line 316: `is_win = random.random() < signal.expected_win_probability...`

## user_monthly_performance.py
Violations: 2
- Line 68: `rr_category = random.choices(...`
- Line 77: `outcome = "WIN" if random.random() < self.system_win_rate else "LOSS"...`

## PERMANENT_FAKE_DATA_PREVENTION.py
Violations: 24
- Line 3: `PERMANENT FAKE DATA PREVENTION SYSTEM...`
- Line 4: `Prevents fake data from being reintroduced into the codebase...`
- Line 13: `FAKE_DATA_PATTERNS = [...`
- Line 15: `r'generate_realistic_.*data',...`
- Line 16: `r'simulate.*trade.*result',...`
- Line 17: `r'fake.*data',...`
- Line 18: `r'mock.*balance',...`
- Line 19: `r'synthetic.*signal',...`
- Line 33: `"""Scan a file for fake data patterns"""...`
- Line 42: `for pattern in FAKE_DATA_PATTERNS:...`
- Line 59: `"""Scan entire directory for fake data"""...`
- Line 81: `report.append("# FAKE DATA VIOLATION REPORT")...`
- Line 109: `"""Create pre-commit hook to prevent fake data"""...`
- Line 113: `echo "🔍 Scanning for fake data violations..."...`
- Line 116: `python3 /root/HydraX-v2/PERMANENT_FAKE_DATA_PREVENTION.py...`
- Line 120: `echo "❌ Commit blocked: Fake data detected!"...`
- Line 121: `echo "Please remove all fake data before committing."...`
- Line 125: `echo "✅ No fake data detected - commit allowed"...`
- Line 137: `print("🔍 PERMANENT FAKE DATA PREVENTION SYSTEM")...`
- Line 148: `with open("/root/HydraX-v2/FAKE_DATA_VIOLATIONS.md", 'w') as f:...`
- Line 151: `print(f"❌ Found fake data in {len(violations)} files!")...`
- Line 152: `print("Report saved to: FAKE_DATA_VIOLATIONS.md")...`
- Line 157: `print(f"\n🚨 CRITICAL: {critical_count} production files contain fake data!")...`
- Line 160: `print("✅ No fake data violations found!")...`

## venom_real_market_analysis.py
Violations: 13
- Line 208: `is_rapid = np.random.random() < 0.6...`
- Line 214: `stop_pips = np.random.uniform(12, 18)  # VENOM typical range...`
- Line 217: `stop_pips = np.random.uniform(15, 22)  # VENOM typical range...`
- Line 229: `'direction': np.random.choice(['BUY', 'SELL']),...`
- Line 246: `base_confidence = np.random.uniform(65, 88)...`
- Line 251: `base_confidence += np.random.uniform(3, 8)...`
- Line 267: `base_confidence += np.random.uniform(2, 5)...`
- Line 269: `base_confidence -= np.random.uniform(3, 7)...`
- Line 305: `actual_pips = target_pips - np.random.uniform(0.2, 0.8)  # Real slippage...`
- Line 310: `actual_pips = -(stop_pips + np.random.uniform(0.2, 1.0))  # Slippage on loss...`
- Line 316: `actual_pips = target_pips - np.random.uniform(0.2, 0.8)...`
- Line 321: `actual_pips = -(stop_pips + np.random.uniform(0.2, 1.0))...`
- Line 454: `return np.random.random() < 0.70  # 70% filter rate...`

## apex_testing_v6_real_data.py
Violations: 18
- Line 708: `'volume_ratio': random.uniform(0.7, 2.2),  # Enhanced with volume analysis later...`
- Line 709: `'rsi': random.uniform(25, 75),  # Real RSI calculation to be added...`
- Line 710: `'ma_alignment': random.uniform(0.3, 0.9),  # Real MA calculation to be added...`
- Line 711: `'macd_signal': random.uniform(-1.0, 1.0),  # Real MACD calculation to be added...`
- Line 712: `'sr_distance': random.uniform(0.1, 0.8),  # Real S&R calculation to be added...`
- Line 713: `'trend_strength': random.uniform(0.2, 0.8),  # Real trend analysis to be added...`
- Line 714: `'pattern_completion': random.uniform(0.4, 0.9),  # Pattern recognition to be add...`
- Line 716: `'momentum_consistency': random.uniform(0.3, 0.8),  # Momentum analysis to be add...`
- Line 717: `'volume_momentum': random.uniform(0.4, 0.9),  # Volume momentum to be added...`
- Line 718: `'market_regime': random.choice(['trending', 'ranging', 'breakout', 'consolidatio...`
- Line 719: `'liquidity_score': random.uniform(0.6, 0.95),  # Liquidity analysis to be added...`
- Line 720: `'correlation_risk': random.uniform(0.1, 0.4),  # Correlation analysis to be adde...`
- Line 734: `technical_score = 45 + random.uniform(0, 35)  # 45-80 range...`
- Line 735: `pattern_score = 40 + random.uniform(0, 35)    # 40-75 range...`
- Line 736: `momentum_score = 42 + random.uniform(0, 33)   # 42-75 range...`
- Line 737: `structure_score = 45 + random.uniform(0, 30)  # 45-75 range...`
- Line 739: `volume_score = 48 + random.uniform(0, 24)     # 48-72 range...`
- Line 860: `return random.random() < generation_prob...`

## apex_6_backtester_complete.py
Violations: 14
- Line 80: `macro_sentiment = random.uniform(-1, 1)...`
- Line 86: `if day % random.randint(7, 14) == 0:...`
- Line 87: `trend = random.uniform(-1, 1)...`
- Line 90: `macro_sentiment += random.uniform(-0.1, 0.1)...`
- Line 101: `change = (trend * 0.2 + macro_sentiment * 0.1 + random.uniform(-0.5, 0.5)) * vol...`
- Line 104: `if random.random() < 0.03:...`
- Line 105: `change += random.uniform(-3, 3) * volatility * 0.0001...`
- Line 113: `high_price = max(open_price, close_price) + range_size * random.random()...`
- Line 114: `low_price = min(open_price, close_price) - range_size * random.random()...`
- Line 117: `base_volume = random.randint(500, 2000) * session_vol...`
- Line 127: `'spread': random.uniform(0.8, 2.5),...`
- Line 464: `is_win = random.random() < win_rate...`
- Line 467: `slippage = random.uniform(0.1, 0.4)...`
- Line 475: `slippage_mult = 1.2 if random.random() > 0.9 else 1.0...`

## hyper_vs_apex_real_comparison.py
Violations: 8
- Line 130: `price_change = (trend_strength + micro_trend + np.random.uniform(-1, 1) * 0.6) *...`
- Line 133: `if np.random.random() < 0.003:...`
- Line 134: `price_change += np.random.choice([-1, 1]) * np.random.uniform(1.5, 3.5) * daily_...`
- Line 136: `open_price = base_price + (np.random.uniform(-0.3, 0.3) * daily_vol)...`
- Line 139: `range_size = daily_vol * np.random.uniform(0.4, 1.4)...`
- Line 140: `high_price = max(open_price, close_price) + range_size * np.random.random()...`
- Line 141: `low_price = min(open_price, close_price) - range_size * np.random.random()...`
- Line 143: `volume = int(np.random.randint(500, 1500) * session_multiplier)...`

## start_live_simple.py
Violations: 2
- Line 129: `change = random.uniform(-0.0010, 0.0010)...`
- Line 167: `confidence = random.randint(65, 95)  # For testing...`

## apex_production_v6_enhanced.py
Violations: 25
- Line 534: `def generate_realistic_market_data(self, symbol: str) -> Dict:...`
- Line 538: `'bid': random.uniform(1.0500, 1.0600),...`
- Line 539: `'ask': random.uniform(1.0502, 1.0602),...`
- Line 540: `'spread': random.uniform(0.8, 2.5),...`
- Line 541: `'volume': random.randint(800000, 5000000),...`
- Line 542: `'volume_ratio': random.uniform(0.7, 2.2),...`
- Line 543: `'rsi': random.uniform(25, 75),...`
- Line 544: `'ma_alignment': random.uniform(0.3, 0.9),...`
- Line 545: `'macd_signal': random.uniform(-1.0, 1.0),...`
- Line 546: `'sr_distance': random.uniform(0.1, 0.8),...`
- Line 547: `'trend_strength': random.uniform(0.2, 0.8),...`
- Line 548: `'pattern_completion': random.uniform(0.4, 0.9),...`
- Line 549: `'price_velocity': random.uniform(-0.001, 0.001),...`
- Line 550: `'momentum_consistency': random.uniform(0.3, 0.8),...`
- Line 551: `'volume_momentum': random.uniform(0.4, 0.9),...`
- Line 552: `'market_regime': random.choice(['trending', 'ranging', 'breakout', 'consolidatio...`
- Line 553: `'liquidity_score': random.uniform(0.6, 0.95),...`
- Line 554: `'correlation_risk': random.uniform(0.1, 0.4),...`
- Line 563: `technical_score = 45 + random.uniform(0, 35)  # 45-80 range...`
- Line 564: `pattern_score = 40 + random.uniform(0, 35)    # 40-75 range...`
- Line 565: `momentum_score = 42 + random.uniform(0, 33)   # 42-75 range...`
- Line 566: `structure_score = 45 + random.uniform(0, 30)  # 45-75 range...`
- Line 568: `volume_score = 48 + random.uniform(0, 24)     # 48-72 range...`
- Line 689: `return random.random() < generation_prob...`
- Line 722: `market_data = self.generate_realistic_market_data(symbol)...`

## venom_vs_apex_validator.py
Violations: 9
- Line 124: `price_change = (trend_strength + np.random.uniform(-1, 1) * 0.5) * daily_vol...`
- Line 125: `if np.random.random() < 0.03:  # News events...`
- Line 126: `price_change += np.random.choice([-1, 1]) * np.random.uniform(0.5, 2.0) * daily_...`
- Line 128: `open_price = base_price + (np.random.uniform(-0.5, 0.5) * daily_vol)...`
- Line 131: `range_size = daily_vol * np.random.uniform(0.8, 1.5)...`
- Line 132: `high_price = max(open_price, close_price) + range_size * np.random.random()...`
- Line 133: `low_price = min(open_price, close_price) - range_size * np.random.random()...`
- Line 135: `volume = int(np.random.randint(800, 2500) * session_multiplier)...`
- Line 445: `Mathematical integrity confirmed: No fake data used in validation....`

## venom_live_reality_analysis.py
Violations: 30
- Line 152: `signal_quality = random.choice(['PLATINUM', 'GOLD', 'SILVER'])...`
- Line 153: `simulator_win_prob = random.uniform(0.75, 0.85)  # VENOM range...`
- Line 181: `is_win = random.random() < adjusted_win_prob...`
- Line 185: `target_pips = random.randint(20, 40)...`
- Line 186: `stop_pips = random.randint(10, 20)...`
- Line 188: `target_pips = random.randint(15, 30)...`
- Line 189: `stop_pips = random.randint(10, 15)...`
- Line 215: `if random.random() < self.live_market_factors['server_issues']:...`
- Line 218: `if random.random() < self.live_market_factors['rejected_trades']:...`
- Line 221: `if random.random() < self.live_market_factors['requotes']:...`
- Line 224: `if random.random() < self.live_market_factors['partial_fills']:...`
- Line 228: `if random.random() < self.live_market_factors['trade_hesitation']:...`
- Line 231: `if random.random() < self.live_market_factors['internet_issues']:...`
- Line 240: `current_hour = random.randint(0, 23)...`
- Line 251: `is_news_time = random.random() < self.live_market_factors['news_events']...`
- Line 252: `is_low_liquidity = random.random() < self.live_market_factors['liquidity_gaps']...`
- Line 253: `is_friday_close = random.random() < 0.05  # 5% chance it's Friday close...`
- Line 258: `volatility_multiplier = random.uniform(2.0, 5.0)...`
- Line 260: `volatility_multiplier = random.uniform(0.3, 0.7)...`
- Line 273: `base_slippage = random.uniform(...`
- Line 280: `base_slippage *= random.uniform(2.0, 4.0)...`
- Line 283: `base_slippage *= random.uniform(1.5, 3.0)...`
- Line 286: `base_slippage *= random.uniform(1.3, 2.0)...`
- Line 292: `if random.random() < self.live_market_factors['flash_crashes']:...`
- Line 300: `base_spread = random.uniform(0.8, 2.0)  # Normal spread...`
- Line 328: `adjusted_prob -= random.uniform(0.05, 0.20)  # 5-20% penalty...`
- Line 332: `adjusted_prob -= random.uniform(0.03, 0.12)  # 3-12% penalty...`
- Line 336: `adjusted_prob -= random.uniform(0.08, 0.25)  # High vol penalty...`
- Line 338: `adjusted_prob -= random.uniform(0.02, 0.08)  # Low vol penalty...`
- Line 342: `adjusted_prob -= random.uniform(0.05, 0.15)...`

## apex_venom_v7_real_data_only.py
Violations: 5
- Line 8: `- NO fake data generation methods...`
- Line 63: `NO FALLBACK TO FAKE DATA...`
- Line 99: `def generate_realistic_market_data(self, pair: str, timestamp: datetime) -> Dict...`
- Line 101: `DISABLED - NO FAKE DATA GENERATION ALLOWED...`
- Line 105: `f"FAKE DATA GENERATION FORBIDDEN! "...`

## apex_production_v6_backup_20250718_232725.py
Violations: 21
- Line 436: `return random.random() < generation_prob...`
- Line 465: `def generate_realistic_market_data(self, symbol: str) -> Dict:...`
- Line 469: `'bid': random.uniform(1.0500, 1.0600),...`
- Line 470: `'ask': random.uniform(1.0502, 1.0602),...`
- Line 471: `'spread': random.uniform(0.5, 2.5),...`
- Line 472: `'volume': random.randint(500000, 5000000),...`
- Line 473: `'rsi': random.uniform(25, 75),...`
- Line 474: `'ma_alignment': random.uniform(0.3, 0.9),...`
- Line 475: `'macd_signal': random.uniform(-1.0, 1.0),...`
- Line 476: `'sr_distance': random.uniform(0.1, 0.8),...`
- Line 477: `'trend_strength': random.uniform(0.2, 0.8),...`
- Line 478: `'pattern_completion': random.uniform(0.4, 0.9),...`
- Line 479: `'price_velocity': random.uniform(-0.001, 0.001),...`
- Line 480: `'momentum_consistency': random.uniform(0.3, 0.8),...`
- Line 481: `'volume_momentum': random.uniform(0.4, 0.9),...`
- Line 482: `'market_regime': random.choice(['trending', 'ranging', 'breakout', 'consolidatio...`
- Line 483: `'liquidity_score': random.uniform(0.6, 0.95),...`
- Line 484: `'correlation_risk': random.uniform(0.1, 0.4),...`
- Line 485: `'volume_ratio': random.uniform(0.8, 2.0),...`
- Line 486: `'volume_trend': random.uniform(0.3, 0.8)...`
- Line 492: `market_data = self.generate_realistic_market_data(symbol)...`

## run_venom_live.py
Violations: 6
- Line 54: `pairs_to_scan = random.sample(venom.trading_pairs, k=min(10, len(venom.trading_p...`
- Line 56: `pairs_to_scan = random.sample(venom.trading_pairs, k=min(8, len(venom.trading_pa...`
- Line 58: `pairs_to_scan = random.sample(venom.trading_pairs, k=min(5, len(venom.trading_pa...`
- Line 60: `pairs_to_scan = random.sample(venom.trading_pairs, k=min(3, len(venom.trading_pa...`
- Line 84: `sleep_time = random.randint(60, 180)  # 1-3 minutes during active sessions...`
- Line 86: `sleep_time = random.randint(180, 300)  # 3-5 minutes during quiet sessions...`

## tcs_breakdown_analysis.py
Violations: 5
- Line 31: `symbol = random.choice(engine.trading_pairs)...`
- Line 88: `simulated_wins = sum(1 for s in signals if random.random() < s.expected_win_prob...`
- Line 95: `raid_wins = sum(1 for s in raid_signals if random.random() < s.expected_win_prob...`
- Line 96: `sniper_wins = sum(1 for s in sniper_signals if random.random() < s.expected_win_...`
- Line 175: `total_simulated_wins = sum(1 for s in all_signals if random.random() < s.expecte...`

## quick_forex_data_completion.py
Violations: 3
- Line 18: `def generate_realistic_data(pair: str, start_date: datetime, end_date: datetime)...`
- Line 87: `volume = int(np.random.randint(100, 500) * session_mult)...`
- Line 141: `data = generate_realistic_data(pair, start_date, end_date)...`

## covid_period_backtest.py
Violations: 25
- Line 82: `vix = random.uniform(50, 82)  # Historical VIX range...`
- Line 83: `volatility_mult = random.uniform(3.0, 5.0)...`
- Line 84: `trend_strength = random.uniform(0.8, 1.0)  # Strong trends during crash...`
- Line 85: `news_impact = random.uniform(0.7, 1.0)     # High news impact...`
- Line 91: `vix = random.uniform(35, 60)...`
- Line 92: `volatility_mult = random.uniform(2.0, 3.5)...`
- Line 93: `trend_strength = random.uniform(0.3, 0.7)  # Whipsaw action...`
- Line 94: `news_impact = random.uniform(0.8, 1.0)     # Fed announcements...`
- Line 100: `vix = random.uniform(25, 45)...`
- Line 101: `volatility_mult = random.uniform(1.5, 2.5)...`
- Line 102: `trend_strength = random.uniform(0.2, 0.5)  # No clear direction...`
- Line 103: `news_impact = random.uniform(0.6, 0.9)...`
- Line 104: `correlation_breakdown = random.choice([True, False])...`
- Line 109: `vix = random.uniform(20, 35)...`
- Line 110: `volatility_mult = random.uniform(1.2, 2.0)...`
- Line 111: `trend_strength = random.uniform(0.6, 0.9)  # Strong uptrend...`
- Line 112: `news_impact = random.uniform(0.4, 0.7)...`
- Line 118: `vix = random.uniform(18, 30)...`
- Line 119: `volatility_mult = random.uniform(1.0, 1.5)...`
- Line 120: `trend_strength = random.uniform(0.3, 0.6)  # Range-bound...`
- Line 121: `news_impact = random.uniform(0.3, 0.6)...`
- Line 232: `if random.random() < generation_probability:...`
- Line 234: `symbol = random.choice(self.engine.trading_pairs)...`
- Line 315: `is_win = random.random() < signal.expected_win_probability...`
- Line 359: `is_win = random.random() < signal.expected_win_probability...`

## apex_venom_v7_complete.py
Violations: 18
- Line 340: `if random.random() < 0.05:...`
- Line 345: `return np.random.choice(regimes, p=weights)...`
- Line 354: `base_technical = random.uniform(65, 95)...`
- Line 498: `return random.random() < final_prob...`
- Line 520: `market_data = self.generate_realistic_market_data(pair, timestamp)...`
- Line 532: `direction = random.choice(['BUY', 'SELL'])...`
- Line 536: `stop_pips = random.randint(10, 15)...`
- Line 539: `stop_pips = random.randint(15, 20)...`
- Line 581: `def generate_realistic_market_data(self, pair: str, timestamp: datetime) -> Dict...`
- Line 603: `spread = random.uniform(spread_min, spread_min + (spread_max - spread_min) * 0.6...`
- Line 605: `spread = random.uniform(spread_min + (spread_max - spread_min) * 0.4, spread_max...`
- Line 608: `base_volume = random.randint(1200, 2200)...`
- Line 610: `volume_ratio = random.uniform(0.8, 2.2)...`
- Line 611: `volatility = random.uniform(0.5, 2.8)...`
- Line 640: `is_win = random.random() < signal['win_probability']...`
- Line 643: `slippage = random.uniform(0.1, 0.25) if signal['quality'] in ['gold', 'platinum'...`
- Line 710: `pairs_to_scan = primary_pairs + random.sample(secondary_pairs, k=min(3, len(seco...`
- Line 712: `pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(4, 8))...`

## test_venom_real_data.py
Violations: 5
- Line 51: `print("\n📊 TEST 3: Proving fake data is disabled")...`
- Line 52: `print("Calling generate_realistic_market_data (should return real data only)..."...`
- Line 53: `fake_test = venom.generate_realistic_market_data("EURUSD", datetime.now())...`
- Line 53: `fake_test = venom.generate_realistic_market_data("EURUSD", datetime.now())...`
- Line 55: `print("✅ This calls get_real_mt5_data() - NO FAKE DATA!")...`

## bitten_player_types_engine.py
Violations: 33
- Line 48: `return random.random() < (tcs_accuracy / 100)...`
- Line 70: `tcs_accuracy = random.uniform(*self.tcs_range)...`
- Line 71: `pip_target = random.randint(*self.pip_range)...`
- Line 72: `risk_reward = round(random.uniform(*self.rr_range), 2)...`
- Line 73: `duration = random.randint(*self.duration_range)...`
- Line 76: `direction = random.choice(['BUY', 'SELL'])...`
- Line 88: `variance = random.uniform(0.9, 1.1)...`
- Line 125: `tcs_accuracy = random.uniform(*self.tcs_range)...`
- Line 126: `pip_target = random.randint(*self.pip_range)...`
- Line 127: `risk_reward = round(random.uniform(*self.rr_range), 2)...`
- Line 128: `duration = random.randint(*self.duration_range)...`
- Line 131: `market_bias = random.random()...`
- Line 143: `confidence = min(tcs_accuracy * random.uniform(0.85, 1.05) / 100, 0.90)...`
- Line 179: `tcs_accuracy = random.uniform(*self.tcs_range)...`
- Line 180: `pip_target = random.randint(*self.pip_range)...`
- Line 181: `risk_reward = round(random.uniform(*self.rr_range), 2)...`
- Line 182: `duration = random.randint(*self.duration_range)...`
- Line 185: `setup_quality = random.random()...`
- Line 200: `confidence = min(tcs_accuracy * random.uniform(0.95, 1.1) / 100, 0.95)...`
- Line 236: `tcs_accuracy = random.uniform(*self.tcs_range)...`
- Line 237: `pip_target = random.randint(*self.pip_range)...`
- Line 238: `risk_reward = round(random.uniform(*self.rr_range), 2)...`
- Line 239: `duration = random.randint(*self.duration_range)...`
- Line 242: `market_strength = random.random()...`
- Line 258: `confidence = min(tcs_accuracy * random.uniform(0.9, 1.05) / 100, 0.88)...`
- Line 301: `num_signals = random.randint(20, 30)...`
- Line 303: `num_signals = random.randint(15, 20)...`
- Line 305: `num_signals = random.randint(8, 12)...`
- Line 307: `num_signals = random.randint(3, 5)...`
- Line 314: `price_movement = random.uniform(-0.0050, 0.0050)...`
- Line 330: `minutes = sorted([random.randint(0, trading_minutes) for _ in range(num_signals)...`
- Line 341: `tcs_accuracy = random.uniform(*profile.tcs_range)...`
- Line 357: `'actual_duration': signal.trade_duration_minutes + random.randint(-5, 5)...`

## apex_comprehensive_real_validator.py
Violations: 10
- Line 138: `if random.random() < 0.03:...`
- Line 139: `news_impact = random.choice([-1, 1]) * random.uniform(0.5, 2.0) * daily_vol...`
- Line 142: `price_change = (trend_strength + random.uniform(-1, 1) * 0.5) * daily_vol + news...`
- Line 145: `open_price = base_price + (random.uniform(-0.5, 0.5) * daily_vol)...`
- Line 148: `range_size = daily_vol * random.uniform(0.8, 1.5)...`
- Line 149: `high_price = max(open_price, close_price) + range_size * random.random()...`
- Line 150: `low_price = min(open_price, close_price) - range_size * random.random()...`
- Line 153: `base_volume = random.randint(800, 2500)...`
- Line 489: `The engine has been comprehensively tested against 6 months of real market data ...`
- Line 495: `This assessment supersedes all previous fake-data backtesting results....`

## AUTHORIZED_SIGNAL_ENGINE.py
Violations: 15
- Line 162: `momentum_score = random.uniform(15, 25)...`
- Line 165: `volume_score = random.uniform(10, 20)...`
- Line 168: `technical_score = random.uniform(10, 20)...`
- Line 171: `structure_score = random.uniform(5, 15)...`
- Line 193: `return random.uniform(8, 12)...`
- Line 196: `return random.uniform(6, 10)...`
- Line 199: `return random.uniform(4, 8)...`
- Line 201: `return random.uniform(2, 6)...`
- Line 223: `return random.random() < base_probability...`
- Line 235: `direction = random.choice(['BUY', 'SELL'])...`
- Line 241: `stop_loss = entry_price - random.uniform(0.0020, 0.0040)...`
- Line 243: `take_profit = entry_price + random.uniform(0.0030, 0.0080)...`
- Line 247: `stop_loss = entry_price + random.uniform(0.0020, 0.0040)...`
- Line 249: `take_profit = entry_price - random.uniform(0.0030, 0.0080)...`
- Line 334: `symbol = random.choice(self.pairs)...`

## apex_6_corrected_backtest.py
Violations: 18
- Line 124: `def generate_realistic_market_data(self, pair: str, timestamp: datetime) -> Dict...`
- Line 146: `price_change = random.uniform(-volatility/2, volatility/2) * pip_size * session_...`
- Line 151: `'EURUSD': random.uniform(0.8, 1.5), 'GBPUSD': random.uniform(1.2, 2.0),...`
- Line 152: `'USDJPY': random.uniform(1.0, 1.8), 'USDCAD': random.uniform(1.5, 2.5),...`
- Line 153: `'AUDUSD': random.uniform(1.0, 2.0), 'NZDUSD': random.uniform(1.5, 2.5),...`
- Line 154: `'XAUUSD': random.uniform(0.3, 0.8), 'XAGUSD': random.uniform(2.0, 4.0)...`
- Line 155: `}.get(pair, random.uniform(1.5, 3.0))...`
- Line 162: `volume = random.randint(800, 2500) * session_vol...`
- Line 179: `technical_score = random.uniform(55, 90)  # Raised minimum for quality...`
- Line 235: `market_data = self.generate_realistic_market_data(pair, timestamp)...`
- Line 254: `if random.random() > generation_prob:...`
- Line 259: `direction = random.choice(['BUY', 'SELL'])...`
- Line 264: `stop_pips = random.randint(10, 15)...`
- Line 269: `stop_pips = random.randint(15, 20)...`
- Line 300: `actual_win_rate = target_win_rate + random.uniform(-0.02, 0.02)...`
- Line 304: `is_win = random.random() < actual_win_rate...`
- Line 307: `slippage = random.uniform(0.2, 0.6)  # Realistic slippage...`
- Line 384: `pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(3, 6))...`

## apex_v5_lean.py
Violations: 1
- Line 242: `is_sniper = random.random() < sniper_chance...`

## apex_v6_premium_backtest.py
Violations: 19
- Line 88: `technical_base = 50 + random.uniform(0, 30)    # 50-80 (raised from 45-75)...`
- Line 89: `pattern_base = 45 + random.uniform(0, 30)      # 45-75 (raised from 40-70)...`
- Line 90: `momentum_base = 47 + random.uniform(0, 28)     # 47-75 (raised from 42-70)...`
- Line 91: `structure_base = 50 + random.uniform(0, 25)    # 50-75 (raised from 45-70)...`
- Line 92: `volume_base = 52 + random.uniform(0, 23)       # 52-75 (raised from 48-70)...`
- Line 177: `price_variation = random.uniform(-0.001, 0.001)...`
- Line 179: `bid = ask - random.uniform(0.00005, 0.00020)  # Tighter spreads for premium...`
- Line 185: `'volume': random.randint(1200000, 3000000),  # Higher volume range...`
- Line 186: `'volume_ratio': random.uniform(0.8, 2.0),   # Better volume ratios...`
- Line 253: `return 'BUY' if random.random() < buy_probability else 'SELL'...`
- Line 398: `price_change = (trend_strength + micro_trend + np.random.uniform(-1, 1) * 0.5) *...`
- Line 400: `if np.random.random() < 0.002:...`
- Line 401: `price_change += np.random.choice([-1, 1]) * np.random.uniform(1.0, 3.0) * daily_...`
- Line 403: `open_price = base_price + (np.random.uniform(-0.3, 0.3) * daily_vol)...`
- Line 406: `range_size = daily_vol * np.random.uniform(0.3, 1.2)...`
- Line 407: `high_price = max(open_price, close_price) + range_size * np.random.random()...`
- Line 408: `low_price = min(open_price, close_price) - range_size * np.random.random()...`
- Line 410: `volume = int(np.random.randint(800, 2000) * session_multiplier)...`
- Line 480: `'volume_ratio': random.uniform(0.8, 2.0),...`

## debug_proven_winner.py
Violations: 1
- Line 36: `volumes = [15000 + np.random.randint(-2000, 2000) for _ in range(100)]...`

## apex_venom_v7_citadel_integrated.py
Violations: 1
- Line 49: `logger.info("🔒 NO FAKE/SYNTHETIC DATA - GUARANTEED")...`

## debug_venom.py
Violations: 4
- Line 32: `'open': base_price - np.random.uniform(0, 0.00005),...`
- Line 33: `'high': base_price + np.random.uniform(0.00005, 0.0002),...`
- Line 34: `'low': base_price - np.random.uniform(0.00005, 0.0002),...`
- Line 36: `'volume': np.random.randint(1000, 3000)...`

## unified_market_service.py
Violations: 1
- Line 5: `NO FAKE DATA - 100% REAL MT5 DATA...`

## venom_filter_analysis.py
Violations: 12
- Line 47: `market_data = self.generate_realistic_market_data(pair, timestamp)...`
- Line 59: `direction = random.choice(['BUY', 'SELL'])...`
- Line 63: `stop_pips = random.randint(10, 15)...`
- Line 66: `stop_pips = random.randint(15, 20)...`
- Line 127: `"""Simulate what the trade result would have been for a filtered signal"""...`
- Line 129: `is_win = random.random() < filtered_signal['win_probability']...`
- Line 132: `base_slippage = random.uniform(0.3, 0.8)  # Higher slippage for "dangerous" sign...`
- Line 137: `base_slippage += random.uniform(0.2, 0.5)  # Wide spreads = more slippage...`
- Line 139: `base_slippage += random.uniform(0.3, 0.7)  # High volatility = more slippage...`
- Line 141: `base_slippage += random.uniform(0.1, 0.3)  # Low volume = some extra slippage...`
- Line 196: `pairs_to_scan = primary_pairs + random.sample(secondary_pairs, k=min(3, len(seco...`
- Line 198: `pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(4, 8))...`

## rr_ratio_analysis.py
Violations: 5
- Line 51: `if random.random() < 0.75:...`
- Line 53: `rr_ratio = random.uniform(1.5, 2.6)  # RAPID_ASSAULT range...`
- Line 56: `rr_ratio = random.uniform(2.7, 3.5)  # SNIPER_OPS range...`
- Line 61: `tcs_score = random.choices(tcs_ranges, weights=tcs_weights)[0]...`
- Line 78: `outcome = "WIN" if random.random() < win_probability else "LOSS"...`

## ZERO_SIMULATION_AUDIT.py
Violations: 9
- Line 4: `CRITICAL: Detects and reports ANY fake data in the system...`
- Line 13: `"""Audits system for ANY fake/simulation data"""...`
- Line 19: `def audit_fake_data_patterns(self):...`
- Line 20: `"""Audit for fake data patterns"""...`
- Line 29: `r'FAKE.*DATA',...`
- Line 115: `'issue': f'Potential fake data: {match.group()}',...`
- Line 126: `self.audit_fake_data_patterns()...`
- Line 147: `print("🚨 SYSTEM NOT READY - FAKE DATA DETECTED!")...`
- Line 151: `print("✅ NO FAKE DATA DETECTED")...`

## hyper_engine_v1.py
Violations: 5
- Line 610: `return min(95, max(45, tcs + np.random.uniform(-2, 2)))...`
- Line 709: `'open': base_price - np.random.uniform(0, 0.00002),...`
- Line 710: `'high': base_price + np.random.uniform(0.00003, 0.00012),...`
- Line 711: `'low': base_price - np.random.uniform(0.00003, 0.00012),...`
- Line 713: `'volume': np.random.randint(800, 2000)...`

## forex_signal_engine_backtest.py
Violations: 8
- Line 201: `price_change = (trend_strength + micro_trend + np.random.uniform(-1, 1) * 0.5) *...`
- Line 204: `if np.random.random() < 0.002:...`
- Line 205: `price_change += np.random.choice([-1, 1]) * np.random.uniform(1.0, 3.0) * daily_...`
- Line 207: `open_price = base_price + (np.random.uniform(-0.3, 0.3) * daily_vol)...`
- Line 210: `range_size = daily_vol * np.random.uniform(0.3, 1.2)...`
- Line 211: `high_price = max(open_price, close_price) + range_size * np.random.random()...`
- Line 212: `low_price = min(open_price, close_price) - range_size * np.random.random()...`
- Line 214: `volume = int(np.random.randint(800, 2000) * session_multiplier)...`

## webapp_server.py
Violations: 5
- Line 561: `return random.randint(45, 89)  # Fallback to random...`
- Line 586: `return random.randint(45, 89)  # Fallback to random...`
- Line 681: `'squad_engagement': random.randint(45, 89)  # Percentage of squad taking this si...`
- Line 700: `'squad_engagement': random.randint(45, 89)  # Percentage of squad taking this si...`
- Line 752: `pattern_key = random.choice(list(PATTERN_NAMES.keys()))...`

## venom_real_market_analysis_alternative.py
Violations: 19
- Line 122: `price_noise = np.random.uniform(-daily_range * 0.02, daily_range * 0.02)...`
- Line 126: `bar_range = daily_range * np.random.uniform(0.01, 0.05)  # Small portion of dail...`
- Line 127: `bar_high = bar_open + np.random.uniform(0, bar_range)...`
- Line 128: `bar_low = bar_open - np.random.uniform(0, bar_range)...`
- Line 129: `bar_close = bar_open + np.random.uniform(-bar_range/2, bar_range/2)...`
- Line 251: `is_rapid = np.random.random() < 0.6...`
- Line 257: `stop_pips = np.random.uniform(12, 18)  # VENOM typical range...`
- Line 260: `stop_pips = np.random.uniform(15, 22)  # VENOM typical range...`
- Line 272: `'direction': np.random.choice(['BUY', 'SELL']),...`
- Line 289: `base_confidence = np.random.uniform(65, 88)...`
- Line 294: `base_confidence += np.random.uniform(3, 8)...`
- Line 305: `base_confidence += np.random.uniform(2, 5)...`
- Line 307: `base_confidence -= np.random.uniform(3, 7)...`
- Line 313: `base_confidence += np.random.uniform(1, 3)...`
- Line 351: `slippage = np.random.uniform(0.2, signal['real_spread'] * 0.5)...`
- Line 357: `slippage = np.random.uniform(0.2, signal['real_spread'] * 0.8)...`
- Line 364: `slippage = np.random.uniform(0.2, signal['real_spread'] * 0.5)...`
- Line 370: `slippage = np.random.uniform(0.2, signal['real_spread'] * 0.8)...`
- Line 430: `return np.random.random() < 0.70  # 70% filter rate to match your test...`

## apex_v5_real_performance_backtest.py
Violations: 10
- Line 131: `tcs += np.random.uniform(-3, 3)...`
- Line 153: `return "buy" if np.random.random() > 0.4 else "sell"...`
- Line 300: `price_change = (trend_strength + micro_trend + np.random.uniform(-1, 1) * 0.5) *...`
- Line 302: `if np.random.random() < 0.002:...`
- Line 303: `price_change += np.random.choice([-1, 1]) * np.random.uniform(1.0, 3.0) * daily_...`
- Line 305: `open_price = base_price + (np.random.uniform(-0.3, 0.3) * daily_vol)...`
- Line 308: `range_size = daily_vol * np.random.uniform(0.3, 1.2)...`
- Line 309: `high_price = max(open_price, close_price) + range_size * np.random.random()...`
- Line 310: `low_price = min(open_price, close_price) - range_size * np.random.random()...`
- Line 312: `volume = int(np.random.randint(400, 1200) * session_multiplier)...`

## venom_production_optimized.py
Violations: 4
- Line 568: `'open': base_price - np.random.uniform(0, 0.00003),...`
- Line 569: `'high': base_price + np.random.uniform(0.00005, 0.00015),...`
- Line 570: `'low': base_price - np.random.uniform(0.00005, 0.00015),...`
- Line 572: `'volume': np.random.randint(1500, 3500)...`

## engine_test_venom_v7.py
Violations: 1
- Line 41: `test_pair = random.choice(['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'])...`

## debug_venom_generation.py
Violations: 1
- Line 58: `market_data = venom.generate_realistic_market_data(pair, current_time)...`

## EDUCATION_TOUCHPOINTS.py
Violations: 3
- Line 175: `'content': random.choice(mini_games),...`
- Line 247: `category = weak_areas[0] if weak_areas else random.choice(list(tips_pool.keys())...`
- Line 248: `tip = random.choice(tips_pool[category])...`

## mt5_instance_lifecycle_manager.py
Violations: 1
- Line 326: `used = random.randint(0, int(total * 0.7))...`

## apex_production_v6.py
Violations: 18
- Line 688: `'volume_ratio': random.uniform(0.7, 2.2),  # Enhanced with volume analysis later...`
- Line 689: `'rsi': random.uniform(25, 75),  # Real RSI calculation to be added...`
- Line 690: `'ma_alignment': random.uniform(0.3, 0.9),  # Real MA calculation to be added...`
- Line 691: `'macd_signal': random.uniform(-1.0, 1.0),  # Real MACD calculation to be added...`
- Line 692: `'sr_distance': random.uniform(0.1, 0.8),  # Real S&R calculation to be added...`
- Line 693: `'trend_strength': random.uniform(0.2, 0.8),  # Real trend analysis to be added...`
- Line 694: `'pattern_completion': random.uniform(0.4, 0.9),  # Pattern recognition to be add...`
- Line 696: `'momentum_consistency': random.uniform(0.3, 0.8),  # Momentum analysis to be add...`
- Line 697: `'volume_momentum': random.uniform(0.4, 0.9),  # Volume momentum to be added...`
- Line 698: `'market_regime': random.choice(['trending', 'ranging', 'breakout', 'consolidatio...`
- Line 699: `'liquidity_score': random.uniform(0.6, 0.95),  # Liquidity analysis to be added...`
- Line 700: `'correlation_risk': random.uniform(0.1, 0.4),  # Correlation analysis to be adde...`
- Line 714: `technical_score = 45 + random.uniform(0, 35)  # 45-80 range...`
- Line 715: `pattern_score = 40 + random.uniform(0, 35)    # 40-75 range...`
- Line 716: `momentum_score = 42 + random.uniform(0, 33)   # 42-75 range...`
- Line 717: `structure_score = 45 + random.uniform(0, 30)  # 45-75 range...`
- Line 719: `volume_score = 48 + random.uniform(0, 24)     # 48-72 range...`
- Line 840: `return random.random() < generation_prob...`

## dynamic_alert_elements.py
Violations: 1
- Line 81: `random.shuffle(all_alerts)...`

## apex_venom_v7_with_smart_timer.py
Violations: 1
- Line 356: `"""Get REAL market data from MT5 container - NO FAKE DATA"""...`

## apex_6_standalone_backtest.py
Violations: 25
- Line 103: `def generate_realistic_market_data(self, pair: str, timestamp: datetime) -> Dict...`
- Line 125: `price_change = random.uniform(-volatility/2, volatility/2) * pip_size * session_...`
- Line 130: `'EURUSD': random.uniform(0.8, 1.5), 'GBPUSD': random.uniform(1.2, 2.0),...`
- Line 131: `'USDJPY': random.uniform(1.0, 1.8), 'USDCAD': random.uniform(1.5, 2.5),...`
- Line 132: `'AUDUSD': random.uniform(1.0, 2.0), 'NZDUSD': random.uniform(1.5, 2.5),...`
- Line 133: `'XAUUSD': random.uniform(0.3, 0.8), 'XAGUSD': random.uniform(2.0, 4.0)...`
- Line 134: `}.get(pair, random.uniform(1.5, 3.0))...`
- Line 141: `volume = random.randint(800, 2500) * session_vol...`
- Line 158: `technical_score = random.uniform(40, 75)      # Technical indicators...`
- Line 159: `pattern_score = random.uniform(35, 70)        # Pattern recognition...`
- Line 160: `momentum_score = random.uniform(40, 75)       # Momentum analysis...`
- Line 161: `structure_score = random.uniform(35, 65)      # Market structure...`
- Line 223: `market_data = self.generate_realistic_market_data(pair, timestamp)...`
- Line 247: `if random.random() > generation_prob:...`
- Line 252: `direction = random.choice(['BUY', 'SELL'])...`
- Line 260: `target_pips = random.randint(25, 40)...`
- Line 261: `stop_pips = random.randint(15, 20)...`
- Line 264: `target_pips = random.randint(15, 30)...`
- Line 265: `stop_pips = random.randint(10, 15)...`
- Line 268: `target_pips = random.randint(10, 20)...`
- Line 269: `stop_pips = random.randint(8, 12)...`
- Line 292: `is_win = random.random() < signal['win_probability']...`
- Line 295: `slippage = random.uniform(0.2, 0.8)  # Realistic slippage...`
- Line 303: `slippage_mult = 1.1 if random.random() > 0.85 else 1.0...`
- Line 365: `pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(3, 6))...`

## extract_historical_forex_data.py
Violations: 6
- Line 254: `synthetic_data = await self.generate_realistic_synthetic_data(pair, start_date, ...`
- Line 261: `return await self.generate_realistic_synthetic_data(pair, start_date, end_date)...`
- Line 263: `async def generate_realistic_synthetic_data(self, pair: str, start_date: datetim...`
- Line 331: `spread = 0.02 + np.random.uniform(0, 0.01)  # 2-3 pip spread for JPY pairs...`
- Line 333: `spread = 0.00015 + np.random.uniform(0, 0.00005)  # 1.5-2 pip spread...`
- Line 343: `base_volume = np.random.randint(100, 500)...`

## disable_fake_data_permanently.py
Violations: 10
- Line 3: `Permanently disable fake data generation in VENOM...`
- Line 13: `fake_method_start = content.find('def generate_realistic_market_data(self, pair:...`
- Line 13: `fake_method_start = content.find('def generate_realistic_market_data(self, pair:...`
- Line 36: `replacement = '''def generate_realistic_market_data(self, pair: str, timestamp: ...`
- Line 37: `"""PERMANENTLY DISABLED - NO FAKE DATA ALLOWED"""...`
- Line 38: `raise RuntimeError(f"FAKE DATA GENERATION FORBIDDEN! Use get_real_mt5_data() for...`
- Line 46: `'market_data = self.generate_realistic_market_data(pair, timestamp)',...`
- Line 54: `print("✅ FAKE DATA GENERATION PERMANENTLY DISABLED!")...`
- Line 55: `print("   - generate_realistic_market_data() now throws RuntimeError")...`
- Line 57: `print("   - NO FAKE DATA can ever be generated again!")...`

## apex_venom_v7_production_mt5.py
Violations: 1
- Line 11: `- Zero fake/synthetic/simulated data...`

## deploy_unified_personality_system.py
Violations: 1
- Line 304: `selected_story = random.choice(story_elements)...`

## TRAINING_INTEGRATION.py
Violations: 1
- Line 194: `activity = random.choice(suitable)...`

## true_signal_backtest.py
Violations: 6
- Line 171: `outcome = "WIN" if random.random() < win_probability else "LOSS"...`
- Line 176: `hours_to_close = random.uniform(4, 48)...`
- Line 181: `hours_to_close = random.uniform(1, 12)...`
- Line 188: `if outcome == "WIN" and random.random() < 0.3:...`
- Line 190: `extended_profit = tp_distance * random.uniform(1.1, 1.5)...`
- Line 195: `pnl_r *= random.uniform(1.1, 1.4)...`

## create_matrix_wallpaper.py
Violations: 5
- Line 44: `col_height = random.randint(height // 4, height)...`
- Line 45: `start_y = random.randint(0, height // 2)...`
- Line 57: `char = random.choice(matrix_chars)...`
- Line 65: `alpha = int(255 * fade_factor * random.uniform(0.3, 1.0))...`
- Line 128: `alpha_factor = random.uniform(0.3, 0.8)...`

## apex_venom_v7_http_realtime.py
Violations: 4
- Line 5: `NO FAKE/SYNTHETIC DATA EVER...`
- Line 40: `logger.info("🔒 100% REAL DATA - NO SYNTHETIC/FAKE DATA")...`
- Line 43: `"""Get REAL market data from HTTP endpoint - NO FAKE DATA EVER"""...`
- Line 174: `logger.info("🔒 Using 100% REAL market data - NO FAKE DATA")...`

## venom_real_performance_backtest.py
Violations: 8
- Line 114: `price_change = (trend_strength + micro_trend + np.random.uniform(-1, 1) * 0.5) *...`
- Line 117: `if np.random.random() < 0.001:  # Rare but impactful...`
- Line 118: `price_change += np.random.choice([-1, 1]) * np.random.uniform(1.0, 3.0) * daily_...`
- Line 121: `open_price = base_price + (np.random.uniform(-0.3, 0.3) * daily_vol)...`
- Line 125: `range_size = daily_vol * np.random.uniform(0.3, 1.2)...`
- Line 126: `high_price = max(open_price, close_price) + range_size * np.random.random()...`
- Line 127: `low_price = min(open_price, close_price) - range_size * np.random.random()...`
- Line 129: `volume = int(np.random.randint(200, 800) * session_multiplier)...`

## apex_backtester_api.py
Violations: 14
- Line 69: `macro_sentiment = random.uniform(-1, 1)...`
- Line 75: `if day % random.randint(7, 14) == 0:...`
- Line 76: `trend = random.uniform(-1, 1)...`
- Line 79: `macro_sentiment += random.uniform(-0.1, 0.1)...`
- Line 90: `change = (trend * 0.2 + macro_sentiment * 0.1 + random.uniform(-0.5, 0.5)) * vol...`
- Line 93: `if random.random() < 0.03:...`
- Line 94: `change += random.uniform(-3, 3) * volatility * 0.0001...`
- Line 102: `high_price = max(open_price, close_price) + range_size * random.random()...`
- Line 103: `low_price = min(open_price, close_price) - range_size * random.random()...`
- Line 106: `base_volume = random.randint(500, 2000) * session_vol...`
- Line 116: `'spread': random.uniform(0.8, 2.5),...`
- Line 445: `is_win = random.random() < win_rate...`
- Line 448: `slippage = random.uniform(0.1, 0.4)...`
- Line 456: `slippage_mult = 1.2 if random.random() > 0.9 else 1.0...`

## full_15_pair_backtest.py
Violations: 23
- Line 109: `structure_score = random.randint(12, 20)...`
- Line 113: `alignment_score = random.randint(8, 15)...`
- Line 117: `momentum_score = random.randint(10, 15)...`
- Line 121: `volatility_score = random.randint(6, 10)...`
- Line 127: `session_score = min(15, session_bonus + random.randint(0, 3))...`
- Line 131: `confluence_score = random.randint(12, 20)...`
- Line 135: `velocity_score = random.choice([6, 4, 3, 6, 4])  # M1/M3 bias...`
- Line 139: `rr_score = random.randint(3, 5)...`
- Line 158: `direction = random.choice(['BUY', 'SELL'])...`
- Line 162: `signal_type = 'RAPID_ASSAULT' if random.random() < 0.75 else 'SNIPER_OPS'...`
- Line 166: `rr_ratio = random.uniform(2.7, 3.0)...`
- Line 168: `rr_ratio = random.uniform(1.5, 2.6)...`
- Line 172: `rr_ratio *= random.uniform(1.05, 1.15)...`
- Line 183: `entry_price += random.uniform(-0.01, 0.01)  # Price variation...`
- Line 194: `sl_pips = random.randint(15, 35)  # Wider range for different volatilities...`
- Line 240: `if random.random() < 0.2:  # 20% chance of extreme outcome...`
- Line 241: `win_probability = random.choice([0.9, 0.1])  # Very high or very low...`
- Line 244: `outcome = "WIN" if random.random() < win_probability else "LOSS"...`
- Line 249: `if tcs_score >= 85 and random.random() < 0.2:...`
- Line 250: `pnl_r *= random.uniform(1.2, 1.8)...`
- Line 288: `if random.random() < signal_probability:...`
- Line 293: `num_signals = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]...`
- Line 297: `symbol = random.choice(active_pairs)...`

## venom_production_validator.py
Violations: 8
- Line 111: `price_change = (trend_strength + np.random.uniform(-1, 1) * 0.5) * daily_vol...`
- Line 112: `if np.random.random() < 0.03:  # News events...`
- Line 113: `price_change += np.random.choice([-1, 1]) * np.random.uniform(0.5, 2.0) * daily_...`
- Line 115: `open_price = base_price + (np.random.uniform(-0.5, 0.5) * daily_vol)...`
- Line 118: `range_size = daily_vol * np.random.uniform(0.8, 1.5)...`
- Line 119: `high_price = max(open_price, close_price) + range_size * np.random.random()...`
- Line 120: `low_price = min(open_price, close_price) - range_size * np.random.random()...`
- Line 122: `volume = int(np.random.randint(800, 2500) * session_multiplier)...`

## apex_realistic_flow_engine.py
Violations: 14
- Line 161: `technical_score = random.uniform(50, 95)...`
- Line 162: `pattern_strength = random.uniform(45, 90)...`
- Line 163: `market_momentum = random.uniform(40, 85)...`
- Line 196: `direction=random.choice(['BUY', 'SELL']),...`
- Line 233: `return TradeType.RAID if random.random() < 0.7 else TradeType.SNIPER...`
- Line 236: `return TradeType.RAID if random.random() < 0.3 else TradeType.SNIPER...`
- Line 239: `return random.choice([TradeType.RAID, TradeType.SNIPER])...`
- Line 256: `base_duration = random.uniform(15, 45)...`
- Line 261: `base_duration = random.uniform(30, 90)...`
- Line 286: `base_pips = random.uniform(8, 25)...`
- Line 291: `base_pips = random.uniform(20, 50)...`
- Line 381: `for symbol in random.sample(self.trading_pairs, 5):  # Random 5 pairs each check...`
- Line 384: `if random.random() < 0.08:  # 8% chance per pair per 10-min interval...`
- Line 421: `is_win = random.random() < signal.expected_win_probability...`

## mt5_real_tick_extractor.py
Violations: 4
- Line 4: `ZERO FAKE DATA - ONLY REAL MT5 PRICES...`
- Line 30: `logger.info(f"⚡ ZERO FAKE DATA - REAL PRICES ONLY")...`
- Line 154: `"""Get REAL tick data from MT5 - NO FAKE DATA"""...`
- Line 219: `logger.info("🎯 MT5 REAL TICK EXTRACTOR - ZERO FAKE DATA")...`

## prove_real_data.py
Violations: 3
- Line 44: `print("   - NO FAKE DATA: Empty dict returned if file missing")...`
- Line 47: `print("\n4️⃣ FAKE DATA GENERATOR DISABLED:")...`
- Line 48: `print("   - generate_realistic_market_data() → OVERRIDDEN")...`

## venom_engine.py
Violations: 4
- Line 550: `'open': base_price - np.random.uniform(0, 0.0001),...`
- Line 551: `'high': base_price + np.random.uniform(0, 0.0002),...`
- Line 552: `'low': base_price - np.random.uniform(0, 0.0002),...`
- Line 554: `'volume': np.random.randint(1000, 3000)...`

## apex_production_live.py
Violations: 1
- Line 11: `- Zero fake/synthetic/simulated data...`

## apex_adaptive_flow_engine.py
Violations: 9
- Line 224: `'direction': random.choice(['BUY', 'SELL']),...`
- Line 250: `base_pattern = random.uniform(35, 85)...`
- Line 251: `base_confluence = random.uniform(40, 90)...`
- Line 252: `base_fundamental = random.uniform(30, 80)...`
- Line 256: `base_confluence += random.uniform(5, 15)...`
- Line 257: `base_fundamental += random.uniform(0, 10)...`
- Line 263: `'market_regime_score': random.uniform(50, 85)...`
- Line 391: `if random.random() < 0.15:  # 15% chance per pair per 5-min interval...`
- Line 433: `is_win = random.random() < win_prob...`

## apex_v6_clean.py
Violations: 10
- Line 73: `technical_base = 45 + random.uniform(0, 30)    # 45-75...`
- Line 74: `pattern_base = 40 + random.uniform(0, 30)      # 40-70...`
- Line 75: `momentum_base = 42 + random.uniform(0, 28)     # 42-70...`
- Line 76: `structure_base = 45 + random.uniform(0, 25)    # 45-70...`
- Line 77: `volume_base = 48 + random.uniform(0, 22)       # 48-70...`
- Line 119: `price_variation = random.uniform(-0.001, 0.001)...`
- Line 121: `bid = ask - random.uniform(0.00008, 0.00025)  # Realistic spread...`
- Line 127: `'volume': random.randint(800000, 2500000),...`
- Line 128: `'volume_ratio': random.uniform(0.7, 1.8),...`
- Line 182: `return 'BUY' if random.random() < buy_probability else 'SELL'...`

## venom_filtered_live_test.py
Violations: 23
- Line 180: `return random.random() < 0.08  # 8% chance of news...`
- Line 257: `direction = random.choice(['BUY', 'SELL'])...`
- Line 261: `stop_pips = random.randint(10, 15)...`
- Line 264: `stop_pips = random.randint(15, 20)...`
- Line 320: `expected_slippage = random.uniform(...`
- Line 329: `is_news_time = random.random() < self.live_market_factors['news_events']...`
- Line 330: `is_low_liquidity = random.random() < self.live_market_factors['liquidity_gaps']...`
- Line 331: `is_friday_close = random.random() < 0.05...`
- Line 332: `broker_issues = random.random() < self.live_market_factors['server_issues']...`
- Line 333: `flash_crash_risk = random.random() < self.live_market_factors['flash_crashes']...`
- Line 337: `expected_slippage *= random.uniform(2.0, 4.0)...`
- Line 341: `expected_slippage *= random.uniform(1.5, 2.5)...`
- Line 345: `expected_slippage *= random.uniform(1.2, 1.8)...`
- Line 373: `execution_success = random.random() < live_conditions['execution_probability']...`
- Line 384: `is_win = random.random() < signal['win_probability']...`
- Line 431: `return random.choice(regimes)...`
- Line 434: `return random.uniform(65, 90)...`
- Line 447: `return random.random() < 0.25  # 25% base generation rate...`
- Line 450: `return random.choice(['RAPID_ASSAULT', 'PRECISION_STRIKE'])...`
- Line 460: `'spread': random.uniform(0.8, 3.0),...`
- Line 461: `'volume': random.randint(1000, 2000),...`
- Line 463: `'volatility': random.uniform(0.5, 2.0)...`
- Line 498: `pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(6, 10))...`

## deploy_intel_command_center.py
Violations: 1
- Line 609: `f"{random.choice(norman_quotes)}\n\n"...`

## apex_ultra_engine.py
Violations: 22
- Line 92: `if random.random() < 0.45:  # 45% chance of pattern detection...`
- Line 93: `strength = random.uniform(0.7, 1.0)...`
- Line 108: `regime = random.choice(regimes)...`
- Line 111: `volatility_percentile = random.uniform(0, 100)...`
- Line 112: `trend_strength = random.uniform(0, 100)...`
- Line 113: `support_resistance_quality = random.uniform(60, 95)  # Bias toward good levels...`
- Line 114: `volume_profile = random.choice(['accumulation', 'distribution', 'neutral'])...`
- Line 115: `news_impact_score = random.uniform(0, 100)...`
- Line 116: `correlation_risk = random.uniform(0, 100)...`
- Line 117: `liquidity_score = random.uniform(70, 100)  # Bias toward good liquidity...`
- Line 150: `agreement = random.random() < base_agreement...`
- Line 153: `strength = random.uniform(0.75, 1.0)  # Strong agreements...`
- Line 187: `if random.random() < alignment_probability:...`
- Line 188: `strength = random.uniform(0.7, 1.0)...`
- Line 301: `direction = random.choice(['BUY', 'SELL'])...`
- Line 323: `entry_price = base_prices.get(symbol, 1.0000) + random.uniform(-0.01, 0.01)...`
- Line 327: `rr_ratio = random.uniform(3.0, 4.5)  # Surgical precision...`
- Line 329: `rr_ratio = random.uniform(2.5, 3.5)  # High precision...`
- Line 331: `rr_ratio = random.uniform(2.0, 3.0)  # Tactical...`
- Line 335: `sl_pips = random.randint(15, 25)...`
- Line 421: `if random.random() < (target_signals_per_hour / len(self.ultra_pairs)):...`
- Line 451: `outcome = "WIN" if random.random() < signal.expected_win_probability else "LOSS"...`

## bitten_voice_personality_bot.py
Violations: 1
- Line 267: `response = random.choice(responses)...`

## apex_engine_reproduction.py
Violations: 15
- Line 94: `structure_score = random.randint(12, 20)  # Strong bias toward good structure...`
- Line 99: `alignment_score = random.randint(8, 15)  # Good alignment typical...`
- Line 104: `momentum_score = random.randint(10, 15)  # Strong momentum required...`
- Line 108: `volatility_score = random.randint(6, 10)...`
- Line 116: `session_score = min(15, session_bonus + random.randint(0, 3))...`
- Line 120: `confluence_score = random.randint(12, 20)  # High importance...`
- Line 125: `velocity_score = random.choice([6, 4, 3, 6, 4])  # Bias toward M1/M3...`
- Line 129: `rr_score = random.randint(3, 5)...`
- Line 144: `rand = random.random()...`
- Line 155: `base_rr = random.uniform(rr_range[0], rr_range[1])...`
- Line 178: `sl_pips = random.randint(10, 25)...`
- Line 199: `direction = random.choice(['BUY', 'SELL'])...`
- Line 220: `entry_price += random.uniform(-0.005, 0.005)...`
- Line 266: `if random.random() < signal_probability:...`
- Line 268: `symbol = random.choice(self.config['TRADING_PAIRS'][:4])  # Focus on major 4...`

## src/bitten_core/daily_drill_report.py
Violations: 4
- Line 348: `header = random.choice(responses["headers"])...`
- Line 349: `comment = random.choice(responses["comments"])...`
- Line 350: `motivational = random.choice(responses["motivational"])...`
- Line 351: `tomorrow = random.choice(self.TOMORROW_GUIDANCE[drill_tone])...`

## src/bitten_core/press_pass_manager.py
Violations: 2
- Line 183: `remaining = max(3, int(base_remaining + random.randint(-2, 2)))...`
- Line 219: `ab_variant = random.choice(self.ab_variants)...`

## src/bitten_core/intel_bot_personalities.py
Violations: 1
- Line 385: `{random.choice(responses)}...`

## src/bitten_core/real_position_calculator.py
Violations: 1
- Line 27: `CRITICAL: NO FAKE DATA - ALL CALCULATIONS REAL...`

## src/bitten_core/audio_configuration.py
Violations: 1
- Line 415: `return random.random() < trigger_chance...`

## src/bitten_core/observer_elon_bot.py
Violations: 15
- Line 190: `mood = random.choice(list(ElonMood))...`
- Line 195: `observation = random.choice(observations)...`
- Line 199: `quote = random.choice(self.quotes['memes'])...`
- Line 201: `quote = random.choice(self.quotes['general'])...`
- Line 203: `quote = random.choice(self.quotes['market'])...`
- Line 221: `market_insight=random.choice(insights),...`
- Line 228: `observation = random.choice(observations)...`
- Line 235: `quote = random.choice(self.quotes['general'][:5])  # More serious quotes...`
- Line 237: `quote = random.choice(self.quotes['motivational'])...`
- Line 275: `return random.choice(feedback_templates.get(behavior_type, ["Keep trading smart....`
- Line 288: `mood, message = random.choice(moods_and_messages)...`
- Line 293: `quote = random.choice(self.quotes[quote_category])...`
- Line 326: `quote = random.choice(self.quotes['market'])...`
- Line 347: `return random.choice(comments)...`
- Line 361: `return random.choice(thoughts)...`

## src/bitten_core/kill_card_generator.py
Violations: 1
- Line 162: `val = random.randint(0, 20)...`

## src/bitten_core/smart_execution_layer.py
Violations: 2
- Line 381: `slippage = random.uniform(-0.0001, 0.0001)...`
- Line 401: `return random.uniform(30, 120)...`

## src/bitten_core/engagement_system.py
Violations: 20
- Line 318: `selected_bots = random.sample(user_bots, mission_count)...`
- Line 323: `mission_type = random.choice(list(MissionType))...`
- Line 349: `"target": random.randint(3, 10),...`
- Line 354: `"target": random.randint(2, 5),...`
- Line 359: `"target": random.randint(10, 20),...`
- Line 364: `"target": random.randint(500, 2000),...`
- Line 374: `"target": random.randint(1, 3),...`
- Line 379: `"target": random.randint(2, 5),...`
- Line 384: `"target": random.randint(1, 3),...`
- Line 467: `rand = random.random()...`
- Line 481: `Reward(RewardType.BITS, random.randint(50, 200)),...`
- Line 482: `Reward(RewardType.XP, random.randint(10, 50))...`
- Line 485: `Reward(RewardType.BITS, random.randint(200, 500)),...`
- Line 486: `Reward(RewardType.XP, random.randint(50, 100)),...`
- Line 490: `Reward(RewardType.BITS, random.randint(500, 1000)),...`
- Line 491: `Reward(RewardType.XP, random.randint(100, 200)),...`
- Line 495: `Reward(RewardType.BITS, random.randint(1000, 2000)),...`
- Line 496: `Reward(RewardType.XP, random.randint(200, 500)),...`
- Line 501: `Reward(RewardType.BITS, random.randint(2000, 5000)),...`
- Line 502: `Reward(RewardType.XP, random.randint(500, 1000)),...`

## src/bitten_core/real_statistics_tracker.py
Violations: 1
- Line 55: `CRITICAL: NO FAKE DATA - ALL STATISTICS REAL...`

## src/bitten_core/trading_audio_feedback.py
Violations: 1
- Line 665: `return random.choice(available_clips) if available_clips else None...`

## src/bitten_core/gear_integration.py
Violations: 6
- Line 126: `if random.random() > base_chance:...`
- Line 196: `if random.random() < 0.7:  # 70% chance to match theme...`
- Line 226: `if random.random() > chance:...`
- Line 245: `if random.random() < 0.3:...`
- Line 269: `if random.random() > base_chance:...`
- Line 322: `if random.random() > chance:...`

## src/bitten_core/personalized_mission_brain.py
Violations: 1
- Line 69: `"SIMULATION_MODE", "DEMO_MODE", "FAKE_DATA",...`

## src/bitten_core/ambient_audio_system.py
Violations: 2
- Line 544: `return random.choice(matching_clips)...`
- Line 667: `if random.random() < 0.1:  # 10% chance every cycle...`

## src/bitten_core/hud_router.py
Violations: 2
- Line 265: `success = random.random() > 0.1  # 90% success rate...`
- Line 271: `'entry_price': signal.entry_price + random.uniform(-0.0001, 0.0001)...`

## src/bitten_core/mississippi_ambient.py
Violations: 5
- Line 504: `base_clip_id = random.choice(cluster.base_clips)...`
- Line 515: `if random.random() < 0.3 and cluster.accent_clips:  # 30% chance...`
- Line 516: `accent_clip_id = random.choice(cluster.accent_clips)...`
- Line 521: `await asyncio.sleep(random.uniform(5, 15))...`
- Line 525: `wait_time = random.uniform(30, 90)  # 30-90 seconds between clips...`

## src/bitten_core/self_optimizing_tcs.py
Violations: 4
- Line 343: `return np.random.uniform(0.5, 0.9)...`
- Line 348: `return np.random.uniform(1.0, 2.0)...`
- Line 353: `return np.random.uniform(0.4, 0.8)...`
- Line 358: `return np.random.uniform(0.5, 0.9)...`

## src/bitten_core/conversion_dashboard.py
Violations: 2
- Line 523: `return round(random.uniform(-20, 30), 2)...`
- Line 535: `f"{h}:00": random.randint(5, 50)...`

## src/bitten_core/bit_integration.py
Violations: 2
- Line 65: `enhancement = random.choice(enhancements)...`
- Line 158: `if not self.bit_active or random.random() > chance:...`

## src/bitten_core/npc_xp_integration.py
Violations: 3
- Line 365: `return random.choice([...`
- Line 371: `return random.choice([...`
- Line 377: `return random.choice([...`

## src/bitten_core/gear_system.py
Violations: 18
- Line 682: `selected_rarity = random.choices(rarities, weights=weights)[0]...`
- Line 685: `item_type = random.choice(list(GearType))...`
- Line 688: `item_id = f"drop_{int(time.time())}_{random.randint(1000, 9999)}"...`
- Line 694: `accuracy_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5...`
- Line 695: `range_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5 el...`
- Line 696: `fire_rate_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0....`
- Line 697: `damage_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5 e...`
- Line 698: `mobility_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5...`
- Line 699: `control_bonus=random.uniform(0, 0.1) * stat_multiplier if random.random() > 0.5 ...`
- Line 700: `xp_multiplier=1.0 + (random.uniform(0, 0.2) * stat_multiplier if selected_rarity...`
- Line 701: `reward_multiplier=1.0 + (random.uniform(0, 0.2) * stat_multiplier if selected_ra...`
- Line 702: `cooldown_reduction=random.uniform(0, 0.1) * stat_multiplier if selected_rarity.v...`
- Line 703: `critical_chance=random.uniform(0, 0.05) * stat_multiplier if selected_rarity.val...`
- Line 725: `prefix = random.choice(prefixes.get(selected_rarity, ["Unknown"]))...`
- Line 726: `suffix = random.choice(suffixes.get(item_type, ["Item"]))...`
- Line 740: `slot = random.choice(available_slots) if available_slots else None...`
- Line 748: `level=max(1, min(user_level + random.randint(-5, 10), 100)),...`
- Line 832: `if random.random() <= recipe.success_rate:...`

## src/bitten_core/universal_stealth_shield.py
Violations: 14
- Line 110: `self.typing_speed = random.uniform(0.08, 0.15)  # Seconds between keystrokes...`
- Line 111: `self.reaction_time = random.uniform(0.3, 0.8)   # Human reaction delay...`
- Line 253: `delay = random.uniform(min_delay, max_delay) * fatigue_multiplier...`
- Line 267: `if time_since_break > random.randint(120, 180):...`
- Line 268: `break_duration = random.randint(10, 30)  # 10-30 min break...`
- Line 272: `if random.random() < 0.02:  # 2% chance per check...`
- Line 273: `return True, random.randint(3, 8)...`
- Line 281: `if random.random() < mistake_chance:...`
- Line 282: `mistake_type = random.choice([...`
- Line 291: `trade_params['volume'] *= random.uniform(0.9, 1.1)...`
- Line 296: `trade_params['volume'] *= random.choice([0.1, 10])...`
- Line 308: `trade_params['entry'] *= random.uniform(0.995, 1.005)...`
- Line 319: `return random.random() < 0.3  # 30% chance to force a loss...`
- Line 360: `return random.choice(personalities)...`

## src/bitten_core/daily_challenges.py
Violations: 1
- Line 385: `selected_types = random.sample(challenge_types, min(3, len(challenge_types)))...`

## src/bitten_core/persona_system.py
Violations: 19
- Line 128: `message = random.choice(lines)...`
- Line 211: `message = random.choice(lines)...`
- Line 289: `message = random.choice(lines)...`
- Line 355: `message = random.choice(lines)...`
- Line 362: `if random.random() < 0.3:...`
- Line 363: `message += " " + random.choice(self.warnings)...`
- Line 456: `if event == 'big_win' and random.random() < 0.3:...`
- Line 457: `message = random.choice(self.bit_memories['celebration'])...`
- Line 458: `elif event == 'loss' and random.random() < 0.4:...`
- Line 459: `message = random.choice(self.bit_memories['comfort'])...`
- Line 460: `elif event in ['perfect_setup', 'danger'] and random.random() < 0.2:...`
- Line 461: `message = random.choice(self.bit_memories['warning'])...`
- Line 464: `if user_state == EmotionalState.DEFEATED and random.random() < 0.5:...`
- Line 465: `message = random.choice(self.bit_memories['comfort'])...`
- Line 467: `elif user_state == EmotionalState.IMPULSIVE and random.random() < 0.3:...`
- Line 468: `message = random.choice(self.bit_memories['warning'])...`
- Line 470: `elif user_state == EmotionalState.EUPHORIC and random.random() < 0.2:...`
- Line 471: `message = random.choice(self.bit_memories['patience'])...`
- Line 537: `if event_type.startswith('user_') and random.random() < 0.2:...`

## src/bitten_core/trade_manager.py
Violations: 1
- Line 293: `change = random.uniform(-0.0005, 0.0005)...`

## src/bitten_core/tactical_mission_framework.py
Violations: 5
- Line 298: `base = random.choice(tier_callsigns.get(user_tier, tier_callsigns['RECRUIT']))...`
- Line 316: `if random.random() < 0.3:  # 30% chance for story enhancement...`
- Line 319: `return base_callsign + random.choice(enhancements)...`
- Line 613: `return random.choice(contexts)...`
- Line 649: `return random.choice(wisdom_options)...`

## src/bitten_core/xp_celebration_system.py
Violations: 5
- Line 313: `title = random.choice(titles)...`
- Line 364: `message=random.choice(drill_responses),...`
- Line 375: `message=random.choice(analyst_responses),...`
- Line 385: `message=random.choice(psych_responses),...`
- Line 395: `message=random.choice(insider_responses),...`

## src/bitten_core/observer_integration.py
Violations: 12
- Line 92: `if random.random() < probability:...`
- Line 136: `r = random.uniform(0, total)...`
- Line 178: `if random.random() < 0.3:  # 30% chance...`
- Line 197: `should_comment = random.random() < 0.4...`
- Line 200: `should_comment = random.random() < 0.5...`
- Line 203: `should_comment = random.random() < 0.3...`
- Line 227: `if random.random() < 0.7:  # 70% chance...`
- Line 237: `if random.random() < 0.3:  # 30% chance for positive reinforcement...`
- Line 249: `if random.random() < 0.8:...`
- Line 292: `return random.choice(category_messages)...`
- Line 319: `insight = random.choice(insights)...`
- Line 320: `quote = random.choice(self.elon_bot.quotes['general'])...`

## src/bitten_core/intel_command_center.py
Violations: 1
- Line 1146: `'message': random.choice(self.easter_eggs['bit_quotes']),...`

## src/bitten_core/zero_simulation_integration.py
Violations: 1
- Line 103: `'DEMO_MODE', 'SIMULATION_MODE', 'FAKE_DATA', 'MOCK_DATA',...`

## src/bitten_core/mt5_fallback.py
Violations: 5
- Line 3: `🔧 MT5 REAL CONNECTION SYSTEM - ZERO FAKE DATA...`
- Line 17: `NO FAKE DATA, NO SIMULATION, NO FALLBACK DATA...`
- Line 38: `raise Exception("CRITICAL: MetaTrader5 package required - NO FAKE DATA ALLOWED")...`
- Line 72: `"""Get REAL account info - NO FAKE DATA"""...`
- Line 94: `"""Get REAL symbol info - NO FAKE DATA"""...`

## src/bitten_core/mission_briefing_generator.py
Violations: 15
- Line 479: `if random.random() < 0.3:...`
- Line 487: `norman_touch = f"\n{random.choice(quick_wisdom)}"...`
- Line 523: `return random.choice(callsigns)...`
- Line 635: `if random.random() < 0.3:...`
- Line 636: `wisdom_type = random.choice(['grandmother', 'mother', 'work_ethic'])...`
- Line 637: `wisdom = random.choice(self.norman_story.family_wisdom[wisdom_type])...`
- Line 648: `bit_warning = random.choice(self.norman_story.bit_presence['caution'])...`
- Line 669: `if random.random() < 0.4:...`
- Line 676: `warnings.append(random.choice(protection_wisdom))...`
- Line 848: `return random.choice(self.norman_story.bit_presence['confidence'])...`
- Line 852: `return random.choice(self.norman_story.bit_presence['caution'])...`
- Line 855: `elif random.random() < 0.2:...`
- Line 856: `return random.choice(self.norman_story.bit_presence['comfort'])...`
- Line 870: `if random.random() < 0.15:  # 15% chance for context...`
- Line 871: `context_type = random.choice(list(context_additions.keys()))...`

## src/bitten_core/event_system.py
Violations: 3
- Line 134: `num_happy_hours = random.randint(2, 3)...`
- Line 138: `hour = random.randint(9, 21)...`
- Line 139: `duration = random.randint(1, 2)  # 1-2 hours...`

## src/bitten_core/bit_warnings.py
Violations: 4
- Line 133: `wisdom_quote = random.choice(self.wisdom_quotes[warning_level]).format(tcs=tcs)...`
- Line 213: `return random.choice(patience_quotes)...`
- Line 232: `warning_message = random.choice(serious_warnings.get(warning_level, ["Proceed at...`
- Line 396: `return random.choice(reactions)...`

## src/bitten_core/master_filter.py
Violations: 1
- Line 278: `if random.random() < 0.05:  # 5% chance when conditions met...`

## src/bitten_core/fire_mode_validator.py
Violations: 2
- Line 703: `return random.randint(120, 300)  # 2-5 minutes...`
- Line 705: `return random.randint(1, 5)  # Realistic latency...`

## src/bitten_core/tradermade_client.py
Violations: 3
- Line 191: `high = open_price * (1 + abs(movement) + random.uniform(0, 0.0002))...`
- Line 192: `low = open_price * (1 - abs(movement) - random.uniform(0, 0.0002))...`
- Line 201: `'volume': random.randint(100, 1000)...`

## src/bitten_core/norman_story_integration.py
Violations: 5
- Line 263: `wisdom = random.choice(appropriate_wisdom)...`
- Line 315: `enhanced_briefing['regional_touch'] = random.choice(self.story_database['mississ...`
- Line 328: `enhanced_briefing['cultural_element'] = random.choice(...`
- Line 347: `if random.random() < 0.15:  # 15% chance for story enhancement...`
- Line 350: `return base_callsign + random.choice(suffixes)...`

## src/bitten_core/enhanced_ghost_tracker.py
Violations: 12
- Line 85: `if random.random() < stealth_intensity:...`
- Line 91: `if 'lot_size' in signal_data and random.random() < stealth_intensity:...`
- Line 97: `if random.random() < stealth_intensity * 0.8:  # Slightly less frequent...`
- Line 119: `if random.random() < stealth_intensity * 0.3:  # Less frequent but powerful...`
- Line 138: `delay = random.uniform(config['min'], max_delay)...`
- Line 159: `variance_pct = random.uniform(config['min'], max_variance)...`
- Line 162: `modifier = 1.0 + (variance_pct / 100) * random.choice([-1, 1])...`
- Line 189: `offset_pips = random.uniform(-max_offset_pips, max_offset_pips)...`
- Line 213: `offset_pips = random.uniform(-max_offset_pips, max_offset_pips)...`
- Line 243: `should_skip = random.random() < skip_probability...`
- Line 258: `base_delay = random.uniform(30, 300)  # seconds...`
- Line 599: `price_change = random.uniform(-volatility, volatility)...`

## src/bitten_core/real_account_balance.py
Violations: 2
- Line 49: `CRITICAL: NO FAKE DATA - ALL VALUES FROM LIVE BROKERS...`
- Line 71: `'DEMO_MODE', 'SIMULATION', 'FAKE_DATA', 'MOCK_BROKER'...`

## src/bitten_core/volatility_integration.py
Violations: 1
- Line 108: `market_condition = random.choice(['normal', 'elevated', 'high', 'extreme'])...`

## src/bitten_core/voice/bit_personality.py
Violations: 1
- Line 152: `return random.choice(responses)...`

## src/bitten_core/voice/character_event_dispatcher.py
Violations: 6
- Line 224: `return random.choice(responses)...`
- Line 247: `return random.choice(responses)...`
- Line 287: `return random.choice(responses)...`
- Line 310: `return random.choice(responses)...`
- Line 328: `return random.choice(responses)...`
- Line 346: `return random.choice(responses)...`

## src/bitten_core/voice/unified_personality_orchestrator.py
Violations: 5
- Line 330: `if persona_elements and random.random() < 0.2:...`
- Line 331: `persona_insight = random.choice(persona_elements)...`
- Line 358: `if random.random() < 0.1:...`
- Line 365: `story_type = random.choice(story_elements)...`
- Line 368: `return random.choice(story_options)...`

## src/bitten_core/voice/doc_personality.py
Violations: 4
- Line 47: `return random.choice(protective_responses)...`
- Line 69: `return random.choice(warnings)...`
- Line 87: `return random.choice(protective_responses)...`
- Line 112: `return random.choice(messages)...`

## src/bitten_core/voice/nexus_personality.py
Violations: 3
- Line 48: `return random.choice(celebrations)...`
- Line 51: `return random.choice([...`
- Line 81: `return random.choice(messages)...`

## src/bitten_core/onboarding/press_pass_manager.py
Violations: 2
- Line 157: `random_suffix = ''.join(random.choices(string.digits, k=4))...`
- Line 164: `password = ''.join(random.choices(chars, k=12))...`

## src/bitten_core/onboarding/handlers.py
Violations: 1
- Line 358: `auto_callsign = f"Trader{random.randint(1000, 9999)}"...`

## src/order_flow/cumulative_delta.py
Violations: 1
- Line 436: `'side': 'buy' if np.random.random() > 0.45 else 'sell'  # Slight buy bias...`

## src/order_flow/dark_pool_scanner.py
Violations: 3
- Line 316: `random_factor = 0.8 + random.random() * 0.2...`
- Line 337: `return 'buy' if random.random() > 0.3 else 'sell'...`
- Line 495: `'price': base_price + random.uniform(-10, 10),...`

## src/analytics/visualization/funnel_visualizer.py
Violations: 1
- Line 396: `conversions = metrics.get('hourly_conversions', [10 + np.random.randint(-5, 5) f...`

## src/market_prediction/transformer/data/preprocessing.py
Violations: 1
- Line 317: `if self.augment and np.random.random() > 0.5:...`

## scripts/simulate_xp_progression_enhanced.py
Violations: 6
- Line 180: `is_win = random.random() < profile.win_rate...`
- Line 187: `if random.random() < profile.high_tcs_rate:...`
- Line 191: `volume = random.uniform(profile.avg_volume * 0.5, profile.avg_volume * 1.5)...`
- Line 323: `if random.random() > player.profile.retention_rate:...`
- Line 331: `trades_count = 1 if random.random() < avg_trades else 0...`
- Line 384: `weekly_active_days = set(random.sample(range(7), profile.session_days_per_week))...`

## scripts/simulate_xp_progression.py
Violations: 5
- Line 159: `is_win = random.random() < profile.win_rate...`
- Line 166: `if random.random() < profile.high_tcs_rate:...`
- Line 170: `volume = random.uniform(profile.avg_volume * 0.5, profile.avg_volume * 1.5)...`
- Line 263: `trades_count = 1 if random.random() < avg_trades else 0...`
- Line 302: `weekly_active_days = set(random.sample(range(7), profile.session_days_per_week))...`


🚨 CRITICAL VIOLATIONS: 1