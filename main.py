import os
import requests
import time
from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from concurrent.futures import ThreadPoolExecutor

PROXY_URL = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
MAX_WORKERS = 20

app = FastAPI()

# Helper: Format timestamp (mm:ss)
def format_timestamp(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

# Proxy Manager Class
class FreeProxyManager:
    def __init__(self):
        self.proxies = []
        self.blacklist = set()

    def update_proxy_list(self):
        print("Fetching and testing proxies...")
        try:
            response = requests.get(PROXY_URL, timeout=10)
            response.raise_for_status()
            proxy_lines = response.text.strip().split("\n")

            proxies_to_test = [{"http": f"http://{proxy}", "https": f"http://{proxy}"} for proxy in proxy_lines]

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                results = list(executor.map(self._test_proxy, proxies_to_test))

            # Keep only working proxies
            self.proxies = [proxy for proxy, is_working in zip(proxies_to_test, results) if is_working]

            print(f"Updated proxy list with {len(self.proxies)} working proxies.")
        except requests.RequestException as e:
            print(f"Error fetching proxies: {e}")

    def _test_proxy(self, proxy):
        test_url = "https://www.google.com"
        try:
            response = requests.get(test_url, proxies=proxy, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_proxy(self):
        if not self.proxies:
            self.update_proxy_list()

        if self.proxies:
            return self.proxies.pop(0)  # Return and remove the first proxy
        else:
            raise HTTPException(status_code=500, detail="No working proxies available")

# Initialize Proxy Manager
proxy_manager = FreeProxyManager()

@app.get("/")
async def root():
    return {"message": "Hello World from Harsh Porwal"}

@app.get("/transcript/{video_id}")
async def get_transcript(video_id: str):
    attempts = 5  # Retry with new proxies up to 5 times

    for attempt in range(attempts):
        proxy = proxy_manager.get_proxy()
        try:
            session = requests.Session()
            session.proxies.update(proxy)

            transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxy)

            formatted_transcript = {
                format_timestamp(item['start']): item['text'] for item in transcript
            }

            return formatted_transcript

        except (TranscriptsDisabled, NoTranscriptFound):
            raise HTTPException(status_code=404, detail="Transcript not available for this video.")

        except Exception as e:
            print(f"Proxy failed: {proxy}, Error: {e}")

    raise HTTPException(status_code=500, detail="Failed to fetch transcript after multiple attempts.")
