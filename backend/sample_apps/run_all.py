"""
Launches all four GuardianOps AI sample applications concurrently
(each in its own thread, each writing to its own log file), so
GuardianOps AI's log watcher has real, continuously-updating logs to
monitor from a single command.

Run:
    cd backend/sample_apps
    python run_all.py

Leave this running in a separate terminal alongside `uvicorn app.main:app --reload`.
"""
import threading

import authentication_service
import inventory_service
import notification_service
import payment_service
from common import run_service_loop

APPS = [
    (authentication_service.SERVICE_NAME, authentication_service.scenario),
    (payment_service.SERVICE_NAME, payment_service.scenario),
    (inventory_service.SERVICE_NAME, inventory_service.scenario),
    (notification_service.SERVICE_NAME, notification_service.scenario),
]


def main() -> None:
    print("🚀 Starting all GuardianOps AI sample applications...")
    threads = []
    for service_name, scenario_fn in APPS:
        t = threading.Thread(target=run_service_loop, args=(service_name, scenario_fn), daemon=True)
        t.start()
        threads.append(t)

    print(f"✅ {len(threads)} sample applications running. Press Ctrl+C to stop.")
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n👋 Stopping all sample applications...")


if __name__ == "__main__":
    main()
