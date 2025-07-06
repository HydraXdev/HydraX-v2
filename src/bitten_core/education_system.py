"""
Education System for HydraX - Bit's Training Framework
Provides educational content, trade analysis, and training features
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
from collections import defaultdict

from src.bitten_core.database import Database
from src.bitten_core.logger import Logger
from src.utils import send_discord_message


class TradingTier(Enum):
    """Trading experience tiers"""
    NIBBLER = "nibbler"  # Beginner
    APPRENTICE = "apprentice"  # Intermediate
    JOURNEYMAN = "journeyman"  # Advanced
    MASTER = "master"  # Expert
    GRANDMASTER = "grandmaster"  # Elite


class EducationTopic(Enum):
    """Educational content topics"""
    RISK_MANAGEMENT = "risk_management"
    TECHNICAL_ANALYSIS = "technical_analysis"
    MARKET_PSYCHOLOGY = "market_psychology"
    STRATEGY_BASICS = "strategy_basics"
    ADVANCED_STRATEGIES = "advanced_strategies"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    MACRO_ANALYSIS = "macro_analysis"
    TRADE_EXECUTION = "trade_execution"


@dataclass
class EducationalContent:
    """Educational content structure"""
    topic: EducationTopic
    tier: TradingTier
    title: str
    content: str
    video_link: Optional[str] = None
    practice_exercise: Optional[str] = None
    quiz_questions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TradeAnalysis:
    """Post-trade analysis structure"""
    trade_id: str
    symbol: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_percentage: float
    duration: timedelta
    strategy_used: str
    market_conditions: Dict[str, Any]
    strengths: List[str]
    weaknesses: List[str]
    lessons: List[str]
    improvement_suggestions: List[str]
    grade: str  # A-F grading
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PaperTrade:
    """Paper trading position"""
    trade_id: str
    user_id: str
    symbol: str
    entry_price: float
    position_size: float
    direction: str  # 'long' or 'short'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: Optional[str] = None
    entry_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "open"  # open, closed
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None


class EducationSystem:
    """Main education system manager"""
    
    def __init__(self, database: Database, logger: Logger):
        self.db = database
        self.logger = logger
        
        # Cooldown tracking for NIBBLERs
        self.cooldown_tracker: Dict[str, datetime] = {}
        self.cooldown_duration = timedelta(minutes=30)  # 30-minute forced cooldown
        
        # Paper trading positions
        self.paper_trades: Dict[str, List[PaperTrade]] = defaultdict(list)
        
        # Educational content library
        self.content_library = self._initialize_content_library()
        
        # Strategy video links by tier
        self.strategy_videos = self._initialize_strategy_videos()
        
        # Weekly review tracking
        self.weekly_reviews: Dict[str, datetime] = {}
        
        # Initialize database tables
        asyncio.create_task(self._initialize_database())
    
    async def _initialize_database(self):
        """Initialize education system database tables"""
        try:
            # User education progress table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS user_education_progress (
                    user_id TEXT PRIMARY KEY,
                    tier TEXT NOT NULL DEFAULT 'nibbler',
                    total_trades INTEGER DEFAULT 0,
                    successful_trades INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0.0,
                    lessons_completed TEXT DEFAULT '[]',
                    quiz_scores TEXT DEFAULT '{}',
                    last_cooldown_tip TIMESTAMP,
                    paper_trading_enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Trade analysis history
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS trade_analyses (
                    analysis_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    trade_id TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,
                    grade TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Paper trades table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS paper_trades (
                    trade_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    trade_data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Weekly reviews table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS weekly_reviews (
                    review_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    week_start DATE NOT NULL,
                    review_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            self.logger.info("Education system database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize education database: {e}")
    
    def _initialize_content_library(self) -> Dict[EducationTopic, List[EducationalContent]]:
        """Initialize educational content library"""
        library = defaultdict(list)
        
        # Risk Management Content
        library[EducationTopic.RISK_MANAGEMENT].extend([
            EducationalContent(
                topic=EducationTopic.RISK_MANAGEMENT,
                tier=TradingTier.NIBBLER,
                title="The 1% Rule: Your Trading Safety Net",
                content="""Never risk more than 1% of your account on a single trade. 
                This ensures you can survive 100 losing trades in a row. 
                Example: $10,000 account = max $100 risk per trade.""",
                video_link="https://youtube.com/watch?v=risk_basics_101",
                practice_exercise="Calculate your 1% risk for different account sizes"
            ),
            EducationalContent(
                topic=EducationTopic.RISK_MANAGEMENT,
                tier=TradingTier.APPRENTICE,
                title="Position Sizing: The Key to Survival",
                content="""Position size = Risk Amount / (Entry - Stop Loss)
                This formula ensures consistent risk across all trades.
                Always calculate position size BEFORE entering a trade.""",
                video_link="https://youtube.com/watch?v=position_sizing_guide"
            )
        ])
        
        # Technical Analysis Content
        library[EducationTopic.TECHNICAL_ANALYSIS].extend([
            EducationalContent(
                topic=EducationTopic.TECHNICAL_ANALYSIS,
                tier=TradingTier.NIBBLER,
                title="Support and Resistance: The Foundation",
                content="""Support = price floor where buying pressure emerges
                Resistance = price ceiling where selling pressure appears
                These levels act as magnets for price action.""",
                video_link="https://youtube.com/watch?v=support_resistance_basics"
            )
        ])
        
        # Market Psychology Content
        library[EducationTopic.MARKET_PSYCHOLOGY].extend([
            EducationalContent(
                topic=EducationTopic.MARKET_PSYCHOLOGY,
                tier=TradingTier.NIBBLER,
                title="FOMO: Your Worst Enemy",
                content="""Fear Of Missing Out leads to:
                - Chasing price moves
                - Entering without a plan
                - Revenge trading
                Solution: Stick to YOUR plan, opportunities are infinite.""",
                practice_exercise="Journal 3 times you felt FOMO and didn't act on it"
            )
        ])
        
        return library
    
    def _initialize_strategy_videos(self) -> Dict[TradingTier, List[Dict[str, str]]]:
        """Initialize strategy video links by tier"""
        return {
            TradingTier.NIBBLER: [
                {
                    "title": "Basic Trend Following for Beginners",
                    "url": "https://youtube.com/watch?v=trend_following_101",
                    "duration": "15 min",
                    "focus": "Identifying and riding trends safely"
                },
                {
                    "title": "Simple Moving Average Strategy",
                    "url": "https://youtube.com/watch?v=sma_strategy_basics",
                    "duration": "20 min",
                    "focus": "Using 20/50/200 MA for entries"
                }
            ],
            TradingTier.APPRENTICE: [
                {
                    "title": "Breakout Trading Strategies",
                    "url": "https://youtube.com/watch?v=breakout_strategies",
                    "duration": "25 min",
                    "focus": "Trading range breakouts with volume"
                },
                {
                    "title": "RSI Divergence Trading",
                    "url": "https://youtube.com/watch?v=rsi_divergence_guide",
                    "duration": "30 min",
                    "focus": "Spotting reversals with RSI"
                }
            ],
            TradingTier.JOURNEYMAN: [
                {
                    "title": "Multi-Timeframe Analysis",
                    "url": "https://youtube.com/watch?v=mtf_analysis_advanced",
                    "duration": "35 min",
                    "focus": "Combining timeframes for high probability setups"
                },
                {
                    "title": "Order Flow Trading",
                    "url": "https://youtube.com/watch?v=order_flow_basics",
                    "duration": "40 min",
                    "focus": "Reading market microstructure"
                }
            ]
        }
    
    async def check_nibbler_cooldown(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """Check if NIBBLER is in cooldown and provide educational tip"""
        user_tier = await self.get_user_tier(user_id)
        
        if user_tier != TradingTier.NIBBLER:
            return False, None
        
        last_trade = self.cooldown_tracker.get(user_id)
        if not last_trade:
            return False, None
        
        time_since_trade = datetime.utcnow() - last_trade
        if time_since_trade < self.cooldown_duration:
            remaining = self.cooldown_duration - time_since_trade
            tip = await self._get_cooldown_tip(user_id)
            
            message = f"""🚦 **Cooldown Active** (NIBBLER Protection)
            
Time remaining: {int(remaining.total_seconds() / 60)} minutes

**Educational Tip:**
{tip}

Use this time to:
• Review your last trade
• Practice on paper trades
• Watch a strategy video
• Update your trading journal"""
            
            return True, message
        
        return False, None
    
    async def _get_cooldown_tip(self, user_id: str) -> str:
        """Get educational tip during cooldown"""
        tips = [
            "Did you know? 90% of traders fail because they overtrade. Quality > Quantity!",
            "Tip: The best traders wait for A+ setups. Everything else is noise.",
            "Remember: Preserving capital is more important than making money.",
            "Fun fact: Jesse Livermore made millions by sitting on his hands and waiting.",
            "Psychology tip: FOMO is temporary, but losses are real. Stay patient!",
            "Strategy insight: The best trades often come after periods of doing nothing.",
            "Risk wisdom: You can't go broke taking profits, but you can by taking bad trades.",
            "Market truth: The market will be here tomorrow. Your capital might not be.",
            "Pro tip: Use this time to review your trading plan. Does your last trade fit it?",
            "Education moment: Study your losing trades - they teach more than winners."
        ]
        
        # Track last tip to avoid repetition
        last_tip_time = await self.db.fetch_one(
            "SELECT last_cooldown_tip FROM user_education_progress WHERE user_id = ?",
            (user_id,)
        )
        
        tip = random.choice(tips)
        
        # Update last tip time
        await self.db.execute(
            "UPDATE user_education_progress SET last_cooldown_tip = ? WHERE user_id = ?",
            (datetime.utcnow(), user_id)
        )
        
        return tip
    
    async def generate_trade_analysis(self, trade_data: Dict[str, Any]) -> TradeAnalysis:
        """Generate comprehensive post-trade analysis"""
        # Calculate basic metrics
        entry_price = trade_data['entry_price']
        exit_price = trade_data['exit_price']
        position_size = trade_data['position_size']
        direction = trade_data['direction']
        
        if direction == 'long':
            pnl = (exit_price - entry_price) * position_size
            pnl_percentage = ((exit_price - entry_price) / entry_price) * 100
        else:
            pnl = (entry_price - exit_price) * position_size
            pnl_percentage = ((entry_price - exit_price) / entry_price) * 100
        
        # Analyze trade quality
        strengths = []
        weaknesses = []
        lessons = []
        suggestions = []
        
        # Risk management analysis
        if 'stop_loss' in trade_data and trade_data['stop_loss']:
            strengths.append("Used stop loss for risk management")
            risk_reward = abs((trade_data.get('take_profit', exit_price) - entry_price) / 
                            (entry_price - trade_data['stop_loss']))
            if risk_reward >= 2:
                strengths.append(f"Good risk/reward ratio: {risk_reward:.2f}:1")
            else:
                weaknesses.append(f"Poor risk/reward ratio: {risk_reward:.2f}:1")
                suggestions.append("Aim for at least 2:1 risk/reward ratio")
        else:
            weaknesses.append("No stop loss used - dangerous!")
            suggestions.append("Always use a stop loss to protect capital")
        
        # Timing analysis
        duration = trade_data.get('duration', timedelta(hours=1))
        if duration < timedelta(minutes=5):
            weaknesses.append("Very short trade duration - possible FOMO entry")
            suggestions.append("Ensure proper analysis before entering trades")
        elif duration > timedelta(days=3):
            if pnl > 0:
                strengths.append("Patient holding for profit")
            else:
                weaknesses.append("Held losing position too long")
                suggestions.append("Cut losses quickly, let winners run")
        
        # Profit/Loss analysis
        if pnl > 0:
            strengths.append(f"Profitable trade: +${pnl:.2f} ({pnl_percentage:.2f}%)")
            if pnl_percentage > 5:
                strengths.append("Excellent profit capture")
            lessons.append("Repeat what worked in this trade")
        else:
            weaknesses.append(f"Loss: -${abs(pnl):.2f} ({abs(pnl_percentage):.2f}%)")
            if abs(pnl_percentage) > 2:
                weaknesses.append("Large loss - review risk management")
                suggestions.append("Tighten stop losses to limit downside")
            lessons.append("Analyze what went wrong to avoid repetition")
        
        # Market conditions
        market_conditions = trade_data.get('market_conditions', {})
        if market_conditions.get('trend') == 'bullish' and direction == 'long':
            strengths.append("Traded with the trend")
        elif market_conditions.get('trend') == 'bearish' and direction == 'short':
            strengths.append("Traded with the trend")
        else:
            weaknesses.append("Traded against the trend")
            suggestions.append("Follow the trend for higher probability trades")
        
        # Grade calculation
        score = 0
        score += len(strengths) * 20
        score -= len(weaknesses) * 15
        score += 50 if pnl > 0 else 0
        
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        # Additional lessons based on grade
        if grade in ['D', 'F']:
            lessons.append("Consider paper trading until consistency improves")
            lessons.append("Review basic trading principles and risk management")
        elif grade in ['A', 'B']:
            lessons.append("Excellent execution - maintain this discipline")
            lessons.append("Consider gradually increasing position size")
        
        analysis = TradeAnalysis(
            trade_id=trade_data['trade_id'],
            symbol=trade_data['symbol'],
            entry_price=entry_price,
            exit_price=exit_price,
            pnl=pnl,
            pnl_percentage=pnl_percentage,
            duration=duration,
            strategy_used=trade_data.get('strategy', 'Unknown'),
            market_conditions=market_conditions,
            strengths=strengths,
            weaknesses=weaknesses,
            lessons=lessons,
            improvement_suggestions=suggestions,
            grade=grade
        )
        
        # Store analysis in database
        await self._store_trade_analysis(trade_data['user_id'], analysis)
        
        return analysis
    
    async def _store_trade_analysis(self, user_id: str, analysis: TradeAnalysis):
        """Store trade analysis in database"""
        try:
            analysis_data = {
                'symbol': analysis.symbol,
                'entry_price': analysis.entry_price,
                'exit_price': analysis.exit_price,
                'pnl': analysis.pnl,
                'pnl_percentage': analysis.pnl_percentage,
                'duration': analysis.duration.total_seconds(),
                'strategy_used': analysis.strategy_used,
                'market_conditions': analysis.market_conditions,
                'strengths': analysis.strengths,
                'weaknesses': analysis.weaknesses,
                'lessons': analysis.lessons,
                'improvement_suggestions': analysis.improvement_suggestions,
                'grade': analysis.grade,
                'timestamp': analysis.timestamp.isoformat()
            }
            
            await self.db.execute(
                """INSERT INTO trade_analyses 
                   (analysis_id, user_id, trade_id, analysis_data, grade, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (f"analysis_{analysis.trade_id}", user_id, analysis.trade_id,
                 json.dumps(analysis_data), analysis.grade, datetime.utcnow())
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store trade analysis: {e}")
    
    async def get_strategy_videos(self, user_id: str) -> List[Dict[str, str]]:
        """Get strategy videos appropriate for user's tier"""
        tier = await self.get_user_tier(user_id)
        videos = self.strategy_videos.get(tier, [])
        
        # Also include some videos from the previous tier for review
        if tier != TradingTier.NIBBLER:
            prev_tier = TradingTier(list(TradingTier).index(tier) - 1)
            videos.extend(self.strategy_videos.get(prev_tier, [])[:1])
        
        return videos
    
    async def get_user_tier(self, user_id: str) -> TradingTier:
        """Get user's current trading tier"""
        result = await self.db.fetch_one(
            "SELECT tier FROM user_education_progress WHERE user_id = ?",
            (user_id,)
        )
        
        if result:
            return TradingTier(result['tier'])
        
        # Create new user profile
        await self.db.execute(
            """INSERT INTO user_education_progress (user_id, tier) 
               VALUES (?, ?)""",
            (user_id, TradingTier.NIBBLER.value)
        )
        
        return TradingTier.NIBBLER
    
    async def update_user_progress(self, user_id: str, trade_result: Dict[str, Any]):
        """Update user's education progress based on trade results"""
        try:
            # Fetch current progress
            progress = await self.db.fetch_one(
                """SELECT total_trades, successful_trades, total_pnl, tier 
                   FROM user_education_progress WHERE user_id = ?""",
                (user_id,)
            )
            
            if not progress:
                return
            
            # Update metrics
            total_trades = progress['total_trades'] + 1
            successful_trades = progress['successful_trades'] + (1 if trade_result['pnl'] > 0 else 0)
            total_pnl = progress['total_pnl'] + trade_result['pnl']
            win_rate = successful_trades / total_trades if total_trades > 0 else 0
            
            # Check for tier promotion
            current_tier = TradingTier(progress['tier'])
            new_tier = await self._check_tier_promotion(
                current_tier, total_trades, win_rate, total_pnl
            )
            
            # Update database
            await self.db.execute(
                """UPDATE user_education_progress 
                   SET total_trades = ?, successful_trades = ?, total_pnl = ?, 
                       tier = ?, updated_at = ?
                   WHERE user_id = ?""",
                (total_trades, successful_trades, total_pnl, new_tier.value,
                 datetime.utcnow(), user_id)
            )
            
            # Notify if promoted
            if new_tier != current_tier:
                await self._notify_tier_promotion(user_id, current_tier, new_tier)
                
        except Exception as e:
            self.logger.error(f"Failed to update user progress: {e}")
    
    async def _check_tier_promotion(self, current_tier: TradingTier, 
                                   total_trades: int, win_rate: float, 
                                   total_pnl: float) -> TradingTier:
        """Check if user qualifies for tier promotion"""
        promotion_criteria = {
            TradingTier.NIBBLER: {
                'min_trades': 10,
                'min_win_rate': 0.4,
                'min_pnl': 0  # Just need to be break-even
            },
            TradingTier.APPRENTICE: {
                'min_trades': 50,
                'min_win_rate': 0.45,
                'min_pnl': 100
            },
            TradingTier.JOURNEYMAN: {
                'min_trades': 200,
                'min_win_rate': 0.5,
                'min_pnl': 1000
            },
            TradingTier.MASTER: {
                'min_trades': 500,
                'min_win_rate': 0.55,
                'min_pnl': 5000
            }
        }
        
        criteria = promotion_criteria.get(current_tier)
        if not criteria:
            return current_tier
        
        if (total_trades >= criteria['min_trades'] and
            win_rate >= criteria['min_win_rate'] and
            total_pnl >= criteria['min_pnl']):
            
            # Promote to next tier
            tier_list = list(TradingTier)
            current_index = tier_list.index(current_tier)
            if current_index < len(tier_list) - 1:
                return tier_list[current_index + 1]
        
        return current_tier
    
    async def _notify_tier_promotion(self, user_id: str, old_tier: TradingTier, 
                                   new_tier: TradingTier):
        """Notify user of tier promotion"""
        message = f"""🎉 **TIER PROMOTION!** 🎉

Congratulations! You've been promoted from **{old_tier.value.title()}** to **{new_tier.value.title()}**!

**New Benefits Unlocked:**
• Access to {new_tier.value} strategy videos
• Advanced educational content
• Increased trading limits
• New paper trading strategies

Keep up the excellent work! 🚀"""
        
        # Send notification (implement based on your notification system)
        await send_discord_message(user_id, message)
    
    # Paper Trading Methods
    
    async def create_paper_trade(self, user_id: str, trade_params: Dict[str, Any]) -> PaperTrade:
        """Create a new paper trade"""
        trade = PaperTrade(
            trade_id=f"paper_{user_id}_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            symbol=trade_params['symbol'],
            entry_price=trade_params['entry_price'],
            position_size=trade_params['position_size'],
            direction=trade_params['direction'],
            stop_loss=trade_params.get('stop_loss'),
            take_profit=trade_params.get('take_profit'),
            strategy=trade_params.get('strategy'),
            entry_reason=trade_params.get('entry_reason')
        )
        
        # Store in memory and database
        self.paper_trades[user_id].append(trade)
        
        await self.db.execute(
            """INSERT INTO paper_trades (trade_id, user_id, trade_data, status)
               VALUES (?, ?, ?, ?)""",
            (trade.trade_id, user_id, json.dumps(trade.__dict__, default=str), 'open')
        )
        
        return trade
    
    async def close_paper_trade(self, user_id: str, trade_id: str, 
                               exit_price: float) -> Optional[TradeAnalysis]:
        """Close a paper trade and generate analysis"""
        # Find the trade
        user_trades = self.paper_trades.get(user_id, [])
        trade = next((t for t in user_trades if t.trade_id == trade_id), None)
        
        if not trade or trade.status != 'open':
            return None
        
        # Calculate P&L
        if trade.direction == 'long':
            pnl = (exit_price - trade.entry_price) * trade.position_size
            pnl_percentage = ((exit_price - trade.entry_price) / trade.entry_price) * 100
        else:
            pnl = (trade.entry_price - exit_price) * trade.position_size
            pnl_percentage = ((trade.entry_price - exit_price) / trade.entry_price) * 100
        
        # Update trade
        trade.exit_price = exit_price
        trade.exit_timestamp = datetime.utcnow()
        trade.pnl = pnl
        trade.pnl_percentage = pnl_percentage
        trade.status = 'closed'
        
        # Update database
        await self.db.execute(
            """UPDATE paper_trades 
               SET trade_data = ?, status = ?, closed_at = ?
               WHERE trade_id = ?""",
            (json.dumps(trade.__dict__, default=str), 'closed', 
             datetime.utcnow(), trade_id)
        )
        
        # Generate analysis
        trade_data = {
            'trade_id': trade.trade_id,
            'user_id': user_id,
            'symbol': trade.symbol,
            'entry_price': trade.entry_price,
            'exit_price': exit_price,
            'position_size': trade.position_size,
            'direction': trade.direction,
            'duration': trade.exit_timestamp - trade.timestamp,
            'strategy': trade.strategy
        }
        
        analysis = await self.generate_trade_analysis(trade_data)
        return analysis
    
    async def get_paper_trading_stats(self, user_id: str) -> Dict[str, Any]:
        """Get paper trading statistics for user"""
        trades = await self.db.fetch_all(
            """SELECT trade_data FROM paper_trades 
               WHERE user_id = ? AND status = 'closed'""",
            (user_id,)
        )
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'average_win': 0,
                'average_loss': 0,
                'profit_factor': 0
            }
        
        # Parse trades and calculate stats
        parsed_trades = [json.loads(t['trade_data']) for t in trades]
        winning_trades = [t for t in parsed_trades if t['pnl'] > 0]
        losing_trades = [t for t in parsed_trades if t['pnl'] < 0]
        
        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))
        
        return {
            'total_trades': len(parsed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(parsed_trades) if parsed_trades else 0,
            'total_pnl': sum(t['pnl'] for t in parsed_trades),
            'average_win': total_wins / len(winning_trades) if winning_trades else 0,
            'average_loss': total_losses / len(losing_trades) if losing_trades else 0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else float('inf')
        }
    
    # Weekly Review System
    
    async def generate_weekly_review(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive weekly review for user"""
        week_start = datetime.utcnow() - timedelta(days=7)
        
        # Fetch week's trades
        real_trades = await self.db.fetch_all(
            """SELECT * FROM trades 
               WHERE user_id = ? AND timestamp >= ?""",
            (user_id, week_start)
        )
        
        paper_trades = await self.db.fetch_all(
            """SELECT trade_data FROM paper_trades 
               WHERE user_id = ? AND created_at >= ?""",
            (user_id, week_start)
        )
        
        # Fetch trade analyses
        analyses = await self.db.fetch_all(
            """SELECT analysis_data, grade FROM trade_analyses 
               WHERE user_id = ? AND created_at >= ?""",
            (user_id, week_start)
        )
        
        # Calculate metrics
        total_real_trades = len(real_trades)
        total_paper_trades = len(paper_trades)
        
        # Grade distribution
        grade_distribution = defaultdict(int)
        for analysis in analyses:
            grade_distribution[analysis['grade']] += 1
        
        # Calculate real trading P&L
        real_pnl = sum(t['pnl'] for t in real_trades) if real_trades else 0
        real_win_rate = (len([t for t in real_trades if t['pnl'] > 0]) / 
                        len(real_trades) if real_trades else 0)
        
        # Get most common mistakes
        all_weaknesses = []
        for analysis in analyses:
            data = json.loads(analysis['analysis_data'])
            all_weaknesses.extend(data.get('weaknesses', []))
        
        weakness_counts = defaultdict(int)
        for weakness in all_weaknesses:
            weakness_counts[weakness] += 1
        
        top_weaknesses = sorted(weakness_counts.items(), 
                               key=lambda x: x[1], reverse=True)[:3]
        
        # Get best trades
        best_trades = sorted(real_trades, key=lambda x: x['pnl'], reverse=True)[:3]
        worst_trades = sorted(real_trades, key=lambda x: x['pnl'])[:3]
        
        # Educational recommendations
        recommendations = await self._get_weekly_recommendations(
            user_id, grade_distribution, weakness_counts
        )
        
        review = {
            'week_start': week_start,
            'week_end': datetime.utcnow(),
            'total_real_trades': total_real_trades,
            'total_paper_trades': total_paper_trades,
            'real_pnl': real_pnl,
            'real_win_rate': real_win_rate,
            'grade_distribution': dict(grade_distribution),
            'top_weaknesses': top_weaknesses,
            'best_trades': best_trades,
            'worst_trades': worst_trades,
            'recommendations': recommendations,
            'next_week_goals': await self._generate_weekly_goals(user_id, review)
        }
        
        # Store review
        await self.db.execute(
            """INSERT INTO weekly_reviews (review_id, user_id, week_start, review_data)
               VALUES (?, ?, ?, ?)""",
            (f"review_{user_id}_{week_start.timestamp()}", user_id, 
             week_start, json.dumps(review, default=str))
        )
        
        return review
    
    async def _get_weekly_recommendations(self, user_id: str, 
                                        grade_distribution: Dict[str, int],
                                        weakness_counts: Dict[str, int]) -> List[str]:
        """Generate educational recommendations based on performance"""
        recommendations = []
        
        # Based on grades
        total_trades = sum(grade_distribution.values())
        if total_trades > 0:
            poor_trades = grade_distribution.get('D', 0) + grade_distribution.get('F', 0)
            if poor_trades / total_trades > 0.3:
                recommendations.append(
                    "Focus on trade quality: Review entry criteria and ensure A+ setups only"
                )
        
        # Based on weaknesses
        if weakness_counts:
            top_weakness = max(weakness_counts.items(), key=lambda x: x[1])[0]
            if "stop loss" in top_weakness.lower():
                recommendations.append(
                    "Risk Management Focus: Practice proper stop loss placement"
                )
            elif "risk/reward" in top_weakness.lower():
                recommendations.append(
                    "Improve Risk/Reward: Aim for minimum 2:1 on all trades"
                )
        
        # Get tier-specific recommendations
        tier = await self.get_user_tier(user_id)
        if tier == TradingTier.NIBBLER:
            recommendations.append(
                "Continue paper trading to build confidence and skills"
            )
        elif tier == TradingTier.APPRENTICE:
            recommendations.append(
                "Start incorporating multi-timeframe analysis"
            )
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    async def _generate_weekly_goals(self, user_id: str, 
                                   current_review: Dict[str, Any]) -> List[str]:
        """Generate goals for the next week"""
        goals = []
        
        # Based on performance
        if current_review['real_win_rate'] < 0.5:
            goals.append("Achieve 50%+ win rate through better trade selection")
        
        if current_review['real_pnl'] < 0:
            goals.append("Focus on capital preservation - aim for break-even")
        
        # Based on activity
        if current_review['total_real_trades'] > 20:
            goals.append("Reduce trading frequency - quality over quantity")
        elif current_review['total_real_trades'] < 5:
            goals.append("Increase market participation with proper setups")
        
        # Educational goals
        goals.append("Complete at least 3 educational videos from your tier")
        goals.append("Maintain detailed trade journal with entry reasons")
        
        return goals[:4]  # Limit to 4 goals
    
    # Integration with Trade Execution
    
    async def pre_trade_check(self, user_id: str, trade_params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform educational checks before trade execution"""
        results = {
            'approved': True,
            'warnings': [],
            'educational_tips': [],
            'paper_trade_suggestion': False
        }
        
        # Check cooldown for NIBBLERs
        in_cooldown, cooldown_message = await self.check_nibbler_cooldown(user_id)
        if in_cooldown:
            results['approved'] = False
            results['warnings'].append(cooldown_message)
            results['paper_trade_suggestion'] = True
            return results
        
        # Check risk management
        account_balance = trade_params.get('account_balance', 10000)
        position_value = (trade_params['entry_price'] * 
                         trade_params['position_size'])
        risk_percentage = (position_value / account_balance) * 100
        
        if risk_percentage > 5:
            results['warnings'].append(
                f"High risk warning: {risk_percentage:.1f}% of account at risk"
            )
            results['educational_tips'].append(
                "Consider reducing position size to stay within 1-2% risk"
            )
        
        # Check if user has stop loss
        if not trade_params.get('stop_loss'):
            results['warnings'].append("No stop loss set - high risk!")
            results['educational_tips'].append(
                "Always use a stop loss to protect your capital"
            )
        
        # Check recent performance
        recent_trades = await self.db.fetch_all(
            """SELECT pnl FROM trades 
               WHERE user_id = ? 
               ORDER BY timestamp DESC 
               LIMIT 5""",
            (user_id,)
        )
        
        if recent_trades:
            recent_losses = sum(1 for t in recent_trades if t['pnl'] < 0)
            if recent_losses >= 3:
                results['warnings'].append("3+ recent losses - consider a break")
                results['paper_trade_suggestion'] = True
                results['educational_tips'].append(
                    "After multiple losses, paper trade to regain confidence"
                )
        
        return results
    
    async def post_trade_education(self, user_id: str, trade_result: Dict[str, Any]):
        """Provide educational content after trade completion"""
        # Update cooldown for NIBBLERs
        tier = await self.get_user_tier(user_id)
        if tier == TradingTier.NIBBLER:
            self.cooldown_tracker[user_id] = datetime.utcnow()
        
        # Generate trade analysis
        analysis = await self.generate_trade_analysis(trade_result)
        
        # Update user progress
        await self.update_user_progress(user_id, trade_result)
        
        # Prepare educational message
        message = f"""📊 **Trade Analysis Complete**

**Grade:** {analysis.grade}
**P&L:** ${analysis.pnl:.2f} ({analysis.pnl_percentage:.2f}%)

**Strengths:**
{chr(10).join(f'✅ {s}' for s in analysis.strengths[:3])}

**Areas for Improvement:**
{chr(10).join(f'⚠️ {w}' for w in analysis.weaknesses[:3])}

**Key Lessons:**
{chr(10).join(f'📖 {l}' for l in analysis.lessons[:2])}

**Next Steps:**
{chr(10).join(f'➡️ {s}' for s in analysis.improvement_suggestions[:2])}"""
        
        # Add tier-specific content
        if tier == TradingTier.NIBBLER:
            message += "\n\n🚦 **30-minute cooldown activated** - Use this time to review and learn!"
        
        # Get relevant educational content
        relevant_content = await self._get_relevant_content(analysis)
        if relevant_content:
            message += f"\n\n📚 **Recommended Learning:**\n{relevant_content}"
        
        return message
    
    async def _get_relevant_content(self, analysis: TradeAnalysis) -> Optional[str]:
        """Get educational content relevant to trade analysis"""
        content_suggestions = []
        
        # Based on weaknesses
        for weakness in analysis.weaknesses:
            if "stop loss" in weakness.lower():
                content_suggestions.append(
                    "Watch: 'Stop Loss Strategies' - https://youtube.com/watch?v=stop_loss_guide"
                )
            elif "risk/reward" in weakness.lower():
                content_suggestions.append(
                    "Read: 'Mastering Risk/Reward Ratios' in the education center"
                )
            elif "trend" in weakness.lower():
                content_suggestions.append(
                    "Study: 'Trend Identification Techniques' video series"
                )
        
        return "\n".join(content_suggestions[:2]) if content_suggestions else None
    
    async def get_education_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive education dashboard for user"""
        tier = await self.get_user_tier(user_id)
        progress = await self.db.fetch_one(
            """SELECT * FROM user_education_progress WHERE user_id = ?""",
            (user_id,)
        )
        
        paper_stats = await self.get_paper_trading_stats(user_id)
        recent_analyses = await self.db.fetch_all(
            """SELECT grade, created_at FROM trade_analyses 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT 10""",
            (user_id,)
        )
        
        # Calculate grade trend
        grade_trend = "improving" if recent_analyses else "no data"
        if len(recent_analyses) >= 5:
            recent_grades = [ord(a['grade']) for a in recent_analyses[:5]]
            older_grades = [ord(a['grade']) for a in recent_analyses[5:]]
            if recent_grades and older_grades:
                if sum(recent_grades) / len(recent_grades) < sum(older_grades) / len(older_grades):
                    grade_trend = "improving"
                else:
                    grade_trend = "declining"
        
        return {
            'user_id': user_id,
            'current_tier': tier.value,
            'total_trades': progress['total_trades'] if progress else 0,
            'win_rate': (progress['successful_trades'] / progress['total_trades'] 
                        if progress and progress['total_trades'] > 0 else 0),
            'total_pnl': progress['total_pnl'] if progress else 0,
            'paper_trading_stats': paper_stats,
            'grade_trend': grade_trend,
            'recent_grades': [a['grade'] for a in recent_analyses],
            'next_tier_requirements': await self._get_next_tier_requirements(tier),
            'recommended_videos': await self.get_strategy_videos(user_id),
            'cooldown_active': user_id in self.cooldown_tracker and 
                             (datetime.utcnow() - self.cooldown_tracker[user_id]) < self.cooldown_duration
        }
    
    async def _get_next_tier_requirements(self, current_tier: TradingTier) -> Dict[str, Any]:
        """Get requirements for next tier promotion"""
        tier_requirements = {
            TradingTier.NIBBLER: {
                'next_tier': 'Apprentice',
                'trades_needed': 10,
                'win_rate_needed': 0.4,
                'pnl_needed': 0
            },
            TradingTier.APPRENTICE: {
                'next_tier': 'Journeyman',
                'trades_needed': 50,
                'win_rate_needed': 0.45,
                'pnl_needed': 100
            },
            TradingTier.JOURNEYMAN: {
                'next_tier': 'Master',
                'trades_needed': 200,
                'win_rate_needed': 0.5,
                'pnl_needed': 1000
            },
            TradingTier.MASTER: {
                'next_tier': 'Grandmaster',
                'trades_needed': 500,
                'win_rate_needed': 0.55,
                'pnl_needed': 5000
            },
            TradingTier.GRANDMASTER: {
                'next_tier': 'Maximum Level',
                'trades_needed': 0,
                'win_rate_needed': 0,
                'pnl_needed': 0
            }
        }
        
        return tier_requirements.get(current_tier, {})