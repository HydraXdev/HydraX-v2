"""
Secure Credential Delivery System

Handles secure delivery of demo account credentials to users via
multiple channels with proper encryption and audit logging.
"""

import asyncio
import logging
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import qrcode
import io
import base64
from cryptography.fernet import Fernet

from ...database.connection import get_async_db
from .demo_account_service import CredentialEncryption

logger = logging.getLogger(__name__)

class DeliveryMethod(Enum):
    """Supported credential delivery methods"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    API = "api"
    QR_CODE = "qr_code"
    SECURE_LINK = "secure_link"

class DeliveryStatus(Enum):
    """Credential delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    VIEWED = "viewed"
    EXPIRED = "expired"
    FAILED = "failed"

@dataclass
class CredentialPackage:
    """Secure credential package for delivery"""
    delivery_id: str
    user_id: str
    account_number: str
    encrypted_credentials: str
    delivery_method: DeliveryMethod
    expires_at: datetime
    one_time_token: str

class SecureCredentialDelivery:
    """Manages secure delivery of demo account credentials"""
    
    def __init__(self):
        self.encryption = CredentialEncryption()
        self.delivery_expiry_minutes = 30  # Credentials expire after 30 minutes
        
    async def prepare_credentials(self, user_id: str, account_data: Dict[str, Any],
                                delivery_method: DeliveryMethod) -> CredentialPackage:
        """Prepare credentials for secure delivery"""
        try:
            # Generate delivery ID and one-time token
            delivery_id = self._generate_delivery_id()
            one_time_token = secrets.token_urlsafe(32)
            
            # Create credential payload
            credential_payload = {
                'account_number': account_data['account_number'],
                'password': account_data['password'],
                'server': account_data['server'],
                'platform': 'MetaTrader 5',
                'expires_at': account_data['expires_at']
            }
            
            # Encrypt credentials with delivery-specific key
            delivery_key = self._generate_delivery_key(delivery_id, one_time_token)
            encrypted_credentials = self._encrypt_payload(credential_payload, delivery_key)
            
            # Create package
            package = CredentialPackage(
                delivery_id=delivery_id,
                user_id=user_id,
                account_number=account_data['account_number'],
                encrypted_credentials=encrypted_credentials,
                delivery_method=delivery_method,
                expires_at=datetime.utcnow() + timedelta(minutes=self.delivery_expiry_minutes),
                one_time_token=one_time_token
            )
            
            # Store delivery record
            await self._store_delivery_record(package)
            
            return package
            
        except Exception as e:
            logger.error(f"Error preparing credentials: {e}")
            raise
            
    async def deliver_via_telegram(self, package: CredentialPackage, 
                                 telegram_user_id: str) -> Dict[str, Any]:
        """Deliver credentials via Telegram bot"""
        try:
            # Generate secure link
            secure_link = await self._generate_secure_link(package)
            
            # Create message with credentials
            message = self._format_telegram_message(package, secure_link)
            
            # TODO: Send via actual Telegram bot API
            # For now, store the message
            async with get_async_db() as conn:
                await conn.execute(
                    """
                    INSERT INTO credential_delivery_queue (
                        delivery_id, user_id, method, recipient,
                        message_content, status, created_at
                    ) VALUES ($1, $2, $3, $4, $5, 'pending', CURRENT_TIMESTAMP)
                    """,
                    package.delivery_id,
                    package.user_id,
                    'telegram',
                    telegram_user_id,
                    message
                )
                
            logger.info(f"Queued Telegram delivery for user {package.user_id}")
            
            return {
                'success': True,
                'delivery_id': package.delivery_id,
                'method': 'telegram',
                'expires_at': package.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Telegram delivery error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def deliver_via_email(self, package: CredentialPackage,
                              email_address: str) -> Dict[str, Any]:
        """Deliver credentials via secure email"""
        try:
            # Generate secure link
            secure_link = await self._generate_secure_link(package)
            
            # Create email content
            email_content = self._format_email_content(package, secure_link)
            
            # TODO: Send via actual email service (SendGrid, SES, etc)
            # For now, store in queue
            async with get_async_db() as conn:
                await conn.execute(
                    """
                    INSERT INTO credential_delivery_queue (
                        delivery_id, user_id, method, recipient,
                        message_content, status, created_at
                    ) VALUES ($1, $2, $3, $4, $5, 'pending', CURRENT_TIMESTAMP)
                    """,
                    package.delivery_id,
                    package.user_id,
                    'email',
                    email_address,
                    json.dumps(email_content)
                )
                
            logger.info(f"Queued email delivery for user {package.user_id}")
            
            return {
                'success': True,
                'delivery_id': package.delivery_id,
                'method': 'email',
                'expires_at': package.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email delivery error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def deliver_via_api(self, package: CredentialPackage) -> Dict[str, Any]:
        """Return credentials for API delivery"""
        try:
            # For API delivery, return encrypted package that can be decrypted
            # with the one-time token
            
            await self._update_delivery_status(package.delivery_id, DeliveryStatus.SENT)
            
            return {
                'success': True,
                'delivery_id': package.delivery_id,
                'encrypted_credentials': package.encrypted_credentials,
                'one_time_token': package.one_time_token,
                'expires_at': package.expires_at.isoformat(),
                'retrieval_endpoint': f'/api/v1/credentials/retrieve/{package.delivery_id}'
            }
            
        except Exception as e:
            logger.error(f"API delivery error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def generate_qr_code(self, package: CredentialPackage) -> Dict[str, Any]:
        """Generate QR code for credential delivery"""
        try:
            # Create QR data with secure link
            secure_link = await self._generate_secure_link(package)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(secure_link)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            await self._update_delivery_status(package.delivery_id, DeliveryStatus.SENT)
            
            return {
                'success': True,
                'delivery_id': package.delivery_id,
                'qr_code': f'data:image/png;base64,{qr_base64}',
                'secure_link': secure_link,
                'expires_at': package.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"QR code generation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def retrieve_credentials(self, delivery_id: str, 
                                 one_time_token: str) -> Optional[Dict[str, Any]]:
        """Retrieve credentials using delivery ID and one-time token"""
        try:
            async with get_async_db() as conn:
                # Get delivery record
                record = await conn.fetchrow(
                    """
                    SELECT user_id, account_number, encrypted_credentials,
                           expires_at, status, view_count
                    FROM credential_deliveries
                    WHERE delivery_id = $1
                      AND one_time_token_hash = $2
                    """,
                    delivery_id,
                    hashlib.sha256(one_time_token.encode()).hexdigest()
                )
                
                if not record:
                    logger.warning(f"Invalid delivery attempt: {delivery_id}")
                    return None
                    
                # Check if expired
                if record['expires_at'] < datetime.utcnow():
                    await self._update_delivery_status(delivery_id, DeliveryStatus.EXPIRED)
                    return None
                    
                # Check if already viewed (one-time use)
                if record['view_count'] > 0:
                    logger.warning(f"Attempted reuse of delivery: {delivery_id}")
                    return None
                    
                # Decrypt credentials
                delivery_key = self._generate_delivery_key(delivery_id, one_time_token)
                decrypted = self._decrypt_payload(record['encrypted_credentials'], delivery_key)
                
                # Update status and view count
                await conn.execute(
                    """
                    UPDATE credential_deliveries
                    SET status = 'viewed',
                        view_count = view_count + 1,
                        viewed_at = CURRENT_TIMESTAMP
                    WHERE delivery_id = $1
                    """,
                    delivery_id
                )
                
                # Log access
                await self._log_credential_access(
                    delivery_id,
                    record['user_id'],
                    'successful_retrieval'
                )
                
                return decrypted
                
        except Exception as e:
            logger.error(f"Credential retrieval error: {e}")
            await self._log_credential_access(
                delivery_id,
                'unknown',
                f'retrieval_failed: {str(e)}'
            )
            return None
            
    async def _generate_secure_link(self, package: CredentialPackage) -> str:
        """Generate secure one-time link for credential retrieval"""
        base_url = "https://app.bitten.com/credentials"  # TODO: Configure base URL
        return f"{base_url}/retrieve/{package.delivery_id}?token={package.one_time_token}"
        
    def _generate_delivery_id(self) -> str:
        """Generate unique delivery ID"""
        timestamp = int(datetime.utcnow().timestamp())
        random_part = secrets.token_hex(8)
        return f"DEL{timestamp}{random_part}"
        
    def _generate_delivery_key(self, delivery_id: str, one_time_token: str) -> bytes:
        """Generate encryption key for specific delivery"""
        combined = f"{delivery_id}:{one_time_token}:bitten-delivery-2025"
        return base64.urlsafe_b64encode(hashlib.sha256(combined.encode()).digest())
        
    def _encrypt_payload(self, payload: Dict[str, Any], key: bytes) -> str:
        """Encrypt credential payload"""
        f = Fernet(key)
        json_payload = json.dumps(payload)
        encrypted = f.encrypt(json_payload.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
        
    def _decrypt_payload(self, encrypted: str, key: bytes) -> Dict[str, Any]:
        """Decrypt credential payload"""
        f = Fernet(key)
        decoded = base64.urlsafe_b64decode(encrypted.encode())
        decrypted = f.decrypt(decoded)
        return json.loads(decrypted.decode())
        
    def _format_telegram_message(self, package: CredentialPackage, 
                               secure_link: str) -> str:
        """Format Telegram message with credentials"""
        return f"""
🎯 **BITTEN Demo Account Ready!**

Your MetaTrader 5 demo account has been provisioned.

**Account Number:** `{package.account_number}`

🔐 **Secure Credentials Link:**
{secure_link}

⏰ **Important:** This link expires in 30 minutes and can only be used once.

**Quick Start:**
1. Click the secure link to view your password
2. Download MetaTrader 5
3. Select "BITTEN-Demo" server
4. Login with your credentials

💡 **Tip:** Save your credentials securely before the link expires!

Need help? Contact @BITTENSupport
"""
        
    def _format_email_content(self, package: CredentialPackage,
                            secure_link: str) -> Dict[str, str]:
        """Format email content with credentials"""
        return {
            'subject': 'Your BITTEN Demo Account is Ready!',
            'html_body': f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1a1a1a; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f5f5f5; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
        .warning {{ background-color: #fff3cd; border: 1px solid #ffeeba; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BITTEN Demo Account</h1>
        </div>
        <div class="content">
            <h2>Your demo account is ready!</h2>
            
            <p>Account Number: <strong>{package.account_number}</strong></p>
            
            <div class="warning">
                <strong>⏰ Time Sensitive:</strong> Your secure credentials link expires in 30 minutes and can only be accessed once.
            </div>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{secure_link}" class="button">View Secure Credentials</a>
            </p>
            
            <h3>Getting Started:</h3>
            <ol>
                <li>Click the button above to securely view your password</li>
                <li>Download MetaTrader 5 from your app store</li>
                <li>Select "BITTEN-Demo" as your server</li>
                <li>Login with your account number and password</li>
            </ol>
            
            <p>Your demo account includes $50,000 in practice funds and expires in 30 days.</p>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                This is an automated message from BITTEN Trading. Please do not reply to this email.
                For support, visit our help center or contact support@bitten.com
            </p>
        </div>
    </div>
</body>
</html>
""",
            'text_body': f"""
BITTEN Demo Account Ready!

Your MetaTrader 5 demo account has been provisioned.

Account Number: {package.account_number}

View your secure credentials here:
{secure_link}

IMPORTANT: This link expires in 30 minutes and can only be used once.

Getting Started:
1. Click the link to view your password
2. Download MetaTrader 5
3. Select "BITTEN-Demo" server
4. Login with your credentials

Your demo account includes $50,000 in practice funds.

Need help? Visit support.bitten.com
"""
        }
        
    async def _store_delivery_record(self, package: CredentialPackage):
        """Store credential delivery record"""
        async with get_async_db() as conn:
            await conn.execute(
                """
                INSERT INTO credential_deliveries (
                    delivery_id, user_id, account_number,
                    encrypted_credentials, one_time_token_hash,
                    delivery_method, expires_at, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending')
                """,
                package.delivery_id,
                package.user_id,
                package.account_number,
                package.encrypted_credentials,
                hashlib.sha256(package.one_time_token.encode()).hexdigest(),
                package.delivery_method.value,
                package.expires_at
            )
            
    async def _update_delivery_status(self, delivery_id: str, status: DeliveryStatus):
        """Update delivery status"""
        async with get_async_db() as conn:
            await conn.execute(
                """
                UPDATE credential_deliveries
                SET status = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE delivery_id = $2
                """,
                status.value,
                delivery_id
            )
            
    async def _log_credential_access(self, delivery_id: str, user_id: str, 
                                   action: str):
        """Log credential access for audit"""
        async with get_async_db() as conn:
            await conn.execute(
                """
                INSERT INTO credential_access_logs (
                    delivery_id, user_id, action, 
                    ip_address, user_agent, timestamp
                ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                """,
                delivery_id,
                user_id,
                action,
                '0.0.0.0',  # TODO: Get actual IP
                'Unknown'   # TODO: Get actual user agent
            )
            
    async def cleanup_expired_deliveries(self) -> int:
        """Clean up expired credential deliveries"""
        async with get_async_db() as conn:
            result = await conn.execute(
                """
                UPDATE credential_deliveries
                SET status = 'expired'
                WHERE expires_at < CURRENT_TIMESTAMP
                  AND status IN ('pending', 'sent')
                """
            )
            
            count = int(result.split()[-1])
            logger.info(f"Cleaned up {count} expired credential deliveries")
            return count

# Create required tables if they don't exist
async def create_delivery_tables():
    """Create credential delivery tables"""
    async with get_async_db() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS credential_deliveries (
                delivery_id VARCHAR(100) PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                account_number VARCHAR(50) NOT NULL,
                encrypted_credentials TEXT NOT NULL,
                one_time_token_hash VARCHAR(64) NOT NULL,
                delivery_method VARCHAR(20) NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                view_count INTEGER DEFAULT 0,
                viewed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_delivery_user (user_id),
                INDEX idx_delivery_expires (expires_at),
                INDEX idx_delivery_status (status)
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS credential_delivery_queue (
                queue_id BIGSERIAL PRIMARY KEY,
                delivery_id VARCHAR(100) NOT NULL,
                user_id VARCHAR(50) NOT NULL,
                method VARCHAR(20) NOT NULL,
                recipient VARCHAR(255) NOT NULL,
                message_content TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                last_attempt_at TIMESTAMP WITH TIME ZONE,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_queue_status (status),
                INDEX idx_queue_created (created_at)
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS credential_access_logs (
                log_id BIGSERIAL PRIMARY KEY,
                delivery_id VARCHAR(100) NOT NULL,
                user_id VARCHAR(50),
                action VARCHAR(50) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_access_delivery (delivery_id),
                INDEX idx_access_timestamp (timestamp DESC)
            )
        """)