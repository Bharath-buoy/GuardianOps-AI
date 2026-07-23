"""
Sample Application: Inventory Service
========================================
Simulates a warehouse/inventory microservice, including occasional
memory-pressure log lines so GuardianOps AI's memory-leak indicator
detector has realistic signals to catch.
"""
import random

from common import run_service_loop, write_log, write_stack_trace

SERVICE_NAME = "inventory-service"

SKUS = ["SKU-4471", "SKU-8823", "SKU-1190", "SKU-6654", "SKU-3302"]


def scenario(service_name: str) -> None:
    roll = random.random()
    sku = random.choice(SKUS)

    if roll < 0.58:
        write_log(service_name, "INFO", f"Stock level updated for {sku}: {random.randint(0, 500)} units available")
    elif roll < 0.75:
        write_log(service_name, "INFO", f"Reservation created for {sku} — quantity {random.randint(1, 20)}")
    elif roll < 0.87:
        write_log(service_name, "WARN", f"In-memory stock cache size growing — now {random.randint(60, 95)}% of allocated heap")
    elif roll < 0.95:
        write_log(service_name, "ERROR", f"Heap usage critical while indexing catalog — possible memory leak in cache layer")
        write_stack_trace(service_name, "raise MemoryError('unable to allocate additional cache segment')")
    else:
        write_log(service_name, "ERROR", f"Failed to sync {sku} with warehouse-gateway: connection reset")
        write_stack_trace(service_name, "raise ConnectionResetError('connection reset by peer: warehouse-gateway:7000')")


if __name__ == "__main__":
    run_service_loop(SERVICE_NAME, scenario)
