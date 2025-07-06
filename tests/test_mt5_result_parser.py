"""
🎯 Tests for MT5 Result Parser
Comprehensive test coverage for all MT5 result formats
"""

import pytest
from datetime import datetime
import json

from src.mt5_bridge.result_parser import (
    MT5ResultParser, MT5ResultAggregator, parse_mt5_result,
    OrderType, TradeStatus
)
from src.mt5_bridge.trade_result_model import TradeResult, TradeResultBatch


class TestMT5ResultParser:
    """Test MT5 result parser functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = MT5ResultParser()
        
    def test_parse_trade_opened(self):
        """Test parsing trade opened result"""
        result_string = (
            "TRADE_OPENED|ticket:12345|symbol:EURUSD|type:BUY|"
            "volume:0.01|price:1.12345|sl:1.11345|tp:1.13345|comment:BITTEN"
        )
        
        result = self.parser.parse(result_string)
        
        assert result['type'] == 'trade_opened'
        assert result['success'] is True
        assert result['ticket'] == 12345
        assert result['symbol'] == 'EURUSD'
        assert result['order_type'] == 'BUY'
        assert result['volume'] == 0.01
        assert result['price'] == 1.12345
        assert result['stop_loss'] == 1.11345
        assert result['take_profit'] == 1.13345
        assert result['comment'] == 'BITTEN'
        assert result['status'] == TradeStatus.OPEN.value
        
    def test_parse_trade_opened_no_comment(self):
        """Test parsing trade opened without comment"""
        result_string = (
            "TRADE_OPENED|ticket:12346|symbol:GBPUSD|type:SELL|"
            "volume:0.02|price:1.26500|sl:1.27500|tp:1.25500"
        )
        
        result = self.parser.parse(result_string)
        
        assert result['type'] == 'trade_opened'
        assert result['ticket'] == 12346
        assert result['comment'] is None
        
    def test_parse_trade_closed(self):
        """Test parsing trade closed result"""
        result_string = (
            "TRADE_CLOSED|ticket:12345|close_price:1.12445|"
            "profit:10.50|swap:0|commission:-0.20|close_time:2024-01-07 15:30:45"
        )
        
        result = self.parser.parse(result_string)
        
        assert result['type'] == 'trade_closed'
        assert result['success'] is True
        assert result['ticket'] == 12345
        assert result['close_price'] == 1.12445
        assert result['profit'] == 10.50
        assert result['swap'] == 0
        assert result['commission'] == -0.20
        assert result['net_profit'] == 10.30
        assert result['status'] == TradeStatus.CLOSED.value
        
    def test_parse_order_placed(self):
        """Test parsing pending order placed"""
        result_string = (
            "ORDER_PLACED|ticket:12347|symbol:USDJPY|type:BUY_LIMIT|"
            "volume:0.05|price:145.500|sl:144.500|tp:147.500"
        )
        
        result = self.parser.parse(result_string)
        
        assert result['type'] == 'order_placed'
        assert result['success'] is True
        assert result['ticket'] == 12347
        assert result['symbol'] == 'USDJPY'
        assert result['order_type'] == 'BUY_LIMIT'
        assert result['volume'] == 0.05
        assert result['status'] == TradeStatus.PENDING.value
        
    def test_parse_position_modified(self):
        """Test parsing position modification"""
        result_string = (
            "POSITION_MODIFIED|ticket:12345|sl:1.11845|tp:1.12845|success:true"
        )
        
        result = self.parser.parse(result_string)
        
        assert result['type'] == 'position_modified'
        assert result['success'] is True
        assert result['ticket'] == 12345
        assert result['new_stop_loss'] == 1.11845
        assert result['new_take_profit'] == 1.12845
        
    def test_parse_error(self):
        """Test parsing error result"""
        result_string = "ERROR|code:10019|message:Insufficient funds|context:TRADE_OPEN"
        
        result = self.parser.parse(result_string)
        
        assert result['type'] == 'error'
        assert result['success'] is False
        assert result['error_code'] == 10019
        assert result['error_message'] == 'Insufficient funds'
        assert result['error_description'] == 'Insufficient funds'
        assert result['context'] == 'TRADE_OPEN'
        assert result['status'] == TradeStatus.ERROR.value
        
    def test_parse_account_update(self):
        """Test parsing account update"""
        result_string = (
            "ACCOUNT_UPDATE|balance:10500.25|equity:10450.75|"
            "margin:250.00|free_margin:10200.75"
        )
        
        result = self.parser.parse(result_string)
        
        assert result['type'] == 'account_update'
        assert result['success'] is True
        assert result['balance'] == 10500.25
        assert result['equity'] == 10450.75
        assert result['margin'] == 250.00
        assert result['free_margin'] == 10200.75
        assert result['margin_level'] == pytest.approx(4180.3, rel=0.1)
        
    def test_parse_json_format(self):
        """Test parsing JSON format result"""
        json_data = {
            "type": "trade_result",
            "ticket": 12348,
            "symbol": "AUDUSD",
            "profit": 25.50,
            "custom_field": "test"
        }
        result_string = json.dumps(json_data)
        
        result = self.parser.parse(result_string)
        
        assert result['type'] == 'trade_result'
        assert result['success'] is True
        assert result['ticket'] == 12348
        assert result['custom_field'] == 'test'
        assert 'timestamp' in result
        
    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = self.parser.parse("")
        
        assert result['type'] == 'parse_error'
        assert result['success'] is False
        assert 'Empty result string' in result['error_message']
        
    def test_parse_unknown_format(self):
        """Test parsing unknown format"""
        result = self.parser.parse("UNKNOWN|format:test")
        
        assert result['type'] == 'parse_error'
        assert result['success'] is False
        assert 'Unknown format' in result['error_message']
        
    def test_extract_trade_summary_opened(self):
        """Test extracting trade summary for opened trade"""
        parsed = {
            'type': 'trade_opened',
            'ticket': 12345,
            'symbol': 'EURUSD',
            'order_type': 'BUY',
            'volume': 0.01,
            'price': 1.12345,
            'stop_loss': 1.11345,
            'take_profit': 1.13345
        }
        
        summary = self.parser.extract_trade_summary(parsed)
        
        assert summary['action'] == 'opened'
        assert summary['ticket'] == 12345
        assert summary['direction'] == 'BUY'
        assert summary['risk'] == pytest.approx(100.0, rel=0.1)
        assert summary['potential_reward'] == pytest.approx(100.0, rel=0.1)
        
    def test_extract_trade_summary_closed(self):
        """Test extracting trade summary for closed trade"""
        parsed = {
            'type': 'trade_closed',
            'ticket': 12345,
            'net_profit': 15.50
        }
        
        summary = self.parser.extract_trade_summary(parsed)
        
        assert summary['action'] == 'closed'
        assert summary['ticket'] == 12345
        assert summary['profit'] == 15.50
        
    def test_validate_result_valid(self):
        """Test validating valid result"""
        result = {
            'type': 'trade_opened',
            'success': True,
            'ticket': 12345,
            'symbol': 'EURUSD',
            'order_type': 'BUY',
            'volume': 0.01,
            'price': 1.12345
        }
        
        is_valid, error = self.parser.validate_result(result)
        
        assert is_valid is True
        assert error is None
        
    def test_validate_result_missing_fields(self):
        """Test validating result with missing fields"""
        result = {
            'type': 'trade_opened',
            'success': True,
            'ticket': 12345
            # Missing required fields
        }
        
        is_valid, error = self.parser.validate_result(result)
        
        assert is_valid is False
        assert 'Missing required field' in error
        
    def test_parse_batch(self):
        """Test parsing batch of results"""
        results = [
            "TRADE_OPENED|ticket:12345|symbol:EURUSD|type:BUY|volume:0.01|price:1.12345|sl:1.11345|tp:1.13345",
            "TRADE_CLOSED|ticket:12345|close_price:1.12445|profit:10.50|swap:0|commission:-0.20|close_time:2024-01-07 15:30:45",
            "ERROR|code:10019|message:Insufficient funds"
        ]
        
        parsed_results = self.parser.parse_batch(results)
        
        assert len(parsed_results) == 3
        assert parsed_results[0]['type'] == 'trade_opened'
        assert parsed_results[1]['type'] == 'trade_closed'
        assert parsed_results[2]['type'] == 'error'


class TestMT5ResultAggregator:
    """Test MT5 result aggregator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.aggregator = MT5ResultAggregator()
        
    def test_add_and_aggregate_results(self):
        """Test adding results and getting summary"""
        # Add various results
        self.aggregator.add_result(
            "TRADE_CLOSED|ticket:12345|close_price:1.12445|"
            "profit:10.50|swap:0|commission:-0.20|close_time:2024-01-07 15:30:45"
        )
        self.aggregator.add_result(
            "TRADE_CLOSED|ticket:12346|close_price:1.26300|"
            "profit:-5.00|swap:0|commission:-0.20|close_time:2024-01-07 16:30:45"
        )
        self.aggregator.add_result(
            "ERROR|code:10019|message:Insufficient funds"
        )
        
        summary = self.aggregator.get_summary()
        
        assert summary['total_results'] == 3
        assert summary['total_trades'] == 2
        assert summary['successful_trades'] == 1
        assert summary['failed_trades'] == 1
        assert summary['win_rate'] == 50.0
        assert summary['total_profit'] == 5.10  # 10.30 - 5.20
        assert len(summary['errors']) == 1
        assert summary['errors'][0]['code'] == 10019
        
    def test_clear_results(self):
        """Test clearing results"""
        self.aggregator.add_result("ERROR|code:10019|message:Test")
        assert len(self.aggregator.results) == 1
        
        self.aggregator.clear()
        assert len(self.aggregator.results) == 0


class TestTradeResultModel:
    """Test TradeResult model"""
    
    def test_create_from_parser_result_opened(self):
        """Test creating TradeResult from parser result (opened)"""
        parsed = {
            'type': 'trade_opened',
            'ticket': 12345,
            'symbol': 'EURUSD',
            'order_type': 'BUY',
            'volume': 0.01,
            'price': 1.12345,
            'stop_loss': 1.11345,
            'take_profit': 1.13345,
            'comment': 'BITTEN',
            'status': 'OPEN'
        }
        
        result = TradeResult.from_parser_result(parsed)
        
        assert result.ticket == 12345
        assert result.symbol == 'EURUSD'
        assert result.order_type == 'BUY'
        assert result.volume == 0.01
        assert result.open_price == 1.12345
        assert result.risk_reward_ratio == 1.0
        
    def test_create_from_parser_result_closed(self):
        """Test creating TradeResult from parser result (closed)"""
        parsed = {
            'type': 'trade_closed',
            'ticket': 12345,
            'close_price': 1.12445,
            'profit': 10.50,
            'commission': -0.20,
            'swap': 0,
            'net_profit': 10.30,
            'close_time': '2024-01-07T15:30:45',
            'status': 'CLOSED'
        }
        
        result = TradeResult.from_parser_result(parsed)
        
        assert result.ticket == 12345
        assert result.close_price == 1.12445
        assert result.net_profit == 10.30
        assert result.is_successful() is True
        
    def test_to_database_model(self):
        """Test converting to database model"""
        result = TradeResult(
            ticket=12345,
            symbol='EURUSD',
            order_type='BUY',
            status='OPEN',
            volume=0.01,
            open_price=1.12345,
            stop_loss=1.11345,
            take_profit=1.13345
        )
        
        db_trade = result.to_database_model(user_id=1, fire_mode='SPRAY')
        
        assert db_trade.user_id == 1
        assert db_trade.mt5_ticket == 12345
        assert db_trade.symbol == 'EURUSD'
        assert db_trade.fire_mode == 'SPRAY'
        assert float(db_trade.volume) == 0.01
        
    def test_get_pips(self):
        """Test calculating pips"""
        # Test forex pair
        result = TradeResult(
            ticket=12345,
            symbol='EURUSD',
            order_type='BUY',
            status='CLOSED',
            open_price=1.12345,
            close_price=1.12445
        )
        
        pips = result.get_pips()
        assert pips == pytest.approx(10.0, rel=0.1)
        
        # Test JPY pair
        result_jpy = TradeResult(
            ticket=12346,
            symbol='USDJPY',
            order_type='SELL',
            status='CLOSED',
            open_price=145.500,
            close_price=145.300
        )
        
        pips_jpy = result_jpy.get_pips()
        assert pips_jpy == pytest.approx(20.0, rel=0.1)
        
    def test_format_summary(self):
        """Test formatting summary"""
        # Test opened trade
        result = TradeResult(
            ticket=12345,
            symbol='EURUSD',
            order_type='BUY',
            status='OPEN',
            volume=0.01,
            open_price=1.12345,
            stop_loss=1.11345,
            take_profit=1.13345
        )
        
        summary = result.format_summary()
        assert '📈' in summary
        assert 'EURUSD' in summary
        assert 'BUY' in summary
        
        # Test closed profitable trade
        result.status = 'CLOSED'
        result.close_price = 1.12445
        result.net_profit = 10.50
        
        summary = result.format_summary()
        assert '✅' in summary
        assert '$10.50' in summary
        
        # Test error
        result_error = TradeResult(
            ticket=12346,
            symbol='GBPUSD',
            order_type='SELL',
            status='ERROR',
            error_code=10019,
            error_message='Insufficient funds'
        )
        
        summary = result_error.format_summary()
        assert '⚠️' in summary
        assert 'Insufficient funds' in summary


class TestTradeResultBatch:
    """Test TradeResultBatch"""
    
    def test_batch_summary(self):
        """Test getting batch summary"""
        batch = TradeResultBatch()
        
        # Add profitable trade
        batch.add_result(TradeResult(
            ticket=1,
            symbol='EURUSD',
            order_type='BUY',
            status='CLOSED',
            volume=0.01,
            net_profit=10.50
        ))
        
        # Add losing trade
        batch.add_result(TradeResult(
            ticket=2,
            symbol='GBPUSD',
            order_type='SELL',
            status='CLOSED',
            volume=0.02,
            net_profit=-5.25
        ))
        
        # Add error
        batch.add_result(TradeResult(
            ticket=3,
            symbol='USDJPY',
            order_type='BUY',
            status='ERROR'
        ))
        
        summary = batch.get_summary()
        
        assert summary['total_trades'] == 3
        assert summary['successful_trades'] == 1
        assert summary['failed_trades'] == 1
        assert summary['total_profit'] == 5.25
        assert summary['total_volume'] == 0.03
        assert summary['average_profit'] == pytest.approx(1.75, rel=0.01)
        
    def test_get_by_status(self):
        """Test filtering by status"""
        batch = TradeResultBatch()
        
        batch.add_result(TradeResult(ticket=1, symbol='EURUSD', order_type='BUY', status='OPEN'))
        batch.add_result(TradeResult(ticket=2, symbol='GBPUSD', order_type='SELL', status='CLOSED'))
        batch.add_result(TradeResult(ticket=3, symbol='USDJPY', order_type='BUY', status='OPEN'))
        
        open_trades = batch.get_by_status('OPEN')
        assert len(open_trades) == 2
        assert all(t.status == 'OPEN' for t in open_trades)


def test_convenience_function():
    """Test parse_mt5_result convenience function"""
    result = parse_mt5_result(
        "TRADE_OPENED|ticket:12345|symbol:EURUSD|type:BUY|"
        "volume:0.01|price:1.12345|sl:1.11345|tp:1.13345"
    )
    
    assert result['type'] == 'trade_opened'
    assert result['ticket'] == 12345