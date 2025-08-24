# 🚖 TaxiTracker Pro

**Professional Taxi Fleet Management System**

A comprehensive, multi-tenant SaaS platform for managing taxi fleets, tracking income/expenses, managing drivers, and ensuring compliance. Built with Flask and modern web technologies.

![TaxiTracker Pro](https://img.shields.io/badge/Version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)
![Flask](https://img.shields.io/badge/Flask-2.3%2B-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

### 💼 **Multi-Tenant Business Management**
- **Company Management**: Full multi-tenant architecture supporting unlimited taxi companies
- **Role-Based Access**: Owner, Manager, and Driver roles with granular permissions
- **User Management**: Secure authentication with session tracking and audit logs

### 🚗 **Fleet Management**
- **Vehicle Tracking**: Complete vehicle lifecycle management
- **Maintenance Scheduling**: Automated service reminders and maintenance history
- **Insurance & Registration**: Automatic renewal alerts and compliance tracking
- **Real-time Fleet Status**: Monitor vehicle availability and utilization

### 💰 **Financial Management**
- **Income Tracking**: Multi-platform trip income with detailed analytics
- **Expense Management**: Categorized expense tracking with receipt management
- **Budget Planning**: Advanced budgeting with variance analysis and forecasting
- **Financial Reporting**: Comprehensive reports with trend analysis
- **Tax Compliance**: Tax-ready reports and automated calculations

### 👥 **Driver & Contract Management**
- **Employment Contracts**: Multiple contract types (rental, commission, hybrid, lease-to-own)
- **Performance Tracking**: Driver performance metrics and KPI monitoring
- **Automated Payroll**: Payroll calculation with tax withholding
- **Bonus Systems**: Performance-based bonus calculations

### 🔔 **Smart Notifications & Compliance**
- **Automated Alerts**: License renewals, insurance expiry, inspection due dates
- **Compliance Dashboard**: Centralized compliance monitoring
- **Custom Notifications**: Rule-based notification system
- **Scheduled Reports**: Automated report generation and delivery

### 📊 **Advanced Analytics & Reporting**
- **Interactive Dashboard**: Real-time KPIs and performance metrics
- **Custom Reports**: Advanced reporting with filtering and export options
- **Financial Forecasting**: Trend analysis and predictive modeling
- **Data Export**: CSV, Excel, PDF, and JSON export capabilities

### 🎯 **Customer Experience**
- **Guided Onboarding**: Step-by-step setup process for new companies
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices
- **Modern UI**: Clean, professional interface with intuitive navigation

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python) or PostgreSQL for production

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/TFL.git
   cd TFL
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python app.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

Visit `http://localhost:5000` to access the application.

### Docker Deployment

```bash
docker build -t taxitracker-pro .
docker run -p 5000:5000 taxitracker-pro
```

## 📖 User Guide

### Getting Started

1. **Company Registration**: Set up your taxi company profile
2. **Add Vehicles**: Register your fleet vehicles with maintenance schedules
3. **Create Driver Profiles**: Add drivers with license and contract information
4. **Start Tracking**: Begin recording income and expenses
5. **Monitor Performance**: Use dashboards and reports to track business performance

### User Roles

#### 🏢 **Owner**
- Full system access
- Company management
- Financial oversight
- User management
- System configuration

#### 👨‍💼 **Manager**
- Fleet management
- Driver supervision
- Report generation
- Contract management
- Compliance monitoring

#### 🚗 **Driver**
- Personal income/expense tracking
- Vehicle assignment
- Profile management
- Performance viewing

## 🛠️ Configuration

### Environment Variables

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///taxi_tracker.db

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Security
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
```

### Database Configuration

The application supports both SQLite (development) and PostgreSQL (production):

```python
# config.py
DATABASES = {
    'development': 'sqlite:///taxi_tracker.db',
    'production': 'postgresql://username:password@localhost/taxitracker'
}
```

## 🏗️ Architecture

### Database Schema
- **Companies**: Multi-tenant company data
- **Users**: User accounts with role-based access
- **Vehicles**: Fleet vehicle information and tracking
- **Contracts**: Employment contracts and terms
- **Income/Expenses**: Financial transaction records
- **Notifications**: Alert and notification system
- **Audit Logs**: Security and compliance logging

### Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Charts**: Chart.js for data visualization
- **Icons**: Lucide Icons
- **Authentication**: Flask-Login
- **Forms**: WTForms (optional)

## 📊 API Reference

### Authentication
```bash
POST /login
POST /register
POST /logout
```

### Fleet Management
```bash
GET /api/vehicles
POST /api/vehicles
PUT /api/vehicles/{id}
DELETE /api/vehicles/{id}
```

### Financial Data
```bash
GET /api/income
POST /api/income
GET /api/expenses
POST /api/expenses
GET /api/financial-summary
```

### Reports
```bash
GET /api/reports/financial
GET /api/reports/driver-performance
GET /api/reports/compliance
```

## 🔧 Development

### Project Structure
```
TFL/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   └── utils/
├── templates/
│   ├── auth/
│   ├── dashboard/
│   ├── fleet/
│   └── reports/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── instance/
├── tests/
├── app.py
├── config.py
├── requirements.txt
└── README.md
```

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
```bash
# Format code
black app.py

# Lint code
flake8 app.py
```

## 🚀 Deployment

### Production Deployment

1. **Prepare environment**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=your-production-db-url
   ```

2. **Use Gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:5000 wsgi:app
   ```

3. **Nginx Configuration**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Raspberry Pi Deployment

See [README_PI_DEPLOYMENT.md](README_PI_DEPLOYMENT.md) for detailed Raspberry Pi setup instructions.

## 📈 Roadmap

### Upcoming Features
- [ ] **API Integrations**: QuickBooks, Xero accounting software
- [ ] **Mobile App**: Native iOS/Android applications
- [ ] **GPS Tracking**: Real-time vehicle location tracking
- [ ] **Customer Management**: Customer database and trip history
- [ ] **Advanced Analytics**: Machine learning insights
- [ ] **Multi-language Support**: Internationalization
- [ ] **Payment Processing**: Integrated payment systems

### Version History
- **v2.0.0** - Multi-tenant SaaS platform with full fleet management
- **v1.0.0** - Basic income/expense tracking application

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [User Manual](docs/user-manual.md)
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)

### Community
- [GitHub Issues](https://github.com/yourusername/TFL/issues)
- [Discussions](https://github.com/yourusername/TFL/discussions)

### Commercial Support
For enterprise support and custom development, contact: support@taxitracker.pro

## 🙏 Acknowledgments

- Flask community for the excellent web framework
- Chart.js for beautiful data visualizations
- Tailwind CSS for the utility-first CSS framework
- Lucide Icons for the comprehensive icon set
- All contributors who have helped improve this project

## 📊 Statistics

![GitHub stars](https://img.shields.io/github/stars/yourusername/TFL.svg)
![GitHub forks](https://img.shields.io/github/forks/yourusername/TFL.svg)
![GitHub issues](https://img.shields.io/github/issues/yourusername/TFL.svg)
![GitHub license](https://img.shields.io/github/license/yourusername/TFL.svg)

---

**Made with ❤️ for taxi fleet operators worldwide**

*Transform your taxi business with professional fleet management tools.*