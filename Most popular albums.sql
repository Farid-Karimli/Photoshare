use photoshare;
	SELECT album_id, album_name, date_created, owner,cover_img
	FROM 
		(SELECT A.*, P.likes FROM Albums A CROSS JOIN Pictures P ON A.album_id = P.album_id)
		AS A1
	GROUP BY album_id, album_name, date_created, owner,cover_img
    ORDER BY SUM(likes) DESC
    LIMIT 5;
	