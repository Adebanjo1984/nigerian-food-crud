import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from functools import wraps
from models import db, Dish

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nigerian_food.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.secret_key = 'your_secret_key_here'

db.init_app(app)

# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/')
@login_required
def index():
    query = request.args.get('q')
    if query:
        dishes = Dish.query.filter(Dish.name.ilike(f"%{query}%")).all()
    else:
        dishes = Dish.query.all()
    return render_template('index.html', dishes=dishes)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        category = request.form['category']
        image = request.files['image']
        filename = None
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_dish = Dish(name=name, description=description, price=price,
                        category=category, image_url=filename)
        db.session.add(new_dish)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    dish = Dish.query.get_or_404(id)
    if request.method == 'POST':
        dish.name = request.form['name']
        dish.description = request.form['description']
        dish.price = float(request.form['price'])
        dish.category = request.form['category']
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            dish.image_url = filename
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('update.html', dish=dish)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    dish = Dish.query.get_or_404(id)
    db.session.delete(dish)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/home')
def home():
    dishes = Dish.query.limit(3).all()
    return render_template('home.html', dishes=dishes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


