"""
Sample Application: Authentication Service
=============================================
A tiny standalone script that behaves like a real auth microservice,
continuously writing realistic logs for GuardianOps AI to monitor.

Run standalone:
    python sample_apps/authentication_service.py

Or launch all four sample apps together:
    python sample_apps/run_all.py
"""
import random

from common import run_service_loop, write_log, write_stack_trace

SERVICE_NAME = "auth-service"

USERS = ["j.doe", "m.smith", "a.patel", "r.chen", "l.garcia", "svc-account-01"]


def scenario(service_name: str) -> None:
    roll = random.random()

    if roll < 0.62:
        user = random.choice(USERS)
        write_log(service_name, "INFO", f"User '{user}' authenticated successfully in {random.randint(40, 180)}ms")
    elif roll < 0.78:
        write_log(service_name, "INFO", f"Token refresh completed for session {random.randint(10000,99999)}")
    elif roll < 0.90:
        user = random.choice(USERS)
        write_log(service_name, "WARN", f"Login attempt for '{user}' exceeded {random.randint(300,900)}ms response time")
    elif roll < 0.96:
        write_log(service_name, "ERROR", "Failed to validate JWT signature: token malformed")
        write_stack_trace(service_name, "raise InvalidTokenError('signature verification failed')")
    else:
        write_log(service_name, "ERROR", "Connection refused while reaching user-profile-service")
        write_stack_trace(service_name, "raise ConnectionError('connection refused: user-profile-service:8080')")


if __name__ == "__main__":
    run_service_loop(SERVICE_NAME, scenario)
