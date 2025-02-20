import threading
from datetime import timedelta

from prometheus_client import Counter, Gauge, Histogram, exposition
from prometheus_client.registry import CollectorRegistry
from sqlalchemy.sql import func

from couchers.db import session_scope
from couchers.models import User
from couchers.sql import couchers_select as select
from couchers.utils import now

main_process_registry = CollectorRegistry()
job_process_registry = CollectorRegistry()

_INF = float("inf")

jobs_duration_histogram = Histogram(
    "couchers_background_jobs_seconds",
    "Durations of background jobs",
    labelnames=["job", "status", "attempt", "exception"],
    registry=job_process_registry,
)


def observe_in_jobs_duration_histogram(job_type, job_state, try_count, exception_name, duration_s):
    jobs_duration_histogram.labels(job_type, job_state, str(try_count), exception_name).observe(duration_s)


servicer_duration_histogram = Histogram(
    "couchers_servicer_duration_seconds",
    "Durations of processing gRPC calls",
    labelnames=["method", "logged_in", "code", "exception"],
    registry=main_process_registry,
)


def observe_in_servicer_duration_histogram(method, user_id, status_code, exception_type, duration_s):
    servicer_duration_histogram.labels(method, user_id is not None, status_code, exception_type).observe(duration_s)


def _get_active_users_5m():
    with session_scope() as session:
        return session.execute(
            select(func.count())
            .select_from(User)
            .where(User.is_visible)
            .where(User.last_active > now() - timedelta(minutes=5))
        ).scalar_one()


active_users_5m_gauge = Gauge(
    "couchers_active_users_5m",
    "Number of active users in the last 5 min",
    registry=main_process_registry,
)
active_users_5m_gauge.set_function(_get_active_users_5m)


def _get_users():
    with session_scope() as session:
        return session.execute(select(func.count()).select_from(User).where(User.is_visible)).scalar_one()


users_gauge = Gauge(
    "couchers_users",
    "Total number of users",
    registry=main_process_registry,
)
users_gauge.set_function(_get_users)


signup_initiations_counter = Counter(
    "couchers_signup_initiations_total",
    "Number of initiated signups",
    registry=main_process_registry,
)
signup_completions_counter = Counter(
    "couchers_signup_completions_total",
    "Number of completed signups",
    labelnames=["gender"],
    registry=main_process_registry,
)
signup_time_histogram = Histogram(
    "couchers_signup_time_seconds",
    "Time taken for a user to sign up",
    labelnames=["gender"],
    registry=main_process_registry,
    buckets=(30, 60, 90, 120, 180, 240, 300, 360, 420, 480, 540, 600, 900, 1200, 1800, 3600, 7200, _INF),
)

logins_counter = Counter(
    "couchers_logins_total",
    "Number of logins",
    labelnames=["gender"],
    registry=main_process_registry,
)

password_reset_initiations_counter = Counter(
    "couchers_password_reset_initiations_total",
    "Number of password reset initiations",
    registry=main_process_registry,
)
password_reset_completions_counter = Counter(
    "couchers_password_reset_completions_total",
    "Number of password reset completions",
    registry=main_process_registry,
)

account_deletion_initiations_counter = Counter(
    "couchers_account_deletion_initiations_total",
    "Number of account deletion initiations",
    labelnames=["gender"],
    registry=main_process_registry,
)
account_deletion_completions_counter = Counter(
    "couchers_account_deletion_completions_total",
    "Number of account deletion completions",
    labelnames=["gender"],
    registry=main_process_registry,
)
account_recoveries_counter = Counter(
    "couchers_account_recoveries_total",
    "Number of account recoveries",
    labelnames=["gender"],
    registry=main_process_registry,
)

strong_verification_initiations_counter = Counter(
    "couchers_strong_verification_initiations_total",
    "Number of strong verification initiations",
    labelnames=["gender"],
    registry=main_process_registry,
)
strong_verification_completions_counter = Counter(
    "couchers_strong_verification_completions_total",
    "Number of strong verification completions",
    registry=main_process_registry,
)
strong_verification_data_deletions_counter = Counter(
    "couchers_strong_verification_data_deletions_total",
    "Number of strong verification data deletions",
    labelnames=["gender"],
    registry=main_process_registry,
)

host_requests_sent_counter = Counter(
    "couchers_host_requests_total",
    "Number of host requests sent",
    labelnames=["from_gender", "to_gender"],
    registry=main_process_registry,
)
host_request_responses_counter = Counter(
    "couchers_host_requests_responses_total",
    "Number of responses to host requests",
    labelnames=["responder_gender", "other_gender", "response_type"],
    registry=main_process_registry,
)

sent_messages_counter = Counter(
    "couchers_sent_messages_total",
    "Number of messages sent",
    labelnames=["gender", "message_type"],
    registry=main_process_registry,
)


host_request_first_response_histogram = Histogram(
    "couchers_host_request_first_response_seconds",
    "Response time to host requests",
    labelnames=["host_gender", "surfer_gender", "response_type"],
    registry=main_process_registry,
    buckets=(
        1 * 60,  # 1m
        2 * 60,  # 2m
        5 * 60,  # 5m
        10 * 60,  # 10m
        15 * 60,  # 15m
        30 * 60,  # 30m
        45 * 60,  # 45m
        3_600,  # 1h
        2 * 3_600,  # 2h
        3 * 3_600,  # 3h
        6 * 3_600,  # 6h
        12 * 3_600,  # 12h
        86_400,  # 24h
        2 * 86_400,  # 2d
        5 * 86_400,  # 4d
        602_000,  # 1w
        2 * 602_000,  # 2w
        3 * 602_000,  # 3w
        4 * 602_000,  # 4w
        _INF,
    ),
)
account_age_on_host_request_create_histogram = Histogram(
    "couchers_account_age_on_host_request_create_histogram_seconds",
    "Age of account sending a host request",
    labelnames=["surfer_gender", "host_gender"],
    registry=main_process_registry,
    buckets=(
        5 * 60,  # 5m
        10 * 60,  # 10m
        15 * 60,  # 15m
        30 * 60,  # 30m
        45 * 60,  # 45m
        3_600,  # 1h
        2 * 3_600,  # 2h
        3 * 3_600,  # 3h
        6 * 3_600,  # 6h
        12 * 3_600,  # 12h
        86_400,  # 24h
        2 * 86_400,  # 2d
        3 * 86_400,  # 3d
        4 * 86_400,  # 4d
        5 * 86_400,  # 5d
        6 * 86_400,  # 6d
        602_000,  # 1w
        2 * 602_000,  # 2w
        3 * 602_000,  # 3w
        4 * 602_000,  # 4w
        5 * 602_000,  # 5w
        10 * 602_000,  # 10w
        25 * 602_000,  # 25w
        52 * 602_000,  # 52w
        104 * 602_000,  # 104w
        _INF,
    ),
)


def create_prometheus_server(registry, port):
    """custom start method to fix problem descrbied in https://github.com/prometheus/client_python/issues/155"""
    app = exposition.make_wsgi_app(registry)
    httpd = exposition.make_server(
        "", port, app, exposition.ThreadingWSGIServer, handler_class=exposition._SilentHandler
    )
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    return httpd
