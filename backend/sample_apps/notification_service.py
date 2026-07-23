"""
Sample Application: Notification Service
===========================================
Simulates a messaging/notification microservice (email, SMS, push).
"""
import random

from common import run_service_loop, write_log, write_stack_trace

SERVICE_NAME = "notification-service"

CHANNELS = ["email", "sms", "push"]


def scenario(service_name: str) -> None:
    roll = random.random()
    channel = random.choice(CHANNELS)

    if roll < 0.60:
        write_log(service_name, "INFO", f"Notification dispatched via {channel} — delivery id {random.randint(10000,99999)}")
    elif roll < 0.78:
        write_log(service_name, "INFO", f"Queue drained: {random.randint(5, 200)} pending {channel} message(s) processed")
    elif roll < 0.90:
        write_log(service_name, "WARN", f"Rate limit approaching for {channel} provider — {random.randint(80,98)}% of quota used")
    elif roll < 0.96:
        write_log(service_name, "ERROR", f"Failed to deliver {channel} notification: provider returned 5xx")
        write_stack_trace(service_name, f"raise DeliveryError('{channel} provider unavailable')")
    else:
        write_log(service_name, "ERROR", "Message broker connection timeout while publishing event")
        write_stack_trace(service_name, "raise TimeoutError('broker ack not received within 5000ms')")


if __name__ == "__main__":
    run_service_loop(SERVICE_NAME, scenario)
