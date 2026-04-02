"""Parser for audio and video files using OpenAI Whisper API."""

import os
import subprocess
import tempfile
from typing import List
from app.parsers.base_parser import BaseParser, ParsedChunk
from app.core.config import get_settings

settings = get_settings()


class AudioParser(BaseParser):
    """Parse audio files by transcribing with OpenAI Whisper API."""

    @staticmethod
    def supported_extensions() -> List[str]:
        return [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"]

    async def parse(self, file_path: str, filename: str) -> List[ParsedChunk]:
        return await _transcribe_file(file_path, filename, "audio")


class VideoParser(BaseParser):
    """Parse video files by extracting audio then transcribing."""

    @staticmethod
    def supported_extensions() -> List[str]:
        return [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"]

    async def parse(self, file_path: str, filename: str) -> List[ParsedChunk]:
        # Extract audio from video using ffmpeg
        audio_path = None
        try:
            audio_path = tempfile.mktemp(suffix=".mp3")
            subprocess.run(
                ["ffmpeg", "-i", file_path, "-vn", "-acodec", "libmp3lame",
                 "-q:a", "4", "-y", audio_path],
                capture_output=True, check=True, timeout=300
            )
            return await _transcribe_file(audio_path, filename, "video")
        except FileNotFoundError:
            return [ParsedChunk(
                text=f"[Video file: {filename} - ffmpeg not installed, cannot extract audio]",
                metadata={"source": filename, "file_type": "video", "error": "ffmpeg not found"}
            )]
        except subprocess.CalledProcessError as e:
            return [ParsedChunk(
                text=f"[Video file: {filename} - audio extraction failed: {e.stderr.decode()[:200]}]",
                metadata={"source": filename, "file_type": "video", "error": "extraction failed"}
            )]
        finally:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)


async def _transcribe_file(file_path: str, filename: str, file_type: str) -> List[ParsedChunk]:
    """Transcribe an audio file using OpenAI Whisper API."""
    if not settings.OPENAI_API_KEY:
        return [ParsedChunk(
            text=f"[{file_type.title()} file: {filename} - OpenAI API key not configured for transcription]",
            metadata={"source": filename, "file_type": file_type}
        )]

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Check file size - Whisper API limit is 25MB
        file_size = os.path.getsize(file_path)
        if file_size > 25 * 1024 * 1024:
            # Split large files into chunks
            return await _transcribe_large_file(client, file_path, filename, file_type)

        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
            )

        text = transcript.text if hasattr(transcript, 'text') else str(transcript)

        if not text.strip():
            return [ParsedChunk(
                text=f"[{file_type.title()} file: {filename} - no speech detected]",
                metadata={"source": filename, "file_type": file_type}
            )]

        return [ParsedChunk(
            text=f"[Transcription of {filename}]\n{text}",
            metadata={
                "source": filename,
                "file_type": file_type,
                "language": getattr(transcript, "language", "unknown"),
            }
        )]

    except Exception as e:
        return [ParsedChunk(
            text=f"[{file_type.title()} file: {filename} - transcription failed: {str(e)[:200]}]",
            metadata={"source": filename, "file_type": file_type, "error": str(e)}
        )]


async def _transcribe_large_file(client, file_path: str, filename: str, file_type: str) -> List[ParsedChunk]:
    """Handle large audio files by splitting them into segments."""
    try:
        segments_dir = tempfile.mkdtemp()
        # Split into 20MB segments using ffmpeg
        subprocess.run(
            ["ffmpeg", "-i", file_path, "-f", "segment", "-segment_time", "600",
             "-c", "copy", os.path.join(segments_dir, "segment_%03d.mp3")],
            capture_output=True, check=True, timeout=300
        )

        segments = sorted([f for f in os.listdir(segments_dir) if f.startswith("segment_")])
        all_text = []

        for seg in segments:
            seg_path = os.path.join(segments_dir, seg)
            with open(seg_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                )
            if transcript.text.strip():
                all_text.append(transcript.text.strip())

        # Cleanup
        for seg in segments:
            os.remove(os.path.join(segments_dir, seg))
        os.rmdir(segments_dir)

        full_text = "\n\n".join(all_text)
        return [ParsedChunk(
            text=f"[Transcription of {filename}]\n{full_text}",
            metadata={"source": filename, "file_type": file_type, "segments": len(segments)}
        )]

    except Exception as e:
        return [ParsedChunk(
            text=f"[{file_type.title()} file: {filename} - large file transcription failed: {str(e)[:200]}]",
            metadata={"source": filename, "file_type": file_type, "error": str(e)}
        )]
