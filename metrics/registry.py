class MetricName:
    EMAILS_ENQUEUED = "emails_enqueued"
    MASSIVE_API_CALLS = "massive_api_calls"
    GOOGLE_OAUTH_CALLBACKS = "google_oauth_callbacks"

    EMAILS_SENT_SUCCESS = "emails_sent_success"
    EMAILS_SENT_FAILURE = "emails_sent_failure"
    EMAIL_SEND_RETRIES = "email_send_retries"
    EMAIL_SEND_PERMANENT_FAILURE = "email_send_permanent_failure"

    # Flask app request for specific routes
    REQUEST_COUNT = "request_count"
    # Static requests
    STATIC_REQUEST_COUNT = "static_request_count"

    # Average latency is calculated using these
    LATENCY_COUNT = "latency_count"
    LATENCY_SUM_MS = "latency_sum_ms"

    # Average latency is calculated using these
    STATIC_LATENCY_COUNT = "static_latency_count"
    STATIC_LATENCY_SUM_MS = "static_latency_sum_ms"

    RESPONSES_5XX = "responses_5xx"
    SLOW_REQUESTS = "slow_requests"

    UNCAUGHT_EXCEPTIONS = "uncaught_exceptions"

    REDIS_FLUSH_SUCCESS = "redis_flush_success"
    REDIS_FLUSH_FAILURE = "redis_flush_failure"
