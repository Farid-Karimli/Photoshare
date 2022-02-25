use photoshare;
SELECT user_id, email, password, firstname, lastname, birthdate, gender, hometown, contribution_score, profile_img FROM
	( SELECT user2
	FROM (
		SELECT F1.user1,F1.user2
		FROM Friends_with F
		INNER JOIN Friends_with F1 WHERE F.user1=4 and F.user2 = F1.user1 and not F1.user2 = 4
		)
		as FF
		GROUP BY user2
		ORDER BY COUNT(user2) DESC
	) as Recommended
INNER JOIN Users ON Recommended.user2 = Users.user_id
    
