import time
import random
from datetime import datetime, timedelta

http_methods = [
    'GET',
    'POST',
    'PATCH',
    'DELETE',
]

# Start time
current_time = datetime.now()

# Simulate traffic
def simulate_django_traffic(num_requests=20):
    method_index = 0  # start with GET
    
    for _ in range(num_requests):
        # Oscillate between methods
        method = http_methods[method_index]
        method_index = (method_index + 1) % len(http_methods)
        
        # Random interval between 0.5s and 2s
        interval = random.uniform(0.5, 2.0)
        time.sleep(interval)
        current_time = datetime.now()

        # Simulate response status and size
        status = random.choice([200, 201, 400, 403, 404, 500])
        size = random.randint(500, 20000)

        # Format Django log line
        log_line = (
            f'[{current_time.strftime("%d/%b/%Y %H:%M:%S")}] '
            f'"{method} / HTTP/1.1" {status} {size}'
        )
        print(log_line)


if __name__ == "__main__":
    simulate_django_traffic(15)  # simulate 15 requests
