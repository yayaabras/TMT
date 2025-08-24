# app.py
# Taxi Tracker Application

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
import csv
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
# import pandas as pd  # Temporarily disabled for frontend testing
import io
import os
from sqlalchemy import func, extract, and_, desc, case
from functools import wraps
from config import config

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config.get(config_name, config['default']))

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Enhanced Models for Production
class Company(db.Model):
    """Multi-tenant company/organization model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(50))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    tax_number = db.Column(db.String(50))
    subscription_tier = db.Column(db.String(20), default='starter')  # starter, professional, enterprise
    subscription_status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    vehicles = db.relationship('Vehicle', backref='company', lazy=True)
    contracts = db.relationship('EmploymentContract', backref='company', lazy=True)

class User(UserMixin, db.Model):
    """Enhanced user model with roles and company association"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    license_number = db.Column(db.String(50))
    license_expiry = db.Column(db.Date)
    role = db.Column(db.String(20), default='driver')  # owner, manager, driver
    is_active = db.Column(db.Boolean, default=True)
    hire_date = db.Column(db.Date)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cars = db.relationship('Car', backref='owner', lazy=True, cascade='all, delete-orphan')
    income_entries = db.relationship('Income', backref='user', lazy=True, cascade='all, delete-orphan')
    expense_entries = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    contracts = db.relationship('EmploymentContract', backref='driver', lazy=True)
    performance_records = db.relationship('DriverPerformance', backref='driver', lazy=True)
    
    def has_permission(self, permission):
        """Check if user has specific permission based on role"""
        role_permissions = {
            'owner': ['manage_all', 'view_all', 'edit_all', 'delete_all'],
            'manager': ['manage_drivers', 'view_reports', 'edit_contracts', 'view_finances'],
            'driver': ['view_own', 'edit_own_profile']
        }
        return permission in role_permissions.get(self.role, [])

class Vehicle(db.Model):
    """Enhanced vehicle model for fleet management"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Current driver
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    vin = db.Column(db.String(17), unique=True)
    license_plate = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(30))
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float)
    current_mileage = db.Column(db.Integer)
    fuel_type = db.Column(db.String(20))
    insurance_policy = db.Column(db.String(50))
    insurance_expiry = db.Column(db.Date)
    registration_expiry = db.Column(db.Date)
    last_service_date = db.Column(db.Date)
    next_service_due = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, maintenance, retired
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    income_entries = db.relationship('Income', backref='vehicle', lazy=True)
    expense_entries = db.relationship('Expense', backref='vehicle', lazy=True)
    maintenance_records = db.relationship('MaintenanceRecord', backref='vehicle', lazy=True)

# Keep Car model for backward compatibility
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    license_plate = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(30))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    income_entries = db.relationship('Income', backref='car', lazy=True)
    expense_entries = db.relationship('Expense', backref='car', lazy=True)

class EmploymentContract(db.Model):
    """Driver employment contracts"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contract_type = db.Column(db.String(50), nullable=False)  # monthly_rental, commission_only, hybrid, lease_to_own
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    monthly_fee = db.Column(db.Float, default=0)
    commission_rate = db.Column(db.Float, default=0)  # Percentage
    security_deposit = db.Column(db.Float, default=0)
    minimum_guarantee = db.Column(db.Float, default=0)
    bonus_threshold = db.Column(db.Float, default=0)
    bonus_rate = db.Column(db.Float, default=0)
    payment_schedule = db.Column(db.String(20), default='monthly')  # weekly, monthly
    auto_renew = db.Column(db.Boolean, default=False)
    terms_conditions = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, expired, terminated, pending
    signed_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('ContractPayment', backref='contract', lazy=True)

class DriverPerformance(db.Model):
    """Monthly driver performance tracking"""
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('employment_contract.id'), nullable=False)
    month = db.Column(db.Date, nullable=False)
    total_revenue = db.Column(db.Float, default=0)
    commission_earned = db.Column(db.Float, default=0)
    bonus_earned = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    net_payment = db.Column(db.Float, default=0)
    hours_worked = db.Column(db.Float, default=0)
    trips_completed = db.Column(db.Integer, default=0)
    customer_rating = db.Column(db.Float)
    fuel_efficiency = db.Column(db.Float)  # km per liter
    maintenance_costs = db.Column(db.Float, default=0)
    violations = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContractPayment(db.Model):
    """Contract payments and payroll"""
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('employment_contract.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # salary, commission, bonus, deposit_refund
    reference_period = db.Column(db.String(20))  # '2024-08' for monthly payments
    payment_method = db.Column(db.String(20), default='bank_transfer')
    transaction_id = db.Column(db.String(100))
    tax_withheld = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MaintenanceRecord(db.Model):
    """Vehicle maintenance tracking"""
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)  # service, repair, inspection
    description = db.Column(db.Text, nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    mileage_at_service = db.Column(db.Integer)
    cost = db.Column(db.Float, nullable=False)
    vendor = db.Column(db.String(100))
    next_service_due = db.Column(db.Date)
    parts_replaced = db.Column(db.Text)
    warranty_until = db.Column(db.Date)
    receipt_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='completed')  # scheduled, completed, overdue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ComplianceAlert(db.Model):
    """Compliance and renewal alerts"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # license_expiry, insurance_renewal, inspection_due
    entity_type = db.Column(db.String(20), nullable=False)  # driver, vehicle, company
    entity_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='active')  # active, dismissed, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=True)  # Made optional for backward compatibility
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=True)  # New vehicle reference
    amount = db.Column(db.Float, nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # Uber, Bolt, Street, etc.
    trip_type = db.Column(db.String(30), default='Regular')
    distance_km = db.Column(db.Float)
    duration_minutes = db.Column(db.Integer)
    start_location = db.Column(db.String(200))
    end_location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    date_recorded = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    time_recorded = db.Column(db.Time, default=datetime.utcnow().time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=True)  # Made optional for backward compatibility
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=True)  # New vehicle reference
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Fuel, Maintenance, Insurance, etc.
    subcategory = db.Column(db.String(50))  # More detailed categorization
    description = db.Column(db.String(200), nullable=False)
    receipt_number = db.Column(db.String(50))
    vendor = db.Column(db.String(100))
    payment_method = db.Column(db.String(20), default='cash')  # cash, card, bank_transfer
    is_tax_deductible = db.Column(db.Boolean, default=True)
    tax_category = db.Column(db.String(50))  # For tax reporting
    approval_status = db.Column(db.String(20), default='approved')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    receipt_image = db.Column(db.String(200))  # File path for receipt images
    notes = db.Column(db.Text)
    date_recorded = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserSession(db.Model):
    """User session tracking for security"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(255), nullable=False, unique=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    logout_time = db.Column(db.DateTime)

class Budget(db.Model):
    """Financial budgets and planning"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    budget_type = db.Column(db.String(20), nullable=False)  # monthly, quarterly, annual
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Budget targets
    target_revenue = db.Column(db.Float, default=0)
    target_expenses = db.Column(db.Float, default=0)
    target_profit = db.Column(db.Float, default=0)
    target_trips = db.Column(db.Integer, default=0)
    target_drivers = db.Column(db.Integer, default=0)
    
    # Actual performance (calculated)
    actual_revenue = db.Column(db.Float, default=0)
    actual_expenses = db.Column(db.Float, default=0)
    actual_profit = db.Column(db.Float, default=0)
    actual_trips = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FinancialForecast(db.Model):
    """Financial forecasting and predictions"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    forecast_type = db.Column(db.String(20), nullable=False)  # monthly, quarterly, annual
    
    # Forecasted metrics
    predicted_revenue = db.Column(db.Float, nullable=False)
    predicted_expenses = db.Column(db.Float, nullable=False)
    predicted_profit = db.Column(db.Float, nullable=False)
    confidence_level = db.Column(db.Float, default=0.8)  # 0.0 to 1.0
    
    # Forecast basis
    historical_months = db.Column(db.Integer, default=12)  # Number of months used for prediction
    growth_rate = db.Column(db.Float, default=0)  # Monthly growth rate
    seasonality_factor = db.Column(db.Float, default=1.0)  # Seasonal adjustment
    
    forecast_method = db.Column(db.String(50), default='trend_analysis')  # trend_analysis, moving_average, seasonal
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    """Audit trail for important actions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))  # user, contract, vehicle, etc.
    entity_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON string of old values
    new_values = db.Column(db.Text)  # JSON string of new values
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    """System notifications for users"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Null for company-wide notifications
    notification_type = db.Column(db.String(50), nullable=False)  # alert, reminder, info, warning, success
    category = db.Column(db.String(50), nullable=False)  # compliance, financial, maintenance, performance
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    action_url = db.Column(db.String(200))  # Optional link for actions
    action_text = db.Column(db.String(50))  # Text for action button
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    metadata = db.Column(db.Text)  # JSON for additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ScheduledReport(db.Model):
    """Scheduled automatic reports"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # financial_summary, driver_performance, etc.
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly, quarterly
    recipients = db.Column(db.Text, nullable=False)  # JSON array of email addresses
    filters = db.Column(db.Text)  # JSON object with report filters
    format = db.Column(db.String(20), default='pdf')  # pdf, excel, csv
    is_active = db.Column(db.Boolean, default=True)
    next_run = db.Column(db.DateTime, nullable=False)
    last_run = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NotificationRule(db.Model):
    """Automated notification rules"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    trigger_type = db.Column(db.String(50), nullable=False)  # date_based, threshold_based, event_based
    trigger_condition = db.Column(db.Text, nullable=False)  # JSON with condition details
    notification_template = db.Column(db.Text, nullable=False)  # JSON with notification content
    target_roles = db.Column(db.String(100))  # Comma-separated roles (owner,manager,driver)
    target_users = db.Column(db.Text)  # JSON array of specific user IDs
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_triggered = db.Column(db.DateTime)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Permission decorator
def requires_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_permission(permission):
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Helper functions
def get_monthly_summary(user_id=None, company_id=None, year=None, month=None):
    """Get monthly summary for dashboard - supports both user and company level"""
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    # Build base queries
    income_query = db.session.query(func.sum(Income.amount))
    expense_query = db.session.query(func.sum(Expense.amount))
    trips_query = Income.query
    
    # Apply filters based on scope
    if company_id:
        # Company-wide summary
        company_users = db.session.query(User.id).filter_by(company_id=company_id).subquery()
        income_query = income_query.filter(Income.user_id.in_(company_users))
        expense_query = expense_query.filter(Expense.user_id.in_(company_users))
        trips_query = trips_query.filter(Income.user_id.in_(company_users))
    elif user_id:
        # Individual user summary
        income_query = income_query.filter(Income.user_id == user_id)
        expense_query = expense_query.filter(Expense.user_id == user_id)
        trips_query = trips_query.filter(Income.user_id == user_id)
    else:
        # Default to current user
        if current_user.is_authenticated:
            if current_user.role in ['owner', 'manager']:
                company_id = current_user.company_id
                company_users = db.session.query(User.id).filter_by(company_id=company_id).subquery()
                income_query = income_query.filter(Income.user_id.in_(company_users))
                expense_query = expense_query.filter(Expense.user_id.in_(company_users))
                trips_query = trips_query.filter(Income.user_id.in_(company_users))
            else:
                user_id = current_user.id
                income_query = income_query.filter(Income.user_id == user_id)
                expense_query = expense_query.filter(Expense.user_id == user_id)
                trips_query = trips_query.filter(Income.user_id == user_id)
    
    # Apply date filters
    income_query = income_query.filter(
        extract('year', Income.date_recorded) == year,
        extract('month', Income.date_recorded) == month
    )
    expense_query = expense_query.filter(
        extract('year', Expense.date_recorded) == year,
        extract('month', Expense.date_recorded) == month
    )
    trips_query = trips_query.filter(
        extract('year', Income.date_recorded) == year,
        extract('month', Income.date_recorded) == month
    )
    
    # Execute queries
    total_income = income_query.scalar() or 0
    total_expenses = expense_query.scalar() or 0
    total_trips = trips_query.count()
    
    net_profit = total_income - total_expenses
    
    # Additional metrics for company summaries
    active_drivers = 0
    if company_id:
        active_drivers = User.query.filter_by(
            company_id=company_id, 
            is_active=True, 
            role='driver'
        ).count()
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'total_trips': total_trips,
        'active_drivers': active_drivers
    }

def create_company_join_code(company):
    """Generate a join code for drivers to join company"""
    return f"JOIN-{company.id}-{company.name[:3].upper()}"

def calculate_driver_payroll(contract, period_date):
    """Calculate payroll for a driver for a specific period"""
    # Get driver performance for the period
    performance = DriverPerformance.query.filter_by(
        driver_id=contract.driver_id,
        contract_id=contract.id,
        month=period_date
    ).first()
    
    # If no performance record, create default values
    if not performance:
        total_revenue = 0
        commission_earned = 0
        bonus_earned = 0
        existing_deductions = 0
    else:
        total_revenue = performance.total_revenue or 0
        commission_earned = performance.commission_earned or 0
        bonus_earned = performance.bonus_earned or 0
        existing_deductions = performance.deductions or 0
    
    # Calculate base payment based on contract type
    base_payment = 0
    calculated_commission = 0
    calculated_bonus = 0
    
    if contract.contract_type == 'monthly_rental':
        # Driver pays monthly fee to company, keeps rest of revenue
        base_payment = total_revenue - contract.monthly_fee
        
    elif contract.contract_type == 'commission_only':
        # Company takes commission percentage
        calculated_commission = total_revenue * (contract.commission_rate / 100)
        base_payment = total_revenue - calculated_commission
        
    elif contract.contract_type == 'hybrid':
        # Base salary minus commission to company
        calculated_commission = total_revenue * (contract.commission_rate / 100)
        base_payment = contract.monthly_fee + (total_revenue - calculated_commission)
        
    elif contract.contract_type == 'lease_to_own':
        # Similar to monthly rental but building equity
        base_payment = total_revenue - contract.monthly_fee
    
    # Apply minimum guarantee if applicable
    if contract.minimum_guarantee > 0 and base_payment < contract.minimum_guarantee:
        base_payment = contract.minimum_guarantee
    
    # Calculate bonus if applicable
    if contract.bonus_threshold > 0 and total_revenue > contract.bonus_threshold:
        excess_revenue = total_revenue - contract.bonus_threshold
        calculated_bonus = excess_revenue * (contract.bonus_rate / 100)
    
    # Total gross payment
    gross_payment = base_payment + calculated_bonus
    
    # Calculate tax withholding (simplified - 30% tax rate)
    tax_rate = 0.30
    tax_withheld = gross_payment * tax_rate if gross_payment > 0 else 0
    
    # Other deductions
    other_deductions = existing_deductions
    total_deductions = tax_withheld + other_deductions
    
    # Net payment
    net_payment = gross_payment - total_deductions
    
    return {
        'contract': contract,
        'driver': contract.driver,
        'period': period_date,
        'total_revenue': total_revenue,
        'base_payment': base_payment,
        'commission_to_company': calculated_commission,
        'bonus_earned': calculated_bonus,
        'gross_payment': gross_payment,
        'tax_withheld': tax_withheld,
        'other_deductions': other_deductions,
        'total_deductions': total_deductions,
        'net_payment': max(0, net_payment)  # Ensure non-negative
    }

def generate_compliance_alerts():
    """Generate compliance alerts for licenses, insurance, etc."""
    alerts = []
    
    # Driver license expiry alerts
    upcoming_expiry = datetime.now().date() + timedelta(days=30)
    drivers_with_expiring_licenses = User.query.filter(
        User.company_id == current_user.company_id,
        User.license_expiry.isnot(None),
        User.license_expiry <= upcoming_expiry,
        User.is_active == True
    ).all()
    
    for driver in drivers_with_expiring_licenses:
        alert = ComplianceAlert(
            company_id=current_user.company_id,
            alert_type='license_expiry',
            entity_type='driver',
            entity_id=driver.id,
            title=f'Driver License Expiring Soon',
            description=f'{driver.first_name} {driver.last_name} license expires on {driver.license_expiry}',
            due_date=driver.license_expiry,
            priority='high' if driver.license_expiry <= datetime.now().date() + timedelta(days=7) else 'medium'
        )
        alerts.append(alert)
    
    # Vehicle insurance expiry alerts
    vehicles_with_expiring_insurance = Vehicle.query.filter(
        Vehicle.company_id == current_user.company_id,
        Vehicle.insurance_expiry.isnot(None),
        Vehicle.insurance_expiry <= upcoming_expiry,
        Vehicle.is_active == True
    ).all()
    
    for vehicle in vehicles_with_expiring_insurance:
        alert = ComplianceAlert(
            company_id=current_user.company_id,
            alert_type='insurance_renewal',
            entity_type='vehicle',
            entity_id=vehicle.id,
            title=f'Vehicle Insurance Expiring',
            description=f'{vehicle.make} {vehicle.model} ({vehicle.license_plate}) insurance expires on {vehicle.insurance_expiry}',
            due_date=vehicle.insurance_expiry,
            priority='critical' if vehicle.insurance_expiry <= datetime.now().date() + timedelta(days=3) else 'high'
        )
        alerts.append(alert)
    
    # Vehicle service due alerts
    vehicles_needing_service = Vehicle.query.filter(
        Vehicle.company_id == current_user.company_id,
        Vehicle.next_service_due.isnot(None),
        Vehicle.next_service_due <= datetime.now().date(),
        Vehicle.is_active == True
    ).all()
    
    for vehicle in vehicles_needing_service:
        alert = ComplianceAlert(
            company_id=current_user.company_id,
            alert_type='service_due',
            entity_type='vehicle',
            entity_id=vehicle.id,
            title=f'Vehicle Service Due',
            description=f'{vehicle.make} {vehicle.model} ({vehicle.license_plate}) service was due on {vehicle.next_service_due}',
            due_date=vehicle.next_service_due,
            priority='medium'
        )
        alerts.append(alert)
    
    # Add alerts to database
    for alert in alerts:
        # Check if alert already exists
        existing_alert = ComplianceAlert.query.filter_by(
            company_id=alert.company_id,
            alert_type=alert.alert_type,
            entity_type=alert.entity_type,
            entity_id=alert.entity_id,
            status='active'
        ).first()
        
        if not existing_alert:
            db.session.add(alert)
    
    db.session.commit()
    return len(alerts)

def generate_financial_forecast(company_id, months_ahead):
    """Generate financial forecasts for specified number of months ahead"""
    forecasts = []
    
    # Get historical data for the last 12 months
    historical_data = []
    for i in range(12, 0, -1):
        date = (datetime.now() - timedelta(days=30 * i)).date()
        year = date.year
        month = date.month
        
        summary = get_monthly_summary(company_id=company_id, year=year, month=month)
        historical_data.append({
            'date': date,
            'revenue': summary['total_income'],
            'expenses': summary['total_expenses'],
            'profit': summary['net_profit'],
            'trips': summary['total_trips']
        })
    
    # Calculate trends
    if len(historical_data) >= 3:
        # Simple trend analysis
        recent_avg_revenue = sum(d['revenue'] for d in historical_data[-3:]) / 3
        older_avg_revenue = sum(d['revenue'] for d in historical_data[-6:-3]) / 3 if len(historical_data) >= 6 else recent_avg_revenue
        
        revenue_growth = (recent_avg_revenue - older_avg_revenue) / max(older_avg_revenue, 1) if older_avg_revenue > 0 else 0
        revenue_growth = max(-0.5, min(0.5, revenue_growth))  # Cap at ±50% growth
        
        # Similar for expenses
        recent_avg_expenses = sum(d['expenses'] for d in historical_data[-3:]) / 3
        older_avg_expenses = sum(d['expenses'] for d in historical_data[-6:-3]) / 3 if len(historical_data) >= 6 else recent_avg_expenses
        
        expense_growth = (recent_avg_expenses - older_avg_expenses) / max(older_avg_expenses, 1) if older_avg_expenses > 0 else 0
        expense_growth = max(-0.3, min(0.3, expense_growth))  # Cap at ±30% growth
    else:
        revenue_growth = 0
        expense_growth = 0
        recent_avg_revenue = sum(d['revenue'] for d in historical_data) / len(historical_data) if historical_data else 0
        recent_avg_expenses = sum(d['expenses'] for d in historical_data) / len(historical_data) if historical_data else 0
    
    # Generate forecasts for upcoming months
    for i in range(1, months_ahead + 1):
        forecast_date = (datetime.now() + timedelta(days=30 * i)).date()
        
        # Apply growth trend with seasonal adjustments
        seasonal_factor = 1.0
        month = forecast_date.month
        if month in [6, 7, 8]:  # Summer months - typically higher for taxi
            seasonal_factor = 1.15
        elif month in [12, 1]:  # Holiday months
            seasonal_factor = 1.10
        elif month in [2, 3]:  # Slower months
            seasonal_factor = 0.90
        
        predicted_revenue = recent_avg_revenue * (1 + revenue_growth) ** i * seasonal_factor
        predicted_expenses = recent_avg_expenses * (1 + expense_growth) ** i
        predicted_profit = predicted_revenue - predicted_expenses
        
        # Confidence decreases with distance
        confidence = max(0.5, 0.9 - (i * 0.1))
        
        forecasts.append({
            'date': forecast_date.isoformat(),
            'month_name': forecast_date.strftime('%B %Y'),
            'predicted_revenue': round(predicted_revenue, 2),
            'predicted_expenses': round(predicted_expenses, 2),
            'predicted_profit': round(predicted_profit, 2),
            'confidence': round(confidence, 2),
            'seasonal_factor': seasonal_factor,
            'growth_rate': revenue_growth
        })
    
    return forecasts

def calculate_budget_performance(budget):
    """Calculate actual performance against budget"""
    # Get actual data for budget period
    start_date = budget.period_start
    end_date = budget.period_end
    current_date = datetime.now().date()
    
    # Adjust end date if budget period is in the future
    actual_end_date = min(end_date, current_date)
    
    total_revenue = 0
    total_expenses = 0
    total_trips = 0
    
    # Calculate monthly totals within budget period
    current_month = start_date.replace(day=1)
    while current_month <= actual_end_date:
        month_summary = get_monthly_summary(
            company_id=budget.company_id,
            year=current_month.year,
            month=current_month.month
        )
        
        total_revenue += month_summary['total_income']
        total_expenses += month_summary['total_expenses']
        total_trips += month_summary['total_trips']
        
        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
    
    return {
        'revenue': total_revenue,
        'expenses': total_expenses,
        'profit': total_revenue - total_expenses,
        'trips': total_trips,
        'period_progress': min(1.0, (actual_end_date - start_date).days / (end_date - start_date).days)
    }

def log_user_action(user_id, action, entity_type=None, entity_id=None, old_values=None, new_values=None):
    """Helper function to log user actions for audit trail"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=request.remote_addr if request else None
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        print(f"Failed to log audit trail: {e}")

# def generate_excel_report(user_id, start_date, end_date):  # Disabled for frontend testing
    """Generate Excel report for given date range"""
    # Get income data
    income_data = db.session.query(
        Income.date_recorded,
        Income.amount,
        Income.platform,
        Income.trip_type,
        Income.distance_km,
        Income.duration_minutes,
        Income.start_location,
        Income.end_location,
        Car.make,
        Car.model,
        Car.license_plate
    ).join(Car).filter(
        Income.user_id == user_id,
        Income.date_recorded >= start_date,
        Income.date_recorded <= end_date
    ).all()
    
    # Get expense data
    expense_data = db.session.query(
        Expense.date_recorded,
        Expense.amount,
        Expense.category,
        Expense.description,
        Expense.vendor,
        Expense.is_tax_deductible,
        Car.make,
        Car.model,
        Car.license_plate
    ).join(Car).filter(
        Expense.user_id == user_id,
        Expense.date_recorded >= start_date,
        Expense.date_recorded <= end_date
    ).all()
    
    # Create DataFrames
    income_df = pd.DataFrame(income_data, columns=[
        'Date', 'Amount', 'Platform', 'Trip Type', 'Distance (km)', 
        'Duration (min)', 'Start Location', 'End Location', 
        'Car Make', 'Car Model', 'License Plate'
    ])
    
    expense_df = pd.DataFrame(expense_data, columns=[
        'Date', 'Amount', 'Category', 'Description', 'Vendor', 
        'Tax Deductible', 'Car Make', 'Car Model', 'License Plate'
    ])
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        income_df.to_excel(writer, sheet_name='Income', index=False)
        expense_df.to_excel(writer, sheet_name='Expenses', index=False)
        
        # Summary sheet
        summary_data = {
            'Metric': ['Total Income', 'Total Expenses', 'Net Profit', 'Total Trips'],
            'Amount': [
                income_df['Amount'].sum() if not income_df.empty else 0,
                expense_df['Amount'].sum() if not expense_df.empty else 0,
                (income_df['Amount'].sum() if not income_df.empty else 0) - 
                (expense_df['Amount'].sum() if not expense_df.empty else 0),
                len(income_df)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    return output

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        license_number = request.form.get('license_number')
        role = request.form.get('role', 'owner')  # Default to owner for new registrations
        
        # Company information (for new companies)
        company_name = request.form.get('company_name')
        company_registration = request.form.get('company_registration')
        company_address = request.form.get('company_address')
        company_city = request.form.get('company_city')
        company_country = request.form.get('company_country', 'Sweden')
        company_phone = request.form.get('company_phone')
        tax_number = request.form.get('tax_number')
        
        # Existing company (for joining existing company)
        existing_company_id = request.form.get('existing_company_id')
        join_code = request.form.get('join_code')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('auth/register.html')
        
        # Create or join company
        company = None
        if existing_company_id and join_code:
            # Join existing company
            company = Company.query.filter_by(id=existing_company_id).first()
            if not company or join_code != f"JOIN-{company.id}-{company.name[:3].upper()}":
                flash('Invalid company or join code.', 'error')
                return render_template('auth/register.html')
            role = 'driver'  # New users joining existing companies are drivers by default
        else:
            # Create new company
            if not company_name:
                flash('Company name is required.', 'error')
                return render_template('auth/register.html')
                
            company = Company(
                name=company_name,
                registration_number=company_registration,
                address=company_address,
                city=company_city,
                country=company_country,
                phone=company_phone,
                email=email,  # Company email same as owner email initially
                tax_number=tax_number
            )
            db.session.add(company)
            db.session.flush()  # Get company ID
        
        # Create new user
        user = User(
            company_id=company.id,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            license_number=license_number,
            role=role,
            hire_date=datetime.now().date()
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Log the registration
        audit_log = AuditLog(
            user_id=user.id,
            action='user_registered',
            entity_type='user',
            entity_id=user.id,
            new_values=f'{{"role": "{role}", "company_id": {company.id}}}',
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash(f'Registration successful! Welcome to {company.name}. Please log in.', 'success')
        return redirect(url_for('login'))
    
    # Get available companies for joining (optional feature)
    companies = Company.query.filter_by(subscription_status='active').all()
    return render_template('auth/register.html', companies=companies)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.first_name}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get appropriate summary based on user role
    if current_user.role in ['owner', 'manager']:
        # Company-wide dashboard
        current_summary = get_monthly_summary(company_id=current_user.company_id)
        recent_income = db.session.query(Income).join(User).filter(
            User.company_id == current_user.company_id
        ).order_by(Income.created_at.desc()).limit(10).all()
        recent_expenses = db.session.query(Expense).join(User).filter(
            User.company_id == current_user.company_id
        ).order_by(Expense.created_at.desc()).limit(10).all()
        
        # Additional company metrics
        company_metrics = {
            'total_drivers': User.query.filter_by(company_id=current_user.company_id, role='driver').count(),
            'active_contracts': EmploymentContract.query.filter_by(company_id=current_user.company_id, status='active').count(),
            'total_vehicles': Vehicle.query.filter_by(company_id=current_user.company_id, is_active=True).count(),
            'pending_alerts': ComplianceAlert.query.filter_by(company_id=current_user.company_id, status='active').count()
        }
    else:
        # Individual driver dashboard
        current_summary = get_monthly_summary(user_id=current_user.id)
        recent_income = Income.query.filter_by(user_id=current_user.id).order_by(Income.created_at.desc()).limit(5).all()
        recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.created_at.desc()).limit(5).all()
        company_metrics = {}
    
    return render_template('dashboard.html', 
                         current_summary=current_summary,
                         recent_income=recent_income,
                         recent_expenses=recent_expenses,
                         company_metrics=company_metrics,
                         user_role=current_user.role)

@app.route('/income')
@login_required
def income():
    page = request.args.get('page', 1, type=int)
    
    # Build query based on user role and permissions
    if current_user.role in ['owner', 'manager']:
        # Can view all company income
        income_query = db.session.query(Income).join(User).filter(
            User.company_id == current_user.company_id
        )
    else:
        # Can only view own income
        income_query = Income.query.filter_by(user_id=current_user.id)
    
    income_entries = income_query.order_by(
        Income.date_recorded.desc(), 
        Income.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('income/list.html', 
                         income_entries=income_entries,
                         user_role=current_user.role)

@app.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    if request.method == 'POST':
        car_id = request.form.get('car_id')
        amount = float(request.form.get('amount'))
        platform = request.form.get('platform')
        trip_type = request.form.get('trip_type', 'Regular')
        distance_km = request.form.get('distance_km')
        duration_minutes = request.form.get('duration_minutes')
        start_location = request.form.get('start_location')
        end_location = request.form.get('end_location')
        date_recorded = datetime.strptime(request.form.get('date_recorded'), '%Y-%m-%d').date()
        notes = request.form.get('notes')
        
        income_entry = Income(
            user_id=current_user.id,
            car_id=car_id,
            amount=amount,
            platform=platform,
            trip_type=trip_type,
            distance_km=float(distance_km) if distance_km else None,
            duration_minutes=int(duration_minutes) if duration_minutes else None,
            start_location=start_location,
            end_location=end_location,
            date_recorded=date_recorded,
            notes=notes
        )
        
        db.session.add(income_entry)
        db.session.commit()
        
        flash('Income entry added successfully!', 'success')
        return redirect(url_for('income'))
    
    cars = Car.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('income/add.html', cars=cars)

@app.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    
    # Build query based on user role and permissions
    if current_user.role in ['owner', 'manager']:
        # Can view all company expenses
        expense_query = db.session.query(Expense).join(User).filter(
            User.company_id == current_user.company_id
        )
    else:
        # Can only view own expenses
        expense_query = Expense.query.filter_by(user_id=current_user.id)
    
    expense_entries = expense_query.order_by(
        Expense.date_recorded.desc(), 
        Expense.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('expenses/list.html', 
                         expense_entries=expense_entries,
                         user_role=current_user.role)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        car_id = request.form.get('car_id')
        amount = float(request.form.get('amount'))
        category = request.form.get('category')
        description = request.form.get('description')
        vendor = request.form.get('vendor')
        receipt_number = request.form.get('receipt_number')
        is_tax_deductible = bool(request.form.get('is_tax_deductible'))
        date_recorded = datetime.strptime(request.form.get('date_recorded'), '%Y-%m-%d').date()
        notes = request.form.get('notes')
        
        expense_entry = Expense(
            user_id=current_user.id,
            car_id=car_id,
            amount=amount,
            category=category,
            description=description,
            vendor=vendor,
            receipt_number=receipt_number,
            is_tax_deductible=is_tax_deductible,
            date_recorded=date_recorded,
            notes=notes
        )
        
        db.session.add(expense_entry)
        db.session.commit()
        
        flash('Expense entry added successfully!', 'success')
        return redirect(url_for('expenses'))
    
    cars = Car.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('expenses/add.html', cars=cars)

@app.route('/cars')
@login_required
def cars():
    if current_user.role in ['owner', 'manager']:
        # Show all company vehicles
        user_cars = Car.query.filter_by(user_id=current_user.id).all()  # Legacy cars
        company_vehicles = Vehicle.query.filter_by(company_id=current_user.company_id).all()  # New vehicles
    else:
        # Show only assigned vehicles
        user_cars = Car.query.filter_by(user_id=current_user.id).all()
        company_vehicles = Vehicle.query.filter_by(
            company_id=current_user.company_id, 
            user_id=current_user.id
        ).all()
    
    return render_template('cars/list.html', 
                         cars=user_cars, 
                         vehicles=company_vehicles,
                         user_role=current_user.role)

@app.route('/add_car', methods=['GET', 'POST'])
@login_required
def add_car():
    if request.method == 'POST':
        make = request.form.get('make')
        model = request.form.get('model')
        year = int(request.form.get('year'))
        license_plate = request.form.get('license_plate')
        color = request.form.get('color')
        
        car = Car(
            user_id=current_user.id,
            make=make,
            model=model,
            year=year,
            license_plate=license_plate,
            color=color
        )
        
        db.session.add(car)
        db.session.commit()
        
        flash('Vehicle added successfully!', 'success')
        return redirect(url_for('cars'))
    
    return render_template('cars/add.html')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports/index.html')

@app.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    report_format = request.form.get('format', 'excel')
    
    if report_format == 'excel':
        # output = generate_excel_report(current_user.id, start_date, end_date)  # Disabled for frontend testing
        flash('Excel reports temporarily disabled for frontend testing', 'warning')
        return redirect(url_for('reports'))
        filename = f"taxi_report_{start_date}_{end_date}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    flash('Report generated successfully!', 'success')
    return redirect(url_for('reports'))

@app.route('/api/monthly_stats')
@login_required
def api_monthly_stats():
    """API endpoint for monthly statistics chart"""
    year = request.args.get('year', datetime.now().year, type=int)
    
    monthly_data = []
    for month in range(1, 13):
        summary = get_monthly_summary(current_user.id, year, month)
        monthly_data.append({
            'month': month,
            'income': summary['total_income'],
            'expenses': summary['total_expenses'],
            'profit': summary['net_profit']
        })
    
    return jsonify(monthly_data)

@app.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard with comprehensive insights"""
    return render_template('analytics/index.html')

@app.route('/api/analytics/overview')
@login_required
def api_analytics_overview():
    """API endpoint for analytics overview data"""
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Monthly trends
    monthly_trends = []
    for month in range(1, 13):
        summary = get_monthly_summary(current_user.id, year, month)
        monthly_trends.append({
            'month': month,
            'income': summary['total_income'],
            'expenses': summary['total_expenses'],
            'profit': summary['net_profit'],
            'trips': summary['total_trips']
        })
    
    # Platform breakdown
    platform_stats = db.session.query(
        Income.platform,
        func.sum(Income.amount).label('total_amount'),
        func.count(Income.id).label('trip_count')
    ).filter(
        Income.user_id == current_user.id,
        extract('year', Income.date_recorded) == year
    ).group_by(Income.platform).all()
    
    platform_data = [{
        'platform': stat.platform,
        'amount': float(stat.total_amount or 0),
        'trips': stat.trip_count
    } for stat in platform_stats]
    
    # Expense categories
    expense_stats = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total_amount'),
        func.count(Expense.id).label('expense_count')
    ).filter(
        Expense.user_id == current_user.id,
        extract('year', Expense.date_recorded) == year
    ).group_by(Expense.category).all()
    
    expense_data = [{
        'category': stat.category,
        'amount': float(stat.total_amount or 0),
        'count': stat.expense_count
    } for stat in expense_stats]
    
    # Performance metrics
    total_income = sum(month['income'] for month in monthly_trends)
    total_expenses = sum(month['expenses'] for month in monthly_trends)
    total_trips = sum(month['trips'] for month in monthly_trends)
    avg_trip_value = total_income / total_trips if total_trips > 0 else 0
    
    return jsonify({
        'monthly_trends': monthly_trends,
        'platform_breakdown': platform_data,
        'expense_breakdown': expense_data,
        'metrics': {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_profit': total_income - total_expenses,
            'total_trips': total_trips,
            'average_trip_value': avg_trip_value,
            'profit_margin': ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
        }
    })

@app.route('/api/analytics/time-analysis')
@login_required
def api_analytics_time():
    """API endpoint for time-based analytics"""
    # Daily averages by weekday
    daily_stats = db.session.query(
        func.extract('dow', Income.date_recorded).label('day_of_week'),
        func.avg(Income.amount).label('avg_income'),
        func.count(Income.id).label('trip_count')
    ).filter(
        Income.user_id == current_user.id
    ).group_by(func.extract('dow', Income.date_recorded)).all()
    
    weekday_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    daily_data = [{
        'day': weekday_names[int(stat.day_of_week)],
        'avg_income': float(stat.avg_income or 0),
        'trips': stat.trip_count
    } for stat in daily_stats]
    
    # Hourly patterns (if time_recorded is available)
    hourly_stats = db.session.query(
        func.extract('hour', Income.time_recorded).label('hour'),
        func.avg(Income.amount).label('avg_income'),
        func.count(Income.id).label('trip_count')
    ).filter(
        Income.user_id == current_user.id,
        Income.time_recorded.isnot(None)
    ).group_by(func.extract('hour', Income.time_recorded)).all()
    
    hourly_data = [{
        'hour': int(stat.hour),
        'avg_income': float(stat.avg_income or 0),
        'trips': stat.trip_count
    } for stat in hourly_stats]
    
    return jsonify({
        'daily_patterns': daily_data,
        'hourly_patterns': hourly_data
    })

@app.route('/api/analytics/performance')
@login_required
def api_analytics_performance():
    """API endpoint for performance analytics"""
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Best performing days
    best_days = db.session.query(
        Income.date_recorded,
        func.sum(Income.amount).label('daily_income'),
        func.count(Income.id).label('trip_count')
    ).filter(
        Income.user_id == current_user.id,
        extract('year', Income.date_recorded) == year
    ).group_by(Income.date_recorded)\
     .order_by(desc('daily_income'))\
     .limit(10).all()
    
    best_days_data = [{
        'date': stat.date_recorded.strftime('%Y-%m-%d'),
        'income': float(stat.daily_income),
        'trips': stat.trip_count
    } for stat in best_days]
    
    # Car performance comparison
    car_stats = db.session.query(
        Car.make,
        Car.model,
        Car.license_plate,
        func.sum(Income.amount).label('total_income'),
        func.count(Income.id).label('trip_count'),
        func.avg(Income.amount).label('avg_trip_value')
    ).join(Income).filter(
        Income.user_id == current_user.id,
        extract('year', Income.date_recorded) == year
    ).group_by(Car.id, Car.make, Car.model, Car.license_plate).all()
    
    car_performance = [{
        'car': f"{stat.make} {stat.model} ({stat.license_plate})",
        'income': float(stat.total_income or 0),
        'trips': stat.trip_count,
        'avg_value': float(stat.avg_trip_value or 0)
    } for stat in car_stats]
    
    return jsonify({
        'best_days': best_days_data,
        'car_performance': car_performance
    })

@app.route('/contracts')
@login_required
@requires_permission('view_all')
def contracts():
    """Employment contracts management"""
    page = request.args.get('page', 1, type=int)
    
    contracts_query = EmploymentContract.query.filter_by(
        company_id=current_user.company_id
    ).join(User).order_by(EmploymentContract.created_at.desc())
    
    contracts = contracts_query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('contracts/list.html', contracts=contracts)

@app.route('/contracts/add', methods=['GET', 'POST'])
@login_required
@requires_permission('manage_drivers')
def add_contract():
    """Add new employment contract"""
    if request.method == 'POST':
        driver_id = request.form.get('driver_id')
        contract_type = request.form.get('contract_type')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date_str = request.form.get('end_date')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        
        monthly_fee = float(request.form.get('monthly_fee', 0))
        commission_rate = float(request.form.get('commission_rate', 0))
        security_deposit = float(request.form.get('security_deposit', 0))
        minimum_guarantee = float(request.form.get('minimum_guarantee', 0))
        bonus_threshold = float(request.form.get('bonus_threshold', 0))
        bonus_rate = float(request.form.get('bonus_rate', 0))
        payment_schedule = request.form.get('payment_schedule', 'monthly')
        auto_renew = bool(request.form.get('auto_renew'))
        terms_conditions = request.form.get('terms_conditions', '')
        
        # Validate driver belongs to same company
        driver = User.query.filter_by(
            id=driver_id, 
            company_id=current_user.company_id,
            role='driver'
        ).first()
        
        if not driver:
            flash('Invalid driver selected.', 'error')
            return redirect(url_for('add_contract'))
        
        # Check for existing active contracts
        existing_contract = EmploymentContract.query.filter_by(
            driver_id=driver_id,
            status='active'
        ).first()
        
        if existing_contract:
            flash('Driver already has an active contract. Terminate existing contract first.', 'error')
            return redirect(url_for('add_contract'))
        
        contract = EmploymentContract(
            company_id=current_user.company_id,
            driver_id=driver_id,
            contract_type=contract_type,
            start_date=start_date,
            end_date=end_date,
            monthly_fee=monthly_fee,
            commission_rate=commission_rate,
            security_deposit=security_deposit,
            minimum_guarantee=minimum_guarantee,
            bonus_threshold=bonus_threshold,
            bonus_rate=bonus_rate,
            payment_schedule=payment_schedule,
            auto_renew=auto_renew,
            terms_conditions=terms_conditions,
            signed_date=datetime.utcnow()
        )
        
        db.session.add(contract)
        db.session.commit()
        
        # Log the action
        log_user_action(
            current_user.id, 
            'contract_created', 
            'employment_contract', 
            contract.id,
            new_values=f'{{"driver_id": {driver_id}, "contract_type": "{contract_type}"}}'
        )
        
        flash(f'Employment contract created for {driver.first_name} {driver.last_name}!', 'success')
        return redirect(url_for('contracts'))
    
    # Get available drivers for the company
    available_drivers = User.query.filter_by(
        company_id=current_user.company_id,
        role='driver',
        is_active=True
    ).all()
    
    return render_template('contracts/add.html', drivers=available_drivers)

@app.route('/contracts/<int:contract_id>/terminate', methods=['POST'])
@login_required
@requires_permission('manage_drivers')
def terminate_contract(contract_id):
    """Terminate employment contract"""
    contract = EmploymentContract.query.filter_by(
        id=contract_id,
        company_id=current_user.company_id
    ).first()
    
    if not contract:
        flash('Contract not found.', 'error')
        return redirect(url_for('contracts'))
    
    if contract.status != 'active':
        flash('Contract is not active.', 'error')
        return redirect(url_for('contracts'))
    
    termination_reason = request.form.get('termination_reason', '')
    
    contract.status = 'terminated'
    contract.end_date = datetime.now().date()
    
    db.session.commit()
    
    # Log the action
    log_user_action(
        current_user.id, 
        'contract_terminated', 
        'employment_contract', 
        contract.id,
        new_values=f'{{"reason": "{termination_reason}"}}'
    )
    
    driver = User.query.get(contract.driver_id)
    flash(f'Contract terminated for {driver.first_name} {driver.last_name}.', 'success')
    return redirect(url_for('contracts'))

@app.route('/fleet')
@login_required
@requires_permission('view_all')
def fleet():
    """Fleet management dashboard"""
    vehicles = Vehicle.query.filter_by(
        company_id=current_user.company_id
    ).all()
    
    # Fleet statistics
    fleet_stats = {
        'total_vehicles': len(vehicles),
        'active_vehicles': len([v for v in vehicles if v.status == 'active']),
        'maintenance_due': len([v for v in vehicles if v.next_service_due and v.next_service_due <= datetime.now().date()]),
        'insurance_expiring': len([v for v in vehicles if v.insurance_expiry and v.insurance_expiry <= datetime.now().date() + timedelta(days=30)])
    }
    
    return render_template('fleet/dashboard.html', 
                         vehicles=vehicles, 
                         fleet_stats=fleet_stats)

@app.route('/fleet/add', methods=['GET', 'POST'])
@login_required
@requires_permission('manage_all')
def add_vehicle():
    """Add new vehicle to fleet"""
    if request.method == 'POST':
        make = request.form.get('make')
        model = request.form.get('model')
        year = int(request.form.get('year'))
        vin = request.form.get('vin')
        license_plate = request.form.get('license_plate')
        color = request.form.get('color')
        purchase_date_str = request.form.get('purchase_date')
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else None
        purchase_price = float(request.form.get('purchase_price', 0))
        fuel_type = request.form.get('fuel_type')
        insurance_policy = request.form.get('insurance_policy')
        insurance_expiry_str = request.form.get('insurance_expiry')
        insurance_expiry = datetime.strptime(insurance_expiry_str, '%Y-%m-%d').date() if insurance_expiry_str else None
        
        vehicle = Vehicle(
            company_id=current_user.company_id,
            make=make,
            model=model,
            year=year,
            vin=vin,
            license_plate=license_plate,
            color=color,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            fuel_type=fuel_type,
            insurance_policy=insurance_policy,
            insurance_expiry=insurance_expiry
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        log_user_action(
            current_user.id, 
            'vehicle_added', 
            'vehicle', 
            vehicle.id,
            new_values=f'{{"make": "{make}", "model": "{model}", "license_plate": "{license_plate}"}}'
        )
        
        flash(f'Vehicle {make} {model} ({license_plate}) added to fleet!', 'success')
        return redirect(url_for('fleet'))
    
    return render_template('fleet/add.html')

@app.route('/performance')
@login_required
@requires_permission('view_reports')
def performance():
    """Driver performance dashboard"""
    if current_user.role == 'driver':
        # Individual driver performance
        performances = DriverPerformance.query.filter_by(
            driver_id=current_user.id
        ).order_by(DriverPerformance.month.desc()).limit(12).all()
        return render_template('performance/individual.html', performances=performances)
    else:
        # Company-wide performance
        performances = db.session.query(DriverPerformance)\\\
            .join(EmploymentContract)\\\
            .filter(EmploymentContract.company_id == current_user.company_id)\\\
            .order_by(DriverPerformance.month.desc())\\\
            .limit(50).all()
        
        return render_template('performance/company.html', performances=performances)

@app.route('/compliance')
@login_required
@requires_permission('view_reports')
def compliance():
    """Compliance tracking dashboard"""
    alerts = ComplianceAlert.query.filter_by(
        company_id=current_user.company_id,
        status='active'
    ).order_by(ComplianceAlert.due_date.asc()).all()
    
    # Categorize alerts by priority and type
    alert_summary = {
        'critical': len([a for a in alerts if a.priority == 'critical']),
        'high': len([a for a in alerts if a.priority == 'high']),
        'medium': len([a for a in alerts if a.priority == 'medium']),
        'low': len([a for a in alerts if a.priority == 'low'])
    }
    
    return render_template('compliance/dashboard.html', 
                         alerts=alerts, 
                         alert_summary=alert_summary)

@app.route('/payroll')
@login_required
@requires_permission('manage_all')
def payroll():
    """Payroll management dashboard"""
    current_month = datetime.now().replace(day=1).date()
    
    # Get all active contracts for the company
    contracts = EmploymentContract.query.filter_by(
        company_id=current_user.company_id,
        status='active'
    ).all()
    
    # Calculate payroll for current month
    payroll_data = []
    for contract in contracts:
        payroll_info = calculate_driver_payroll(contract, current_month)
        payroll_data.append(payroll_info)
    
    # Payroll summary
    total_gross = sum(p['gross_payment'] for p in payroll_data)
    total_deductions = sum(p['total_deductions'] for p in payroll_data)
    total_net = sum(p['net_payment'] for p in payroll_data)
    
    payroll_summary = {
        'total_gross': total_gross,
        'total_deductions': total_deductions,
        'total_net': total_net,
        'drivers_count': len(payroll_data),
        'period': current_month.strftime('%Y-%m')
    }
    
    return render_template('payroll/dashboard.html', 
                         payroll_data=payroll_data,
                         payroll_summary=payroll_summary,
                         current_month=current_month)

@app.route('/payroll/process', methods=['POST'])
@login_required
@requires_permission('manage_all')
def process_payroll():
    """Process payroll for selected period"""
    period = request.form.get('period')  # Format: YYYY-MM
    period_date = datetime.strptime(period, '%Y-%m').date()
    
    # Get all active contracts
    contracts = EmploymentContract.query.filter_by(
        company_id=current_user.company_id,
        status='active'
    ).all()
    
    processed_count = 0
    total_amount = 0
    
    for contract in contracts:
        # Check if payroll already processed for this period
        existing_payment = ContractPayment.query.filter_by(
            contract_id=contract.id,
            reference_period=period,
            payment_type='salary'
        ).first()
        
        if existing_payment:
            continue  # Skip if already processed
        
        # Calculate payroll
        payroll_info = calculate_driver_payroll(contract, period_date)
        
        if payroll_info['net_payment'] > 0:
            # Create payment record
            payment = ContractPayment(
                contract_id=contract.id,
                payment_date=datetime.now().date(),
                amount=payroll_info['net_payment'],
                payment_type='salary',
                reference_period=period,
                tax_withheld=payroll_info['tax_withheld'],
                status='pending'
            )
            
            db.session.add(payment)
            processed_count += 1
            total_amount += payroll_info['net_payment']
    
    db.session.commit()
    
    # Log the action
    log_user_action(
        current_user.id,
        'payroll_processed',
        'payroll',
        None,
        new_values=f'{{"period": "{period}", "drivers": {processed_count}, "total": {total_amount}}}'
    )
    
    flash(f'Payroll processed for {processed_count} drivers. Total amount: {total_amount:,.2f} SEK', 'success')
    return redirect(url_for('payroll'))

@app.route('/export')
@login_required
@requires_permission('view_reports')
def export_data():
    """Data export dashboard"""
    return render_template('export/index.html')

@app.route('/export/contracts')
@login_required
@requires_permission('view_all')
def export_contracts():
    """Export employment contracts data"""
    format_type = request.args.get('format', 'csv')
    
    # Get contracts data
    contracts = db.session.query(EmploymentContract)\
        .join(User)\
        .filter(EmploymentContract.company_id == current_user.company_id)\
        .all()
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Driver Name', 'Email', 'Contract Type', 'Start Date', 'End Date',
            'Monthly Fee', 'Commission Rate', 'Security Deposit', 'Status',
            'Payment Schedule', 'Auto Renew', 'Created Date'
        ])
        
        # Write data
        for contract in contracts:
            writer.writerow([
                f"{contract.driver.first_name} {contract.driver.last_name}",
                contract.driver.email,
                contract.contract_type,
                contract.start_date.strftime('%Y-%m-%d'),
                contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '',
                contract.monthly_fee,
                contract.commission_rate,
                contract.security_deposit,
                contract.status,
                contract.payment_schedule,
                contract.auto_renew,
                contract.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=contracts_{datetime.now().strftime("%Y%m%d")}.csv'
        
    elif format_type == 'json':
        contracts_data = []
        for contract in contracts:
            contracts_data.append({
                'id': contract.id,
                'driver': {
                    'name': f"{contract.driver.first_name} {contract.driver.last_name}",
                    'email': contract.driver.email,
                    'phone': contract.driver.phone
                },
                'contract_type': contract.contract_type,
                'start_date': contract.start_date.isoformat(),
                'end_date': contract.end_date.isoformat() if contract.end_date else None,
                'financial_terms': {
                    'monthly_fee': contract.monthly_fee,
                    'commission_rate': contract.commission_rate,
                    'security_deposit': contract.security_deposit,
                    'minimum_guarantee': contract.minimum_guarantee,
                    'bonus_threshold': contract.bonus_threshold,
                    'bonus_rate': contract.bonus_rate
                },
                'status': contract.status,
                'payment_schedule': contract.payment_schedule,
                'auto_renew': contract.auto_renew,
                'created_at': contract.created_at.isoformat()
            })
        
        response = make_response(json.dumps(contracts_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=contracts_{datetime.now().strftime("%Y%m%d")}.json'
    
    # Log export action
    log_user_action(
        current_user.id,
        'data_export',
        'contracts',
        None,
        new_values=f'{{"format": "{format_type}", "count": {len(contracts)}}}'
    )
    
    return response

@app.route('/export/income')
@login_required
@requires_permission('view_reports')
def export_income():
    """Export income data"""
    format_type = request.args.get('format', 'csv')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query based on user permissions
    if current_user.role in ['owner', 'manager']:
        income_query = db.session.query(Income).join(User).filter(
            User.company_id == current_user.company_id
        )
    else:
        income_query = Income.query.filter_by(user_id=current_user.id)
    
    # Apply date filters if provided
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        income_query = income_query.filter(Income.date_recorded >= start_date_obj)
    
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        income_query = income_query.filter(Income.date_recorded <= end_date_obj)
    
    income_entries = income_query.order_by(Income.date_recorded.desc()).all()
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Date', 'Driver', 'Amount', 'Platform', 'Trip Type',
            'Distance (km)', 'Duration (min)', 'Start Location', 'End Location',
            'Vehicle', 'Notes'
        ])
        
        # Write data
        for entry in income_entries:
            vehicle_info = ''
            if entry.car:
                vehicle_info = f"{entry.car.make} {entry.car.model} ({entry.car.license_plate})"
            elif entry.vehicle:
                vehicle_info = f"{entry.vehicle.make} {entry.vehicle.model} ({entry.vehicle.license_plate})"
                
            writer.writerow([
                entry.date_recorded.strftime('%Y-%m-%d'),
                f"{entry.user.first_name} {entry.user.last_name}",
                entry.amount,
                entry.platform,
                entry.trip_type,
                entry.distance_km or '',
                entry.duration_minutes or '',
                entry.start_location or '',
                entry.end_location or '',
                vehicle_info,
                entry.notes or ''
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=income_{datetime.now().strftime("%Y%m%d")}.csv'
    
    else:  # JSON format
        income_data = []
        for entry in income_entries:
            income_data.append({
                'id': entry.id,
                'date': entry.date_recorded.isoformat(),
                'driver': {
                    'name': f"{entry.user.first_name} {entry.user.last_name}",
                    'email': entry.user.email
                },
                'amount': entry.amount,
                'platform': entry.platform,
                'trip_type': entry.trip_type,
                'distance_km': entry.distance_km,
                'duration_minutes': entry.duration_minutes,
                'locations': {
                    'start': entry.start_location,
                    'end': entry.end_location
                },
                'vehicle': {
                    'make': entry.car.make if entry.car else (entry.vehicle.make if entry.vehicle else None),
                    'model': entry.car.model if entry.car else (entry.vehicle.model if entry.vehicle else None),
                    'license_plate': entry.car.license_plate if entry.car else (entry.vehicle.license_plate if entry.vehicle else None)
                } if (entry.car or entry.vehicle) else None,
                'notes': entry.notes,
                'created_at': entry.created_at.isoformat()
            })
        
        response = make_response(json.dumps(income_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=income_{datetime.now().strftime("%Y%m%d")}.json'
    
    # Log export action
    log_user_action(
        current_user.id,
        'data_export',
        'income',
        None,
        new_values=f'{{"format": "{format_type}", "count": {len(income_entries)}, "date_range": "{start_date} to {end_date}"}}}'
    )
    
    return response

@app.route('/export/expenses')
@login_required
@requires_permission('view_reports')
def export_expenses():
    """Export expenses data"""
    format_type = request.args.get('format', 'csv')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query based on user permissions
    if current_user.role in ['owner', 'manager']:
        expense_query = db.session.query(Expense).join(User).filter(
            User.company_id == current_user.company_id
        )
    else:
        expense_query = Expense.query.filter_by(user_id=current_user.id)
    
    # Apply date filters if provided
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        expense_query = expense_query.filter(Expense.date_recorded >= start_date_obj)
    
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        expense_query = expense_query.filter(Expense.date_recorded <= end_date_obj)
    
    expense_entries = expense_query.order_by(Expense.date_recorded.desc()).all()
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Date', 'Driver', 'Amount', 'Category', 'Description',
            'Vendor', 'Receipt Number', 'Payment Method', 'Tax Deductible',
            'Vehicle', 'Notes'
        ])
        
        # Write data
        for entry in expense_entries:
            vehicle_info = ''
            if entry.car:
                vehicle_info = f"{entry.car.make} {entry.car.model} ({entry.car.license_plate})"
            elif entry.vehicle:
                vehicle_info = f"{entry.vehicle.make} {entry.vehicle.model} ({entry.vehicle.license_plate})"
            
            writer.writerow([
                entry.date_recorded.strftime('%Y-%m-%d'),
                f"{entry.user.first_name} {entry.user.last_name}",
                entry.amount,
                entry.category,
                entry.description,
                entry.vendor or '',
                entry.receipt_number or '',
                getattr(entry, 'payment_method', '') or 'cash',
                'Yes' if entry.is_tax_deductible else 'No',
                vehicle_info,
                entry.notes or ''
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=expenses_{datetime.now().strftime("%Y%m%d")}.csv'
    
    else:  # JSON format
        expense_data = []
        for entry in expense_entries:
            expense_data.append({
                'id': entry.id,
                'date': entry.date_recorded.isoformat(),
                'driver': {
                    'name': f"{entry.user.first_name} {entry.user.last_name}",
                    'email': entry.user.email
                },
                'amount': entry.amount,
                'category': entry.category,
                'description': entry.description,
                'vendor': entry.vendor,
                'receipt_number': entry.receipt_number,
                'payment_method': getattr(entry, 'payment_method', 'cash'),
                'is_tax_deductible': entry.is_tax_deductible,
                'vehicle': {
                    'make': entry.car.make if entry.car else (entry.vehicle.make if entry.vehicle else None),
                    'model': entry.car.model if entry.car else (entry.vehicle.model if entry.vehicle else None),
                    'license_plate': entry.car.license_plate if entry.car else (entry.vehicle.license_plate if entry.vehicle else None)
                } if (entry.car or entry.vehicle) else None,
                'notes': entry.notes,
                'created_at': entry.created_at.isoformat()
            })
        
        response = make_response(json.dumps(expense_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=expenses_{datetime.now().strftime("%Y%m%d")}.json'
    
    # Log export action
    log_user_action(
        current_user.id,
        'data_export',
        'expenses',
        None,
        new_values=f'{{"format": "{format_type}", "count": {len(expense_entries)}, "date_range": "{start_date} to {end_date}"}}}'
    )
    
    return response

@app.route('/financial-planning')
@login_required
@requires_permission('view_reports')
def financial_planning():
    """Financial planning and forecasting dashboard"""
    # Get current budgets
    current_budgets = Budget.query.filter_by(
        company_id=current_user.company_id,
        status='active'
    ).order_by(Budget.period_start.desc()).all()
    
    # Get latest forecasts
    latest_forecasts = FinancialForecast.query.filter_by(
        company_id=current_user.company_id
    ).order_by(FinancialForecast.forecast_date.desc()).limit(6).all()
    
    # Calculate current month performance
    current_month_summary = get_monthly_summary(company_id=current_user.company_id)
    
    # Generate next 3 months forecast
    upcoming_forecasts = generate_financial_forecast(current_user.company_id, 3)
    
    return render_template('financial/planning.html',
                         budgets=current_budgets,
                         forecasts=latest_forecasts,
                         current_summary=current_month_summary,
                         upcoming_forecasts=upcoming_forecasts)

@app.route('/financial-planning/budget/add', methods=['GET', 'POST'])
@login_required
@requires_permission('manage_all')
def add_budget():
    """Create new budget"""
    if request.method == 'POST':
        name = request.form.get('name')
        budget_type = request.form.get('budget_type')
        period_start = datetime.strptime(request.form.get('period_start'), '%Y-%m-%d').date()
        period_end = datetime.strptime(request.form.get('period_end'), '%Y-%m-%d').date()
        
        target_revenue = float(request.form.get('target_revenue', 0))
        target_expenses = float(request.form.get('target_expenses', 0))
        target_trips = int(request.form.get('target_trips', 0))
        target_drivers = int(request.form.get('target_drivers', 0))
        notes = request.form.get('notes', '')
        
        budget = Budget(
            company_id=current_user.company_id,
            name=name,
            budget_type=budget_type,
            period_start=period_start,
            period_end=period_end,
            target_revenue=target_revenue,
            target_expenses=target_expenses,
            target_profit=target_revenue - target_expenses,
            target_trips=target_trips,
            target_drivers=target_drivers,
            notes=notes,
            created_by=current_user.id
        )
        
        db.session.add(budget)
        db.session.commit()
        
        log_user_action(
            current_user.id,
            'budget_created',
            'budget',
            budget.id,
            new_values=f'{{"name": "{name}", "type": "{budget_type}", "target_revenue": {target_revenue}}}'
        )
        
        flash(f'Budget "{name}" created successfully!', 'success')
        return redirect(url_for('financial_planning'))
    
    return render_template('financial/add_budget.html')

@app.route('/api/financial/forecast/<int:months>')
@login_required
@requires_permission('view_reports')
def api_financial_forecast(months):
    """Generate financial forecast API"""
    forecasts = generate_financial_forecast(current_user.company_id, months)
    return jsonify(forecasts)

@app.route('/api/financial/budget-performance')
@login_required
@requires_permission('view_reports')
def api_budget_performance():
    """Get budget vs actual performance"""
    budget_id = request.args.get('budget_id', type=int)
    
    if budget_id:
        budget = Budget.query.filter_by(
            id=budget_id,
            company_id=current_user.company_id
        ).first()
        
        if not budget:
            return jsonify({'error': 'Budget not found'}), 404
        
        # Calculate actual performance for budget period
        actual_data = calculate_budget_performance(budget)
        
        return jsonify({
            'budget': {
                'name': budget.name,
                'period_start': budget.period_start.isoformat(),
                'period_end': budget.period_end.isoformat(),
                'targets': {
                    'revenue': budget.target_revenue,
                    'expenses': budget.target_expenses,
                    'profit': budget.target_profit,
                    'trips': budget.target_trips
                }
            },
            'actual': actual_data,
            'variance': {
                'revenue': actual_data['revenue'] - budget.target_revenue,
                'expenses': actual_data['expenses'] - budget.target_expenses,
                'profit': actual_data['profit'] - budget.target_profit,
                'trips': actual_data['trips'] - budget.target_trips
            }
        })
    
    return jsonify({'error': 'Budget ID required'}), 400

# Notification System Routes
@app.route('/notifications')
@login_required
def notifications():
    """Display user notifications"""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')
    
    # Build query based on filter
    query = Notification.query.filter_by(company_id=current_user.company_id)
    
    if current_user.role != 'owner':
        # Non-owners can only see their notifications or company-wide notifications
        query = query.filter(
            (Notification.user_id == current_user.id) | 
            (Notification.user_id.is_(None))
        )
    
    if filter_type == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_type == 'alerts':
        query = query.filter_by(notification_type='alert')
    elif filter_type != 'all':
        query = query.filter_by(category=filter_type)
    
    notifications_page = query.order_by(
        Notification.priority.desc(),
        Notification.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('notifications/list.html', 
                         notifications=notifications_page,
                         filter_type=filter_type)

@app.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id,
        company_id=current_user.company_id
    ).first_or_404()
    
    # Check permission to read this notification
    if notification.user_id and notification.user_id != current_user.id and current_user.role not in ['owner', 'manager']:
        flash('Access denied', 'error')
        return redirect(url_for('notifications'))
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/notifications/dismiss/<int:notification_id>', methods=['POST'])
@login_required
def dismiss_notification(notification_id):
    """Dismiss a notification"""
    notification = Notification.query.filter_by(
        id=notification_id,
        company_id=current_user.company_id
    ).first_or_404()
    
    # Check permission to dismiss this notification
    if notification.user_id and notification.user_id != current_user.id and current_user.role not in ['owner', 'manager']:
        flash('Access denied', 'error')
        return redirect(url_for('notifications'))
    
    notification.is_dismissed = True
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/notifications/settings')
@login_required
@requires_permission('manage_all')
def notification_settings():
    """Manage notification rules and scheduled reports"""
    notification_rules = NotificationRule.query.filter_by(
        company_id=current_user.company_id
    ).all()
    
    scheduled_reports = ScheduledReport.query.filter_by(
        company_id=current_user.company_id
    ).all()
    
    return render_template('notifications/settings.html',
                         notification_rules=notification_rules,
                         scheduled_reports=scheduled_reports)

@app.route('/notifications/create-rule', methods=['GET', 'POST'])
@login_required
@requires_permission('manage_all')
def create_notification_rule():
    """Create automated notification rule"""
    if request.method == 'POST':
        name = request.form.get('name')
        trigger_type = request.form.get('trigger_type')
        trigger_condition = request.form.get('trigger_condition')
        notification_template = request.form.get('notification_template')
        target_roles = request.form.get('target_roles')
        target_users = request.form.get('target_users')
        
        rule = NotificationRule(
            company_id=current_user.company_id,
            created_by=current_user.id,
            name=name,
            trigger_type=trigger_type,
            trigger_condition=trigger_condition,
            notification_template=notification_template,
            target_roles=target_roles,
            target_users=target_users
        )
        
        db.session.add(rule)
        db.session.commit()
        
        flash(f'Notification rule "{name}" created successfully!', 'success')
        return redirect(url_for('notification_settings'))
    
    return render_template('notifications/create_rule.html')

@app.route('/notifications/schedule-report', methods=['GET', 'POST'])
@login_required
@requires_permission('manage_all')
def schedule_report():
    """Schedule automated reports"""
    if request.method == 'POST':
        name = request.form.get('name')
        report_type = request.form.get('report_type')
        frequency = request.form.get('frequency')
        recipients = request.form.get('recipients')
        format = request.form.get('format', 'pdf')
        
        # Calculate next run time based on frequency
        next_run = calculate_next_run_time(frequency)
        
        scheduled_report = ScheduledReport(
            company_id=current_user.company_id,
            created_by=current_user.id,
            name=name,
            report_type=report_type,
            frequency=frequency,
            recipients=recipients,
            format=format,
            next_run=next_run
        )
        
        db.session.add(scheduled_report)
        db.session.commit()
        
        flash(f'Report "{name}" scheduled successfully!', 'success')
        return redirect(url_for('notification_settings'))
    
    return render_template('notifications/schedule_report.html')

@app.route('/api/notifications/unread-count')
@login_required
def api_unread_notifications_count():
    """Get count of unread notifications for current user"""
    query = Notification.query.filter_by(
        company_id=current_user.company_id,
        is_read=False,
        is_dismissed=False
    )
    
    if current_user.role != 'owner':
        query = query.filter(
            (Notification.user_id == current_user.id) | 
            (Notification.user_id.is_(None))
        )
    
    count = query.count()
    return jsonify({'count': count})

# Notification Helper Functions
def create_notification(company_id, title, message, notification_type='info', 
                       category='general', user_id=None, action_url=None, 
                       action_text=None, priority='medium', expires_at=None, metadata=None):
    """Create a new notification"""
    notification = Notification(
        company_id=company_id,
        user_id=user_id,
        notification_type=notification_type,
        category=category,
        title=title,
        message=message,
        action_url=action_url,
        action_text=action_text,
        priority=priority,
        expires_at=expires_at,
        metadata=json.dumps(metadata) if metadata else None
    )
    
    db.session.add(notification)
    db.session.commit()
    return notification

def create_compliance_notifications():
    """Create notifications for compliance items due soon"""
    # License expiry notifications
    upcoming_license_expiry = User.query.filter(
        User.license_expiry.isnot(None),
        User.license_expiry <= datetime.now().date() + timedelta(days=30),
        User.license_expiry > datetime.now().date(),
        User.is_active == True
    ).all()
    
    for driver in upcoming_license_expiry:
        days_until_expiry = (driver.license_expiry - datetime.now().date()).days
        
        create_notification(
            company_id=driver.company_id,
            title=f"Driver License Expiring Soon",
            message=f"{driver.first_name} {driver.last_name}'s license expires in {days_until_expiry} days",
            notification_type='warning',
            category='compliance',
            action_url=f"/drivers/{driver.id}",
            action_text="Update License",
            priority='high' if days_until_expiry <= 7 else 'medium'
        )
    
    # Vehicle insurance/registration expiry
    vehicles_expiry = Vehicle.query.filter(
        Vehicle.is_active == True
    ).all()
    
    for vehicle in vehicles_expiry:
        # Check insurance expiry
        if vehicle.insurance_expiry:
            days_until_insurance = (vehicle.insurance_expiry - datetime.now().date()).days
            if 0 < days_until_insurance <= 30:
                create_notification(
                    company_id=vehicle.company_id,
                    title=f"Vehicle Insurance Expiring",
                    message=f"Insurance for {vehicle.license_plate} expires in {days_until_insurance} days",
                    notification_type='warning',
                    category='compliance',
                    action_url=f"/fleet/{vehicle.id}",
                    action_text="Renew Insurance",
                    priority='high' if days_until_insurance <= 7 else 'medium'
                )
        
        # Check registration expiry
        if vehicle.registration_expiry:
            days_until_registration = (vehicle.registration_expiry - datetime.now().date()).days
            if 0 < days_until_registration <= 30:
                create_notification(
                    company_id=vehicle.company_id,
                    title=f"Vehicle Registration Expiring",
                    message=f"Registration for {vehicle.license_plate} expires in {days_until_registration} days",
                    notification_type='warning',
                    category='compliance',
                    action_url=f"/fleet/{vehicle.id}",
                    action_text="Renew Registration",
                    priority='high' if days_until_registration <= 7 else 'medium'
                )

def create_financial_notifications():
    """Create notifications for financial milestones and alerts"""
    companies = Company.query.filter_by(subscription_status='active').all()
    
    for company in companies:
        # Check budget performance
        active_budgets = Budget.query.filter_by(
            company_id=company.id,
            status='active'
        ).filter(
            Budget.period_start <= datetime.now().date(),
            Budget.period_end >= datetime.now().date()
        ).all()
        
        for budget in active_budgets:
            performance = calculate_budget_performance(budget)
            
            # Alert if over budget by more than 10%
            if performance['expenses'] > budget.target_expenses * 1.1:
                variance_pct = ((performance['expenses'] - budget.target_expenses) / budget.target_expenses) * 100
                
                create_notification(
                    company_id=company.id,
                    title=f"Budget Alert: {budget.name}",
                    message=f"Expenses are {variance_pct:.1f}% over budget for the current period",
                    notification_type='alert',
                    category='financial',
                    action_url="/financial-planning",
                    action_text="Review Budget",
                    priority='high'
                )
            
            # Alert if revenue significantly under target
            if performance['revenue'] < budget.target_revenue * 0.8:
                variance_pct = ((budget.target_revenue - performance['revenue']) / budget.target_revenue) * 100
                
                create_notification(
                    company_id=company.id,
                    title=f"Revenue Alert: {budget.name}",
                    message=f"Revenue is {variance_pct:.1f}% below target for the current period",
                    notification_type='warning',
                    category='financial',
                    action_url="/financial-planning",
                    action_text="Review Performance",
                    priority='medium'
                )

def calculate_next_run_time(frequency):
    """Calculate next run time for scheduled reports"""
    now = datetime.now()
    
    if frequency == 'daily':
        return now + timedelta(days=1)
    elif frequency == 'weekly':
        # Next Monday
        days_ahead = 7 - now.weekday()
        return now + timedelta(days=days_ahead)
    elif frequency == 'monthly':
        # First day of next month
        next_month = now.replace(day=1) + timedelta(days=32)
        return next_month.replace(day=1)
    elif frequency == 'quarterly':
        # Next quarter start
        month = now.month
        next_quarter_month = ((month - 1) // 3 + 1) * 3 + 1
        if next_quarter_month > 12:
            next_quarter_month = 1
            year = now.year + 1
        else:
            year = now.year
        return datetime(year, next_quarter_month, 1)
    
    return now + timedelta(days=1)  # Default to daily

def process_scheduled_reports():
    """Process and send scheduled reports (called by background job)"""
    due_reports = ScheduledReport.query.filter(
        ScheduledReport.is_active == True,
        ScheduledReport.next_run <= datetime.now()
    ).all()
    
    for report in due_reports:
        try:
            # Generate and send report
            generate_and_send_report(report)
            
            # Update next run time
            report.last_run = datetime.now()
            report.next_run = calculate_next_run_time(report.frequency)
            db.session.commit()
            
        except Exception as e:
            print(f"Error processing scheduled report {report.id}: {str(e)}")
            continue

def generate_and_send_report(scheduled_report):
    """Generate and send a scheduled report"""
    # This would integrate with email service to send reports
    # For now, create a notification about the report
    
    create_notification(
        company_id=scheduled_report.company_id,
        title=f"Scheduled Report: {scheduled_report.name}",
        message=f"Your {scheduled_report.frequency} {scheduled_report.report_type} report has been generated",
        notification_type='info',
        category='reports',
        action_url="/reports/advanced",
        action_text="View Reports",
        priority='low'
    )

# Customer Onboarding Routes
@app.route('/onboarding/welcome')
@login_required
def onboarding_welcome():
    """Welcome screen for new users"""
    # Skip onboarding if company is already set up
    if current_user.company_id and current_user.company:
        return redirect(url_for('dashboard'))
    
    return render_template('onboarding/welcome.html')

@app.route('/onboarding/company', methods=['GET', 'POST'])
@login_required
def onboarding_company():
    """Company setup step"""
    if request.method == 'POST':
        # Create new company
        company = Company(
            name=request.form.get('company_name'),
            registration_number=request.form.get('registration_number'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            country=request.form.get('country'),
            tax_number=request.form.get('tax_number')
        )
        
        db.session.add(company)
        db.session.flush()  # Get company ID
        
        # Update user with company association and make them owner
        current_user.company_id = company.id
        current_user.role = 'owner'
        
        # Store onboarding data in session for later steps
        session['onboarding'] = {
            'company_id': company.id,
            'business_type': request.form.get('business_type'),
            'current_vehicles': request.form.get('current_vehicles'),
            'current_drivers': request.form.get('current_drivers'),
            'operation_area': request.form.get('operation_area')
        }
        
        db.session.commit()
        
        # Create welcome notification
        create_notification(
            company_id=company.id,
            title="Welcome to TaxiTracker Pro!",
            message=f"Your company '{company.name}' has been successfully set up. Continue the onboarding process to get the most out of your fleet management system.",
            notification_type='success',
            category='onboarding',
            user_id=current_user.id,
            action_url='/onboarding/fleet',
            action_text='Continue Setup'
        )
        
        log_user_action(
            current_user.id,
            'company_created',
            'company',
            company.id,
            new_values=f'{{"name": "{company.name}", "city": "{company.city}"}}'
        )
        
        flash(f'Company "{company.name}" created successfully!', 'success')
        return redirect(url_for('onboarding_fleet'))
    
    return render_template('onboarding/company.html')

@app.route('/onboarding/fleet', methods=['GET', 'POST'])
@login_required
def onboarding_fleet():
    """Fleet setup step"""
    if not current_user.company_id:
        return redirect(url_for('onboarding_company'))
    
    if request.method == 'POST':
        vehicles_data = request.form.getlist('vehicles')
        
        # Create vehicles from form data
        for vehicle_data in vehicles_data:
            if vehicle_data.strip():  # Only create if data provided
                # Parse vehicle data (JSON string from frontend)
                import json
                try:
                    vehicle_info = json.loads(vehicle_data)
                    vehicle = Vehicle(
                        company_id=current_user.company_id,
                        make=vehicle_info.get('make'),
                        model=vehicle_info.get('model'),
                        year=int(vehicle_info.get('year', 0)),
                        license_plate=vehicle_info.get('license_plate'),
                        color=vehicle_info.get('color'),
                        fuel_type=vehicle_info.get('fuel_type', 'petrol')
                    )
                    db.session.add(vehicle)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        db.session.commit()
        return redirect(url_for('onboarding_drivers'))
    
    return render_template('onboarding/fleet.html')

@app.route('/onboarding/drivers', methods=['GET', 'POST'])
@login_required
def onboarding_drivers():
    """Driver setup step"""
    if not current_user.company_id:
        return redirect(url_for('onboarding_company'))
    
    if request.method == 'POST':
        drivers_data = request.form.getlist('drivers')
        
        # Create drivers from form data
        for driver_data in drivers_data:
            if driver_data.strip():
                import json
                try:
                    driver_info = json.loads(driver_data)
                    
                    # Create user account for driver
                    driver = User(
                        company_id=current_user.company_id,
                        email=driver_info.get('email'),
                        password_hash=generate_password_hash('temporary123'),  # Temporary password
                        first_name=driver_info.get('first_name'),
                        last_name=driver_info.get('last_name'),
                        phone=driver_info.get('phone'),
                        license_number=driver_info.get('license_number'),
                        role='driver'
                    )
                    db.session.add(driver)
                    
                    # Send welcome email/notification to driver
                    # (Implementation would include actual email sending)
                    
                except (json.JSONDecodeError, ValueError):
                    continue
        
        db.session.commit()
        return redirect(url_for('onboarding_complete'))
    
    return render_template('onboarding/drivers.html')

@app.route('/onboarding/complete')
@login_required
def onboarding_complete():
    """Onboarding completion step"""
    if not current_user.company_id:
        return redirect(url_for('onboarding_company'))
    
    # Create completion notification
    create_notification(
        company_id=current_user.company_id,
        title="Onboarding Complete!",
        message="Congratulations! Your TaxiTracker Pro setup is complete. You can now start tracking income, managing drivers, and growing your business.",
        notification_type='success',
        category='onboarding',
        user_id=current_user.id,
        action_url='/dashboard',
        action_text='Go to Dashboard'
    )
    
    # Clear onboarding session data
    if 'onboarding' in session:
        del session['onboarding']
    
    return render_template('onboarding/complete.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring and load balancers"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Database initialization
def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    # Use environment variables for host and port
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host=host, port=port, debug=debug)