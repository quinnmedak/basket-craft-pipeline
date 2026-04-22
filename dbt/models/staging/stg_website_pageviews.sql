select
    website_pageview_id::integer as pageview_id,
    website_session_id::integer as website_session_id,
    pageview_url,
    created_at as pageview_date
from {{ source('raw', 'website_pageviews') }}
