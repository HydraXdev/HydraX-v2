"""
Email Service Integration for BITTEN Press Pass Campaign
Supports multiple email providers: SMTP, SendGrid, AWS SES
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional, Any
import jinja2
from pathlib import Path

# Optional imports for email providers
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_SES_AVAILABLE = True
except ImportError:
    AWS_SES_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Custom exception for email service errors"""
    pass


class EmailService:
    """Base email service class"""
    
    def __init__(self, provider: str = "smtp"):
        self.provider = provider.lower()
        self.from_email = os.getenv("EMAIL_FROM", "noreply@bitten.trading")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "BITTEN Trading")
        
        # Initialize template engine
        template_dir = Path(__file__).parent.parent.parent / "templates" / "emails"
        self.template_loader = jinja2.FileSystemLoader(str(template_dir))
        self.template_env = jinja2.Environment(loader=self.template_loader)
        
        # Initialize provider
        if self.provider == "smtp":
            self._init_smtp()
        elif self.provider == "sendgrid" and SENDGRID_AVAILABLE:
            self._init_sendgrid()
        elif self.provider == "ses" and AWS_SES_AVAILABLE:
            self._init_ses()
        else:
            raise EmailServiceError(f"Unsupported email provider: {provider}")
    
    def _init_smtp(self):
        """Initialize SMTP configuration"""
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        if not self.smtp_username or not self.smtp_password:
            raise EmailServiceError("SMTP credentials not configured")
    
    def _init_sendgrid(self):
        """Initialize SendGrid configuration"""
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")
        if not self.sendgrid_api_key:
            raise EmailServiceError("SendGrid API key not configured")
        self.sg_client = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
    
    def _init_ses(self):
        """Initialize AWS SES configuration"""
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.ses_client = boto3.client('ses', region_name=self.aws_region)
    
    def send_email(self, 
                   to_email: str,
                   subject: str,
                   html_content: str,
                   text_content: Optional[str] = None,
                   attachments: Optional[List[Dict[str, Any]]] = None,
                   tracking_data: Optional[Dict[str, Any]] = None) -> bool:
        """Send email using configured provider"""
        try:
            if self.provider == "smtp":
                return self._send_smtp(to_email, subject, html_content, text_content, attachments)
            elif self.provider == "sendgrid":
                return self._send_sendgrid(to_email, subject, html_content, text_content, attachments, tracking_data)
            elif self.provider == "ses":
                return self._send_ses(to_email, subject, html_content, text_content, attachments)
            else:
                raise EmailServiceError(f"Unknown provider: {self.provider}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _send_smtp(self, to_email: str, subject: str, html_content: str, 
                   text_content: Optional[str] = None, 
                   attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Send email via SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email
        
        # Add text and HTML parts
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Add attachments if any
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={attachment["filename"]}')
                msg.attach(part)
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
    
    def _send_sendgrid(self, to_email: str, subject: str, html_content: str,
                       text_content: Optional[str] = None,
                       attachments: Optional[List[Dict[str, Any]]] = None,
                       tracking_data: Optional[Dict[str, Any]] = None) -> bool:
        """Send email via SendGrid"""
        message = Mail(
            from_email=Email(self.from_email, self.from_name),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        if text_content:
            message.plain_text_content = Content("text/plain", text_content)
        
        # Add tracking data
        if tracking_data:
            message.tracking_settings = {
                "click_tracking": {"enable": True},
                "open_tracking": {"enable": True}
            }
            message.custom_args = tracking_data
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                encoded_content = base64.b64encode(attachment['content']).decode()
                message.add_attachment(
                    encoded_content,
                    attachment.get('type', 'application/octet-stream'),
                    attachment['filename']
                )
        
        try:
            response = self.sg_client.send(message)
            logger.info(f"SendGrid email sent: {response.status_code}")
            return response.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return False
    
    def _send_ses(self, to_email: str, subject: str, html_content: str,
                  text_content: Optional[str] = None,
                  attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Send email via AWS SES"""
        try:
            # Create message
            message = {
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': html_content}}
            }
            
            if text_content:
                message['Body']['Text'] = {'Data': text_content}
            
            # Send email
            response = self.ses_client.send_email(
                Source=f"{self.from_name} <{self.from_email}>",
                Destination={'ToAddresses': [to_email]},
                Message=message
            )
            
            logger.info(f"SES email sent: {response['MessageId']}")
            return True
        except ClientError as e:
            logger.error(f"AWS SES error: {e.response['Error']['Message']}")
            return False
    
    def send_template_email(self, 
                           to_email: str,
                           template_name: str,
                           template_data: Dict[str, Any],
                           subject: Optional[str] = None,
                           tracking_data: Optional[Dict[str, Any]] = None) -> bool:
        """Send email using template"""
        try:
            # Load and render template
            template = self.template_env.get_template(template_name)
            html_content = template.render(**template_data)
            
            # Extract subject from template if not provided
            if not subject and 'subject' in template_data:
                subject = template_data['subject']
            elif not subject:
                subject = "BITTEN Trading Update"
            
            # Send email
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                tracking_data=tracking_data
            )
        except Exception as e:
            logger.error(f"Template email error: {str(e)}")
            return False
    
    def send_batch_emails(self, 
                         recipients: List[Dict[str, Any]],
                         template_name: str,
                         default_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send batch emails to multiple recipients"""
        results = {}
        
        for recipient in recipients:
            email = recipient.get('email')
            if not email:
                continue
            
            # Merge recipient data with defaults
            template_data = {**default_data, **recipient.get('data', {})}
            
            # Send email
            success = self.send_template_email(
                to_email=email,
                template_name=template_name,
                template_data=template_data,
                tracking_data=recipient.get('tracking_data')
            )
            
            results[email] = success
        
        return results


class EmailQueueManager:
    """Manages email queue for scheduled sending"""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
        self.queue = []
    
    def add_to_queue(self, 
                     to_email: str,
                     template_name: str,
                     template_data: Dict[str, Any],
                     send_at: datetime,
                     priority: int = 5):
        """Add email to queue"""
        self.queue.append({
            'to_email': to_email,
            'template_name': template_name,
            'template_data': template_data,
            'send_at': send_at,
            'priority': priority,
            'status': 'pending'
        })
    
    def process_queue(self) -> Dict[str, int]:
        """Process pending emails in queue"""
        now = datetime.now()
        sent = 0
        failed = 0
        
        # Sort by priority and send time
        pending = [e for e in self.queue if e['status'] == 'pending' and e['send_at'] <= now]
        pending.sort(key=lambda x: (x['priority'], x['send_at']))
        
        for email in pending:
            success = self.email_service.send_template_email(
                to_email=email['to_email'],
                template_name=email['template_name'],
                template_data=email['template_data']
            )
            
            if success:
                email['status'] = 'sent'
                email['sent_at'] = now
                sent += 1
            else:
                email['status'] = 'failed'
                email['failed_at'] = now
                failed += 1
        
        return {'sent': sent, 'failed': failed}


# Factory function
def create_email_service(provider: Optional[str] = None) -> EmailService:
    """Create email service instance"""
    if not provider:
        provider = os.getenv("EMAIL_PROVIDER", "smtp")
    
    return EmailService(provider)