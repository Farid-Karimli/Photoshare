######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Cs460MYSQL'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

def getUserInfo(uid):
	cursor = conn.cursor()
	cursor.execute(f"SELECT firstname,lastname FROM Users WHERE user_id = {uid}")
	info_raw = cursor.fetchall()[0]
	info = {'firstname': info_raw[0], 'lastname': info_raw[1]}
	return info



@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='Enter your password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		date=request.form.get('birthdate')
		context = {'firstname': firstname, 'lastname': lastname, 'email': email}
		print(request.form)
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password,firstname,lastname,birthdate) VALUES ('{0}','{1}','{2}','{3}','{4}')".format(email, password,firstname,lastname,date)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', info=context, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

# NOTE list of tuples, [(imgdata, pid), ...]

def getUserAlbums(uid):
	cursor = conn.cursor()
	cursor.execute(f"SELECT album_id,album_name,date_created,cover_img FROM Albums WHERE owner = {uid}")
	info_raw = cursor.fetchall()
	return info_raw

def getUserFriends(uid):
	cursor = conn.cursor()
	cursor.execute(f"SELECT user2 FROM friends_with WHERE user1 = {uid}")
	info_raw = cursor.fetchall()
	return info_raw

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]


def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute(f"SELECT firstname,lastname FROM Users WHERE user_id = {uid}")
	info_raw = cursor.fetchall()[0]
	info = {'firstname':info_raw[0],'lastname': info_raw[1]}
	return render_template('hello.html', name=flask_login.current_user.id,photos=getUsersPhotos(uid),base64=base64,info=info)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload/<album_id>', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file(album_id):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption,album_id) VALUES (%s, %s, %s, %s )''' ,(photo_data,uid, caption,album_id))
		conn.commit()
		return flask.redirect(flask.url_for('album',id=album_id))
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html',album_id=album_id)
#end photo uploading code



@app.route('/add_friends', methods=['GET', 'POST'])
@flask_login.login_required
def add_friends():
	cursor = conn.cursor()
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		fullname=request.form.get('name')
		print(fullname)
		fullname = fullname.split()
		cursor.execute('''SELECT user_id, firstname, lastname FROM Users WHERE firstname = %s and lastname = %s''', (fullname[0], fullname[1]))
		data = cursor.fetchall()
		found = False
		if data:
			found = True
		return render_template('add_friends.html', data=data,found=found)
		
	else:
		return render_template('add_friends.html', data={},found=True)
		
	#The method is GET so we return a  HTML form to upload the a photo.
	
#end photo uploading code
@app.route('/add_friend', methods=['POST'])
@flask_login.login_required
def add_friend():
	cursor = conn.cursor()
	uid = getUserIdFromEmail(flask_login.current_user.id)
	data = {}
	if request.method == 'POST':

		friend_id = request.form.get('added_friend')[0]

		print(friend_id)

		cursor.execute('''SELECT user1, user2 FROM friends_with WHERE user1 = %s and user2 = %s''',
					   (uid, friend_id))

		existing_friends = cursor.fetchall()
		print(f"existing_friends: {existing_friends}")

		if existing_friends:
			print(f"You are already friends with {friend_id} ")
			return '''<p> You're already friends with this person </p>'''
		else:
			cursor.execute('''INSERT INTO friends_with (user1, user2) VALUES (%s, %s )''', (uid, friend_id))
			conn.commit()
			return render_template('friend.html', friends=getUserFriends(uid))


@app.route('/friends', methods=['GET'])
@flask_login.login_required
def friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friend.html', friends=getUserFriends(uid))


@app.route('/delete', methods=['GET','POST'])
@flask_login.login_required
def delete_photo():

	if request.method == "POST":
		print(request.form.get('photo'))
		photo_id = request.form.get('photo')
		cursor = conn.cursor()
		cursor.execute(f'DELETE FROM Pictures WHERE picture_id={photo_id}')
		conn.commit()
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)

	uid=getUserIdFromEmail(flask_login.current_user.id)
	photos = getUsersPhotos(uid)
	return render_template("delete_photos.html",photos=photos,base64=base64)

@app.route("/upload-album", methods=['GET','POST'])
@flask_login.login_required
def create_album():
	if request.method == "POST":
		uid = getUserIdFromEmail(flask_login.current_user.id)

		album_name = request.form.get('name')
		cover_img_file = request.files['cover_img']
		date = request.form.get('created')
		cover_img_data = cover_img_file.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (owner, album_name, date_created,cover_img) VALUES (%s, %s, %s, %s)''' ,(uid,album_name, date,cover_img_data))


		conn.commit()
		return flask.redirect("/albums")

	return '''
			   <form action='upload-album' method='POST' enctype="multipart/form-data">
			    <label for="name">Enter the name of the album:</label>
				<input type='text' name='name' id='album_name' placeholder='Album name'></input><br/>
				
				<label for="cover_img">Select cover image:</label>
                <input type="file" name="cover_img" required='true' /><br />
                
                				
				<input type='date' name='created'/>
				
				<input type='submit' name='submit' value="Create"></input>
			   </form></br>
			   '''



@app.route("/albums", methods=['GET','POST'])
@flask_login.login_required
def albums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	album_list = getUserAlbums(uid)

	return render_template("albums.html", albums=album_list, base64=base64)

@app.route("/album/<id>",methods=['GET'])
@flask_login.login_required
def album(id):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute(f"SELECT album_name,date_created,cover_img FROM Albums WHERE album_id={id}")
	album = cursor.fetchall()[0]
	cursor.execute(f'SELECT picture_id, imgdata,caption FROM Pictures WHERE album_id = {id}')
	photos = cursor.fetchall()
	return render_template("album.html", photos=photos, album=album, album_id=id, base64=base64)

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)

