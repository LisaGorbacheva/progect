import sqlite3


class DB:
    def __init__(self):
        conn = sqlite3.connect('news.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class UserModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             login VARCHAR(50),
                             password VARCHAR(128),
                             username VARCHAR(200),
                             info VARCHAR(500)

                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, login, username, password, info):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users 
                          (login, username, password, info) 
                          VALUES (?,?,?,?)''', (login, username, password, info))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id)))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, username, password):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False, None)


class FollowModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS follows 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             user_id VARCHAR(50),
                             follow_id VARCHAR(50)

                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, my_id, follow_id):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO follows 
                          (user_id, follow_id) 
                          VALUES (?,?)''', (my_id, follow_id))
        cursor.close()
        self.connection.commit()

    def get_follow_post(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE user_id in (select follow_id from follows where user_id = " + (
            str(user_id)) + " ) ORDER BY id DESC")
        rows = cursor.fetchall()
        return rows

    def delete(self, user_id, follow_id):
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM follows WHERE follow_id = ' + str(follow_id) + ' user_id = ' + str(user_id))
        cursor.close()
        self.connection.commit()


class NewsModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS news 
                                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                   post VARCHAR(1000),
                                   user_id INTEGER
                                   )''')
        cursor.close()
        self.connection.commit()

    def insert(self, content, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO news 
                            ( post, user_id) 
                            VALUES (?,?)''', (content, str(user_id)))
        cursor.close()
        self.connection.commit()

    def get(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE id = ?", (str(news_id)))
        row = cursor.fetchone()
        return row

    def get_all(self, user_id=None):
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM news WHERE user_id = " + (str(user_id)) + " ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM news")
        rows = cursor.fetchall()
        return rows

    def delete(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM news WHERE id = ''' + str(news_id))
        cursor.close()
        self.connection.commit()


db = DB()
user_model = UserModel(db.get_connection())
news_model = NewsModel(db.get_connection())
follow_model = FollowModel(db.get_connection())
user_model.init_table()
news_model.init_table()
follow_model.init_table()

from flask import Flask, redirect, render_template, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


class RegistrationForm(FlaskForm):
    username = StringField('Nickname', validators=[DataRequired()])
    login = StringField('Login', validators=[DataRequired()])
    info = StringField('Info', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_test = PasswordField('Повторите пароль', validators=[DataRequired()])
    reg = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class AddPost(FlaskForm):
    post = TextAreaField('Post', validators=[DataRequired()])
    submit = SubmitField('Добавить')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
user_id = None
user_status = False


# http://127.0.0.1:8080/login
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    global user_id, user_status
    form = LoginForm()
    user_status, user_id = user_model.exists(form.username.data, form.password.data)

    if form.validate_on_submit() and user_status:
        session["username"] = form.username.data
        return redirect('/news')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session["username"] = ""
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    global user_id, user_status
    form = RegistrationForm()
    if form.validate_on_submit():
        user_model.insert(form.login.data, form.username.data, form.password.data, form.info.data)
        return redirect('/login')
    return render_template('register.html', title='Авторизация', form=form)


@app.route('/index')
def index():
    if user_status:
        news_list = news_model.get_all(user_id)
        print(news_list)
        return render_template('index.html', posts=news_list)
    else:
        return redirect('/login')


@app.route('/news')
def news():
    if user_status:
        news_list = follow_model.get_follow_post(user_id)
        return render_template('news.html', posts=news_list)
    else:
        return redirect('/login')


@app.route('/all_user')
def all_user():
    if user_status:
        user_list = user_model.get_all()
        return render_template('userlist.html', users=user_list)
    else:
        return redirect('/login')


@app.route('/tweet', methods=['GET', 'POST'])
def add_news():
    if not user_status:
        return redirect('/login')
    form = AddPost()
    if form.validate_on_submit():
        post = form.post.data
        news_model.insert(post, user_id)
        return redirect("/index")
    return render_template('tweet.html', title='Добавление post', form=form, username=user_id)


@app.route('/delete_post/<int:news_id>', methods=['GET'])
def delete_post(news_id):
    if not user_status:
        return redirect('/login')
    news_model.delete(news_id)
    return redirect("/index")


@app.route('/add_user/<int:follow_id>', methods=['GET'])
def add_user(follow_id):
    if not user_status:
        return redirect('/login')
    follow_model.insert(user_id, follow_id)
    return redirect("/all_user")


@app.route('/del_user/<int:follow_id>', methods=['GET'])
def del_user(follow_id):
    if not user_status:
        return redirect('/login')
        follow_model.delete(user_id, follow_id)
    return redirect("/all_user")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', debug=True)
