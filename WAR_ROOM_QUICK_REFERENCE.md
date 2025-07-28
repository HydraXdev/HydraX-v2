# 🎖️ WAR ROOM QUICK REFERENCE

## Access the War Room
```
https://joinbitten.com/me?user_id={telegram_id}
```

## Code Location
- **File**: `/root/HydraX-v2/webapp_server_optimized.py`
- **Route**: `@app.route('/me')` (line ~2070)
- **API**: `@app.route('/api/user/<user_id>/war_room_stats')` (line ~2600)

## Key Features
1. **Military Callsigns** - Dynamic based on rank
2. **Live Stats** - Win rate, P&L, streak, global rank
3. **Kill Cards** - Recent successful trades
4. **Achievements** - 12 unlockable badges
5. **Squad Command** - Referral tracking
6. **Social Sharing** - Facebook, X, Instagram
7. **Quick Links** - Notebook, History, Stats, Tiers

## Database Connections
```python
# Import systems
from src.bitten_core.user_engagement import EngagementDB
from src.bitten_core.referral_system import ReferralSystem
from src.bitten_core.rank_access import RankAccess

# Get user data
db = EngagementDB()
user_stats = db.get_user_engagement_stats(user_id)

referral_system = ReferralSystem()
referral_data = referral_system.get_referral_stats(user_id)

rank_system = RankAccess()
user_rank = rank_system.get_user_rank(user_id)
```

## Testing
```bash
# Test with your Telegram ID
curl "https://joinbitten.com/me?user_id=YOUR_TELEGRAM_ID"

# Test API endpoint
curl "https://joinbitten.com/api/user/YOUR_TELEGRAM_ID/war_room_stats"
```

## Common Issues
1. **No stats showing**: Check if user exists in EngagementDB
2. **Wrong rank**: Verify RankAccess has correct tier
3. **No referrals**: Check ReferralSystem initialization
4. **Mobile layout**: Test at 768px and 480px breakpoints

## Customization
- **Callsigns**: Edit rank-to-callsign mapping in route
- **Achievements**: Modify achievements array
- **Colors**: Update CSS variables at top of template
- **Animations**: Edit @keyframes in style section

## Files to Reference
- `/WAR_ROOM_DOCUMENTATION.md` - Full documentation
- `/CLAUDE.md` - War Room section (line ~1671)
- `/src/bitten_core/war_room_enhanced.py` - Enhanced features
- `/src/bitten_core/social_sharing.py` - Sharing templates