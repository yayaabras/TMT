# Taxi Tracker - Raspberry Pi 5 Deployment

This Flask application helps taxi drivers track their income, expenses, and generate reports.

## Features
- User authentication and registration
- Vehicle management
- Income tracking with trip details
- Expense tracking with categories
- Monthly reports and analytics
- Excel report generation
- Responsive web interface

## Prerequisites for Raspberry Pi 5

### Hardware Requirements
- Raspberry Pi 5 (4GB+ RAM recommended)
- MicroSD card (32GB+ recommended)
- Stable internet connection

### Software Requirements
- Raspberry Pi OS (Bookworm or later)
- Python 3.9+
- Git

## Deployment Instructions

### Method 1: Automatic Deployment (Recommended)

1. **Transfer files to your Raspberry Pi:**
   ```bash
   # On your Pi, clone or copy the project files
   git clone <your-repo> /home/pi/TFL
   # OR use SCP to copy files from your Windows machine
   ```

2. **Make the deployment script executable:**
   ```bash
   cd /home/pi/TFL
   chmod +x deploy.sh
   ```

3. **Run the deployment script:**
   ```bash
   ./deploy.sh
   ```

The script will automatically:
- Update system packages
- Install dependencies
- Create a Python virtual environment
- Install Python packages
- Set up the database
- Configure systemd service
- Optionally configure Nginx

### Method 2: Manual Deployment

1. **Update your Raspberry Pi:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install system dependencies:**
   ```bash
   sudo apt install -y python3 python3-pip python3-venv nginx git
   ```

3. **Set up the project:**
   ```bash
   cd /home/pi
   # Copy your project files here
   cd TFL
   ```

4. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. **Set up environment variables:**
   ```bash
   # Edit .env file with your production settings
   nano .env
   ```

7. **Initialize database:**
   ```bash
   python3 -c "from app import create_tables; create_tables()"
   ```

8. **Set up systemd service:**
   ```bash
   sudo cp taxi-tracker.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable taxi-tracker
   sudo systemctl start taxi-tracker
   ```

## Accessing the Application

After deployment, you can access the application at:
- **Direct access:** `http://<your-pi-ip>:5000`
- **With Nginx:** `http://<your-pi-ip>`

To find your Pi's IP address:
```bash
hostname -I
```

## Managing the Service

- **Check status:** `sudo systemctl status taxi-tracker`
- **Start service:** `sudo systemctl start taxi-tracker`
- **Stop service:** `sudo systemctl stop taxi-tracker`
- **Restart service:** `sudo systemctl restart taxi-tracker`
- **View logs:** `sudo journalctl -u taxi-tracker -f`

## Configuration

### Environment Variables (.env)
- `SECRET_KEY`: Flask secret key for sessions
- `FLASK_ENV`: Set to 'production' for Pi deployment
- `DATABASE_URI`: SQLite database path
- `HOST`: Bind address (0.0.0.0 for external access)
- `PORT`: Port number (default: 5000)

### Security Considerations
1. Change the default secret key in `.env`
2. Consider setting up SSL/HTTPS for production
3. Configure firewall rules if needed
4. Keep your Pi updated with security patches

## Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo journalctl -u taxi-tracker -n 50
   ```

2. **Database issues:**
   ```bash
   cd /home/pi/TFL
   source venv/bin/activate
   python3 -c "from app import create_tables; create_tables()"
   ```

3. **Permission issues:**
   ```bash
   sudo chown -R pi:pi /home/pi/TFL
   ```

4. **Port already in use:**
   ```bash
   sudo netstat -tlnp | grep :5000
   sudo kill <process-id>
   ```

### Performance Tips for Pi 5
- Use a fast MicroSD card (Class 10 or better)
- Consider using an SSD via USB for better performance
- Monitor CPU and memory usage: `htop`
- Adjust worker count in systemd service based on usage

## Development on Pi

To make changes and restart the service:
```bash
cd /home/pi/TFL
# Make your changes
sudo systemctl restart taxi-tracker
```

## Backup

Regular backup of your database:
```bash
cp /home/pi/TFL/instance/taxi_tracker.db /home/pi/backups/taxi_tracker_$(date +%Y%m%d).db
```
