import sqlalchemy.orm

from flask_wtf import RecaptchaField
from wtforms import Form

import sqlite3
from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user, login_manager
from flask_sqlalchemy import SQLAlchemy
import verify

from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.secret_key = 'some secret code123@#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

manager = LoginManager(app)
manager.init_app(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    isActive = db.Column(db.Boolean, default=True)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return self.title

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=True, unique=True)
    password = db.Column(db.String(255), nullable=False)
    fio = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True, unique=True)
    balance = db.Column(db.Integer, default=5000)

@manager.user_loader
def load_user(id):
    return User.query.get(id)

@app.route('/')
def selection():
    return render_template('selection.html')

@app.route('/index')
def Index():
    fio = session['fio']  # Извлекает фамилию из сессии и отображает её в поисковой строке
    balance = session['balance']
    item = Item.query.order_by(Item.price).all()
    return render_template('index.html', data=item, fio=fio, balance=balance)

@app.route('/search', methods=['POST'])
def search():
    # Получение данных из формы поиска
    query = request.form.get('query')
    fio = session['fio']  # Извлекает фамилию из сессии и отображает её в поисковой строке
    balance = session['balance']
    # Поиск услуг по запросу в названии или описании
    item = Item.query.filter((Item.title.like(f'%{query}%')) | (Item.text.like(f'%{query}%'))).all()
    return render_template('index.html', data=item, fio=fio, balance=balance)

@app.route('/sort', methods=['POST'])
def sort():
    # Получение значения сортировки из запроса
    sort_by = request.form.get('sort_by')

    # Получение списка всех услуг из базы данных с учетом сортировки
    if sort_by == 'price_asc':
        item = Item.query.order_by(Item.price.asc()).all()
    elif sort_by == 'price_desc':
        item = Item.query.order_by(Item.price.desc()).all()
    elif sort_by == 'name_asc':
        item = Item.query.order_by(Item.title.asc()).all()
    elif sort_by == 'name_desc':
        item = Item.query.order_by(Item.title.desc()).all()
    else:
        # Если не указано как сортировать, просто вернуть все услуги
        item = Item.query.all()

    return render_template('index.html', data=item)

@app.route('/registration', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        email = request.form.get('email')
        fio = request.form.get('fio')
        login = request.form.get('login')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if not (email and fio and login and password and password2):
            flash('Заполните все поля')
        elif password != password2:
            flash('Пароли не совпадают')
        else:
            hashed_pwd = generate_password_hash(password)
            new_user = User(login=login, password=hashed_pwd, fio=fio, email=email)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('Login'))

    return render_template('reg.html')

@app.route('/login', methods=['POST', 'GET'])
def Login():
    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user_id = User.query.filter_by(login=login).first()

        if user_id and check_password_hash(user_id.password, password):
            session['fio'] = user_id.fio  # Сохраняем фамилию пользователя в сессии
            session['balance'] = user_id.balance  # Сохраняем фамилию пользователя в сессии
            return redirect('/index')
            flash("Вы вошли как администратор")
        else:
            print('пользователь перенаправлен')
            return redirect('submit')
    else:
        flash("Вы не зарегистрированы")

    return render_template('log.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return 'вы вышли'

@app.route('/buy/<int:id>')
def Item_buy(id):
    item = Item.query.filter_by(id=id).first_or_404()
    balance = session.get('balance', 0)
    cost = item.price
    amount = item.amount
    print(id)
    print(cost)
    print(balance)

    if balance >= cost:
        session['balance'] = balance - cost
        item.amount = amount - 1
        db.session.commit()
        return redirect(url_for('.Index'))
    else:
        return jsonify({'message': 'Not enough balance to buy this item.'}), 400  # Возвращаем сообщение об ошибке'''

    return jsonify(results)
@app.route('/create', methods=['POST', 'GET'])
def Create():
    if request.method == "POST":
        title = request.form['title']
        price = request.form['price']
        text = request.form['text']
        amount = request.form['amount']
        item = Item(title=title, price=price, text=text, amount=amount)
        try:
            db.session.add(item)
            db.session.commit()
            return redirect('/index')
        except:
            return "Получилась Ошибка"
    else:
        return render_template('create.html')

@app.route('/<int:id>/update', methods=['POST', 'GET'])
def Update(id):
    item = Item.query.get(id)
    if request.method == "POST":
        item.title = request.form['title']
        item.price = request.form['price']
        item.text = request.form['text']

        try:
            db.session.commit()
            return redirect('/index')
        except:
            return "Получилась ошибка"
    else:

        return render_template('update.html', item=item)

@app.route('/<int:id>/delete')
def Del_Item(id):
    item = Item.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        return redirect('/index')
    except:
        return "При удалении товара произошла ошибка"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
