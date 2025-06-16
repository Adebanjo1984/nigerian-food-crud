from flask import Flask, render_template, request, redirect, url_for
from models import db, Dish

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nigerian_food.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def index():
    dishes = Dish.query.all()
    return render_template('index.html', dishes=dishes)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        category = request.form['category']
        new_dish = Dish(name=name, description=description, price=price, category=category)
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
    app.run(debug=True)
