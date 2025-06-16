import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nigerian_food.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.secret_key = 'your_secret_key_here'

db = SQLAlchemy(app)
# ------------------ LOGIN REQUIRED DECORATOR ------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Login required to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------ MODELS ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(50))
    reviews = db.relationship('Review', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(100), unique=True)
    dishes = db.relationship('Dish', backref='vendor', lazy=True)

class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(200))
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    order_items = db.relationship('OrderItem', backref='dish', lazy=True)
    reviews = db.relationship('Review', backref='dish', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50))
    total_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    payment = db.relationship('Payment', backref='order', uselist=False)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'))
    quantity = db.Column(db.Integer)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    method = db.Column(db.String(50))
    amount = db.Column(db.Float)
    status = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)

# ------------------ ROUTES ------------------

@app.route('/')
def index():
    dishes = Dish.query.limit(3).all()
    return render_template('home.html', dishes=dishes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = 'customer'
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_role'] = user.role
            flash('Login successful.', 'success')
            if user.role == 'vendor':
                return redirect(url_for('vendor_dashboard'))
            return redirect(url_for('index'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/vendor')
def vendor_dashboard():
    if 'user_role' in session and session['user_role'] == 'vendor':
        return render_template('vendor_dashboard.html')
    flash('Access restricted to vendors.', 'danger')
    return redirect(url_for('login'))

@app.route('/checkout/<int:order_id>', methods=['GET', 'POST'])
@login_required
def checkout(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        method = request.form['method']
        transaction_id = request.form['transaction_id']
        payment = Payment(order_id=order.id, method=method, amount=order.total_price, status='Paid', transaction_id=transaction_id)
        db.session.add(payment)
        order.status = 'Paid'
        db.session.commit()
        flash('Payment successful!', 'success')
        return redirect(url_for('my_orders'))
    return render_template('checkout.html', order=order)

@app.route('/order/<int:dish_id>', methods=['POST'])
@login_required
def place_order(dish_id):
    quantity = int(request.form['quantity'])
    dish = Dish.query.get_or_404(dish_id)
    total_price = dish.price * quantity
    order = Order(user_id=session['user_id'], status='Pending', total_price=total_price)
    db.session.add(order)
    db.session.commit()

    order_item = OrderItem(order_id=order.id, dish_id=dish.id, quantity=quantity)
    db.session.add(order_item)
    db.session.commit()

    flash('Order placed successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/vendor/orders')
@login_required
def vendor_orders():
    if session.get('user_role') != 'vendor':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    vendor = Vendor.query.filter_by(contact_email=session.get('user_email')).first()
    dishes = Dish.query.filter_by(vendor_id=vendor.id).all()
    dish_ids = [dish.id for dish in dishes]
    order_items = OrderItem.query.filter(OrderItem.dish_id.in_(dish_ids)).all()
    return render_template('vendor_orders.html', order_items=order_items)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)






