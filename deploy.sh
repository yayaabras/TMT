#!/bin/bash

# Deployment script for Taxi Tracker on Raspberry Pi 5
echo "=== Taxi Tracker Deployment Script for Raspberry Pi 5 ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}Warning: This script is designed for Raspberry Pi${NC}"
fi

# Update system
echo -e "${GREEN}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo -e "${GREEN}Installing system dependencies...${NC}"
sudo apt install -y python3 python3-pip python3-venv nginx git

# Create project directory
PROJECT_DIR="/home/pi/TFL"
echo -e "${GREEN}Setting up project directory: $PROJECT_DIR${NC}"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Create virtual environment
echo -e "${GREEN}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Installing Python packages...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create instance directory for database
mkdir -p instance
mkdir -p logs

# Set up environment variables
echo -e "${GREEN}Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')" > .env
    echo "FLASK_ENV=production" >> .env
    echo "DATABASE_URI=sqlite:///instance/taxi_tracker.db" >> .env
    echo "HOST=0.0.0.0" >> .env
    echo "PORT=5000" >> .env
fi

# Initialize database
echo -e "${GREEN}Initializing database...${NC}"
python3 -c "from app import create_tables; create_tables()"

# Set up systemd service
echo -e "${GREEN}Setting up systemd service...${NC}"
sudo cp taxi-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable taxi-tracker
sudo systemctl start taxi-tracker

# Configure Nginx (optional)
echo -e "${YELLOW}Do you want to configure Nginx as a reverse proxy? (y/n)${NC}"
read -r configure_nginx
if [[ $configure_nginx =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Configuring Nginx...${NC}"
    sudo tee /etc/nginx/sites-available/taxi-tracker > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $PROJECT_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    sudo ln -sf /etc/nginx/sites-available/taxi-tracker /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl restart nginx
fi

# Set proper permissions
echo -e "${GREEN}Setting file permissions...${NC}"
sudo chown -R pi:pi $PROJECT_DIR
chmod +x wsgi.py

# Display status
echo -e "${GREEN}Checking service status...${NC}"
sudo systemctl status taxi-tracker --no-pager

# Get Pi's IP address
PI_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Your Taxi Tracker app is now running on your Raspberry Pi 5${NC}"
echo -e "${GREEN}Access it at: http://$PI_IP:5000${NC}"
if [[ $configure_nginx =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Or via Nginx at: http://$PI_IP${NC}"
fi
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  - Check app status: sudo systemctl status taxi-tracker"
echo "  - Restart app: sudo systemctl restart taxi-tracker"
echo "  - View logs: sudo journalctl -u taxi-tracker -f"
echo "  - Stop app: sudo systemctl stop taxi-tracker"
echo ""
echo -e "${GREEN}To access from other devices on your network, use: http://$PI_IP:5000${NC}"
