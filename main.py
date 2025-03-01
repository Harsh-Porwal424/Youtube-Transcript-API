from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi

app = FastAPI()

def format_timestamp(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"  # Formats to mm:ss

@app.get("/")
async def root():
    return {"message": "Hello World from Harsh Porwal"}

@app.get("/transcript/{video_id}")
async def get_transcript(video_id: str):
    try:
        # Fetch the transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        # Format transcript into a dictionary
        formatted_transcript = {format_timestamp(item['start']): item['text'] for item in transcript}

        return formatted_transcript

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
