# MetaQuotes Demo Account Provisioning System

Production-ready integration with MetaQuotes for instant demo account creation, secure credential delivery, and lifecycle management.

## Overview

The MetaQuotes Demo Account Provisioning System provides:

- **Instant Account Creation**: Pre-provisioned pool of demo accounts for immediate assignment
- **Secure Credential Delivery**: Multiple delivery methods with encryption and one-time access
- **Lifecycle Management**: Automated health monitoring, expiration handling, and cleanup
- **Press Pass Integration**: Seamless integration with BITTEN's Press Pass onboarding
- **API Endpoints**: RESTful API for account management and monitoring

## Architecture

### Core Components

1. **Demo Account Service** (`demo_account_service.py`)
   - Handles account provisioning via MetaQuotes API
   - Manages user account assignments
   - Provides credential encryption/decryption

2. **Account Pool Manager** (`account_pool_manager.py`)
   - Maintains pool of pre-provisioned accounts
   - Ensures minimum availability for instant assignment
   - Performs health checks and cleanup

3. **Credential Delivery** (`credential_delivery.py`)
   - Secure credential packaging and encryption
   - Multiple delivery methods (Telegram, Email, API, QR Code)
   - One-time access links with expiration

4. **Press Pass Manager V2** (`../onboarding/press_pass_manager_v2.py`)
   - Enhanced Press Pass activation with real accounts
   - Integrated credential delivery
   - Account health monitoring

## Database Schema

The system uses PostgreSQL with the following main tables:

- `demo_account_pool`: Pre-provisioned accounts ready for assignment
- `user_demo_accounts`: Active accounts assigned to users
- `demo_provisioning_queue`: Queue for account creation requests
- `credential_deliveries`: Secure credential delivery tracking
- `demo_account_health_logs`: Health monitoring history

## Setup Instructions

### 1. Database Migration

Run the migration to create required tables:

```bash
cd /root/HydraX-v2/migrations
./run_metaquotes_migration.sh
```

### 2. Configure API Credentials

Set MetaQuotes API credentials in environment variables:

```bash
export METAQUOTES_API_KEY="your-api-key"
export METAQUOTES_API_SECRET="your-api-secret"
export METAQUOTES_PARTNER_ID="your-partner-id"
export BITTEN_ENCRYPTION_SEED="your-encryption-seed"
```

### 3. Start Services

Start the MetaQuotes services:

```bash
cd /root/HydraX-v2
python start_metaquotes_services.py
```

This starts:
- Account pool manager
- Health monitoring
- Credential delivery processor

### 4. Run Tests

Verify the integration:

```bash
python test_metaquotes_integration.py
```

## API Usage

### Activate Press Pass

```bash
curl -X POST https://api.bitten.com/api/v1/metaquotes/press-pass/activate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123456",
    "real_name": "John Doe",
    "delivery_method": "telegram",
    "contact_info": "@johndoe"
  }'
```

### Check Account Health

```bash
curl -X GET https://api.bitten.com/api/v1/metaquotes/account/123456/health \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Get Pool Status

```bash
curl -X GET https://api.bitten.com/api/v1/metaquotes/pool/status \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Configuration

### Pool Configuration

Adjust pool settings in `start_metaquotes_services.py`:

```python
pool_config = PoolConfig(
    min_available_accounts=25,  # Minimum ready accounts
    max_pool_size=100,         # Maximum total accounts
    target_buffer=40,          # Target available accounts
    provision_batch_size=5,    # Batch provisioning size
    health_check_interval_minutes=15,
    cleanup_interval_hours=4
)
```

### Demo Account Configuration

Default account settings:

```python
config = DemoAccountConfig(
    initial_balance=50000.0,   # $50,000 USD
    currency="USD",
    leverage="1:100",
    expiry_days=30,           # 30-day expiration
    server="BITTEN-Demo"
)
```

## Security Features

1. **Credential Encryption**
   - AES-256 encryption for stored passwords
   - Unique encryption keys per delivery
   - Master key rotation support

2. **One-Time Access**
   - Credentials viewable only once
   - 30-minute expiration on delivery links
   - Audit logging of all access attempts

3. **API Authentication**
   - Bearer token authentication
   - Rate limiting on all endpoints
   - Request signing for MetaQuotes API

## Monitoring

### Health Checks

The system performs automatic health checks:
- Account connectivity verification
- Balance and status monitoring
- Expiration tracking
- Error detection and logging

### Metrics

Key metrics tracked:
- Pool availability rate
- Account provisioning speed
- Credential delivery success rate
- User conversion metrics

### Logs

Log files location:
- Service logs: `/root/HydraX-v2/logs/metaquotes_services.log`
- Health checks: Database table `demo_account_health_logs`
- Access logs: Database table `credential_access_logs`

## Troubleshooting

### Common Issues

1. **Pool Running Low**
   - Check `pool_status` endpoint
   - Force replenishment if needed
   - Adjust `min_available_accounts` setting

2. **Account Provisioning Failures**
   - Check MetaQuotes API credentials
   - Verify network connectivity
   - Review error logs

3. **Credential Delivery Issues**
   - Verify delivery method configuration
   - Check delivery queue status
   - Ensure contact info is correct

### Manual Operations

Force pool replenishment:
```bash
curl -X POST https://api.bitten.com/api/v1/metaquotes/pool/replenish?count=10 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Resend credentials:
```bash
curl -X POST https://api.bitten.com/api/v1/metaquotes/account/resend-credentials \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123456",
    "delivery_method": "email",
    "contact_info": "user@example.com"
  }'
```

## Production Considerations

1. **Scaling**
   - Pool manager runs as singleton
   - Use multiple workers for API endpoints
   - Database connection pooling recommended

2. **High Availability**
   - Deploy services on multiple nodes
   - Use PostgreSQL replication
   - Implement health check endpoints

3. **Disaster Recovery**
   - Regular database backups
   - Encrypted credential backups
   - Account pool state persistence

## Integration with BITTEN

The MetaQuotes system integrates seamlessly with BITTEN's architecture:

1. **Press Pass Flow**
   - User requests Press Pass
   - System provisions MetaQuotes account
   - Credentials delivered securely
   - Account tracked for 7-day trial

2. **XP Reset System**
   - Press Pass users registered automatically
   - Nightly XP resets applied
   - Shadow stats maintained

3. **Conversion Tracking**
   - Demo account usage monitored
   - Conversion signals tracked
   - Upgrade paths optimized

## Future Enhancements

Planned improvements:
- [ ] Real-time account usage analytics
- [ ] Advanced fraud detection
- [ ] Multi-broker support
- [ ] WebSocket streaming for live updates
- [ ] Mobile SDK for direct integration
- [ ] Advanced credential delivery (SMS, WhatsApp)

## Support

For issues or questions:
- Technical documentation: This README
- API documentation: `/api/docs`
- Support: support@bitten.com