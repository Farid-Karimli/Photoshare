CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255),
    firstname char(20),
	lastname char(20),
	birthdate DATE,
    gender char(10),
    hometown char(20),
	CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);

CREATE TABLE Albums(
	album_id int4 AUTO_INCREMENT,
    album_name char(20),
    date_created DATE,
    CONSTRAINT albums_pk PRIMARY KEY (album_id)
);

CREATE TABLE Tags(
	tag_id int4 AUTO_INCREMENT,
    text char(20),
    CONSTRAINT tags_pk PRIMARY KEY (tag_id)
);

CREATE TABLE Comments(
	comment_id int4 AUTO_INCREMENT,
    text char(50),
    date_created DATE,
    CONSTRAINT comments_pk PRIMARY KEY (comment_id)
);

CREATE TABLE friends_with(
	user1 int4,
    user2 int4,
	PRIMARY KEY(user1, user2),
    FOREIGN KEY(user1) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(user2) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE comment_by(
	picture_id int4,
    user_id int4,
    PRIMARY KEY(picture_id, user_id),
    FOREIGN KEY(picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE has_tag(
	tag_id int4,
    picture_id int4,
	PRIMARY KEY(tag_id, picture_id),
    FOREIGN KEY(tag_id) REFERENCES Tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY(picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE under(
	comment_id int4,
    picture_id int4,
	PRIMARY KEY(comment_id, picture_id),
    FOREIGN KEY(comment_id) REFERENCES Comments(comment_id) ON DELETE CASCADE,
    FOREIGN KEY(picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE

);

CREATE TABLE owner_of(
	album_id int4,
    user_id int4,
	PRIMARY KEY(album_id, user_id),
    FOREIGN KEY(album_id) REFERENCES Albums(album_id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE contains(
	album_id int4,
    picture_id int4,
	PRIMARY KEY(album_id, picture_id),
    FOREIGN KEY(album_id) REFERENCES Albums(album_id) ON DELETE CASCADE,
    FOREIGN KEY(picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);


INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
