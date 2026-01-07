import os
import cv2
import subprocess
from docx import Document
from tqdm import tqdm
import openai
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ===================== CONFIG =====================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in .env file.")
openai.api_key = OPENAI_API_KEY

VIDEO_DIR = "app/modules/neo_chatbot/data/documents/training_docs/CBS_training_videos"
OUTPUT_DIR = "app/modules/neo_chatbot/data/video_word_output_docs"
TEMP_AUDIO_DIR = "temp/audio"
TEMP_FRAME_DIR = "temp/frames"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(TEMP_FRAME_DIR, exist_ok=True)

IMPORTANT_CUES = [
    "as you can see", "this diagram", "here", "notice",
    "flow", "process", "architecture", "system"
]

FRAME_INTERVAL_SECONDS = 2  # for scene change sampling
SCENE_DIFF_THRESHOLD = 30   # tune if needed

# =================================================


def extract_audio(video_path, audio_path):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "mp3",
        audio_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def transcribe_audio(audio_path):
    with open(audio_path, "rb") as f:
        transcript = openai.audio.transcriptions.create(
            file=f,
            model="whisper-1",
            response_format="verbose_json"
        )
    return transcript["segments"]


def contains_visual_cue(text):
    text = text.lower()
    return any(cue in text for cue in IMPORTANT_CUES)


def extract_important_frames(video_path, segments, video_name):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    prev_gray = None
    extracted = []

    for seg in segments:
        if not contains_visual_cue(seg["text"]):
            continue

        timestamp = seg["start"]
        frame_no = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)

        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            score = diff.mean()
            if score < SCENE_DIFF_THRESHOLD:
                continue

        frame_path = os.path.join(
            TEMP_FRAME_DIR,
            f"{video_name}_{int(timestamp)}s.png"
        )
        cv2.imwrite(frame_path, frame)

        extracted.append({
            "timestamp": timestamp,
            "text": seg["text"],
            "frame_path": frame_path
        })

        prev_gray = gray

    cap.release()
    return extracted


def describe_image(image_path, context_text):
    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"The speaker said: {context_text}. Explain what the image shows."},
                    {"type": "image_url", "image_url": {"url": f"file://{image_path}"}}
                ]
            }
        ],
        max_tokens=150
    )
    return response.choices[0].message.content


def create_word_doc(video_name, segments, frames):
    doc = Document()
    doc.add_heading(video_name, level=1)

    frame_map = {f["timestamp"]: f for f in frames}

    for seg in segments:
        doc.add_paragraph(seg["text"])

        for ts, frame in frame_map.items():
            if abs(ts - seg["start"]) < 1.5:
                doc.add_picture(frame["frame_path"], width=None)
                description = describe_image(
                    frame["frame_path"],
                    seg["text"]
                )
                doc.add_paragraph(description, style="Intense Quote")

    output_path = os.path.join(OUTPUT_DIR, f"{video_name}.docx")
    doc.save(output_path)


def process_video(video_file):
    video_path = os.path.join(VIDEO_DIR, video_file)
    video_name = os.path.splitext(video_file)[0]

    audio_path = os.path.join(TEMP_AUDIO_DIR, f"{video_name}.mp3")

    extract_audio(video_path, audio_path)
    segments = transcribe_audio(audio_path)
    frames = extract_important_frames(video_path, segments, video_name)
    create_word_doc(video_name, segments, frames)


def main():
    videos = [v for v in os.listdir(VIDEO_DIR) if v.endswith(".mp4")]

    for video in tqdm(videos, desc="Processing videos"):
        process_video(video)


if __name__ == "__main__":
    main()
