from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Depends
from pydantic import BaseModel
from typing import List
import httpx
import asyncio
import logging
from chonkie import RecursiveChunker
from tokenizers import Tokenizer
import os
from dotenv import load_dotenv
load_dotenv()


API_KEY = os.getenv("EDTRY_INTERNAL_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#load the tokenizer
tokenizer = Tokenizer.from_pretrained("BAAI/bge-base-en-v1.5")

chunker = RecursiveChunker(
    chunk_size=400,
    tokenizer_or_token_counter=lambda text: len(tokenizer.encode(text).ids),
    min_characters_per_chunk=100
)

LARAVEL_API_URL = os.getenv("LARAVEL_API_URL")

# FastAPI app
app = FastAPI()


class LessonInput(BaseModel):
    course_id: int
    lesson_id: int
    lesson_title: str
    lesson_content: str
    type: str  # "created", "updated", "deleted"

class ChunkedResponse(BaseModel):
    course_id: int
    lesson_id: int
    type: str
    chunks: List[str]

# AUTH

async def verify_api_key(x_internal_api_key: str = Header(...)):
    if x_internal_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")



async def send_to_laravel_with_retry(payload: dict, retries: int = 3, delay: float = 2.0):
    headers = {"X-Internal-API-Key": API_KEY}
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=50.0) as client:
                response = await client.post(LARAVEL_API_URL, json=payload, headers=headers)
                response.raise_for_status()
                logger.info("Successfully sent to Laravel.")
                return response.json()
        except httpx.HTTPError as e:
            logger.warning(f"[Attempt {attempt+1}] Failed to send to Laravel: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))
            else:
                logger.error(f"All retries failed. Could not send payload for lesson {payload.get('lesson_id')}")
                raise

async def process_lesson(data: LessonInput):
    full_text = data.lesson_content.strip()

    try:
        chunked_objs = chunker(full_text)
        chunks = [{"text": c.text, "chunk_index": idx} for idx, c in enumerate(chunked_objs)]

        if not chunks:
            raise ValueError("No chunks produced.")
    except Exception as e:
        logger.error(f"Chunking failed for lesson {data.lesson_id}: {e}")
        return

    payload = {
        "title": data.lesson_title.strip(),
        "text": full_text,
        "course_id": data.course_id,
        "lesson_id": data.lesson_id,
        "type": data.type,
        "chunks": chunks,
    }
    print(payload)
    try:
        await send_to_laravel_with_retry(payload)
        logger.info(f"Successfully processed and sent lesson {data.lesson_id}")
    except Exception as e:
        logger.error(f"Final failure sending lesson {data.lesson_id} to Laravel: {e}")

# ROUTES

@app.post("/chunk")
async def chunk_lesson(
    data: LessonInput,
    background_tasks: BackgroundTasks,
    _ = Depends(verify_api_key)
):
    """
    Accepts lesson data and processes it in the background.
    """
    if data.type not in {"created", "updated", "deleted"}:
        raise HTTPException(status_code=400, detail="Invalid lesson type")

    background_tasks.add_task(process_lesson, data)
    return {"message": "Chunking request accepted and processing in background."}

@app.get("/")
async def root():
    """
    Simple health check endpoint.
    """
    return {"message": "Welcome to the Chunking API. Use POST /chunk to process lessons."}