import requests
import time

# API endpoints to test
endpoints = {
    "Dashboard Metrics": "http://localhost:8001/api/v1/dashboard/metrics",
    "High-Risk Users": "http://localhost:8001/api/v1/dashboard/high-risk-users?limit=10",
    "Latest Alerts": "http://localhost:8001/api/v1/dashboard/latest-alerts?limit=20",
    "List All Users": "http://localhost:8001/api/v1/users?limit=100"
}

# Number of requests to send for each endpoint
NUM_REQUESTS = 20

def run_performance_test():
    print("Starting performance test...")
    
    for name, url in endpoints.items():
        print(f"\nTesting endpoint: {name}")
        
        total_time = 0
        min_time = float('inf')
        max_time = 0
        
        for i in range(NUM_REQUESTS):
            start_time = time.time()
            response = requests.get(url)
            end_time = time.time()
            
            if response.status_code != 200:
                print(f"  Request {i+1}/{NUM_REQUESTS}: Error {response.status_code}")
                continue
                
            duration = (end_time - start_time) * 1000 # in milliseconds
            total_time += duration
            
            if duration < min_time:
                min_time = duration
            if duration > max_time:
                max_time = duration
                
            print(f"  Request {i+1}/{NUM_REQUESTS}: {duration:.2f} ms")
            time.sleep(0.1) # Small delay between requests
            
        avg_time = total_time / NUM_REQUESTS
        
        print(f"\n  Results for {name}:")
        print(f"    Average response time: {avg_time:.2f} ms")
        print(f"    Minimum response time: {min_time:.2f} ms")
        print(f"    Maximum response time: {max_time:.2f} ms")
        
if __name__ == "__main__":
    run_performance_test()
