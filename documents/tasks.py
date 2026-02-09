from celery import shared_task
import time

@shared_task
def debug_task(x, y):
    """A useless task just to test the worker."""
    print(f"I am working on: {x} + {y}...")
    time.sleep(5)  # Simulate a slow job (like reading a PDF)
    result = x + y
    print(f"Done! The result is: {result}")
    return result