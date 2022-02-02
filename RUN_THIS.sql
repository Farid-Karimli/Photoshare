USE photoshare;
ALTER TABLE Users;
add column firstname char(20),
add column lastname char(20),
add column birthdate DATE;
-- User needs these attributes, as per the document --

USE photoshare;
DROP TABLE IF EXISTS Albums;

CREATE TABLE Albums (
	album_id int4 AUTO_INCREMENT,
    user int4,
    name VARCHAR(30),
    created DATE,
    PRIMARY KEY (album_id,user),
    FOREIGN KEY (user)
		REFERENCES Users(user_id) --Relationship between Users and Albums--
);

-- This creates the relationship between Albums and Pictures
use photoshare;
ALTER TABLE Pictures
ADD COLUMN album_id int4;

use photoshare;
ALTER TABLE Pictures
ADD FOREIGN KEY (album_id) REFERENCES Albums(album_id);

