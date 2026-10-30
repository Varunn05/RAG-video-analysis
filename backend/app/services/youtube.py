import re
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """Return an 11-character YouTube id or raise a helpful error."""
    parsed = urlparse(url)
    if parsed.netloc in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/")
    elif "youtube.com" in parsed.netloc:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        if not video_id and "/embed/" in parsed.path:
            video_id = parsed.path.rsplit("/", 1)[-1]
    else:
        raise ValueError("Please provide a valid YouTube URL.")

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Could not find a valid YouTube video id in that URL.")
    return video_id


def fetch_transcript(video_id: str) -> str:
    """Fetch and normalize captions while retaining the timestamp per sentence."""
    transcript = YouTubeTranscriptApi().fetch(video_id, languages=["en", "en-IN", "hi"])
    lines: list[str] = []
    buffer: list[str] = []
    start: float | None = None
    for item in transcript:
        text = item.text.strip()
        if not text:
            continue
        if start is None:
            start = item.start
        buffer.append(text)
        if text.endswith((".", "?", "!")):
            lines.append(f"[{start:.2f}s] {' '.join(buffer)}")
            buffer, start = [], None
    if buffer and start is not None:
        lines.append(f"[{start:.2f}s] {' '.join(buffer)}")
    return "\n".join(lines)
