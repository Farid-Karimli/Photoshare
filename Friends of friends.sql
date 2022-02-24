use photoshare;



SELECT user2
FROM (
	SELECT F1.user1,F1.user2 
	FROM Friends_with F
	INNER JOIN Friends_with F1 WHERE F.user1=3 and F.user2 = F1.user1 and not F1.user2 = 3)
    as FF

GROUP BY user2 
ORDER BY COUNT(user2) DESC
    
