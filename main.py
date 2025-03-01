from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

app = FastAPI()

# Helper function to format timestamps (e.g., 8:01)
def format_timestamp(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

@app.get("/")
async def root():
    return {"message": "Hello World from Harsh Porwal"}

@app.get("/transcript/{video_id}")
async def get_transcript(video_id: str):
    try:
        available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

        # Attempt to fetch transcript (prioritize manual over auto-generated)
        transcript = None
        for transcript_obj in available_transcripts:
            try:
                if transcript_obj.is_generated:
                    continue  # Prefer human-created subtitles
                transcript = transcript_obj.fetch()
                break
            except Exception as e:
                continue

        # If no manual transcript is found, try fetching auto-generated
        if not transcript:
            try:
                transcript = available_transcripts.find_generated_transcript().fetch()
            except Exception:
                raise NoTranscriptFound("No suitable transcript available.")

        # Format the transcript into a JSON object
        formatted_transcript = {format_timestamp(item['start']): item['text'] for item in transcript}

        return formatted_transcript

    except (TranscriptsDisabled, NoTranscriptFound):
        raise HTTPException(status_code=404, detail="Transcript not available for this video.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
