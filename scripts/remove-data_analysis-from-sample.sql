ALTER TABLE `sample` DROP COLUMN `data_analysis`;

# FIX THIS EXPRESSION
Update `family` as f
SET f.ordered_at =
(
select s.ordered_at
from family_sample as f_s
join sample as s on f_s.sample_id = s.id
where f_s.family_id = f.id
order by s.ordered_at desc
LIMIT 1;
)

where f.comment = "created by data_analysis migration";
and f.ordered_at = f.created_at
