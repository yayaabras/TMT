# Pre-production Demo - TaxiTracker Pro
# Monthly Employment Management & Control System
# For managing taxi drivers, monthly contracts, and business operations

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'demo-secret-key-for-testing'

# Mock data that mirrors production structure
class MockUser:
    is_authenticated = True
    first_name = 'John'
    last_name = 'Doe'
    id = 1
    email = 'john.doe@example.com'

mock_cars = [
    {'id': 1, 'make': 'Toyota', 'model': 'Camry', 'year': 2020, 'license_plate': 'ABC-123', 'color': 'White', 'is_active': True},
    {'id': 2, 'make': 'Honda', 'model': 'Civic', 'year': 2019, 'license_plate': 'XYZ-789', 'color': 'Black', 'is_active': True}
]

# Mock monthly employment contracts - initialized empty, populated from user input
mock_employment_contracts = []

# Mock expenses - initialized empty, populated from user input
mock_expenses = []

def calculate_mock_summary():
    """Calculate monthly business summary from user-entered data"""
    total_monthly_revenue = sum(contract.get('total_revenue', 0) for contract in mock_employment_contracts)
    total_monthly_income = sum(contract.get('net_income', 0) for contract in mock_employment_contracts)
    total_expenses = sum(expense.get('amount', 0) for expense in mock_expenses)
    return {
        'total_revenue': total_monthly_revenue,
        'total_income': total_monthly_income,
        'total_expenses': total_expenses,
        'net_profit': total_monthly_income - total_expenses,
        'active_drivers': len([c for c in mock_employment_contracts if c.get('status') == 'Active']),
        'total_contracts': len(mock_employment_contracts)
    }

# Mock pagination class
class MockPagination:
    def __init__(self, items, page=1, per_page=20):
        self.items = items
        self.page = page
        self.pages = 1
        self.has_prev = False
        self.has_next = False
        self.prev_num = None
        self.next_num = None
        self.total = len(items)

@app.context_processor
def inject_user():
    return dict(current_user=MockUser())

# Routes - Exact copies of production with mock data
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        flash(f'Demo: Account created for {email}!', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        flash(f'Demo: Welcome back, {email}!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    flash('Demo: You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', 
                         current_summary=calculate_mock_summary(),
                         recent_contracts=mock_employment_contracts[:3],
                         recent_expenses=mock_expenses[:3])

@app.route('/contracts')
def income():
    page = request.args.get('page', 1, type=int)
    contract_entries = MockPagination(mock_employment_contracts, page)
    return render_template('income/list.html', income_entries=contract_entries)

@app.route('/add_contract', methods=['GET', 'POST'])
def add_income():
    if request.method == 'POST':
        driver_name = request.form.get('driver_name', 'Unknown Driver')
        contract_type = request.form.get('contract_type', 'Regular')
        monthly_fee = float(request.form.get('monthly_fee', 0))
        commission_rate = float(request.form.get('commission_rate', 0))
        total_revenue = float(request.form.get('total_revenue', 0))
        
        # Calculate net income based on contract type
        if contract_type == 'Commission Only':
            net_income = total_revenue * (1 - commission_rate / 100)
        elif contract_type == 'Monthly Rental':
            net_income = total_revenue - monthly_fee
        else:  # Fixed Monthly
            net_income = monthly_fee
        
        new_contract = {
            'id': len(mock_employment_contracts) + 1,
            'driver_name': driver_name,
            'contract_type': contract_type,
            'monthly_fee': monthly_fee,
            'commission_rate': commission_rate,
            'total_revenue': total_revenue,
            'net_income': net_income,
            'status': 'Active',
            'month': datetime.now().strftime('%B %Y'),
            'start_date': datetime.now().date(),
            'car': mock_cars[0] if mock_cars else None
        }
        
        mock_employment_contracts.append(new_contract)
        flash(f'Employment contract for {driver_name} ({contract_type}) added successfully!', 'success')
        return redirect(url_for('income'))
    return render_template('income/add.html', cars=mock_cars, datetime=datetime)

# Keep old routes for compatibility
@app.route('/income')
def income_redirect():
    return redirect(url_for('income'))

@app.route('/add_income', methods=['GET', 'POST'])
def add_income_redirect():
    return redirect(url_for('add_income'))

@app.route('/expenses')
def expenses():
    page = request.args.get('page', 1, type=int)
    expense_entries = MockPagination(mock_expenses, page)
    return render_template('expenses/list.html', expense_entries=expense_entries)

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        category = request.form.get('category', 'Miscellaneous')
        description = request.form.get('description', '')
        vendor = request.form.get('vendor', '')
        receipt_number = request.form.get('receipt_number', '')
        is_tax_deductible = bool(request.form.get('is_tax_deductible'))
        
        new_expense = {
            'id': len(mock_expenses) + 1,
            'amount': amount,
            'category': category,
            'description': description,
            'vendor': vendor,
            'receipt_number': receipt_number,
            'is_tax_deductible': is_tax_deductible,
            'date_recorded': datetime.now().date(),
            'created_at': datetime.now(),
            'car': mock_cars[0] if mock_cars else None
        }
        
        mock_expenses.append(new_expense)
        flash(f'Expense entry of {amount} SEK for {category} added successfully!', 'success')
        return redirect(url_for('expenses'))
    return render_template('expenses/add.html', cars=mock_cars)

@app.route('/cars')
def cars():
    return render_template('cars/list.html', cars=mock_cars)

@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        make = request.form.get('make')
        model = request.form.get('model')
        flash(f'Demo: Vehicle {make} {model} added successfully!', 'success')
        return redirect(url_for('cars'))
    return render_template('cars/add.html')

@app.route('/reports')
def reports():
    return render_template('reports/index.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    flash(f'Demo: Report for {start_date} to {end_date} would be generated in production!', 'info')
    return redirect(url_for('reports'))

@app.route('/analytics')
def analytics():
    """Analytics dashboard with comprehensive insights"""
    return render_template('analytics/index.html')

@app.route('/api/analytics/overview')
def api_analytics_overview():
    """API endpoint for analytics overview data"""
    current_summary = calculate_mock_summary()
    
    # Mock monthly trends based on actual data
    monthly_trends = []
    for month in range(1, 13):
        if month == datetime.now().month:
            monthly_trends.append({
                'month': month,
                'income': current_summary.get('total_income', 0),
                'expenses': current_summary.get('total_expenses', 0),
                'profit': current_summary.get('net_profit', 0),
                'trips': len(mock_employment_contracts)
            })
        else:
            monthly_trends.append({
                'month': month,
                'income': 0,
                'expenses': 0,
                'profit': 0,
                'trips': 0
            })
    
    # Platform breakdown from contracts
    platform_data = []
    platform_totals = {}
    for contract in mock_employment_contracts:
        platform = contract.get('contract_type', 'Unknown')
        if platform not in platform_totals:
            platform_totals[platform] = {'amount': 0, 'trips': 0}
        platform_totals[platform]['amount'] += contract.get('net_income', 0)
        platform_totals[platform]['trips'] += 1
    
    platform_data = [{
        'platform': platform,
        'amount': data['amount'],
        'trips': data['trips']
    } for platform, data in platform_totals.items()]
    
    # Expense categories from expenses
    expense_data = []
    expense_totals = {}
    for expense in mock_expenses:
        category = expense.get('category', 'Miscellaneous')
        if category not in expense_totals:
            expense_totals[category] = {'amount': 0, 'count': 0}
        expense_totals[category]['amount'] += expense.get('amount', 0)
        expense_totals[category]['count'] += 1
    
    expense_data = [{
        'category': category,
        'amount': data['amount'],
        'count': data['count']
    } for category, data in expense_totals.items()]
    
    # Calculate metrics
    total_income = current_summary.get('total_income', 0)
    total_expenses = current_summary.get('total_expenses', 0)
    total_trips = len(mock_employment_contracts)
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
def api_analytics_time():
    """API endpoint for time-based analytics"""
    # Mock daily patterns
    daily_data = [
        {'day': 'Sunday', 'avg_income': 800, 'trips': 3},
        {'day': 'Monday', 'avg_income': 1200, 'trips': 5},
        {'day': 'Tuesday', 'avg_income': 1100, 'trips': 4},
        {'day': 'Wednesday', 'avg_income': 1300, 'trips': 6},
        {'day': 'Thursday', 'avg_income': 1400, 'trips': 6},
        {'day': 'Friday', 'avg_income': 1800, 'trips': 8},
        {'day': 'Saturday', 'avg_income': 2000, 'trips': 9}
    ]
    
    return jsonify({
        'daily_patterns': daily_data,
        'hourly_patterns': []
    })

@app.route('/api/analytics/performance')
def api_analytics_performance():
    """API endpoint for performance analytics"""
    # Mock best days based on current contracts
    best_days = []
    for i, contract in enumerate(mock_employment_contracts[:10]):
        best_days.append({
            'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
            'income': contract.get('net_income', 0),
            'trips': 1
        })
    
    # Mock car performance
    car_performance = []
    for car in mock_cars:
        total_income = sum(c.get('net_income', 0) for c in mock_employment_contracts)
        car_performance.append({
            'car': f"{car['make']} {car['model']} ({car['license_plate']})",
            'income': total_income / len(mock_cars) if mock_cars else 0,
            'trips': len(mock_employment_contracts) // len(mock_cars) if mock_cars else 0,
            'avg_value': (total_income / len(mock_cars) / max(1, len(mock_employment_contracts))) if mock_cars and mock_employment_contracts else 0
        })
    
    return jsonify({
        'best_days': best_days,
        'car_performance': car_performance
    })

@app.route('/api/monthly_stats')
def api_monthly_stats():
    """API endpoint for monthly statistics - returns actual user data"""
    current_summary = calculate_mock_summary()
    monthly_data = []
    for month in range(1, 13):
        # Use actual data for current month, zero for other months in demo
        if month == datetime.now().month:
            monthly_data.append({
                'month': month,
                'income': current_summary.get('total_income', 0),
                'expenses': current_summary.get('total_expenses', 0),
                'profit': current_summary.get('net_profit', 0)
            })
        else:
            monthly_data.append({
                'month': month,
                'income': 0,
                'expenses': 0,
                'profit': 0
            })
    return monthly_data

@app.route('/profile')
def profile():
    return render_template('profile.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    print("TaxiTracker Pro - Demo Version Starting...")
    print("Access at: http://localhost:5000")
    print("All pages functional with mock data")
    print("Perfect for frontend testing!")
    app.run(host='127.0.0.1', port=5000, debug=True)