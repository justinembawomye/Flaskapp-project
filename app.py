from flask import Flask, render_template, url_for, request, flash, redirect, session, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps 


app = Flask(__name__)
app.secret_key = "123ert"

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'justine'
app.config['MYSQL_DB'] = 'myflaskproject'
app.config['MYSQL_CURSORCLASS'] ='DictCursor' 

#initialize MYSQl
mysql = MySQL(app)


dogs = ['jack','billy','jery']
youngones = ['kid','puppy','calf','kitten']

#@app.route('/')
#def hello_world():
    #return 'Todo_List App'


#Articles = Articles()

'''@app.route('/')
def justine():
    return render_template('home.html', animals=dogs,sample = youngones)'''

@app.route('/')
def layout():
    return render_template('layout.html')

'''@app.route('/todo')    
def myApp():
    return render_template('todolist.html')
@app.route('/active')
def active():
    return render_template('active.html')
@app.route('/completed') 
def completed():
    return render_template('completed.html')''' 
'''@app.route('/logout')
def logout():
    return render_template('home.html')'''
         
#@app.route('/login')
#def login():
 #   return render_template('active.html')


'''#tasks
@app.route('/tasks')
def tasks():'''


#single article
@app.route('/article/<string:id>/')
def article(id):
     #create cursor
    cur = mysql.connection.cursor()

    #Get tasks
    result = cur.execute("SELECT * FROM tasks")


    tasks = cur.fetchall()

    if result > 0:
        return render_template('article.html', tasks=tasks)
    else:
        msg ="No tasks Found"    
        return render_template('article.html', msg=msg)

     #close connection
    cur.close()   
    

#Register Form class
#WTforms
class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1, max=50)])  
    username = StringField('Username',[validators.Length(min=4, max=25)])
    email = StringField('Email',[validators.Length(min=7, max=50)])  
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

#User Register
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        '''return render_template('register.html') '''
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create Cursor
        cur = mysql.connection.cursor()

        #Execute Query  
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))
        #commit to database(DB)
        mysql.connection.commit()
        #close connection
        cur.close()

        #flash msg
        flash('You are now registered and can login','success')

        return redirect(url_for('layout'))
    return render_template('register.html',form=form)    

#login
@app.route('/login', methods = ['GET', 'POST'])
def login():
   if request.method == 'POST':
    #Get Form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create a cursor
        cur = mysql.connection.cursor()

        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])


        if result > 0:
            data = cur.fetchone()
            password = data['password']


            if sha256_crypt.verify(password_candidate, password):
                   #passed
                    session['logged_in'] = True
                    session['username'] = username

                    flash('You are now logged in', 'success')
                    return redirect(url_for('dashboard'))
           

           
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            #close connection   
            cur.close()
             
        else:
            error = 'username not found'
            return render_template('login.html', error=error)

   return render_template('login.html')

#Check if the user is logged_in 
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login',  'danger')
            return redirect(url_for('login'))
    return wrap




   #logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('login')) 

#dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #create cursor
    cur = mysql.connection.cursor()

    #Get tasks
    result = cur.execute("SELECT * FROM tasks")


    tasks = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', tasks=tasks)
    else:
        msg ="No tasks Found"    
        return render_template('dashboard.html', msg=msg)

     #close connection
    cur.close()   


#Task Form class
#WTforms
class TaskForm(Form):
    title= StringField('Title',[validators.Length(min=1, max=150)])  
    body = TextAreaField('Body',[validators.Length(min=5)])

    

#Add_tasks
@app.route('/add_tasks', methods = ['GET', 'POST'])
@is_logged_in
def add_tasks():
   form = TaskForm(request.form)
   if request.method == 'POST' and form.validate():
       title = form.title.data
       body = form.body.data


       #create cursor
       cur = mysql.connection.cursor()


      #Execute
       cur.execute("INSERT  INTO tasks(title, body, author) VALUES(%s, %s, %s)",  (title, body, session['username']))

      #commit
       mysql.connection.commit()
      

      #close connection
       cur.close()
 
      #flash
       flash('Task added',  'success')

       return redirect(url_for('dashboard'))

   return render_template('add_tasks.html',  form=form) 
                        

            