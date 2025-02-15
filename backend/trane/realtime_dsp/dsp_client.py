import requests
from django.conf import settings

DSP_SERVICE_URL = getattr(settings, "DSP_SERVICE_URL", "http://localhost:9000")

def get_latest_features():
    """
    Fetch the latest real-time features from the DSP service.
    Expected JSON format: { "pitch": <float>, "tempo": <float>, "beat_positions": [<int>, ...] }
    """
    try:
        response = requests.get(f"{DSP_SERVICE_URL}/latest_features", timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # In production, log the error
        print(f"Error fetching DSP features: {e}")
        return {}
