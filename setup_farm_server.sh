#!/bin/bash
# BITTEN MT5 Farm Server Setup Script
# Run this on the farm server (129.212.185.102)

echo "🚀 BITTEN MT5 Farm Server Setup"
echo "================================"

# Add SSH key for main server
echo "📝 Setting up SSH access from main server..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add the public key
cat >> ~/.ssh/authorized_keys << 'EOF'
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDOunIdMiizmOTRy3QPctWm3uXEtNMxgogdeTgcucH9fZBW1xkVIGubDzsHoPx5vk6LqNbe+Jra2UVb9wkObaZXmZV6bPkMAvmTuFgynfSo28wHD5gpUXYmVXBus8fRya+K0L8ZZWx4iQpYu0SVkHkoqGZbEsWj0jTxxc4odYiVRTdl5xbUzHHRtSd2coorUJoqAYu3sWDAvSZUmoyxzVdDAWkcqd7H+cHzC6d2K3paSLMF+G23gTPcjyol/SngfEKMzz779Sij4CMdeFMgjzFWOu1q+HYnCwO7xj6ZYkqOTzbN4HwRCYHfi2Gqe68IQ7CuZkBO2GNT+9eH3i4nkWOOQMmPCBxvKsSX1lOQHMVOZePiHSJ4ryxIc+u5FVV3khzo9xGW7giW7hGmG3rIAtWWW3DinuZ7yCfxxH8bUgdv/nqAqgwdzL0Y9z6TLmbCumQJ/+4vC8V8w0NfAayKcUOLNQI9yetoL1NoQCwdhbvMOnhoXAljLhFdGEpARr1QkzDlwtgsM0c+DNrXMFhv+R0jGiJqRs/evl26AeQowvisNFDcALqa4p/2oor9Qw1Xl+ReFxsw8BmwcqCHUwUwL0pEJTVhh2zf4h6lagXA8Mio7KYSXCvyyjPRt/4uVxU+GXePKEZ55SX1mURgiJxzjseHvCHMu/4pcktx/xQ1VdhvQQ== bitten-main-to-farm
EOF

chmod 600 ~/.ssh/authorized_keys

# Check SSH daemon config
echo "🔧 Checking SSH configuration..."
if ! grep -q "^PubkeyAuthentication yes" /etc/ssh/sshd_config; then
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
    echo "Added PubkeyAuthentication yes"
fi

if ! grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config; then
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
    echo "Added PermitRootLogin yes"
fi

# Restart SSH service
echo "🔄 Restarting SSH service..."
systemctl restart sshd || service ssh restart

echo "✅ SSH setup complete!"
echo ""
echo "📦 Installing Docker..."
# Install Docker if not present
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker installed!"
else
    echo "✅ Docker already installed"
fi

echo ""
echo "🐍 Installing Python and dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx

echo ""
echo "📁 Creating directory structure..."
mkdir -p /mt5/{broker1,broker2,broker3}/Files/BITTEN
mkdir -p /backups/daily
mkdir -p /var/log/bitten

echo ""
echo "✅ Basic setup complete!"
echo "The main server should now be able to connect via SSH"
echo "Next steps: Deploy MT5 containers and API server"