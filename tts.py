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
#app.jsx
/**
 * Hero FinCorp AI Avatar
 * ----------------------
 * Keeps the STT, LLM, and PCM recording flow aligned with the code shown
 * in the provided screenshots while preserving the upgraded UI and avatar
 * loading experience already present in this repo.
 */

import React, {
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

const Avatar = lazy(() => import("./Avatar.jsx"));

const WS_URL =
  import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws`;
const DEFAULT_AVATAR_URL =
  import.meta.env.VITE_AVATAR_GLB_URL ||
  "/subsurface_scattering_sss_demo_lara.glb";
const RECORDING_DURATION_MS = 3000;
const MIN_PCM_BYTES = 20000;

function uint8ArrayToBase64(bytes) {
  let binary = "";
  const chunkSize = 0x8000;

  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    const chunk = bytes.subarray(offset, offset + chunkSize);
    binary += String.fromCharCode(...chunk);
  }

  return btoa(binary);
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentVisemes, setCurrentVisemes] = useState([]);
  const [avatarUrl, setAvatarUrl] = useState(null);
  const [avatarError, setAvatarError] = useState("");
  const [isAvatarLoading, setIsAvatarLoading] = useState(true);
  const [avatarSourceLabel, setAvatarSourceLabel] = useState("Default avatar");

  const wsRef = useRef(null);
  const audioRef = useRef(null);
  const audioUrlRef = useRef(null);
  const messagesEndRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectDelayRef = useRef(3000);
  const uploadedAvatarUrlRef = useRef(null);
  const fetchedAvatarUrlRef = useRef(null);
  const avatarInputRef = useRef(null);

  const mediaStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const sourceNodeRef = useRef(null);
  const workletNodeRef = useRef(null);
  const recordingTimeoutRef = useRef(null);
  const pcmChunksRef = useRef([]);

  const cleanupPlayback = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }

    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }

    setIsSpeaking(false);
    setCurrentVisemes([]);
  }, []);

  const revokeAvatarUrl = useCallback((url) => {
    if (url?.startsWith("blob:")) {
      URL.revokeObjectURL(url);
    }
  }, []);

  const closeRecordingResources = useCallback(async () => {
    if (recordingTimeoutRef.current) {
      clearTimeout(recordingTimeoutRef.current);
      recordingTimeoutRef.current = null;
    }

    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.disconnect();
      } catch (error) {
        console.debug("Source node disconnect skipped:", error);
      }
      sourceNodeRef.current = null;
    }

    if (workletNodeRef.current) {
      workletNodeRef.current.port.onmessage = null;
      try {
        workletNodeRef.current.disconnect();
      } catch (error) {
        console.debug("Worklet disconnect skipped:", error);
      }
      workletNodeRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      const context = audioContextRef.current;
      audioContextRef.current = null;

      if (context.state !== "closed") {
        try {
          await context.close();
        } catch (error) {
          console.debug("Audio context close skipped:", error);
        }
      }
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  useEffect(
    () => () => {
      cleanupPlayback();
      revokeAvatarUrl(uploadedAvatarUrlRef.current);
      revokeAvatarUrl(fetchedAvatarUrlRef.current);
      closeRecordingResources();
    },
    [cleanupPlayback, closeRecordingResources, revokeAvatarUrl]
  );

  useEffect(() => {
    let isCancelled = false;

    async function loadDefaultAvatar() {
      setIsAvatarLoading(true);
      setAvatarError("");

      try {
        const response = await fetch(DEFAULT_AVATAR_URL, { cache: "no-store" });

        if (!response.ok) {
          throw new Error(`Avatar request failed with status ${response.status}`);
        }

        const avatarBlob = await response.blob();
        const nextAvatarUrl = URL.createObjectURL(avatarBlob);

        revokeAvatarUrl(fetchedAvatarUrlRef.current);
        fetchedAvatarUrlRef.current = nextAvatarUrl;

        if (!isCancelled) {
          setAvatarUrl(nextAvatarUrl);
          setAvatarSourceLabel("Local public GLB");
        }
      } catch (error) {
        console.error("Avatar fetch error:", error);

        if (!isCancelled) {
          setAvatarUrl(null);
          setAvatarError(
            "The realistic avatar model could not be loaded. Upload a local .glb file below."
          );
          setAvatarSourceLabel("Procedural fallback");
        }
      } finally {
        if (!isCancelled) {
          setIsAvatarLoading(false);
        }
      }
    }

    if (uploadedAvatarUrlRef.current) {
      setAvatarUrl(uploadedAvatarUrlRef.current);
      setAvatarError("");
      setIsAvatarLoading(false);
      setAvatarSourceLabel("Uploaded local GLB");
      return undefined;
    }

    loadDefaultAvatar();

    return () => {
      isCancelled = true;
    };
  }, [revokeAvatarUrl]);

  const handleAvatarUpload = useCallback((event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (!file.name.toLowerCase().endsWith(".glb")) {
      setAvatarError("Please select a .glb file for the avatar.");
      return;
    }

    revokeAvatarUrl(uploadedAvatarUrlRef.current);
    const nextAvatarUrl = URL.createObjectURL(file);
    uploadedAvatarUrlRef.current = nextAvatarUrl;

    setAvatarUrl(nextAvatarUrl);
    setAvatarError("");
    setIsAvatarLoading(false);
    setAvatarSourceLabel(file.name);

    event.target.value = "";
  }, [revokeAvatarUrl]);

  const handleAvatarRenderError = useCallback(() => {
    setAvatarError(
      "The current GLB could not be rendered. Try a different avatar .glb file."
    );
  }, []);

  const openAvatarPicker = useCallback(() => {
    avatarInputRef.current?.click();
  }, []);

  const playAudioWithVisemes = useCallback((base64Audio, visemes) => {
    cleanupPlayback();

    const audioBytes = Uint8Array.from(atob(base64Audio), (char) =>
      char.charCodeAt(0)
    );
    const blob = new Blob([audioBytes], { type: "audio/wav" });
    const url = URL.createObjectURL(blob);
    audioUrlRef.current = url;

    const audio = new Audio(url);
    audioRef.current = audio;
    setCurrentVisemes(visemes || []);
    setIsSpeaking(true);

    audio.onended = () => {
      cleanupPlayback();
    };

    audio.onerror = (event) => {
      console.error("TTS audio error:", event);
      cleanupPlayback();
    };

    audio.play().catch((error) => {
      console.error("Audio play failed:", error);
      cleanupPlayback();
    });
  }, [cleanupPlayback]);

  const handleServerMessage = useCallback((data) => {
    switch (data.type) {
      case "thinking":
        setIsThinking(true);
        break;

      case "transcription":
        setMessages((previous) => [...previous, { role: "user", text: data.text }]);
        break;

      case "response":
        setIsThinking(false);
        setMessages((previous) => [
          ...previous,
          { role: "assistant", text: data.text },
        ]);

        if (data.audio) {
          playAudioWithVisemes(data.audio, data.visemes || []);
        } else {
          cleanupPlayback();
        }
        break;

      case "error":
        setIsThinking(false);
        setMessages((previous) => [
          ...previous,
          { role: "assistant", text: `⚠️ ${data.message}` },
        ]);
        cleanupPlayback();
        break;

      default:
        console.warn("Unknown message type:", data.type);
    }
  }, [cleanupPlayback, playAudioWithVisemes]);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setIsConnected(true);
        reconnectDelayRef.current = 3000;
      };

      ws.onclose = () => {
        setIsConnected(false);
        const delay = reconnectDelayRef.current;
        reconnectDelayRef.current = Math.min(delay * 1.5, 30000);
        reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
      };

      ws.onerror = () => {
        // Let onclose manage retries.
      };

      ws.onmessage = (event) => {
        handleServerMessage(JSON.parse(event.data));
      };

      wsRef.current = ws;
    } catch (error) {
      const delay = reconnectDelayRef.current;
      reconnectDelayRef.current = Math.min(delay * 1.5, 30000);
      reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
    }
  }, [handleServerMessage]);

  useEffect(() => {
    connectWebSocket();

    return () => {
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  const sendTextMessage = useCallback(() => {
    const text = inputText.trim();

    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    setMessages((previous) => [...previous, { role: "user", text }]);
    wsRef.current.send(JSON.stringify({ type: "text", content: text }));
    setInputText("");
  }, [inputText]);

  const handleKeyPress = useCallback(
    (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendTextMessage();
      }
    },
    [sendTextMessage]
  );

  const finalizeRecording = useCallback(async () => {
    const pcmChunks = pcmChunksRef.current;
    pcmChunksRef.current = [];
    setIsRecording(false);
    await closeRecordingResources();

    const totalLength = pcmChunks.reduce((sum, chunk) => sum + chunk.length, 0);

    if (totalLength < MIN_PCM_BYTES) {
      console.warn("PCM audio too short");
      return;
    }

    const pcmBytes = new Uint8Array(totalLength);
    let offset = 0;

    pcmChunks.forEach((chunk) => {
      pcmBytes.set(chunk, offset);
      offset += chunk.length;
    });

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: "⚠️ Connection lost while sending your voice input.",
        },
      ]);
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: "audio",
        content: uint8ArrayToBase64(pcmBytes),
      })
    );
  }, [closeRecordingResources]);

  const startRecording = useCallback(async () => {
    if (isRecording) {
      return;
    }

    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;

      if (!AudioContextClass || typeof AudioWorkletNode === "undefined") {
        throw new Error("AudioWorklet is not supported in this browser.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioContext = new AudioContextClass({ sampleRate: 16000 });
      const source = audioContext.createMediaStreamSource(stream);

      await audioContext.audioWorklet.addModule("/pcm-processor.js");

      const worklet = new AudioWorkletNode(audioContext, "pcm-processor");
      source.connect(worklet);
      worklet.connect(audioContext.destination);

      mediaStreamRef.current = stream;
      audioContextRef.current = audioContext;
      sourceNodeRef.current = source;
      workletNodeRef.current = worklet;
      pcmChunksRef.current = [];

      worklet.port.onmessage = (event) => {
        pcmChunksRef.current.push(new Uint8Array(event.data));
      };

      setIsRecording(true);

      recordingTimeoutRef.current = setTimeout(() => {
        finalizeRecording().catch((error) => {
          console.error("PCM finalize error:", error);
          setIsRecording(false);
        });
      }, RECORDING_DURATION_MS);
    } catch (error) {
      console.error("Microphone/PCM error:", error);
      setIsRecording(false);
      await closeRecordingResources();
      alert("Please allow microphone access to use voice input.");
    }
  }, [closeRecordingResources, finalizeRecording, isRecording]);

  const stopRecording = useCallback(() => {
    finalizeRecording().catch((error) => {
      console.error("PCM stop error:", error);
      setIsRecording(false);
    });
  }, [finalizeRecording]);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  return (
    <div className="app">
      <header className="header" id="app-header">
        <div className="header-brand">
          <div className="header-logo">HF</div>
          <div>
            <div className="header-title">Hero FinCorp</div>
            <div className="header-subtitle">AI Assistant</div>
          </div>
        </div>
        <div className="header-status">
          <span className={`status-dot ${isConnected ? "connected" : ""}`}></span>
          {isConnected ? "Connected" : "Connecting..."}
        </div>
      </header>

      <div className="main-content">
        <div className="avatar-panel" id="avatar-panel">
          <div className="avatar-toolbar">
            <button
              type="button"
              className="avatar-upload-btn"
              onClick={openAvatarPicker}
            >
              Upload GLB
            </button>
            <span className="avatar-source-label">{avatarSourceLabel}</span>
            <input
              ref={avatarInputRef}
              type="file"
              accept=".glb,model/gltf-binary"
              className="avatar-file-input"
              onChange={handleAvatarUpload}
            />
          </div>

          <div className="avatar-canvas-container">
            <Suspense
              fallback={
                <div className="loading-screen">
                  <div className="loading-spinner"></div>
                  <p>Loading 3D avatar...</p>
                </div>
              }
            >
              <Avatar
                visemes={currentVisemes}
                isSpeaking={isSpeaking}
                audioRef={audioRef}
                avatarUrl={avatarUrl}
                onAvatarError={handleAvatarRenderError}
              />
            </Suspense>
          </div>

          {(avatarError || isAvatarLoading) && (
            <div className="avatar-status-panel">
              <strong>{isAvatarLoading ? "Loading avatar..." : "Avatar issue"}</strong>
              <span>
                {isAvatarLoading
                  ? "Trying to load the realistic GLB model."
                  : avatarError}
              </span>
            </div>
          )}

          <div className="avatar-label">
            <span>●</span> Hero FinCorp AI Assistant
          </div>
        </div>

        <div className="chat-panel" id="chat-panel">
          <div className="chat-header">
            <h2>Conversation</h2>
            <p>Ask about loans, EMIs, accounts & more</p>
          </div>

          <div className="chat-messages" id="chat-messages">
            {messages.length === 0 && !isThinking && (
              <div className="welcome-message">
                <div className="welcome-icon">👋</div>
                <h3>Welcome to Hero FinCorp</h3>
                <p>
                  I&apos;m your AI assistant. Ask me about personal loans, EMI
                  payments, account status, or any other financial queries.
                </p>
              </div>
            )}

            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-sender">
                  {message.role === "user" ? "You" : "Assistant"}
                </div>
                {message.text}
              </div>
            ))}

            {isThinking && (
              <div className="thinking-indicator">
                <div className="thinking-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                Thinking...
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="input-bar" id="input-bar">
            <div className="input-row">
              <input
                id="chat-input"
                type="text"
                placeholder={isRecording ? "Listening..." : "Type your message..."}
                value={inputText}
                onChange={(event) => setInputText(event.target.value)}
                onKeyDown={handleKeyPress}
                disabled={isRecording || isThinking}
              />
              <button
                id="mic-button"
                className={`btn-icon btn-mic ${isRecording ? "recording" : ""}`}
                onClick={toggleRecording}
                title={isRecording ? "Stop recording" : "Start voice input"}
                disabled={isThinking}
              >
                {isRecording ? "⏹" : "🎤"}
              </button>
              <button
                id="send-button"
                className="btn-icon btn-send"
                onClick={sendTextMessage}
                disabled={!inputText.trim() || isThinking}
                title="Send message"
              >
                ▶
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
