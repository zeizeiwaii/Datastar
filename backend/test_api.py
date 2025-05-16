import requests
import json

def test_route_planning():
    url = "http://localhost:8000/api/routes/plan"
    headers = {"Content-Type": "application/json"}
    data = {
        "timeWindow": 60,
        "spatialThreshold": 2.0,
        "maxPointsPerRoute": 8,
        "minSamples": 2
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_route_planning() 