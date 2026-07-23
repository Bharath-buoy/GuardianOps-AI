"""
Sample Application: Payment Service
======================================
Simulates a payment processing microservice, including occasional
database timeout and connection failure scenarios so GuardianOps AI's
incident detection rules have realistic signals to catch.
"""
import random

from common import run_service_loop, write_log, write_stack_trace

SERVICE_NAME = "payment-service"


def scenario(service_name: str) -> None:
    roll = random.random()
    amount = round(random.uniform(9.99, 499.99), 2)
    txn_id = f"txn_{random.randint(100000, 999999)}"

    if roll < 0.55:
        write_log(service_name, "INFO", f"Payment {txn_id} processed successfully — ${amount}")
    elif roll < 0.72:
        write_log(service_name, "INFO", f"Refund issued for {txn_id} — ${amount}")
    elif roll < 0.84:
        write_log(service_name, "WARN", f"Payment gateway response time {random.randint(400, 950)}ms exceeds SLA")
    elif roll < 0.92:
        write_log(service_name, "ERROR", f"Database query timeout while committing transaction {txn_id}")
        write_stack_trace(service_name, "raise TimeoutError('query exceeded statement_timeout=5000ms')")
    else:
        write_log(service_name, "ERROR", "Connection failed to reach fraud-detection-service")
        write_stack_trace(service_name, "raise ConnectionError('connection refused: fraud-detection-service:9090')")


if __name__ == "__main__":
    run_service_loop(SERVICE_NAME, scenario)
