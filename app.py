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
import datetime
#for image uploading
import os, base64
import datetime

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
	cursor.execute(f"SELECT * FROM Users WHERE user_id = {uid}")
	info_raw = cursor.fetchall()[0]
	return info_raw

def editUserInfo(info_raw, info_map, old_pass):
	if(info_map[2] != "" and info_map[9] != old_pass):
		return render_template('edit_profile.html', incorrect_pass= True, supress = True)

	for i in range(len(info_raw)):
		if(info_map[i] == ''):
			info_map[i] = info_raw[i]

	cursor = conn.cursor()
	cursor.execute('''UPDATE users SET password = %s, firstname = %s, lastname = %s, birthdate = %s,\
					gender = %s, hometown = %s  where user_id = %s ''',\
					(info_map[2], info_map[3], info_map[4], info_map[5], info_map[6], info_map[7], info_map[0]))
	
	conn.commit()
	return getUserInfo(info_raw[0])

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
		return render_template('login.html')
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
	return render_template('hello.html', message='Logged out',need_login=True)

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

def getAlbumPhotos(album_id):
	cursor = conn.cursor()
	cursor.execute(f"SELECT imgdata,picture_id FROM Pictures WHERE album_id = {album_id}")
	info_raw = cursor.fetchall()
	return info_raw



def getUserFriends(uid):
	cursor = conn.cursor()
	cursor.execute(f'''SELECT user1,email,firstname,lastname,user2, contribution_score
						FROM photoshare.Users U
						LEFT JOIN friends_with F
						ON U.user_id = F.user2
						WHERE user1 = {uid}''')
	info_raw = cursor.fetchall()
	print(info_raw)
	return info_raw

def getLikedUsers(photo_id):
	cursor = conn.cursor()
	cursor.execute(f''' SELECT u.user_id, u.email, u.firstname, u.lastname, u.contribution_score, l.photo_id
					 	FROM Users u
						LEFT JOIN likes l 
						USING(user_id)
						Where photo_id = {photo_id}''')
	info_raw = cursor.fetchall()
	print(info_raw)
	return info_raw

def getPhotoComments(photo_id,comment_filter=None):
	cursor = conn.cursor()
	info_raw = None

	"""if filter is not None:
		print('Filtered')
		cursor.execute('''SELECT firstname,lastname,text,owner_id,comment_id
								FROM photoshare.Users U
								CROSS JOIN photoshare.Comments C
								ON U.user_id = C.owner_id
								WHERE picture_id = %s and text=\'%s\'''',(photo_id,comment_filter))
		info_raw = cursor.fetchall()
	else:
		cursor.execute(f'''SELECT firstname,lastname,text,owner_id,comment_id
							FROM photoshare.Users U
							CROSS JOIN photoshare.Comments C
							ON U.user_id = C.owner_id
							WHERE picture_id = {photo_id}; ''')
		info_raw = cursor.fetchall()"""

	cursor.execute(f'''SELECT firstname,lastname,text,owner_id,comment_id
								FROM photoshare.Users U
								CROSS JOIN photoshare.Comments C
								ON U.user_id = C.owner_id
								WHERE picture_id = {photo_id}; ''')
	info_raw = cursor.fetchall()
	print(info_raw)
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
		cursor.execute(f"UPDATE Users SET contribution_score = contribution_score+1 WHERE user_id = {uid};")
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
		


@app.route('/add_friend', methods=['POST'])
@flask_login.login_required
def add_friend():
	cursor = conn.cursor()
	uid = getUserIdFromEmail(flask_login.current_user.id)
	data = {}
	if request.method == 'POST':

		friend_id = request.form.get('added_friend')[0]

		print("same", uid == friend_id)

		if((int)(uid) == (int)(friend_id)):
			print(f"You can't be friends with yourself. ")
			return render_template('add_friends.html', data={},found=True, friend_self = True)

		else:
			cursor.execute('''SELECT user1, user2 FROM friends_with WHERE user1 = %s and user2 = %s''',
						(uid, friend_id))

			existing_friends = cursor.fetchall()
			if existing_friends:
				return render_template('add_friends.html', data={},found=True, existing_friends = True)
			else:
				print("No issue until here")
				cursor.execute('''INSERT INTO friends_with (user1, user2) VALUES (%s, %s )''', (uid, friend_id))
				cursor.execute('''INSERT INTO friends_with (user1, user2) VALUES (%s, %s )''', (friend_id, uid))
				cursor.execute('''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''',(uid))
				cursor.execute('''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''',(friend_id))
				conn.commit()
				return render_template('friend.html', friends=getUserFriends(uid))



@app.route('/friends', methods=['GET'])
@flask_login.login_required
def friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friend.html', friends=getUserFriends(uid))


@app.route('/delete/<album_id>', methods=['GET','POST'])
@flask_login.login_required
def delete_photo(album_id):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == "POST":
		print(request.form.get('photo'))
		photo_id = request.form.get('photo')
		cursor = conn.cursor()
		cursor.execute('DELETE FROM Pictures WHERE picture_id=%s and album_id=%s',(photo_id,album_id))
		cursor.execute('''UPDATE Users SET contribution_score = (contribution_score - 1) WHERE user_id = %s''',(uid))
		conn.commit()
		return flask.redirect(flask.url_for('album',id=album_id))


	photos = getAlbumPhotos(album_id)
	return render_template("delete_photos.html",photos=photos,base64=base64,album=album_id)


@app.route("/upload-album", methods=['GET','POST'])
@flask_login.login_required
def create_album():
	if request.method == "POST":
		uid = getUserIdFromEmail(flask_login.current_user.id)

		album_name = request.form.get('name')
		cover_img_file = request.files['cover_img']
		#date = request.form.get('created')
		cover_img_data = cover_img_file.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (owner, album_name,cover_img) VALUES ( %s, %s, %s)''' ,(uid,album_name,cover_img_data))
		conn.commit()
		return flask.redirect("/albums")

	return '''
			   <form action='upload-album' method='POST' enctype="multipart/form-data">
			    <label for="name">Enter the name of the album:</label>
				<input type='text' name='name' id='album_name' placeholder='Album name'></input><br/>
				
				<label for="cover_img">Select cover image:</label>
                <input type="file" name="cover_img" required='true' /><br />
				
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
def album(id):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute(f"SELECT album_name,date_created,cover_img FROM Albums WHERE album_id={id}")
	album = cursor.fetchall()[0]
	cursor.execute(f'SELECT picture_id, imgdata,caption FROM Pictures WHERE album_id = {id}')
	photos = cursor.fetchall()
	return render_template("album.html", photos=photos, album=album, album_id=id, base64=base64)

@app.route("/album/<album_id>/photo/<photo_id>",methods=['GET','POST'])
def photo(album_id,photo_id,comment_filter=None):
	uid=getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute('''SELECT imgdata,caption,likes FROM Pictures WHERE album_id=%s and picture_id = %s''',
				   (album_id, photo_id))
	data = cursor.fetchall()[0]

	if request.method=="POST":
		uid = getUserIdFromEmail(flask_login.current_user.id)
		comment = request.form.get('comment')
		to_delete = request.form.get('delete')
		like = request.form.get('like')
		cursor.execute('''SELECT user_id FROM Pictures WHERE picture_id = %s''', (photo_id))
		pic_owner = cursor.fetchall()[0][0]
		filter = request.form.get('filter')
		users_liked = request.form.get('users_liked')
		if comment:
			todays_date = str(datetime.date.today())
			if(pic_owner == uid):
				return render_template('photo.html', data=data, album_id=album_id, photo_id=photo_id, base64=base64,comments=getPhotoComments(photo_id),user=uid, dismiss_comment = True)
			cursor.execute('''INSERT INTO Comments (text, date_created, picture_id,owner_id) VALUES (%s, %s, %s, %s)''' ,(comment,todays_date, photo_id,uid))
			cursor.execute('''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''',(uid))
			conn.commit()

		elif to_delete:
			cursor.execute(f'''DELETE FROM Comments WHERE comment_id={to_delete}''')
			cursor.execute('''UPDATE Users SET contribution_score = (contribution_score - 1) WHERE user_id = %s''',(uid))
			conn.commit()

		elif like:
			if(pic_owner == uid):
				return render_template('photo.html', data=data, album_id=album_id, photo_id=photo_id, base64=base64,comments=getPhotoComments(photo_id),user=uid, dismiss_like = True)
			cursor.execute('''SELECT count(*) FROM likes WHERE user_id = %s and photo_id = %s  ''', (uid, photo_id))
			liked_earlier = cursor.fetchall()[0][0]
			if liked_earlier:
				cursor.execute('''DELETE FROM likes WHERE user_id = %s and photo_id = %s''', (uid, photo_id))
				cursor.execute(f'''UPDATE Pictures SET likes=likes-1 WHERE picture_id={photo_id}''')
				cursor.execute('''UPDATE Users SET contribution_score = (contribution_score - 1) WHERE user_id = %s''',(uid))
				conn.commit()
			else:
				cursor.execute(f'''UPDATE Pictures SET likes=likes+1 WHERE picture_id={photo_id}''')
				cursor.execute('''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''',(uid))
				cursor.execute('''INSERT INTO likes (user_id, photo_id) VALUES (%s, %s)''', (uid, photo_id))
				conn.commit()
		elif users_liked:
			users_liked = getLikedUsers(photo_id)
			print(users_liked)
			return render_template('photo.html', data=data, album_id=album_id, photo_id=photo_id, base64=base64,comments=getPhotoComments(photo_id),user=uid, get_liked_users = True, users_liked = users_liked)
		elif filter:
			print(f'Filtering... by filter: {filter}')
			return flask.redirect(url_for('photo', album_id=album_id, photo_id=photo_id,comment_filter=filter))

		return flask.redirect(url_for('photo',album_id=album_id,photo_id=photo_id))


	return render_template('photo.html', data=data,album_id=album_id,photo_id=photo_id,base64=base64,comments=getPhotoComments(photo_id,comment_filter=comment_filter),user=uid)

@app.route("/profile/upload",methods=['GET','POST'])
@flask_login.login_required
def upload_profile_pic():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method=='POST':
		imgfile = request.files['photo']
		photo_data = imgfile.read()
		cursor = conn.cursor()
		cursor.execute('UPDATE Users SET profile_img=%s WHERE user_id=%s',(photo_data,uid))
		cursor.execute('''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''',(uid))
		conn.commit()
		return flask.redirect(flask.url_for('profile'))

	return render_template('profile_upload.html',user=uid)



@app.route("/profile", methods=['GET'])
@flask_login.login_required
def profile():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	userInfo = getUserInfo(uid)
	print(f'userinfo {userInfo}')
	return render_template("profile.html", userInfo = userInfo,base64=base64)

@app.route("/edit_profile", methods=['GET', "POST"])
@flask_login.login_required
def edit_profile():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method=="POST":
		info_raw = getUserInfo(uid)
		old_password=request.form.get('old_password')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		birthdate= request.form.get('birthdate')
		hometown = request.form.get('hometown')
		gender = request.form.get('gender')
		info_map = [info_raw[0], info_raw[1], password, firstname, lastname, birthdate, gender, hometown, info_raw[8], old_password]
		print("1", info_raw)
		print("2", info_map)
		current_password = info_raw[2]
		print("3",editUserInfo(info_raw, info_map, current_password))
		return flask.redirect(flask.url_for('profile'))
	return render_template("edit_profile.html", supress = True)

@app.route('/explore')
def explore():
	cursor = conn.cursor()
	cursor.execute('''SELECT cover_img, album_name, album_id
						FROM Albums 
						CROSS JOIN Users
						ON Albums.owner = Users.user_id''')
	albums = cursor.fetchall()
	return render_template('explore.html',albums=albums,base64=base64)


@app.route('/')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute(f"SELECT firstname,lastname FROM Users WHERE user_id = {uid}")
	info_raw = cursor.fetchall()[0]
	info = {'firstname':info_raw[0],'lastname': info_raw[1]}
	return render_template('hello.html', name=flask_login.current_user.id,info=info)
#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)