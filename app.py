from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.secret_key='secret123'

# CONFIG MySQL 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'roxy'
app.config['MYSQL_DB'] = 'flaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)



@app.route('/')
def home():
    return render_template('home.html')


#Register Form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=30)])
    username = StringField('Username', [validators.Length(min=4, max=30)])
    email = StringField('Email', [validators.Length(min=6, max=40)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create Cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to Database
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash("You are now registered and can log in", "success")

        #redirect(url_for('index'))

        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error= error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error= error)

    return render_template('login.html')

# Check if User is Logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM tasks")

    tasks = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', tasks=tasks)
    else:
        msg = 'No Tasks found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

    

#Task Form class
class TaskForm(Form):
    title = StringField('Title', [validators.Length(min=4, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Task
@app.route('/add_task', methods=['GET', 'POST'])
@is_logged_in
def add_task():
    form = TaskForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO tasks(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to the Database
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Task added', 'success')

        #redirect
        return redirect(url_for('dashboard'))

    return render_template('add_task.html', form=form)

# Edit Task
@app.route('/edit_task/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_task(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get task by id
    result = cur.execute("SELECT * FROM tasks WHERE id = %s", [id])

    task = cur.fetchone()

    # Get form
    form = TaskForm(request.form)

    # Populate task form fields
    form.title.data = task['title']
    form.body.data = task['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE tasks SET title=%s, body=%s WHERE id = %s", (title, body, id))

        # Commit to the Database
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Task Updated', 'success')

        #redirect
        return redirect(url_for('dashboard'))

    return render_template('edit_task.html', form=form)

# Delete Task
@app.route('/delete_task/<string:id>', methods=['POST'])
@is_logged_in
def delete_task(id):
    # Create a cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM tasks WHERE id = %s", [id])

    # Commit to Database
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('Task Deleted', 'success')

    #redirect
    return redirect(url_for('dashboard'))


@app.route('/tasks')
def tasks():
    # Create cursor
    cur = mysql.connection.cursor()
 
    # Get articles
    result = cur.execute("SELECT * FROM tasks")

    tasks = cur.fetchall()

    if result > 0:
        return render_template('tasks.html', tasks=tasks)
    else:
        msg = 'No Tasks found'
        return render_template('tasks.html', msg=msg)
    # Close connection
    cur.close()

# Single Task
@app.route('/task/<string:id>/')
def task(id):
    # Create cursor
    cur = mysql.connection.cursor()
 
    # Get task
    result = cur.execute("SELECT * FROM tasks WHERE id = %s", [id])

    task = cur.fetchone()

    return render_template('task.html', task=task)