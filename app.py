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
# for image uploading
import os
import base64
import datetime

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Cs460MYSQL'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# begin code used for login
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


def convertTupleStr(tuple):
	string = '('
	for t in tuple:
		string = (string + str(t)) + ','
	string = string[:-1]
	string = string + ")"
	return string


def isFriend(uid1,uid2):
	SQL = f'SELECT * FROM Friends_with WHERE user1={uid1} AND user2={uid2}'
	cursor=conn.cursor()
	cursor.execute(SQL)
	data = cursor.fetchall()
	print(f'data: {data}')
	return not len(data) == 0


def getPhotos(caption=None):
	cursor = conn.cursor()
	if caption is None or caption == "":
		cursor.execute('''SELECT imgdata, caption, picture_id, album_id
							FROM Pictures
							ORDER BY likes DESC
							LIMIT 5''')
		data = cursor.fetchall()
		return data
	else:
		cursor.execute(f'''SELECT imgdata, caption, picture_id, album_id
							FROM Pictures
							WHERE caption="{caption}"
						''')
		data = cursor.fetchall()
		return data

def getComments(filter):
	SQL = f'''SELECT user_id, firstname, lastname 
				FROM Users U INNER JOIN Comments C ON U.user_id = C.owner_id 
				WHERE NOT U.user_id = 20 AND text = '{filter}'
				GROUP BY user_id
				ORDER BY Count(comment_id) DESC
				;'''
	cursor = conn.cursor()
	cursor.execute(SQL)
	info_raw = cursor.fetchall()
	return info_raw



def getUserInfo(uid):
	cursor = conn.cursor()
	cursor.execute(f"SELECT * FROM Users WHERE user_id = {uid}")
	info_raw = cursor.fetchall()[0]
	return info_raw


def editUserInfo(info_raw, info_map, old_pass):
	if(info_map[2] != "" and info_map[9] != old_pass):
		return render_template('edit_profile.html', incorrect_pass=True, supress=True)

	for i in range(len(info_raw)):
		if(info_map[i] == ''):
			info_map[i] = info_raw[i]

	cursor = conn.cursor()
	cursor.execute('''UPDATE users SET password = %s, firstname = %s, lastname = %s, birthdate = %s,\
					gender = %s, hometown = %s  where user_id = %s ''',
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
	pwd = str(data[0][0])
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
	# The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	# check if email is registered
	found = True
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):

		data = cursor.fetchall()
		pwd = str(data[0][0])
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user)  # okay login in user
			# protected is a function defined in this file
			return flask.redirect(flask.url_for('protected'))
		found = False
		return flask.redirect(url_for('unauth'))
	else:
		found = False
		return flask.redirect(url_for('unauth'))

	# information did not match


@app.route('/login/unauth', methods=['GET'])
def unauth():
	return render_template('login.html', unauth=True)


@app.route('/logout')
def logout():
	flask_login.logout_user()
	return flask.redirect(url_for('unregistered'))

@login_manager.unauthorized_handler
def unauthorized_handler():
	return flask.redirect(url_for('unregistered'))

# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier


@app.route("/register", methods=['GET'])
def register():
	message = request.args.get('message')
	return render_template('register.html',msg=message)


@app.route("/register", methods=['POST'])
def register_user():
	try:
		email = request.form.get('email')
		password = request.form.get('password')
		firstname = request.form.get('firstname')
		lastname = request.form.get('lastname')
		date = request.form.get('birthdate')
		context = {'firstname': firstname, 'lastname': lastname, 'email': email}
	except:
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test = isEmailUnique(email)
	if test:
		cursor.execute("INSERT INTO Users (email, password,firstname,lastname,birthdate) VALUES ('{0}','{1}','{2}','{3}','{4}')".format(
		    email, password, firstname, lastname, date))
		conn.commit()
		# log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('hello.html', message='Account Created!', name=flask_login.current_user.id,info=context,contribution_info = getAllUsersContribution(),recent_albums=getUserRecentAlbums(uid),recommend_friends=getTopFriendsOfFriends(uid),base64=base64, recommend_photos = getYouMayAlsoLike(uid))
	else:
		return flask.redirect('/register?message=True')


def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute(
	    "SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]

# NOTE list of tuples, [(imgdata, pid), ...]


def getUserAlbums(uid):
	cursor = conn.cursor()
	cursor.execute(
	    f"SELECT album_id,album_name,date_created,cover_img FROM Albums WHERE owner = {uid}")
	info_raw = cursor.fetchall()
	return info_raw


def getUserRecentAlbums(uid):
	cursor = conn.cursor()
	cursor.execute(
	    f"SELECT * FROM Albums WHERE owner={uid} ORDER BY date_created DESC LIMIT 5")
	info_raw = cursor.fetchall()
	return info_raw


def getAlbumPhotos(album_id):
	cursor = conn.cursor()
	cursor.execute(
	    f"SELECT imgdata,picture_id, caption FROM Pictures WHERE album_id = {album_id}")
	info_raw = cursor.fetchall()
	return info_raw


def getAlbums(uid):
	cursor = conn.cursor()
	cursor.execute(
	    f"SELECT cover_img, album_id, album_name FROM Albums WHERE owner ={uid}")
	info_raw = cursor.fetchall()
	return info_raw


def getUserFriends(uid):
	cursor = conn.cursor()
	cursor.execute(f'''SELECT user1,email,firstname,lastname,user2,contribution_score,profile_img
						FROM photoshare.Users U
						LEFT JOIN friends_with F
						ON U.user_id = F.user2
						WHERE user1 = {uid}''')
	info_raw = cursor.fetchall()
	return info_raw


def getLikedUsers(photo_id):
	cursor = conn.cursor()
	cursor.execute(f''' SELECT u.user_id, u.email, u.firstname, u.lastname, u.contribution_score, l.photo_id
					 	FROM Users u
						LEFT JOIN likes l
						USING(user_id)
						Where photo_id = {photo_id}''')
	info_raw = cursor.fetchall()
	return info_raw


def getPhotoComments(photo_id, comment_filter=None):
	cursor = conn.cursor()
	info_raw = None

	if comment_filter is not None:
		cursor.execute(f'''SELECT firstname,lastname,text,owner_id,comment_id
								FROM photoshare.Users U
								CROSS JOIN photoshare.Comments C
								ON U.user_id = C.owner_id
								WHERE picture_id = {photo_id} and text="{comment_filter}"''')
		info_raw = cursor.fetchall()
	else:
		cursor.execute(f'''SELECT firstname,lastname,text,owner_id,comment_id
							FROM photoshare.Users U
							CROSS JOIN photoshare.Comments C
							ON U.user_id = C.owner_id
							WHERE picture_id = {photo_id}; ''')
		info_raw = cursor.fetchall()

	return info_raw


def getPhotoTags(photo_id):
	cursor = conn.cursor()
	cursor.execute(f'''SELECT * FROM has_tag H
					   CROSS JOIN Tags T
					   ON H.tag_id = T.tag_id
					   WHERE picture_id = {photo_id}; ''')
	tags_raw = cursor.fetchall()
	tags = []
	if(tags_raw):
		for t in tags_raw:
			tags.append((t[0], t[3]))
	return tags


def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]


def isEmailUnique(email):
	# use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		# this means there are greater than zero entries with that email
		return False
	else:
		return True
# end login code


def getAllUsersContribution():
	cursor = conn.cursor()
	cursor.execute(
	    """SELECT user_id,firstname,lastname,contribution_score FROM Users WHERE NOT firstname="Guest" ORDER BY contribution_score DESC LIMIT 10;""")
	data = cursor.fetchall()
	return data


def getTopFriendsOfFriends(uid):
	Sql_statement = f'''
		SELECT user_id, email, password, firstname, lastname, birthdate, gender, hometown, contribution_score, profile_img FROM
			( SELECT user2
				FROM (
					SELECT F1.user1,F1.user2
					FROM Friends_with F
					INNER JOIN Friends_with F1 WHERE F.user1={uid} and F.user2 = F1.user1 and not F1.user2 = {uid}
					)
					as FF
				WHERE not user2  IN (SELECT user2 FROM Friends_with WHERE user1 = {uid})
				GROUP BY user2
				ORDER BY COUNT(user2) DESC
			) as Recommended
		INNER JOIN Users ON Recommended.user2 = Users.user_id'''

	cursor = conn.cursor()
	cursor.execute(Sql_statement)
	data = cursor.fetchall()
	return data


def getPhotosWithMultipleTags(tag_search):
	cursor = conn.cursor()
	cursor.execute('''DROP TABLE IF EXISTS temp''')
	cursor.execute('''CREATE TABLE temp( tags char(20))''')
	conn.commit()
	for t in tag_search:
		cursor.execute('''INSERT INTO temp SET tags = %s ''', t)

	cursor.execute('''SELECT DISTINCT H.picture_id  FROM has_tag H
					CROSS JOIN Tags T, Temp M
					WHERE H.tag_id = T.tag_id
					AND M.tags = T.text
					GROUP BY (H.picture_id)
					HAVING Count(H.picture_id) >= %s''', len(tag_search))
	pics_with_tags_raw = cursor.fetchall()
	if(pics_with_tags_raw):
		pics_with_tags = []
		for p in pics_with_tags_raw:
			pics_with_tags.append(p[0])
		format_strings = ','.join(['%s'] * len(pics_with_tags))
		cursor.execute("SELECT DISTINCT P.picture_id, P.imgdata, P.caption, P.album_id FROM has_tag H\
				CROSS JOIN Pictures P\
				ON P.picture_id = H.picture_id\
				WHERE P.picture_id in (%s)" % format_strings, tuple(pics_with_tags))
		photos = cursor.fetchall()
		cursor.execute('''DROP TABLE temp''')
		cursor.fetchall()
		conn.commit()
		return photos
	return None


def getPopularTags():
	SQL = '''
			SELECT tag_id, text
			FROM (
				SELECT T.tag_id, text,picture_id
				FROM has_tag HT
				JOIN Tags T on HT.tag_id = T.tag_id
				)
				AS TagInfo
			GROUP BY tag_id, text
			ORDER BY COUNT(picture_id) DESC
			LIMIT 10
		 '''
	cursor = conn.cursor()
	cursor.execute(SQL)
	data = cursor.fetchall()
	return data


def getPopularAlbums():
	statement = """SELECT cover_img, album_name, album_id
	FROM
		(SELECT A.*, P.likes FROM Albums A CROSS JOIN Pictures P ON A.album_id = P.album_id)
		AS A1
	GROUP BY album_id, album_name, date_created, owner,cover_img
    ORDER BY SUM(likes) DESC
    LIMIT 5;"""
	cursor = conn.cursor()
	cursor.execute(statement)
	data = cursor.fetchall()
	return data


def getMyPhotosWithMultipleTags(tag_search, uid):
	cursor = conn.cursor()
	cursor.execute('''DROP TABLE IF EXISTS temp''')
	cursor.execute('''CREATE TABLE temp( tags char(20))''')
	conn.commit()
	for t in tag_search:
		cursor.execute('''INSERT INTO temp SET tags = %s ''', t)

	cursor.execute('''SELECT DISTINCT H.picture_id  FROM has_tag H
					CROSS JOIN Tags T, Temp M, Users U, Pictures P
					WHERE H.tag_id = T.tag_id
					AND M.tags = T.text
                    AND H.picture_id = P.picture_id
                    AND P.user_id = U.user_id
                    AND U.user_id = %s
					GROUP BY (H.picture_id)
					HAVING Count(H.picture_id) >= %s''', (uid, len(tag_search)))
	pics_with_tags_raw = cursor.fetchall()
	if(pics_with_tags_raw):
		pics_with_tags = []
		for p in pics_with_tags_raw:
			pics_with_tags.append(p[0])
		format_strings = ','.join(['%s'] * len(pics_with_tags))
		cursor.execute("SELECT DISTINCT P.picture_id, P.imgdata, P.caption, P.album_id FROM has_tag H\
				CROSS JOIN Pictures P\
				ON P.picture_id = H.picture_id\
				WHERE P.picture_id in (%s)" % format_strings, tuple(pics_with_tags))
		photos = cursor.fetchall()
		cursor.execute('''DROP TABLE temp''')
		cursor.fetchall()
		conn.commit()
		return photos
	return None



def getAlbumOwner(id):
	cursor = conn.cursor()
	cursor.execute(f'''SELECT owner FROM albums Where album_id = {id}''')
	owner = cursor.fetchall()[0][0]
	conn.commit()
	return owner


def getYouMayAlsoLike(uid):
	cursor = conn.cursor()

	#getting the top 5 most commonly used tags of the user
	cursor.execute(f'''SELECT * FROM
						(SELECT T.tag_id 
						FROM has_tag H, Pictures P, tags t 
						WHERE P.picture_id =H.Picture_id 
						AND T.tag_id = H.tag_id
						AND P.user_id = {uid}
						GROUP BY H.tag_id, P.user_id
						ORDER BY count(*) DESC LIMIT 5 ) AS top_tags''')
	top_5_raw = cursor.fetchall()
	#user has enough tags for custom recommendation recommend photos with top 5 tags
	if len(top_5_raw) != 5:
		cursor.execute(f''' SELECT P.user_id, h.tag_id, t.text, Count(*) 
							from has_tag H, Pictures P, tags t 
							Where P.picture_id =H.Picture_id 
							And T.tag_id = H.tag_id
							And P.user_id != {uid}
							Group by H.tag_id, P.user_id
							order by count(*) Desc LIMIT 5;''')
		top_5_raw = cursor.fetchall()
	if len(top_5_raw) < 5:
		return None

	#getting top photos with given tags
	cursor.execute(f''' SELECT X.picture_id FROM(
						SELECT P.picture_id, Count(H.tag_id) AS CNUMTAGS 
						FROM HAS_Tag H, ((SELECT t1.picture_id, COUNT(*) AS CMATCH FROM (
						(SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id = {top_5_raw[0][0]} AND P.user_id != {uid})
						UNION ALL 
						(SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id = {top_5_raw[1][0]} AND P.user_id != {uid})
						UNION ALL
						(SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id = {top_5_raw[2][0]} AND P.user_id != {uid})
						UNION ALL 
						(SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id = {top_5_raw[3][0]} AND P.user_id != {uid})
						UNION ALL
						(SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id = {top_5_raw[4][0]} AND P.user_id != {uid})
						) AS t1 GROUP BY picture_id HAVING count(*) >= 1 ORDER BY CMATCH DESC)) P
						WHERE P.picture_id = H.picture_id GROUP BY P.picture_id ORDER BY P.CMATCH DESC, CNUMTAGS ASC LIMIT 5) X''')
	rec_photos_raw = cursor.fetchall()
	conn.commit()
	rec_photos = []
	for photo in rec_photos_raw:
		rec_photos.append(photo[0])
	try:
		cursor.execute(f"SELECT caption, imgdata, album_id, picture_id FROM Pictures WHERE picture_id IN ({rec_photos[0]}, {rec_photos[1]}, {rec_photos[2]}, {rec_photos[3]}, {rec_photos[4]}) ORDER BY FIELD(picture_id, {rec_photos[0]}, {rec_photos[1]}, {rec_photos[2]}, {rec_photos[3]}, {rec_photos[4]} )")
	except IndexError:
		return None
	photos = cursor.fetchall()
	return photos
	
	
	


# begin photo uploading code
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
		tags_raw = request.form.get('tags')
		tags = ((tags_raw.replace("#", "")).lower()).split(", ")
		photo_data = imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption,album_id) VALUES (%s, %s, %s, %s )''',
		               (photo_data, uid, caption, album_id))
		cursor.execute(
		    '''SELECT picture_id from Pictures where picture_id =(SELECT LAST_INSERT_ID())''')
		photo_id = cursor.fetchall()[0][0]
		cursor.execute(
		    f"UPDATE Users SET contribution_score = contribution_score+1 WHERE user_id = {uid};")
		for t in tags:
			cursor.execute('''SELECT count(*) FROM Tags WHERE text = %s  ''', t)
			tag_exists = cursor.fetchall()[0][0]
			if(not tag_exists):
				cursor.execute('''INSERT INTO Tags SET text = %s ''', t)
				conn.commit()
			cursor.execute('''SELECT tag_id FROM Tags where text = %s''', t)
			tag_id = cursor.fetchall()[0][0]
			cursor.execute(
			    '''INSERT INTO has_tag (tag_id, picture_id) VALUES (%s, %s) ''', (tag_id, photo_id))
		conn.commit()
		return flask.redirect(flask.url_for('album', id=album_id))
	else:
		return render_template('upload.html', album_id=album_id)
# end photo uploading code


@app.route('/add_friends', methods=['GET', 'POST'])
@flask_login.login_required
def add_friends():
	cursor = conn.cursor()
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		fullname = request.form.get('name')
		fullname = fullname.split()
		if len(fullname) > 1:
			cursor.execute('''SELECT user_id, firstname, lastname FROM Users WHERE firstname = %s and lastname = %s''',
		               (fullname[0], fullname[1]))
		else:
			cursor.execute('''SELECT user_id, firstname FROM Users WHERE firstname = %s and lastname = %s''',
		               (fullname[0]))
		
		data = cursor.fetchall()
		found = False
		if data:
			found = True
		return render_template('add_friends.html', data=data, found=found)

	else:
		return render_template('add_friends.html', data={}, found=True)


@app.route('/many_tags/<uid>/<search>')
def photosWithManyTags(search, uid):
	if search:
		tag_search = ((search.replace("#", "")).lower()).split(", ")
		if (int(uid) == 0):
			photos = getPhotosWithMultipleTags(tag_search)
			return render_template("tag.html", photos=photos, base64=base64, tag_txt=search, user = False)

		else:
			photos = getMyPhotosWithMultipleTags(tag_search, uid)
	if photos == None and int(uid) != 0:
		return render_template("tag.html", photos=photos, base64=base64, tag_txt=search, userNoPhotos=True)
	else:
		return render_template("tag.html", photos=photos, base64=base64, tag_txt=search, user = True)

@app.route('/add_friend', methods=['POST'])
@flask_login.login_required
def add_friend():
	cursor = conn.cursor()
	uid = getUserIdFromEmail(flask_login.current_user.id)
	data = {}
	if request.method == 'POST':

		friend_id = request.form.get('added_friend')

		if((int)(uid) == (int)(friend_id)):
			return render_template('add_friends.html', data={}, found=True, friend_self=True)

		else:
			cursor.execute('''SELECT user1, user2 FROM friends_with WHERE user1 = %s and user2 = %s''',
						(uid, friend_id))

			existing_friends = cursor.fetchall()
			if existing_friends:
				return render_template('add_friends.html', data={}, found=True, existing_friends=True)
			else:
				cursor.execute(
				    '''INSERT INTO friends_with (user1, user2) VALUES (%s, %s )''', (uid, friend_id))
				cursor.execute(
				    '''INSERT INTO friends_with (user1, user2) VALUES (%s, %s )''', (friend_id, uid))
				cursor.execute(
				    '''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''', (uid))
				cursor.execute(
				    '''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''', (friend_id))
				conn.commit()
				return render_template('friend.html', friends=getUserFriends(uid), base64=base64)


@app.route('/friends', methods=['GET'])
@flask_login.login_required
def friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friend.html', friends=getUserFriends(uid), base64=base64)


@app.route('/delete/<album_id>', methods=['GET', 'POST'])
@flask_login.login_required
def delete_photo(album_id):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == "POST":
		photo_id = request.form.get('photo')
		cursor = conn.cursor()
		cursor.execute(
		    'DELETE FROM Pictures WHERE picture_id=%s and album_id=%s', (photo_id, album_id))
		cursor.execute(
		    '''UPDATE Users SET contribution_score = (contribution_score - 1) WHERE user_id = %s''', (uid))
		conn.commit()
		return flask.redirect(flask.url_for('album', id=album_id))

	photos = getAlbumPhotos(album_id)
	return render_template("delete_photos.html", photos=photos, base64=base64, album=album_id)


@app.route('/delete_album', methods=['GET', 'POST'])
@flask_login.login_required
def delete_album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == "POST":
		album_id = request.form.get('album')
		cursor = conn.cursor()
		cursor.execute('DELETE FROM Albums WHERE album_id=%s', (album_id))
		conn.commit()
		return flask.redirect(flask.url_for('albums'))
	albums = getAlbums(uid)
	return render_template("delete_album.html", albums=albums, base64=base64)


@app.route("/upload-album", methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == "POST":
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_name = request.form.get('name')
		cover_img_file = request.files['cover_img']
		# date = request.form.get('created')
		cover_img_data = cover_img_file.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (owner, album_name,cover_img) VALUES ( %s, %s, %s)''',
		               (uid, album_name, cover_img_data))

		conn.commit()
		return flask.redirect("/albums")

	return render_template('upload_album.html')


@app.route("/albums", methods=['GET', 'POST'])
@flask_login.login_required
def albums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	album_list = getUserAlbums(uid)
	cursor = conn.cursor()

	if request.method == "POST":
			search = request.form.get('tags')
			if(search):
				return flask.redirect(url_for('photosWithManyTags', search=search, uid=uid))
			else:
				return render_template("albums.html", albums=album_list, base64=base64, no_input=True)

	return render_template("albums.html", albums=album_list, base64=base64)


@app.route('/albums', methods=['GET', 'POST'])
def albums_public():
	name = request.args.get('album_name')
	SQL = f"SELECT * FROM photoshare.Albums WHERE album_name LIKE '{name}'"

	cursor = conn.cursor()
	cursor.execute(SQL)
	album_list = cursor.fetchall()

	return render_template("albums.html", albums=album_list, base64=base64)


@app.route("/album/<id>", methods=['GET'])
def album(id):
	cursor = conn.cursor()
	cursor.execute(
	    f"SELECT album_name,date_created,cover_img FROM Albums WHERE album_id={id}")
	album = cursor.fetchall()[0]
	cursor.execute(
	    f'SELECT picture_id, imgdata,caption FROM Pictures WHERE album_id = {id}')
	photos = cursor.fetchall()
	if(flask_login.current_user.is_authenticated):
		owner = getAlbumOwner(id)
		uid = getUserIdFromEmail(flask_login.current_user.id)
		if(owner == uid):
			return render_template("album.html", photos=photos, album=album, album_id=id, base64=base64, unauth = False)
	return render_template("album.html", photos=photos, album=album, album_id=id, base64=base64, unauth = True)

@app.route("/add_tag/<photo_id>",methods=['GET','POST'])
def add_tag(photo_id):
	if request.method=='POST':
		tag_text = request.form.get('text')
		cursor = conn.cursor()
		cursor.execute(f"INSERT INTO tags(text) VALUES ('{tag_text}')")
		conn.commit()
		cursor.execute(f"SELECT tag_id FROM tags WHERE text='{tag_text}'")
		tag_id = cursor.fetchall()[0][0]
		cursor.execute(f"INSERT INTO has_tag(tag_id,picture_id) VALUES ({tag_id},{photo_id})")
		conn.commit()
		cursor.execute(f'SELECT album_id FROM Pictures WHERE picture_id={photo_id}')
		album_id=cursor.fetchall()[0][0]
		return flask.redirect(url_for('photo',album_id=album_id,photo_id=photo_id))
	return render_template("add_tag.html",id=photo_id)

@app.route("/album/<album_id>/photo/<photo_id>", methods=['GET', 'POST'], defaults={'comment_filter': None})
def photo(album_id, photo_id, comment_filter):
	if flask_login.current_user.is_authenticated:
		uid = getUserIdFromEmail(flask_login.current_user.id)

	else:
		uid=20

	cursor = conn.cursor()
	cursor.execute('''SELECT imgdata,caption,likes,user_id FROM Pictures WHERE album_id=%s and picture_id = %s''',
				   (album_id, photo_id))
	data = cursor.fetchall()[0]
	pic_owner = data[3]
	if pic_owner==uid:
		can_add_tag = True
	else:
		can_add_tag=False
	userInfo = getUserInfo(pic_owner)
	if request.method == "POST":
		if flask_login.current_user.is_authenticated:
			uid = getUserIdFromEmail(flask_login.current_user.id)
			can_add_tag=True
		else:
			uid = 20
			can_add_tag=False
		comment = request.form.get('comment')
		to_delete = request.form.get('delete')
		like = request.form.get('like')
		cursor.execute(
		    '''SELECT user_id FROM Pictures WHERE picture_id = %s''', (photo_id))
		pic_owner = cursor.fetchall()[0][0]
		comment_query = request.form.get('filter')
		users_liked = request.form.get('users_liked')

		if comment:
			todays_date = str(datetime.date.today())
			if(pic_owner == uid):
				return render_template('photo.html', data=data, album_id=album_id, photo_id=photo_id, base64=base64, comments=getPhotoComments(photo_id), user=uid, dismiss_comment=True, tags=getPhotoTags(photo_id), user_info=userInfo)
			cursor.execute('''INSERT INTO Comments (text, date_created, picture_id,owner_id) VALUES (%s, %s, %s, %s)''',
			               (comment, todays_date, photo_id, uid))
			cursor.execute(
			    '''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''', (uid))
			conn.commit()

		elif to_delete:
			cursor.execute(f'''DELETE FROM Comments WHERE comment_id={to_delete}''')
			cursor.execute(
			    '''UPDATE Users SET contribution_score = (contribution_score - 1) WHERE user_id = %s''', (uid))
			conn.commit()
		elif like:
			if(pic_owner == uid):
				return render_template('photo.html', data=data, album_id=album_id, photo_id=photo_id, base64=base64, comments=getPhotoComments(photo_id), user=uid, dismiss_like=True, tags=getPhotoTags(photo_id), user_info=userInfo,tag_owner=can_add_tag)
			else:
				cursor.execute(
				    '''SELECT count(*) FROM likes WHERE user_id = %s and photo_id = %s  ''', (uid, photo_id))
				liked_earlier = cursor.fetchall()[0][0]
				if(liked_earlier):
					cursor.execute(
					    '''DELETE FROM likes WHERE user_id = %s and photo_id = %s''', (uid, photo_id))
					cursor.execute(
					    f'''UPDATE Pictures SET likes=likes-1 WHERE picture_id={photo_id}''')
					cursor.execute(
					    '''UPDATE Users SET contribution_score = (contribution_score - 1) WHERE user_id = %s''', (uid))
					conn.commit()
				else:
					cursor.execute(
					    f'''UPDATE Pictures SET likes=likes+1 WHERE picture_id={photo_id}''')
					cursor.execute(
					    '''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''', (uid))
					cursor.execute(
					    '''INSERT INTO likes (user_id, photo_id) VALUES (%s, %s)''', (uid, photo_id))
					conn.commit()
			'''elif users_liked:
			users_liked = getLikedUsers(photo_id)
			return render_template('photo.html', data=data, album_id=album_id, photo_id=photo_id, base64=base64,
								   comments=getPhotoComments(photo_id), user=uid, get_liked_users=True,
								   users_liked=users_liked, user_info=userInfo, tags=getPhotoTags(photo_id))'''
		elif comment_query:
			return render_template('photo.html', data=data, album_id=album_id, photo_id=photo_id, base64=base64,
								   comments=getPhotoComments(photo_id, comment_query), user=uid, tags=getPhotoTags(photo_id), user_info=userInfo, users_liked = getLikedUsers(photo_id),tag_owner=can_add_tag)

		return flask.redirect(url_for('photo', album_id=album_id, photo_id=photo_id))

	return render_template('photo.html', data=data, album_id=album_id, photo_id=photo_id, base64=base64, comments=getPhotoComments(photo_id, comment_filter), user=uid, tags=getPhotoTags(photo_id), user_info=userInfo, get_liked_users=False,users_liked = getLikedUsers(photo_id),tag_owner=can_add_tag)


@app.route("/tags/<tag_id>", methods=['GET'])
def photosWithTag(tag_id):
	if tag_id is None:
		return render_template(url_for('explore'))
	cursor = conn.cursor()
	cursor.execute(f'''SELECT DISTINCT P.picture_id, P.imgdata, P.caption, P.album_id FROM has_tag H
					CROSS JOIN Pictures P
					ON P.picture_id = H.picture_id
					WHERE tag_id = {tag_id}; ''')
	photos = cursor.fetchall()
	cursor.execute('''SELECT text FROM Tags where tag_id = %s''', tag_id)
	tag_txt = cursor.fetchall()[0][0]
	return render_template("tag.html", photos=photos, base64=base64, tag_txt=tag_txt)


@app.route("/comment/<query>", methods=['GET'])
def comments(query):
	return render_template("comments.html",data=getComments(query),search=query)

@app.route("/profile/upload", methods=['GET', 'POST'])
@flask_login.login_required
def upload_profile_pic():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		imgfile = request.files['photo']
		photo_data = imgfile.read()
		cursor = conn.cursor()
		cursor.execute(
		    'UPDATE Users SET profile_img=%s WHERE user_id=%s', (photo_data, uid))
		cursor.execute(
		    '''UPDATE Users SET contribution_score = (contribution_score + 1) WHERE user_id = %s''', (uid))
		conn.commit()
		return flask.redirect(flask.url_for('profile'))

	return render_template('profile_upload.html', user=uid)


@app.route("/profile/<user_id>", methods=['GET'])
def profile_public(user_id):
	uid=getUserIdFromEmail(flask_login.current_user.id)
	userInfo = getUserInfo(user_id)
	return render_template("profile.html", userInfo=userInfo, base64=base64, public=True,friend=isFriend(uid,user_id))


@app.route("/profile", methods=['GET'])
@flask_login.login_required
def profile():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	userInfo = getUserInfo(uid)
	return render_template("profile.html", userInfo=userInfo, base64=base64)


@app.route("/edit_profile", methods=['GET', "POST"])
@flask_login.login_required
def edit_profile():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == "POST":
		info_raw = getUserInfo(uid)
		old_password = request.form.get('old_password')
		password = request.form.get('password')
		firstname = request.form.get('firstname')
		lastname = request.form.get('lastname')
		birthdate = request.form.get('birthdate')
		hometown = request.form.get('hometown')
		gender = request.form.get('gender')
		info_map = [info_raw[0], info_raw[1], password, firstname,
		    lastname, birthdate, gender, hometown, info_raw[8], old_password]
		current_password = info_raw[2]
		return flask.redirect(flask.url_for('profile'))
	return render_template("edit_profile.html", supress=True)


@app.route('/explore', methods=['GET', "POST"])
def explore():
	if not flask_login.current_user.is_authenticated:
		unAuth=True
	else:
		unAuth=False
	cursor = conn.cursor()
	cursor.execute('''SELECT cover_img, album_name, album_id
						FROM Albums
						CROSS JOIN Users
						ON Albums.owner = Users.user_id''')
	albums = cursor.fetchall()

	tags = getPopularTags()

	if request.method == "POST":
		search = request.form.get('tags')
		if search:
			return flask.redirect(url_for('photosWithManyTags', search= search, uid = 0))
	return render_template('explore.html',albums=albums,base64=base64, tags = tags, photos=getPhotos(),unauth=unAuth)




def getAlbumsWithName(name=None):
	if name is None or name=="":
		return getPopularAlbums()
	else:
		cursor.execute(f'''SELECT cover_img,album_name,album_id FROM Albums WHERE album_name="{name}"''')
		data = cursor.fetchall()
		return data

@app.route('/browse', methods=['GET','POST'])
def browse():
	search_query = request.form.get('browse_query')
	option = request.form.get('browse_option')
	not_found = False
	if option=='photo':
		data = getPhotos(search_query)
		if data == ():
			not_found = True
		return render_template('explore.html', albums=None, photos=data,base64=base64, tags=getPopularTags(),notFound = not_found)
	elif option=='comment':
		return flask.redirect(url_for('comments',query=search_query))
	else:
		data = getAlbumsWithName(search_query)
		if data == ():
			not_found = True
		return render_template('explore.html', albums=data, photos=None, base64=base64, tags=getPopularTags(),notFound = not_found)




@app.route('/')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute(f"SELECT firstname,lastname FROM Users WHERE user_id = {uid}")
	info_raw = cursor.fetchall()[0]
	info = {'firstname':info_raw[0],'lastname': info_raw[1]}
	
	
	return render_template('hello.html', name=flask_login.current_user.id,info=info,contribution_info = getAllUsersContribution(),recent_albums=getUserRecentAlbums(uid),recommend_friends=getTopFriendsOfFriends(uid),base64=base64, recommend_photos = getYouMayAlsoLike(uid))
# default page

@app.route("/logged_out",methods=['GET'])
def unregistered():
	return render_template('hello.html', unauth=True,info=None,contribution_info = getAllUsersContribution(),recent_albums=None,recommend_friends=None,base64=base64,need_login=True)

@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	# this is invoked when in the shell  you run
	# $ python app.py
	app.run(port=5000, debug=True)

