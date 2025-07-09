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


class PersonaType(Enum):
    """Core education personas"""
    NEXUS = "nexus"  # Strategic commander
    DRILL = "drill"  # Tough love trainer
    AEGIS = "aegis"  # Protective mentor


class TradingTier(Enum):
    """Trading experience tiers - Military ranks in the trading academy"""
    NIBBLER = "nibbler"  # Recruit
    APPRENTICE = "apprentice"  # Private
    JOURNEYMAN = "journeyman"  # Sergeant
    MASTER = "master"  # Lieutenant
    GRANDMASTER = "grandmaster"  # Commander


class MissionStatus(Enum):
    """Mission (trade) status types"""
    BRIEFING = "briefing"  # Pre-trade
    ACTIVE = "active"  # In position
    EXTRACTION = "extraction"  # Closing trade
    DEBRIEF = "debrief"  # Post-trade analysis
    COOLDOWN = "cooldown"  # Tactical recovery


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


class EducationPersonas:
    """Core personas that guide traders through their journey"""
    
    def __init__(self):
        self.bit_emotions = {
            'happy': '*chirps excitedly*',
            'proud': '*purrs contentedly*',
            'worried': '*concerned warble*',
            'encouraging': '*supportive trill*',
            'alert': '*sharp chirp*',
            'celebrating': '*victory screech*',
            'comforting': '*soft purr*'
        }
    
    def get_persona_response(self, persona: PersonaType, context: Dict[str, Any]) -> str:
        """Get response from specific persona based on context"""
        if persona == PersonaType.NEXUS:
            return self._nexus_response(context)
        elif persona == PersonaType.DRILL:
            return self._drill_response(context)
        elif persona == PersonaType.AEGIS:
            return self._aegis_response(context)
    
    def _nexus_response(self, context: Dict[str, Any]) -> str:
        """Sergeant Nexus - Strategic commander voice"""
        situation = context.get('situation', 'general')
        performance = context.get('performance', 'neutral')
        
        responses = {
            'pre_trade': {
                'good': "Excellent reconnaissance, soldier. The battlefield is mapped, objectives are clear. This is a textbook setup - execute with precision.",
                'risky': "Hold position. I'm seeing multiple threat vectors on the tactical display. Reassess your entry point and confirm your extraction plan.",
                'neutral': "Mission parameters received. Remember: every trade is a tactical operation. Confirm your stop-loss coordinates and proceed when ready."
            },
            'post_trade': {
                'win': "Outstanding execution! That's how we dominate the battlefield. Your tactical assessment was flawless. Log this victory and prepare for the next mission.",
                'loss': "Tactical retreat executed successfully. You preserved capital - that's a strategic win. Every great commander knows when to fall back and regroup.",
                'breakeven': "Clean extraction, minimal exposure. Sometimes the best trade is the one that doesn't hurt you. Ready for the next engagement."
            },
            'cooldown': {
                'forced': "Stand down, soldier. Mandatory R&R in effect. Use this time to review battlefield intelligence and sharpen your strategies. The market isn't going anywhere.",
                'voluntary': "Smart call taking a tactical pause. The best operators know when to observe rather than engage. Study the terrain while others rush in."
            },
            'education': {
                'lesson': "Intelligence briefing incoming. This knowledge could save your portfolio. Pay attention - I don't repeat myself.",
                'achievement': "Promotion earned through battlefield excellence! You've proven yourself worthy of advanced tactical knowledge. New strategies unlocked."
            }
        }
        
        response_type = responses.get(situation, responses['pre_trade'])
        base_response = response_type.get(performance, response_type.get('neutral', ''))
        
        # Add Bit's emotion
        bit_emotion = self._get_bit_emotion(situation, performance)
        
        return f"**[SERGEANT NEXUS]** {base_response}\n\n{bit_emotion}"
    
    def _drill_response(self, context: Dict[str, Any]) -> str:
        """Drill - Tough love trainer voice"""
        situation = context.get('situation', 'general')
        performance = context.get('performance', 'neutral')
        user_tier = context.get('tier', TradingTier.NIBBLER)
        
        responses = {
            'pre_trade': {
                'good': "Now THAT'S what I'm talking about! Clean setup, solid risk management. Make me proud out there!",
                'risky': "What the hell is this, recruit?! That position size could blow up your whole account! Get your head in the game!",
                'neutral': "Alright, I see what you're doing. Not terrible, but not great either. Tighten up that stop loss and show me what you've got!"
            },
            'post_trade': {
                'win': "BOOM! That's my trader! You just showed those bears who's boss! But don't get cocky - stay hungry, stay disciplined!",
                'loss': "You call that trading?! At least you used a stop loss... barely acceptable. Drop and give me 20 pushups worth of market analysis!",
                'breakeven': "Survived to fight another day. That's something, I guess. Next time, I want to see some CONVICTION in your trades!"
            },
            'cooldown': {
                'forced': "TIMEOUT! You're benched, hot shot! Too much adrenaline, not enough thinking. Hit the books before you hit the buy button again!",
                'voluntary': "Good! Finally showing some discipline! Use this time to study, not to sulk. Champions are made in the gym, not the ring!"
            },
            'nibbler_specific': {
                'encouragement': "Listen up, Nibbler! You're green, but you've got potential. Follow my lead and you'll be eating steaks instead of ramen!",
                'correction': "WRONG! But that's why you're here to learn. Every master was once a disaster. Now pay attention!"
            }
        }
        
        response_type = responses.get(situation, responses['pre_trade'])
        base_response = response_type.get(performance, response_type.get('neutral', ''))
        
        # Add tier-specific tough love
        if user_tier == TradingTier.NIBBLER and random.random() < 0.3:
            nibbler_addon = responses['nibbler_specific']['encouragement'] if performance in ['good', 'win'] else responses['nibbler_specific']['correction']
            base_response = f"{base_response}\n\n{nibbler_addon}"
        
        # Add Bit's emotion
        bit_emotion = self._get_bit_emotion(situation, performance)
        
        return f"**[DRILL]** {base_response}\n\n{bit_emotion}"
    
    def _aegis_response(self, context: Dict[str, Any]) -> str:
        """Captain Aegis - Protective mentor voice"""
        situation = context.get('situation', 'general')
        performance = context.get('performance', 'neutral')
        consecutive_losses = context.get('consecutive_losses', 0)
        
        responses = {
            'pre_trade': {
                'good': "I've reviewed your analysis - this shows real growth. Your risk parameters are well-defined. I'm here if you need me. You've got this.",
                'risky': "Hold on, let's talk about this. I see some red flags in your setup. Would you consider reducing position size? Your account's safety is my priority.",
                'neutral': "I'm monitoring your trade setup. Remember, there's no shame in passing on uncertain opportunities. Quality over quantity, always."
            },
            'post_trade': {
                'win': "Beautifully executed! You stayed true to your plan and it paid off. I'm genuinely proud of your discipline. Let's build on this momentum carefully.",
                'loss': "I know losses hurt, but you handled this professionally. Your stop loss protected you from worse. Every loss is tuition in the market's university.",
                'breakeven': "Perfect capital preservation. Not every trade needs to be a home run. You showed maturity here - that's the mark of a sustainable trader."
            },
            'cooldown': {
                'forced': "This cooldown isn't punishment - it's protection. Your mind needs rest to process what happened. I'll be here when you're ready to discuss.",
                'voluntary': "Wise decision to step back. Self-awareness is a superpower in trading. Let's use this time to strengthen your foundation."
            },
            'support': {
                'struggling': "I see you're going through a rough patch. This happens to everyone - even the legends had losing streaks. Your resilience will define your success.",
                'improving': "Your progress is remarkable. The dedication you're showing will compound over time. Keep this steady pace - no need to rush.",
                'consistent': "Your consistency is admirable. This is how fortunes are built - one careful trade at a time. I'm honored to guide your journey."
            }
        }
        
        response_type = responses.get(situation, responses['pre_trade'])
        base_response = response_type.get(performance, response_type.get('neutral', ''))
        
        # Add extra support for struggling traders
        if consecutive_losses >= 3:
            base_response += f"\n\n{responses['support']['struggling']}"
        elif performance == 'win' and context.get('win_streak', 0) >= 3:
            base_response += f"\n\n{responses['support']['consistent']}"
        
        # Add Bit's emotion
        bit_emotion = self._get_bit_emotion(situation, performance)
        
        return f"**[CAPTAIN AEGIS]** {base_response}\n\n{bit_emotion}"
    
    def _get_bit_emotion(self, situation: str, performance: str) -> str:
        """Get Bit's emotional response based on context"""
        emotion_map = {
            ('pre_trade', 'good'): 'encouraging',
            ('pre_trade', 'risky'): 'worried',
            ('post_trade', 'win'): 'celebrating',
            ('post_trade', 'loss'): 'comforting',
            ('cooldown', 'forced'): 'alert',
            ('cooldown', 'voluntary'): 'proud',
            ('education', 'achievement'): 'celebrating'
        }
        
        emotion_key = emotion_map.get((situation, performance), 'happy')
        return f"Bit: {self.bit_emotions.get(emotion_key, '*chirps*')}"
    
    def select_persona(self, context: Dict[str, Any]) -> PersonaType:
        """Dynamically select the best persona for the situation"""
        situation = context.get('situation', 'general')
        user_tier = context.get('tier', TradingTier.NIBBLER)
        consecutive_losses = context.get('consecutive_losses', 0)
        need_tough_love = context.get('need_tough_love', False)
        
        # Aegis for traders who are struggling
        if consecutive_losses >= 3 or context.get('major_loss', False):
            return PersonaType.AEGIS
        
        # Drill for motivation and discipline issues
        if need_tough_love or context.get('revenge_trading', False):
            return PersonaType.DRILL
        
        # Nexus for strategic discussions and analysis
        if situation in ['pre_trade', 'education'] and user_tier.value in ['journeyman', 'master', 'grandmaster']:
            return PersonaType.NEXUS
        
        # Default based on tier
        if user_tier == TradingTier.NIBBLER:
            # Mix of Drill (40%), Aegis (40%), Nexus (20%)
            rand = random.random()
            if rand < 0.4:
                return PersonaType.DRILL
            elif rand < 0.8:
                return PersonaType.AEGIS
            else:
                return PersonaType.NEXUS
        else:
            # More balanced for experienced traders
            return random.choice(list(PersonaType))
    
    def get_mission_briefing(self, trade_params: Dict[str, Any], user_tier: TradingTier) -> str:
        """Generate mission-style briefing for trades"""
        symbol = trade_params.get('symbol', 'UNKNOWN')
        direction = trade_params.get('direction', 'long')
        risk_reward = trade_params.get('risk_reward_ratio', 1.0)
        
        briefing = f"""🎯 **MISSION BRIEFING: OPERATION {symbol.upper()}**
═══════════════════════════════════════

**OBJECTIVE:** {direction.upper()} position on {symbol}
**RISK LEVEL:** {'🟢 LOW' if risk_reward >= 3 else '🟡 MEDIUM' if risk_reward >= 2 else '🔴 HIGH'}
**INTEL CONFIDENCE:** {trade_params.get('confidence', 'MODERATE')}

**MISSION PARAMETERS:**
• Entry Point: ${trade_params.get('entry_price', 0):.2f}
• Stop Loss: ${trade_params.get('stop_loss', 0):.2f} (Abort mission threshold)
• Target: ${trade_params.get('take_profit', 0):.2f} (Mission success)
• Risk/Reward: {risk_reward:.1f}:1

**TACTICAL NOTES:**
{self._get_tactical_notes(trade_params, user_tier)}

**EQUIPMENT CHECK:**
✓ Stop loss armed and ready
✓ Position size calculated
✓ Exit strategy confirmed
{'✓ Nibbler safety protocols active' if user_tier == TradingTier.NIBBLER else '✓ Advanced tactics authorized'}

**COMMS CHANNEL:** HydraX tactical support standing by

*Remember: No trade is worth your account. Protect capital at all costs.*

═══════════════════════════════════════
Ready to deploy? Confirm when prepared for market insertion."""
        
        return briefing
    
    def _get_tactical_notes(self, trade_params: Dict[str, Any], user_tier: TradingTier) -> str:
        """Get tactical notes based on trade setup"""
        notes = []
        
        # Market conditions
        if trade_params.get('trend_alignment', False):
            notes.append("• ✅ Trading with prevailing trend - high probability")
        else:
            notes.append("• ⚠️ Counter-trend position - exercise extreme caution")
        
        # Support/Resistance
        if trade_params.get('near_support', False):
            notes.append("• 🛡️ Strong support nearby - good risk entry")
        if trade_params.get('near_resistance', False):
            notes.append("• 🚧 Resistance overhead - prepare for turbulence")
        
        # Volume
        if trade_params.get('volume_confirmation', False):
            notes.append("• 📊 Volume confirms move - institutional backing likely")
        
        # Tier-specific notes
        if user_tier == TradingTier.NIBBLER:
            notes.append("• 🔰 Nibbler Protocol: 30-min cooldown after mission completion")
        
        return '\n'.join(notes) if notes else "• Standard market conditions - proceed with caution"


class EducationSystem:
    """Main education system manager - HydraX Trading Academy"""
    
    def __init__(self, database: Database, logger: Logger):
        self.db = database
        self.logger = logger
        
        # Initialize personas
        self.personas = EducationPersonas()
        
        # Cooldown tracking for NIBBLERs (Tactical Recovery)
        self.cooldown_tracker: Dict[str, datetime] = {}
        self.cooldown_duration = timedelta(minutes=30)  # 30-minute tactical recovery
        
        # Paper trading positions (Training Simulations)
        self.paper_trades: Dict[str, List[PaperTrade]] = defaultdict(list)
        
        # Educational content library (Intel Database)
        self.content_library = self._initialize_content_library()
        
        # Strategy video links by tier (Tactical Training Videos)
        self.strategy_videos = self._initialize_strategy_videos()
        
        # Weekly review tracking (After Action Reports)
        self.weekly_reviews: Dict[str, datetime] = {}
        
        # Performance tracking for dynamic responses
        self.user_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'consecutive_losses': 0,
            'consecutive_wins': 0,
            'last_trade_result': None,
            'mood': 'neutral',
            'needs_encouragement': False
        })
        
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
        """Initialize tactical training modules (Intel Database)"""
        library = defaultdict(list)
        
        # Risk Management Content - Defensive Tactics Division
        library[EducationTopic.RISK_MANAGEMENT].extend([
            EducationalContent(
                topic=EducationTopic.RISK_MANAGEMENT,
                tier=TradingTier.NIBBLER,
                title="OPERATION: CAPITAL SHIELD - The 1% Protocol",
                content="""🛡️ **MISSION BRIEFING: Protect Your Base**
                
**Tactical Rule #1:** Never expose more than 1% of your arsenal to enemy fire.
                
**Why?** You can survive 100 failed missions and live to fight another day.
                
**Field Example:**
• Base Capital: $10,000
• Maximum Risk per Mission: $100
• This is your survival guarantee, soldier!
                
**Remember:** Dead traders can't trade. Protect capital above all else.""",
                video_link="https://youtube.com/watch?v=risk_basics_101",
                practice_exercise="DRILL: Calculate 1% risk for these accounts: $5K, $25K, $100K"
            ),
            EducationalContent(
                topic=EducationTopic.RISK_MANAGEMENT,
                tier=TradingTier.APPRENTICE,
                title="ADVANCED TACTICS: Position Size Calculator",
                content="""🎯 **MISSION INTEL: Precision Ammunition Control**
                
**The Formula:** Position Size = Risk Amount ÷ (Entry - Stop Loss)
                
**Field Application:**
• Account: $10,000
• Risk (1%): $100
• Entry: $50, Stop: $48
• Position Size: $100 ÷ $2 = 50 shares
                
**Critical:** Calculate BEFORE you pull the trigger. No exceptions!""",
                video_link="https://youtube.com/watch?v=position_sizing_guide"
            )
        ])
        
        # Technical Analysis Content - Reconnaissance Division
        library[EducationTopic.TECHNICAL_ANALYSIS].extend([
            EducationalContent(
                topic=EducationTopic.TECHNICAL_ANALYSIS,
                tier=TradingTier.NIBBLER,
                title="RECON 101: Identifying Enemy Lines",
                content="""🔍 **BATTLEFIELD INTELLIGENCE: Support & Resistance**
                
**Support Lines:** Where allied forces (buyers) defend
• Price bounces here like troops behind fortifications
• Breaking support = Retreat signal!
                
**Resistance Lines:** Where enemy forces (sellers) attack
• Price struggles here like advancing into enemy territory
• Breaking resistance = Victory advance!
                
**Tactical Tip:** These lines are your battle map. Respect them!""",
                video_link="https://youtube.com/watch?v=support_resistance_basics",
                practice_exercise="MISSION: Mark 3 support and 3 resistance levels on SPY"
            )
        ])
        
        # Market Psychology Content - Psychological Warfare Division
        library[EducationTopic.MARKET_PSYCHOLOGY].extend([
            EducationalContent(
                topic=EducationTopic.MARKET_PSYCHOLOGY,
                tier=TradingTier.NIBBLER,
                title="PSYOPS DEFENSE: Defeating FOMO",
                content="""🧠 **ENEMY INTEL: Fear Of Missing Out**
                
**FOMO Symptoms (Red Alert!):**
• Heart racing seeing others' profits
• Finger hovering over BUY button
• Abandoning your battle plan
• Chasing price like a rookie
                
**Defense Protocol:**
1. Remember: The market is an infinite battlefield
2. There's ALWAYS another mission tomorrow
3. Stick to YOUR intel, not others' war stories
4. Better to miss one battle than lose the war
                
**Mantra:** "Discipline over dopamine, soldier!"''',
                practice_exercise="DEBRIEF: Document 3 FOMO moments you resisted this week"
            ),
            EducationalContent(
                topic=EducationTopic.MARKET_PSYCHOLOGY,
                tier=TradingTier.APPRENTICE,
                title="COMBAT PSYCHOLOGY: The Winner's Mindset",
                content="""💪 **ELITE TRAINING: Mental Fortitude**
                
**The Warrior's Code:**
• Losses = Combat experience, not failure
• Every scar teaches survival
• Emotions are the enemy - neutralize them
• Process > Profits
                
**Daily Mental Training:**
1. Morning: Visualize successful trades
2. Pre-market: Review your rules of engagement
3. Post-market: Debrief without judgment
4. Evening: Plan tomorrow's campaign
                
**Remember:** Markets test warriors, not weaklings.""",
                video_link="https://youtube.com/watch?v=trading_psychology_advanced"
            )
        ])
        
        return library
    
    def _initialize_strategy_videos(self) -> Dict[TradingTier, List[Dict[str, str]]]:
        """Initialize tactical training videos by rank"""
        return {
            TradingTier.NIBBLER: [
                {
                    "title": "🎯 OPERATION: TREND HUNTER",
                    "url": "https://youtube.com/watch?v=trend_following_101",
                    "duration": "15 min",
                    "focus": "Basic reconnaissance - Identifying friendly vs hostile trends",
                    "mission": "Complete 5 paper trades following trends"
                },
                {
                    "title": "📊 TACTICAL TOOL: Moving Average Warfare",
                    "url": "https://youtube.com/watch?v=sma_strategy_basics",
                    "duration": "20 min",
                    "focus": "Deploy the 20/50/200 MA trinity for battle entries",
                    "mission": "Identify 3 MA crossover setups"
                },
                {
                    "title": "🛡️ DEFENSIVE MANEUVERS: Stop Loss Mastery",
                    "url": "https://youtube.com/watch?v=stop_loss_bootcamp",
                    "duration": "18 min",
                    "focus": "Where to place your shields for maximum protection",
                    "mission": "Calculate stop losses for 10 hypothetical trades"
                }
            ],
            TradingTier.APPRENTICE: [
                {
                    "title": "💥 OPERATION: BREAKOUT BLITZ",
                    "url": "https://youtube.com/watch?v=breakout_strategies",
                    "duration": "25 min",
                    "focus": "Assault tactics - Breaking enemy resistance with volume",
                    "mission": "Find 3 breakout setups with volume confirmation"
                },
                {
                    "title": "🔄 COUNTER-INTELLIGENCE: RSI Divergence",
                    "url": "https://youtube.com/watch?v=rsi_divergence_guide",
                    "duration": "30 min",
                    "focus": "Detecting enemy weakness before the retreat",
                    "mission": "Spot 5 divergences on different timeframes"
                },
                {
                    "title": "🎪 TRAP DETECTION: False Breakout Defense",
                    "url": "https://youtube.com/watch?v=false_breakout_defense",
                    "duration": "22 min",
                    "focus": "Avoiding enemy ambushes and bull/bear traps",
                    "mission": "Identify 3 false breakouts from this week"
                }
            ],
            TradingTier.JOURNEYMAN: [
                {
                    "title": "🔭 ADVANCED RECON: Multi-Timeframe Mastery",
                    "url": "https://youtube.com/watch?v=mtf_analysis_advanced",
                    "duration": "35 min",
                    "focus": "Satellite, drone, and ground intel combined",
                    "mission": "Execute 1 trade using 3+ timeframe confluence"
                },
                {
                    "title": "🌊 SPECIAL OPS: Order Flow Intelligence",
                    "url": "https://youtube.com/watch?v=order_flow_basics",
                    "duration": "40 min",
                    "focus": "Reading the enemy's actual movements, not just positions",
                    "mission": "Track order flow on 5 major moves"
                },
                {
                    "title": "🚁 AIR SUPPORT: Options for Directional Trades",
                    "url": "https://youtube.com/watch?v=options_for_direction",
                    "duration": "45 min",
                    "focus": "Calling in options strikes for leverage",
                    "mission": "Design 3 options strategies for current setups"
                }
            ],
            TradingTier.MASTER: [
                {
                    "title": "🎖️ COMMAND TACTICS: Portfolio Warfare",
                    "url": "https://youtube.com/watch?v=portfolio_command",
                    "duration": "50 min",
                    "focus": "Managing multiple fronts simultaneously",
                    "mission": "Design sector rotation strategy"
                },
                {
                    "title": "🔮 PREDICTIVE WARFARE: Market Regime Analysis",
                    "url": "https://youtube.com/watch?v=regime_analysis",
                    "duration": "55 min",
                    "focus": "Identifying changing battlefield conditions",
                    "mission": "Backtest regime-based strategies"
                }
            ]
        }
    
    async def check_nibbler_cooldown(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """Check if NIBBLER is in tactical recovery phase"""
        user_tier = await self.get_user_tier(user_id)
        
        if user_tier != TradingTier.NIBBLER:
            return False, None
        
        last_trade = self.cooldown_tracker.get(user_id)
        if not last_trade:
            return False, None
        
        time_since_trade = datetime.utcnow() - last_trade
        if time_since_trade < self.cooldown_duration:
            remaining = self.cooldown_duration - time_since_trade
            minutes_left = int(remaining.total_seconds() / 60)
            
            # Get context for persona selection
            perf = self.user_performance.get(user_id, {})
            context = {
                'situation': 'cooldown',
                'performance': 'forced',
                'tier': user_tier,
                'consecutive_losses': perf.get('consecutive_losses', 0),
                'last_trade_result': perf.get('last_trade_result', 'unknown')
            }
            
            # Get persona response
            persona = self.personas.select_persona(context)
            persona_message = self.personas.get_persona_response(persona, context)
            
            # Get tactical recovery activity
            recovery_activity = await self._get_tactical_recovery_activity(user_id, minutes_left)
            
            message = f"""⏰ **TACTICAL RECOVERY PHASE** ⏰
═══════════════════════════════════════

**Time until combat ready:** {minutes_left} minutes

{persona_message}

{recovery_activity}

**Available during recovery:**
🎯 Paper trading simulations
📚 Strategy intel review
📊 Market reconnaissance
📝 Mission debrief analysis

*Recovery isn't punishment - it's preparation for victory.*"""
            
            return True, message
        
        return False, None
    
    async def _get_tactical_recovery_activity(self, user_id: str, minutes_remaining: int) -> str:
        """Get tactical recovery activity based on performance"""
        perf = self.user_performance.get(user_id, {})
        last_result = perf.get('last_trade_result', 'unknown')
        
        # Mission-style recovery activities
        if last_result == 'loss':
            activities = [
                f"""📋 **RECOVERY MISSION: Post-Combat Analysis**
                
Your last engagement resulted in casualties. Time to review:
1. Entry point tactical error? Check your recon data
2. Stop loss placement optimal? Review defensive positions
3. Market conditions hostile? Assess battlefield intel
                
**Reward:** Understanding = Future victories""",
                
                f"""🎮 **RECOVERY MISSION: Simulation Training**
                
Jump into paper trading simulator:
- Practice the EXACT same setup with zero risk
- Test alternative entry points
- Experiment with tighter stop losses
                
**Objective:** Turn that loss into a learning victory""",
                
                f"""📺 **RECOVERY MISSION: Combat Training Video**
                
Watch: "Recovering from Losses Like a Pro"
Focus areas:
- Psychological reset techniques
- Common revenge trading traps
- Building back confidence
                
**Duration:** Perfect for your {minutes_remaining} minute recovery"""
            ]
        else:  # Win or neutral
            activities = [
                f"""🎯 **RECOVERY MISSION: Victory Consolidation**
                
Excellent work, soldier! Now solidify your gains:
1. Document what worked in your trade journal
2. Screenshot the setup for future reference
3. Plan similar high-probability missions
                
**Remember:** Discipline wins wars, not single battles""",
                
                f"""📊 **RECOVERY MISSION: Market Reconnaissance**
                
Scout for your next opportunity:
- Scan top movers for momentum plays
- Check support/resistance levels
- Monitor volume for institutional activity
                
**Intel gathering time:** {minutes_remaining} minutes""",
                
                f"""🏋️ **RECOVERY MISSION: Skill Enhancement**
                
Quick drill session:
- Calculate position sizes for 3 hypothetical trades
- Identify risk/reward on current market setups
- Practice your pre-trade checklist
                
**Goal:** Sharper skills = Better execution"""
            ]
        
        # Add some variety based on time of day
        activity = random.choice(activities)
        
        # Track recovery mission completion
        await self.db.execute(
            "UPDATE user_education_progress SET last_cooldown_tip = ? WHERE user_id = ?",
            (datetime.utcnow(), user_id)
        )
        
        return activity
    
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
        tier_titles = {
            TradingTier.NIBBLER: "Recruit",
            TradingTier.APPRENTICE: "Private First Class",
            TradingTier.JOURNEYMAN: "Sergeant",
            TradingTier.MASTER: "Lieutenant",
            TradingTier.GRANDMASTER: "Commander"
        }
        
        # Get promotion-specific persona message
        context = {
            'situation': 'education',
            'performance': 'achievement',
            'tier': new_tier
        }
        
        # Always use Nexus for promotions (commanding officer)
        nexus_message = self.personas.get_persona_response(PersonaType.NEXUS, context)
        
        tier_benefits = {
            TradingTier.APPRENTICE: [
                "🔓 Advanced reconnaissance training unlocked",
                "📈 Breakout assault tactics authorized", 
                "⚡ 25% faster cooldown recovery",
                "🎯 Access to Private-level intel"
            ],
            TradingTier.JOURNEYMAN: [
                "🔭 Multi-timeframe surveillance access granted",
                "💰 Increased position size limits",
                "🌊 Order flow intelligence clearance",
                "🎖️ Sergeant's tactical handbook unlocked"
            ],
            TradingTier.MASTER: [
                "🚁 Options air support authorized",
                "📊 Portfolio command center access",
                "🔮 Market regime analysis tools",
                "⭐ Lieutenant's strategic planning suite"
            ],
            TradingTier.GRANDMASTER: [
                "🎪 Full arsenal unlocked",
                "👑 Commander's war room access",
                "🌟 Unlimited tactical resources",
                "🏆 Elite trader status achieved"
            ]
        }
        
        message = f"""🎖️ **BATTLEFIELD PROMOTION** 🎖️
═══════════════════════════════════════

**ATTENTION!** By order of HydraX High Command:

{tier_titles.get(old_tier, old_tier.value)} has been promoted to **{tier_titles.get(new_tier, new_tier.value)}**!

{nexus_message}

🎯 **NEW TACTICAL CAPABILITIES:**
{chr(10).join(tier_benefits.get(new_tier, ['• Advanced training modules', '• New strategy clearance']))}

📜 **YOUR NEW MISSION:**
Master your new rank's tactics and lead by example!

*Salute your achievement, soldier! The battlefield awaits.*

Bit: {self.personas.bit_emotions['celebrating']}"""
        
        # Send notification
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
        """Perform pre-mission checks and generate briefing"""
        results = {
            'approved': True,
            'warnings': [],
            'educational_tips': [],
            'paper_trade_suggestion': False,
            'mission_briefing': None,
            'persona_message': None
        }
        
        # Get user tier and performance
        user_tier = await self.get_user_tier(user_id)
        perf = self.user_performance.get(user_id, {})
        
        # Check cooldown for NIBBLERs
        in_cooldown, cooldown_message = await self.check_nibbler_cooldown(user_id)
        if in_cooldown:
            results['approved'] = False
            results['warnings'].append(cooldown_message)
            results['paper_trade_suggestion'] = True
            return results
        
        # Risk assessment
        account_balance = trade_params.get('account_balance', 10000)
        position_value = (trade_params['entry_price'] * 
                         trade_params['position_size'])
        risk_percentage = (position_value / account_balance) * 100
        
        # Calculate risk/reward
        if trade_params.get('stop_loss') and trade_params.get('take_profit'):
            risk = abs(trade_params['entry_price'] - trade_params['stop_loss'])
            reward = abs(trade_params['take_profit'] - trade_params['entry_price'])
            risk_reward_ratio = reward / risk if risk > 0 else 0
            trade_params['risk_reward_ratio'] = risk_reward_ratio
        
        # Determine trade quality
        trade_quality = 'neutral'
        if risk_percentage > 5:
            trade_quality = 'risky'
            results['warnings'].append("⚠️ **HIGH RISK ALERT**: Position size exceeds safe parameters!")
        elif trade_params.get('risk_reward_ratio', 0) >= 2 and risk_percentage <= 2:
            trade_quality = 'good'
        
        # Check for stop loss
        if not trade_params.get('stop_loss'):
            trade_quality = 'risky'
            results['warnings'].append("🚨 **CRITICAL**: No stop loss detected! Abort mission recommended!")
        
        # Recent performance check
        recent_trades = await self.db.fetch_all(
            """SELECT pnl FROM trades 
               WHERE user_id = ? 
               ORDER BY timestamp DESC 
               LIMIT 5""",
            (user_id,)
        )
        
        consecutive_losses = 0
        if recent_trades:
            for trade in recent_trades:
                if trade['pnl'] < 0:
                    consecutive_losses += 1
                else:
                    break
        
        # Update performance tracking
        self.user_performance[user_id]['consecutive_losses'] = consecutive_losses
        
        # Check for revenge trading patterns
        revenge_trading = consecutive_losses >= 3
        need_tough_love = risk_percentage > 10 or not trade_params.get('stop_loss')
        
        # Generate context for persona
        context = {
            'situation': 'pre_trade',
            'performance': trade_quality,
            'tier': user_tier,
            'consecutive_losses': consecutive_losses,
            'revenge_trading': revenge_trading,
            'need_tough_love': need_tough_love
        }
        
        # Get persona response
        persona = self.personas.select_persona(context)
        persona_message = self.personas.get_persona_response(persona, context)
        results['persona_message'] = persona_message
        
        # Generate mission briefing
        if results['approved']:
            results['mission_briefing'] = self.personas.get_mission_briefing(trade_params, user_tier)
        
        # Additional warnings for struggling traders
        if consecutive_losses >= 3:
            results['warnings'].append("⚠️ **TACTICAL ADVISORY**: Multiple casualties detected. Consider simulation mode.")
            results['paper_trade_suggestion'] = True
        
        return results
    
    async def post_trade_education(self, user_id: str, trade_result: Dict[str, Any]):
        """Mission debrief with personalized education"""
        # Update cooldown for NIBBLERs
        tier = await self.get_user_tier(user_id)
        if tier == TradingTier.NIBBLER:
            self.cooldown_tracker[user_id] = datetime.utcnow()
        
        # Generate trade analysis
        analysis = await self.generate_trade_analysis(trade_result)
        
        # Update performance tracking
        perf = self.user_performance[user_id]
        if trade_result.get('pnl', 0) > 0:
            perf['consecutive_wins'] = perf.get('consecutive_wins', 0) + 1
            perf['consecutive_losses'] = 0
            perf['last_trade_result'] = 'win'
            trade_performance = 'win'
        elif trade_result.get('pnl', 0) < 0:
            perf['consecutive_losses'] = perf.get('consecutive_losses', 0) + 1
            perf['consecutive_wins'] = 0
            perf['last_trade_result'] = 'loss'
            trade_performance = 'loss'
        else:
            perf['last_trade_result'] = 'breakeven'
            trade_performance = 'breakeven'
        
        # Update user progress
        await self.update_user_progress(user_id, trade_result)
        
        # Generate context for persona
        context = {
            'situation': 'post_trade',
            'performance': trade_performance,
            'tier': tier,
            'consecutive_losses': perf.get('consecutive_losses', 0),
            'consecutive_wins': perf.get('consecutive_wins', 0),
            'win_streak': perf.get('consecutive_wins', 0),
            'major_loss': abs(trade_result.get('pnl', 0)) > trade_result.get('account_balance', 10000) * 0.05 if trade_result.get('account_balance') else False
        }
        
        # Get persona response
        persona = self.personas.select_persona(context)
        persona_message = self.personas.get_persona_response(persona, context)
        
        # Create mission debrief
        grade_emoji = {
            'A': '🏆', 'B': '🥈', 'C': '🥉', 
            'D': '⚠️', 'F': '💀'
        }
        
        message = f"""📋 **MISSION DEBRIEF: {trade_result.get('symbol', 'CLASSIFIED')}**
═══════════════════════════════════════

**Mission Grade:** {grade_emoji.get(analysis.grade, '📊')} {analysis.grade}
**Outcome:** ${analysis.pnl:.2f} ({analysis.pnl_percentage:+.2f}%)
**Duration:** {str(analysis.duration).split('.')[0]}

{persona_message}

🎯 **TACTICAL ASSESSMENT**
{self._format_tactical_assessment(analysis)}

📚 **INTEL LEARNED**
{chr(10).join(f'• {l}' for l in analysis.lessons[:3])}

🚀 **NEXT MISSION PREP**
{chr(10).join(f'• {s}' for s in analysis.improvement_suggestions[:3])}"""
        
        # Add cooldown notice for NIBBLERs
        if tier == TradingTier.NIBBLER:
            message += f"""

⏰ **TACTICAL RECOVERY INITIATED**
30-minute recovery phase activated. Use this time wisely!

Bit: {self.personas.bit_emotions.get('alert', '*chirps*')}"""
        
        # Get relevant educational content
        relevant_content = await self._get_mission_specific_training(analysis, tier)
        if relevant_content:
            message += f"\n\n{relevant_content}"
        
        return message
    
    def _format_tactical_assessment(self, analysis: TradeAnalysis) -> str:
        """Format tactical assessment in military style"""
        assessment = []
        
        # Strengths as successful tactics
        if analysis.strengths:
            assessment.append("✅ **Successful Tactics:**")
            for strength in analysis.strengths[:3]:
                assessment.append(f"   • {strength}")
        
        # Weaknesses as areas needing improvement
        if analysis.weaknesses:
            assessment.append("\n❌ **Tactical Failures:**")
            for weakness in analysis.weaknesses[:3]:
                assessment.append(f"   • {weakness}")
        
        # Add performance summary
        if analysis.pnl > 0:
            assessment.append("\n🎖️ **Mission Status:** SUCCESSFUL - Objective secured")
        elif analysis.pnl < 0:
            assessment.append("\n⚠️ **Mission Status:** FAILED - Tactical retreat executed")
        else:
            assessment.append("\n🛡️ **Mission Status:** NEUTRAL - No casualties")
        
        return '\n'.join(assessment)
    
    async def _get_mission_specific_training(self, analysis: TradeAnalysis, tier: TradingTier) -> Optional[str]:
        """Get mission-specific training recommendations"""
        training_modules = []
        
        # Priority training based on grade
        if analysis.grade in ['D', 'F']:
            training_modules.append("""🎯 **PRIORITY TRAINING REQUIRED**
            
Your performance indicates critical skill gaps. Mandatory training modules:
1. **Risk Management Bootcamp** - Protect your capital like a fortress
2. **Entry Point Mastery** - Learn to identify A+ setups only
3. **Psychology Reset** - Break the losing streak mentality""")
        
        # Weakness-specific training
        weakness_training = {
            "stop loss": """🛡️ **DEFENSIVE TACTICS TRAINING**
Watch: "Stop Loss Mastery - Your Account's Body Armor"
Practice: Set 10 paper trades with proper stop losses""",
            
            "risk/reward": """📊 **TACTICAL MATHEMATICS**
Drill: "2:1 Risk/Reward Calculator Challenge"
Mission: Find 5 setups with 3:1 or better ratios""",
            
            "trend": """🌊 **BATTLEFIELD RECONNAISSANCE**
Study: "Reading Market Terrain - Trend Identification"
Exercise: Mark trend lines on 20 different charts""",
            
            "fomo": """🧠 **PSYCHOLOGICAL WARFARE DEFENSE**
Watch: "FOMO - The Trader's Enemy Within"
Task: Journal 3 trades you DIDN'T take and why""",
            
            "position size": """💰 **AMMUNITION MANAGEMENT**
Calculator: "Position Size = Victory Size"
Rule: Never risk more than 1% per mission"""
        }
        
        # Add specific training based on weaknesses
        for weakness in analysis.weaknesses[:2]:
            for key, training in weakness_training.items():
                if key in weakness.lower():
                    training_modules.append(training)
                    break
        
        # Tier-specific advanced training
        if tier in [TradingTier.JOURNEYMAN, TradingTier.MASTER] and analysis.grade in ['A', 'B']:
            training_modules.append("""🚀 **ADVANCED OPERATOR TRAINING**
            
Excellence detected! Ready for next-level tactics:
• Multi-timeframe confluence mastery
• Volume profile advanced strategies
• Options hedging for large positions""")
        
        if training_modules:
            return "\n\n".join(training_modules)
        
        # Default encouragement
        return """📚 **CONTINUOUS IMPROVEMENT PROTOCOL**
        
Keep sharpening your skills, soldier:
• Review today's trade in your journal
• Watch one strategy video from your tier
• Practice risk calculations"""
    
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
    
    async def get_dynamic_education_response(self, user_id: str, action: str, 
                                           params: Dict[str, Any] = None) -> str:
        """Get dynamic educational response based on user action"""
        user_tier = await self.get_user_tier(user_id)
        perf = self.user_performance.get(user_id, {})
        
        # Build context
        context = {
            'tier': user_tier,
            'consecutive_losses': perf.get('consecutive_losses', 0),
            'consecutive_wins': perf.get('consecutive_wins', 0),
            'last_trade_result': perf.get('last_trade_result'),
            'mood': perf.get('mood', 'neutral')
        }
        
        # Action-specific responses
        if action == 'help_request':
            context['situation'] = 'education'
            context['performance'] = 'neutral'
            persona = PersonaType.AEGIS  # Always supportive for help
            
            message = self.personas.get_persona_response(persona, context)
            
            # Add specific help based on tier
            if user_tier == TradingTier.NIBBLER:
                message += """

📚 **RECRUIT RESOURCES:**
• /paper_trade - Practice without risk
• /education videos - Watch your tier's training
• /analyze - Get trade analysis
• /cooldown status - Check recovery time

Remember: Every expert was once a beginner!"""
            
            return message
        
        elif action == 'streak_alert':
            # Determine if winning or losing streak
            if perf.get('consecutive_wins', 0) >= 3:
                context['situation'] = 'post_trade'
                context['performance'] = 'win'
                context['win_streak'] = perf['consecutive_wins']
                persona = PersonaType.DRILL  # Pump them up but keep them grounded
            else:
                context['situation'] = 'support'
                context['performance'] = 'loss'
                persona = PersonaType.AEGIS  # Supportive during tough times
            
            return self.personas.get_persona_response(persona, context)
        
        elif action == 'market_analysis':
            context['situation'] = 'pre_trade'
            context['performance'] = 'neutral'
            persona = PersonaType.NEXUS  # Strategic analysis
            
            return self.personas.get_persona_response(persona, context)
        
        elif action == 'achievement':
            context['situation'] = 'education'
            context['performance'] = 'achievement'
            
            # Random celebration from any persona
            persona = self.personas.select_persona(context)
            
            return self.personas.get_persona_response(persona, context)
        
        # Default educational encouragement
        context['situation'] = 'education'
        context['performance'] = 'neutral'
        persona = self.personas.select_persona(context)
        
        return self.personas.get_persona_response(persona, context)
    
    async def get_motivational_quote(self, user_id: str) -> str:
        """Get a motivational quote based on user's current state"""
        user_tier = await self.get_user_tier(user_id)
        perf = self.user_performance.get(user_id, {})
        
        # Tier and performance-based quotes
        quotes = {
            'struggling': [
                "The market is a patient teacher, but an expensive one. Learn the lessons cheaply through discipline.",
                "Every loss is a brick in the foundation of your future success. Build strong.",
                "Warriors aren't defined by their victories, but by how they rise after defeat.",
                "The comeback is always stronger than the setback. Trust the process."
            ],
            'winning': [
                "Discipline got you here. Discipline keeps you here. Never abandon your rules.",
                "Success is rented, never owned. The rent is due every single day.",
                "Stay humble or the market will humble you. Respect every trade.",
                "Victory loves preparation. Keep sharpening your blade."
            ],
            'neutral': [
                "The best trades are often the ones you don't take. Patience pays.",
                "Risk management is the difference between a career and a story.",
                "Trade what you see, not what you think. The market doesn't care about opinions.",
                "Consistency beats intensity. Small wins compound into wealth."
            ],
            'nibbler': [
                "Every master trader started exactly where you are. Keep going.",
                "Focus on the process, not the profits. The money follows mastery.",
                "Your only competition is who you were yesterday. Progress over perfection.",
                "Paper bullets teach real lessons. Practice with purpose."
            ]
        }
        
        # Select appropriate quote category
        if perf.get('consecutive_losses', 0) >= 3:
            category = 'struggling'
        elif perf.get('consecutive_wins', 0) >= 3:
            category = 'winning'
        elif user_tier == TradingTier.NIBBLER:
            category = 'nibbler'
        else:
            category = 'neutral'
        
        quote = random.choice(quotes[category])
        
        # Add persona flavor
        if random.random() < 0.5:
            return f"**[DRILL]** {quote} NOW GET BACK OUT THERE!"
        else:
            return f"**[CAPTAIN AEGIS]** {quote} I believe in you."