import asyncio
import logging
import os

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TextToSpeechService:
    def __init__(self):
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_endpoint = os.getenv("AZURE_SPEECH_ENDPOINT")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")
        self.voice_name = os.getenv("AZURE_TTS_VOICE", "en-US-JennyNeural")

        logger.info("TTS endpoint configured: %s", bool(self.speech_endpoint))
        logger.info("TTS region configured: %s", bool(self.speech_region))
        logger.info("TTS voice: %s", self.voice_name)

    def _build_speech_config(self):
        if not self.speech_key:
            raise RuntimeError("AZURE_SPEECH_KEY is missing")

        if self.speech_endpoint:
            return speechsdk.SpeechConfig(
                subscription=self.speech_key,
                endpoint=self.speech_endpoint,
            )

        if self.speech_region:
            return speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region,
            )

        raise RuntimeError("Set AZURE_SPEECH_ENDPOINT or AZURE_SPEECH_REGION")

    async def synthesize(self, text: str):
        try:
            if not text or not text.strip():
                return None, []

            speech_config = self._build_speech_config()
            speech_config.speech_synthesis_voice_name = self.voice_name
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
            )

            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=None,
            )

            viseme_timeline = []

            def on_viseme(event):
                viseme_timeline.append(
                    {
                        "time": event.audio_offset / 10_000,
                        "visemeId": event.viseme_id,
                    }
                )

            synthesizer.viseme_received.connect(on_viseme)

            result = await asyncio.to_thread(
                lambda: synthesizer.speak_text_async(text).get()
            )

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("TTS audio bytes length: %s", len(result.audio_data))
                return result.audio_data, viseme_timeline

            if result.reason == speechsdk.ResultReason.Canceled:
                cancellation = speechsdk.CancellationDetails.from_result(result)
                logger.error("TTS canceled: %s", cancellation.reason)
                logger.error("TTS error details: %s", cancellation.error_details)
                logger.error("TTS error code: %s", cancellation.error_code)
                return None, []

            logger.warning("TTS synthesis did not complete. Reason: %s", result.reason)
            return None, []

        except Exception as e:
            logger.exception("TTS error: %s", e)
            return None, []
#main.py 
import base64
import io
import json
import logging
import wave

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from rag.knowledgeBase import KnowledgeBase
from services.llm import LLMService
from services.stt import SpeechToTextService
from services.tts import TextToSpeechService
from services.viseme import convert_azure_visemes

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Avatar Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stt_service = SpeechToTextService()
llm_service = LLMService()
tts_service = TextToSpeechService()

try:
    knowledge_base = KnowledgeBase()
except Exception as exc:
    logger.exception("Knowledge base init failed: %s", exc)
    knowledge_base = None


def pcm_to_wav_bytes(pcm_bytes: bytes) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(pcm_bytes)
    return buffer.getvalue()


async def build_response_payload(query: str) -> dict:
    context_docs = []

    if knowledge_base:
        try:
            context_docs = knowledge_base.query(query, top_k=3) or []
        except Exception as exc:
            logger.exception("Knowledge base query failed: %s", exc)

    answer_text = await llm_service.generate_response(query, context_docs)
    audio_bytes, raw_visemes = await tts_service.synthesize(answer_text)

    audio_base64 = (
        base64.b64encode(audio_bytes).decode("utf-8")
        if audio_bytes
        else None
    )

    return {
        "type": "response",
        "text": answer_text,
        "audio": audio_base64,
        "visemes": convert_azure_visemes(raw_visemes or []),
    }


@app.get("/")
async def root():
    return {"status": "ok", "service": "ai-avatar-backend"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected")

    try:
        while True:
            raw_message = await websocket.receive_text()
            data = json.loads(raw_message)

            message_type = data.get("type")
            content = data.get("content", "")

            if message_type == "audio":
                if not content:
                    continue

                pcm_bytes = base64.b64decode(content)
                wav_bytes = pcm_to_wav_bytes(pcm_bytes)

                transcription = await stt_service.transcribe(wav_bytes)

                if not transcription:
                    await websocket.send_json(
                        {
                            "type": "response",
                            "text": "I could not hear that clearly. Please try again.",
                            "audio": None,
                            "visemes": [],
                        }
                    )
                    continue

                await websocket.send_json(
                    {"type": "transcription", "text": transcription}
                )
                await websocket.send_json({"type": "thinking"})

                response_payload = await build_response_payload(transcription)
                await websocket.send_json(response_payload)
                continue

            if message_type == "text":
                query = content.strip()
                if not query:
                    continue

                await websocket.send_json({"type": "thinking"})
                response_payload = await build_response_payload(query)
                await websocket.send_json(response_payload)
                continue

            logger.warning("Unknown message type: %s", message_type)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
        try:
            await websocket.send_json(
                {
                    "type": "response",
                    "text": "Sorry, something went wrong while generating the response.",
                    "audio": None,
                    "visemes": [],
                }
            )
        except Exception:
            pass
