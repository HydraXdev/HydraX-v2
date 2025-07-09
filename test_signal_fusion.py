#!/usr/bin/env python3
"""
Test and demonstrate the BITTEN Signal Fusion System
"""

import asyncio
from datetime import datetime
import logging
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import fusion components
from src.bitten_core.signal_fusion import (
    IntelSource, SignalFusionEngine, ConfidenceTier,
    tier_router, engagement_balancer
)
from src.bitten_core.intelligence_aggregator import IntelligenceAggregator
from src.bitten_core.complete_signal_flow_v3 import FusionEnhancedSignalFlow

console = Console()


class SignalFusionDemo:
    """Demonstration of the signal fusion system"""
    
    def __init__(self):
        self.fusion_engine = SignalFusionEngine()
        self.pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        
    async def generate_mock_intel_sources(self, pair: str) -> list[IntelSource]:
        """Generate mock intelligence sources for testing"""
        sources = []
        
        # Technical Analysis Source
        sources.append(IntelSource(
            source_id='technical_analyzer',
            source_type='technical',
            signal='BUY' if pair in ['EURUSD', 'GBPUSD'] else 'SELL',
            confidence=85.5,
            weight=0.4,
            metadata={
                'entry': 1.0850 if pair == 'EURUSD' else 1.2650,
                'sl': 1.0820 if pair == 'EURUSD' else 1.2620,
                'tp': 1.0900 if pair == 'EURUSD' else 1.2700,
                'indicators': {'RSI': 65, 'MACD': 'bullish'}
            }
        ))
        
        # Sentiment Analysis Source
        sources.append(IntelSource(
            source_id='sentiment_analyzer',
            source_type='sentiment',
            signal='BUY' if pair != 'USDJPY' else 'NEUTRAL',
            confidence=72.3,
            weight=0.2,
            metadata={
                'volume_surge': True,
                'spread_normal': True,
                'market_mood': 'risk-on'
            }
        ))
        
        # Fundamental Analysis Source
        sources.append(IntelSource(
            source_id='fundamental_analyzer',
            source_type='fundamental',
            signal='BUY',
            confidence=78.9,
            weight=0.2,
            metadata={
                'session': 'LONDON',
                'news_impact': 'low',
                'economic_bias': 'bullish'
            }
        ))
        
        # AI Bot Analysis Source
        sources.append(IntelSource(
            source_id='ai_bot_analyzer',
            source_type='ai_bot',
            signal='BUY' if pair == 'EURUSD' else 'SELL',
            confidence=91.2 if pair == 'EURUSD' else 68.5,
            weight=0.2,
            metadata={
                'bot_consensus': 3,
                'overwatch_view': 'tactical_long',
                'risk_assessment': 'acceptable'
            }
        ))
        
        return sources
    
    async def demonstrate_fusion(self):
        """Demonstrate the signal fusion process"""
        console.print("\n[bold cyan]🎯 BITTEN Signal Fusion System Demonstration[/bold cyan]\n")
        
        # Process each pair
        for pair in self.pairs:
            console.print(f"\n[yellow]Processing {pair}...[/yellow]")
            
            # Generate mock sources
            sources = await self.generate_mock_intel_sources(pair)
            
            # Display sources
            source_table = Table(title=f"Intelligence Sources for {pair}")
            source_table.add_column("Source", style="cyan")
            source_table.add_column("Type", style="magenta")
            source_table.add_column("Signal", style="green")
            source_table.add_column("Confidence", style="yellow")
            source_table.add_column("Weight", style="blue")
            
            for source in sources:
                source_table.add_row(
                    source.source_id,
                    source.source_type,
                    source.signal,
                    f"{source.confidence:.1f}%",
                    f"{source.weight:.1f}"
                )
            
            console.print(source_table)
            
            # Fuse signals
            fused_signal = self.fusion_engine.fuse_signals(sources, pair)
            
            if fused_signal:
                # Display fused result
                tier_colors = {
                    ConfidenceTier.SNIPER: "red",
                    ConfidenceTier.PRECISION: "yellow",
                    ConfidenceTier.RAPID: "blue",
                    ConfidenceTier.TRAINING: "green"
                }
                
                color = tier_colors.get(fused_signal.tier, "white")
                
                result_panel = Panel(
                    f"""[bold]Fused Signal Result[/bold]
                    
Signal ID: {fused_signal.signal_id}
Direction: [{color}]{fused_signal.direction}[/{color}]
Confidence: [bold]{fused_signal.confidence:.1f}%[/bold]
Tier: [bold {color}]{fused_signal.tier.name}[/bold {color}]

Entry: {fused_signal.entry:.5f}
Stop Loss: {fused_signal.sl:.5f}
Take Profit: {fused_signal.tp:.5f}

Agreement Score: {fused_signal.agreement_score:.1f}%
Source Diversity: {fused_signal.source_diversity:.1f}

Fusion Scores:
  • Weighted Confidence: {fused_signal.fusion_scores['weighted_confidence']:.1f}%
  • Type Coverage: {fused_signal.fusion_scores['type_coverage']:.1f}%
  • Consistency: {fused_signal.fusion_scores['confidence_consistency']:.1f}%
  • Time Sync: {fused_signal.fusion_scores['time_sync']:.1f}%""",
                    title=f"✨ {pair} Fusion Result",
                    border_style=color
                )
                
                console.print(result_panel)
                
                # Test tier routing
                console.print("\n[cyan]Testing Tier-Based Routing:[/cyan]")
                for tier in ['nibbler', 'fang', 'commander', 'apex']:
                    can_receive = tier_router.route_signal(fused_signal, tier)
                    status = "✅ Yes" if can_receive else "❌ No"
                    console.print(f"  {tier.capitalize()}: {status}")
            else:
                console.print("[red]❌ No consensus reached - signal not generated[/red]")
            
            await asyncio.sleep(1)  # Brief pause between pairs
    
    async def demonstrate_tier_performance(self):
        """Show tier performance statistics"""
        console.print("\n[bold cyan]📊 Tier Performance Statistics[/bold cyan]\n")
        
        # Simulate some historical performance
        test_signals = [
            (ConfidenceTier.SNIPER, True),
            (ConfidenceTier.SNIPER, True),
            (ConfidenceTier.SNIPER, False),
            (ConfidenceTier.PRECISION, True),
            (ConfidenceTier.PRECISION, True),
            (ConfidenceTier.PRECISION, False),
            (ConfidenceTier.RAPID, True),
            (ConfidenceTier.RAPID, False),
            (ConfidenceTier.RAPID, False),
            (ConfidenceTier.TRAINING, True),
            (ConfidenceTier.TRAINING, False),
        ]
        
        # Create mock signals and update performance
        for tier, result in test_signals:
            mock_signal = self.fusion_engine.fuse_signals(
                await self.generate_mock_intel_sources('EURUSD'),
                'EURUSD'
            )
            if mock_signal:
                mock_signal.tier = tier  # Override tier for testing
                self.fusion_engine.quality_optimizer.update_performance(mock_signal, result)
        
        # Display tier stats
        tier_stats = self.fusion_engine.get_tier_stats()
        
        stats_table = Table(title="Confidence Tier Performance")
        stats_table.add_column("Tier", style="cyan")
        stats_table.add_column("Threshold", style="magenta")
        stats_table.add_column("Total Signals", style="yellow")
        stats_table.add_column("Wins", style="green")
        stats_table.add_column("Win Rate", style="bold")
        
        for tier_name, stats in tier_stats.items():
            win_rate_str = f"{stats['win_rate']:.1%}"
            if stats['win_rate'] >= 0.7:
                win_rate_str = f"[green]{win_rate_str}[/green]"
            elif stats['win_rate'] < 0.5:
                win_rate_str = f"[red]{win_rate_str}[/red]"
            
            stats_table.add_row(
                stats['name'],
                f"{stats['threshold']}%+",
                str(stats['total_signals']),
                str(stats['wins']),
                win_rate_str
            )
        
        console.print(stats_table)
    
    async def demonstrate_user_routing(self):
        """Demonstrate user tier routing limits"""
        console.print("\n[bold cyan]🚦 User Tier Routing Demonstration[/bold cyan]\n")
        
        # Reset daily counters
        tier_router._check_daily_reset()
        
        # Simulate signals for different user tiers
        routing_table = Table(title="Daily Signal Routing Limits")
        routing_table.add_column("User Tier", style="cyan")
        routing_table.add_column("Daily Limit", style="magenta")
        routing_table.add_column("Quality Filter", style="yellow")
        routing_table.add_column("Current Count", style="green")
        routing_table.add_column("Status", style="bold")
        
        # Generate some test signals
        test_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'AUDUSD', 'NZDUSD', 'USDCAD']
        
        for i, pair in enumerate(test_pairs):
            sources = await self.generate_mock_intel_sources(pair)
            # Vary confidence for different tiers
            for source in sources:
                source.confidence = 95 - (i * 5)  # Decreasing confidence
            
            signal = self.fusion_engine.fuse_signals(sources, pair)
            if signal:
                # Test routing for each tier
                for tier in ['nibbler', 'fang', 'commander', 'apex']:
                    tier_router.route_signal(signal, tier)
        
        # Display results
        tier_info = {
            'nibbler': 'SNIPER & top PRECISION only',
            'fang': 'SNIPER, PRECISION & top RAPID',
            'commander': 'All except low TRAINING',
            'apex': 'All signals'
        }
        
        for tier in ['nibbler', 'fang', 'commander', 'apex']:
            stats = tier_router.get_user_stats(tier)
            status = "🔴 Limit Reached" if stats['limit_reached'] else "🟢 Active"
            
            routing_table.add_row(
                tier.capitalize(),
                str(stats['daily_limit']),
                tier_info[tier],
                f"{stats['signals_today']}/{stats['daily_limit']}",
                status
            )
        
        console.print(routing_table)
    
    async def run_demo(self):
        """Run the complete demonstration"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Fusion demonstration
            task1 = progress.add_task("[cyan]Signal Fusion Process...", total=None)
            await self.demonstrate_fusion()
            progress.update(task1, completed=True)
            
            # Performance statistics
            task2 = progress.add_task("[yellow]Tier Performance...", total=None)
            await self.demonstrate_tier_performance()
            progress.update(task2, completed=True)
            
            # User routing
            task3 = progress.add_task("[green]User Routing...", total=None)
            await self.demonstrate_user_routing()
            progress.update(task3, completed=True)
        
        console.print("\n[bold green]✅ Signal Fusion System Demonstration Complete![/bold green]\n")


async def main():
    """Main entry point"""
    demo = SignalFusionDemo()
    await demo.run_demo()
    
    # Optional: Start live monitoring
    console.print("[cyan]Would you like to start live monitoring? (y/n):[/cyan] ", end="")
    response = input().lower()
    
    if response == 'y':
        console.print("\n[yellow]Starting live signal monitoring...[/yellow]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        # Initialize flow
        flow = FusionEnhancedSignalFlow()
        
        try:
            await flow.start_monitoring()
        except KeyboardInterrupt:
            console.print("\n[red]Monitoring stopped by user[/red]")


if __name__ == "__main__":
    asyncio.run(main())