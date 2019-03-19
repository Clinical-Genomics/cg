-- R_P
select avg(DATEDIFF(s.prepared_at, s.received_at)) from sample as s
where s.received_at is not null and s.prepared_at is not null
and DATEDIFF(s.prepared_at, s.received_at) >= 0 AND DATEDIFF(s.prepared_at, s.received_at) <= 31;

-- P_S
select avg(DATEDIFF(s.sequenced_at, s.prepared_at)) from sample as s
where s.sequenced_at is not null and s.prepared_at is not null
and DATEDIFF(s.sequenced_at, s.prepared_at) >= 0 AND DATEDIFF(s.sequenced_at, s.prepared_at) <= 31;

-- S_A
select avg(DATEDIFF(a.completed_at, s.sequenced_at))
from sample as s
join family_sample as f_s on f_s.`sample_id` = s.id
join family as f on f.id = f_s.`family_id`
join analysis as a on a.`family_id` = f.id
where a.completed_at is not null and s.sequenced_at is not null
and DATEDIFF(a.completed_at, s.sequenced_at) >= 0 AND DATEDIFF(a.completed_at, s.sequenced_at) <= 31;

-- A_U
select avg(DATEDIFF(a.uploaded_at, a.completed_at)) from analysis as a
where a.uploaded_at is not null and a.completed_at is not null
and DATEDIFF(a.uploaded_at, a.completed_at) >= 0 AND DATEDIFF(a.uploaded_at, a.completed_at) <= 31;

-- U_D
select avg(DATEDIFF(s.delivered_at, a.uploaded_at))
from sample as s
join family_sample as f_s on f_s.`sample_id` = s.id
join family as f on f.id = f_s.`family_id`
join analysis as a on a.`family_id` = f.id
where s.delivered_at is not null and a.uploaded_at is not null
and DATEDIFF(s.delivered_at, a.uploaded_at) >= 0 AND DATEDIFF(s.delivered_at, a.uploaded_at) <= 31;