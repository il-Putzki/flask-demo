from flask import Flask, flash, render_template, request, redirect, session, url_for
from flask_table import Table, Col
from werkzeug.security import generate_password_hash
import pymysql
from flaskext.mysql import MySQL
from wtforms import StringField, PasswordField, validators, Form
from passlib.hash import sha256_crypt
import os


app = Flask(__name__)
mysql = MySQL()
app.config['SECRET_KEY'] = os.getenv('app_secret')
app.config['MYSQL_DATABASE_USER'] = os.getenv('mysql_user')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('mysql_pass')
app.config['MYSQL_DATABASE_DB'] = os.getenv('mysql_db')
app.config['MYSQL_DATABASE_HOST'] = os.getenv('mysql_host')
mysql.init_app(app)

table_name1 = 'admins'
table_name2 = 'users'
connection = mysql.connect()
cur = connection.cursor()
sql1 = "CREATE table if not exists " + table_name1 + "(username varchar(30), password varchar(100))"
sql2 = "CREATE table if not exists " + table_name2 + "(user_id int(5) NOT NULL AUTO_INCREMENT PRIMARY KEY, " \
                                                     "user_name varchar(30), " \
                                                     "user_email varchar(50), user_password varchar(100))"
cur.execute(sql1)
cur.execute(sql2)
connection.commit()
cur.close()


@app.route('/', methods=['GET', 'POST'])
def main_page():
    if session.get('logged_in'):
        return redirect((url_for('dashboard')))
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        db_select = f"SELECT password FROM admins WHERE username = '{username}'"
        cursor = mysql.connect().cursor()
        cursor.execute(db_select)
        res = cursor.fetchone()

        if res:
            password = res[0]
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid password'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


class RegisterForm(Form):
    username = StringField('Username', [validators.length(min=1, max=50)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    regform = RegisterForm(request.form)
    if request.method == 'POST' and regform.validate():
        username = regform.username.data
        password = sha256_crypt.encrypt(str(regform.password.data))
        conn = mysql.connect()
        cur = conn.cursor()
        query = f"INSERT INTO admins(username, password) VALUES ('{username}', '{password}')"
        cur.execute(query)
        conn.commit()
        cur.close()
        flash("You are registered", 'success')
        return redirect((url_for('dashboard')))
    return render_template('register.html', form=regform)


@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'logout')
    return redirect(url_for('main_page'))


@app.route('/dashboard')
def dashboard():
    if session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('main_page'))


class AddUserForm(Form):
    user_name = StringField('Username', [validators.DataRequired(), validators.length(min=1, max=50)])
    user_email = StringField('Email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


@app.route('/add', methods=['POST', 'GET'])
def add_user():
    form_user = AddUserForm(request.form)
    if request.method == 'POST' and form_user.validate():
        user_name = request.form['user_name']
        user_email = request.form['user_email']
        user_password = request.form['password']
        _hashed_password = sha256_crypt.encrypt(str(user_password))
        # save edits
        sql = f"INSERT INTO users(user_name, user_email, user_password) VALUES('{user_name}', '{user_email}', '{_hashed_password}')"
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        flash('User added successfully!')
        return redirect('/list')
    else:
        return render_template('add.html')


class ItemTable(Table):
    name = Col('Name')
    description = Col('Description')


@app.route('/list', methods=['GET'])
def users():
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, user_name, user_email FROM users")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('users.html', rows=rows)


@app.route('/edit/<int:id>')
def edit(id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE user_id=%s", id)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit.html', row=row)


@app.route('/update', methods=['POST'])
def update_user():
    _name = request.form['user_name']
    _email = request.form['user_email']
    _password = request.form['user_password']
    _id = request.form['id']
    # validate the received values
    if _name and _email and _password and _id and request.method == 'POST':
        # do not save password as a plain text
        _hashed_password = generate_password_hash(_password)
        # save edits
        sql = "UPDATE users SET user_name=%s, user_email=%s, user_password=%s WHERE user_id=%s"
        data = (_name, _email, _hashed_password, _id,)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        flash('User updated successfully!')
        return redirect('/')
    else:
        return 'Error while updating user'


@app.route('/delete/<int:id>')
def delete_user(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id=%s", (id,))
    conn.commit()
    flash('User deleted successfully!')
    cursor.close()
    conn.close()
    return redirect('/')


if __name__ == "__main__":
    app.run()
