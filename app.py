import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from models import db, Dish

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nigerian_food.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

@app.route('/')
def index():
    query = request.args.get('q')
    if query:
        dishes = Dish.query.filter(Dish.name.ilike(f"%{query}%")).all()
    else:
        dishes = Dish.query.all()
    return render_template('index.html', dishes=dishes)

@app.route('/create', methods=['GET', 'POST'])
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

        new_dish = Dish(
            name=name,
            description=description,
            price=price,
            category=category,
            image_url=filename
        )
        db.session.add(new_dish)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
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
def delete(id):
    dish = Dish.query.get_or_404(id)
    db.session.delete(dish)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

