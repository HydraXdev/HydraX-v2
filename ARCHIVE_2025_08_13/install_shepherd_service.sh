#!/bin/bash
# Install SHEPHERD as a systemd service

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Installing SHEPHERD systemd service...${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}" 
   exit 1
fi

# Copy service file
cp /root/HydraX-v2/shepherd.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable shepherd.service

echo -e "${GREEN}SHEPHERD service installed successfully!${NC}"
echo -e "${YELLOW}To start the service, run:${NC}"
echo "  systemctl start shepherd"
echo ""
echo -e "${YELLOW}To check status:${NC}"
echo "  systemctl status shepherd"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo "  journalctl -u shepherd -f"