import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Email the EA file
def email_ea(to_email):
    msg = MIMEMultipart()
    msg['Subject'] = 'BITTEN EA v3 Enhanced'
    msg['From'] = 'bitten@yourserver.com'
    msg['To'] = to_email
    
    # Attach EA file
    with open('/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5', 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="BITTENBridge_v3_ENHANCED.mq5"')
        msg.attach(part)
    
    # Add instructions
    body = """
    BITTEN EA Installation:
    1. Save the attached file
    2. Copy to: C:\\Users\\[YourUser]\\AppData\\Roaming\\MetaQuotes\\Terminal\\[ID]\\MQL5\\Experts\\
    3. Open MT5, press F4 for MetaEditor
    4. Compile with F7
    """
    msg.attach(MIMEText(body, 'plain'))
    
    # Send (configure SMTP as needed)
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    # server.send_message(msg)
    
print("Email function ready - configure SMTP settings to use")