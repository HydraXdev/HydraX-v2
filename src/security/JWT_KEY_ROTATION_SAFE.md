# JWT Key Rotation Safety Guide

## Current Key Configuration

**Location**: `/root/HydraX-v2/keys/`

- `jwt_private.pem` - RS256 private key (2048-bit)
- `jwt_public.pem` - RS256 public key

**Key ID**: `key-2025-10` (set in .env as JWT_KEY_ID)

## Safe Rotation Procedure

### Step 1: Generate New Key Pair

```bash
cd /root/HydraX-v2/keys

# Generate new key with different ID
openssl genrsa -out jwt_private_new.pem 2048
openssl rsa -in jwt_private_new.pem -pubout -out jwt_public_new.pem

# Set proper permissions
chmod 600 jwt_private_new.pem
chmod 644 jwt_public_new.pem
```

### Step 2: Update JWT Manager to Support Multiple Keys

The JWT manager already supports key rotation via the `kid` (key ID) parameter in tokens.

**File**: `/root/HydraX-v2/src/security/jwt_manager.py`

Add support for multiple public keys by loading both old and new:

```python
# Load multiple public keys for validation
self.public_keys = {
    'key-2025-10': self._load_public_key('/root/HydraX-v2/keys/jwt_public.pem'),
    'key-2025-11': self._load_public_key('/root/HydraX-v2/keys/jwt_public_new.pem')
}
```

### Step 3: Graceful Transition

1. **Deploy new keys** without changing JWT_KEY_ID
   - Old tokens still validate with old key
   - System continues working

2. **Update JWT_KEY_ID** to new value (e.g., `key-2025-11`)
   - New tokens use new key
   - Old tokens still valid until expiry (10 minutes)

3. **Wait for all old tokens to expire** (15 minutes to be safe)

4. **Remove old key** from public_keys dictionary

### Step 4: Cleanup Old Keys

```bash
# Archive old keys (don't delete immediately)
mv /root/HydraX-v2/keys/jwt_private.pem /root/HydraX-v2/keys/archive/jwt_private_2025_10.pem
mv /root/HydraX-v2/keys/jwt_public.pem /root/HydraX-v2/keys/archive/jwt_public_2025_10.pem

# Rename new keys to active
mv /root/HydraX-v2/keys/jwt_private_new.pem /root/HydraX-v2/keys/jwt_private.pem
mv /root/HydraX-v2/keys/jwt_public_new.pem /root/HydraX-v2/keys/jwt_public.pem
```

## Important Safety Notes

### ✅ Safe Operations

- ✅ Adding new public keys for validation (backward compatible)
- ✅ Generating new key pairs in parallel
- ✅ Updating JWT_KEY_ID to use new signing key
- ✅ Archiving old keys after transition period

### ❌ Dangerous Operations

- ❌ Deleting old public keys immediately (breaks active tokens)
- ❌ Changing JWT_ALGORITHM without migration
- ❌ Modifying key files in place (use atomic rename)
- ❌ Rotating keys during high traffic (wait for off-peak)

## Rotation Schedule

**Recommended**: Rotate keys every 90 days

**Next Rotation**: Add reminder to rotate keys on:

- January 2026 (from October 2025)

## Emergency Key Compromise

If a private key is compromised:

1. **Immediately** change JWT_KEY_ID to new value
2. **Immediately** deploy new key pair
3. **Immediately** restart webapp to load new keys
4. **Immediately** invalidate all active mission sessions:

```sql
UPDATE mission_sessions SET status = 'EXPIRED' WHERE status = 'PENDING';
```

5. **Notify users** that they need new mission links

## Testing Key Rotation

```bash
# Test token validation with old and new keys
python3 /root/HydraX-v2/src/security/jwt_manager.py

# Expected: Both old and new key IDs validate correctly
```

## Monitoring

- Watch for JWT validation errors in webapp logs
- Monitor mission session creation rate (should not drop during rotation)
- Check that expired sessions are cleaned up (via session_cleanup daemon)
