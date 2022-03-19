use photoshare;
SELECT HT2.picture_id, COUNT(HT2.tag_id) FROM
(SELECT T.tag_id, text
FROM Tags T, Has_tag HT, Pictures P
WHERE HT.tag_id = T.tag_id AND HT.picture_id = P.picture_id AND P.user_id = 4
GROUP BY T.tag_id
ORDER BY Count(T.tag_id) DESC
LIMIT 5)
AS popular_tags
JOIN Has_tag HT2, Pictures P2
WHERE popular_tags.tag_id = HT2.tag_id AND P2.picture_id = HT2.picture_id
GROUP BY HT2.picture_id
ORDER BY Count(HT2.tag_id) DESC