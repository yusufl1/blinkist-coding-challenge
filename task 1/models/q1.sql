
SELECT COUNT(user_id) user_count    -- DISTINCT user_id if there is duplication in user_fact
FROM user_fact 
WHERE created_at >= GETDATE() - interval '2 weeks'  -- created in the past two weeks 
AND country_code IN ('DE', 'AT', 'CH')   -- in the DACH region
