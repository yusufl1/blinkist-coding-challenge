

SELECT DISTINCT user_fact.user_id
FROM user_fact 
LEFT JOIN daily_web_activity
    ON user_fact.user_id = daily_web_activity.user_id       
    AND daily_web_activity.date >= GETDATE() - interval '2 weeks'   --only join when activity is in past two weeeks
LEFT JOIN daily_app_activity 
    ON user_fact.user_id = daily_app_activity.user_id 
    AND daily_app_activity.date >= GETDATE() - interval '2 weeks'
WHERE EXTRACT('year' from user_fact.created_at) = 2021  --users created in 2021
--this assumes user_id is not included in the daily_activity tables when their activity is 0.
--so if there was a successful join and user_id is not null in one of activity tables,
--then the user was active
AND (NOT daily_app_activity.user_id IS NULL      
	OR NOT daily_web_activity.user_id IS NULL)  
