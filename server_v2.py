import os
import json
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Malayalam Companion - Sarvam AI Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "").strip()
SARVAM_ASR_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"

VOICE_CATALOG = {
    "anger": "clip_anger.mp3",
    "anxiety": "clip_anxiety.mp3",
    "loneliness": "clip_loneliness.mp3",
    "sadness": "clip_sadness.mp3",
    "happy": "clip_happy.mp3",
    "confused": "clip_confused.mp3",
    "crisis": "clip_crisis.mp3",
    "neutral": "clip_happy.mp3"
}

LABEL_DETAILS = {
    "anger": "🔥 ANGER (ദേഷ്യം)",
    "anxiety": "⚠️ ANXIETY (പരിഭ്രാന്തി)",
    "loneliness": "🫂 LONELINESS (ഒറ്റപ്പെടൽ / സംസാരിക്കാൻ ആഗ്രഹം)",
    "sadness": "💧 SADNESS (സങ്കടം)",
    "happy": "✨ HAPPINESS (സന്തോഷം)",
    "confused": "🌀 CONFUSION (ആശയക്കുഴപ്പം)",
    "neutral": "🌿 NEUTRAL (സാധാരണ സംഭാഷണം)",
    "crisis": "🚨 CRISIS (ഗുരുതരം)"
}

def query_sarvam_asr(audio_bytes: bytes):
    key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not key:
        return "", "SARVAM_API_KEY is not set in Render Environment settings."

    headers = {
        "api-subscription-key": key
    }
    files = {
        "file": ("input.wav", audio_bytes, "audio/wav")
    }
    data = {
        "model": "saaras:v3",
        "language_code": "ml-IN",
        "mode": "transcribe"
    }

    try:
        res = requests.post(SARVAM_ASR_URL, headers=headers, files=files, data=data, timeout=15)
        if res.status_code != 200:
            return "", f"Sarvam ASR HTTP {res.status_code}: {res.text[:140]}"

        res_json = res.json()
        transcript = res_json.get("transcript", "").strip()
        return transcript, None
    except Exception as e:
        return "", f"ASR connection error: {str(e)}"

def query_sarvam_chat_emotion(transcript: str) -> str:
    key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not key or not transcript:
        return "neutral"

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": key
    }

    system_prompt = (
        "You are an empathetic Malayalam emotional classifier. "
        "Analyze the user's spoken Malayalam text and classify their emotional state into EXACTLY one of these labels:\n"
        "- anger\n"
        "- anxiety\n"
        "- loneliness\n"
        "- sadness\n"
        "- happy\n"
        "- confused\n"
        "- crisis\n"
        "- neutral\n\n"
        "Guidelines:\n"
        "- 'anxiety': Fear, stress, panic, upcoming exams/interviews, nervous dread.\n"
        "- 'sadness': Feeling down, crying, heartbreak, loss, exhaustion.\n"
        "- 'loneliness': Having no one to talk to, isolated, craving connection.\n"
        "- 'anger': Frustration, irritation, betrayed, rage.\n"
        "- 'happy': Joy, celebration, relief, exciting news.\n"
        "- 'confused': Puzzled, indecisive, not knowing what to do.\n"
        "- 'crisis': Thoughts of self-harm, ending life, utter despair.\n"
        "- 'neutral': Greetings, casual everyday remarks.\n\n"
        "Output ONLY the single label word in lowercase. Do not add any punctuation or other words."
    )

    payload = {
        "model": "sarvam-2b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Text: \"{transcript}\""}
        ],
        "temperature": 0.1,
        "max_tokens": 10
    }

    try:
        res = requests.post(SARVAM_CHAT_URL, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            res_json = res.json()
            raw_emotion = res_json["choices"][0]["message"]["content"].strip().lower()
            # Clean response to ensure exact tag matching
            for tag in VOICE_CATALOG.keys():
                if tag in raw_emotion:
                    return tag
        else:
            print(f"[CHAT API ERROR]: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[CHAT REQUEST EXCEPTION]: {str(e)}")

    return "neutral"

@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Malayalam Companion</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #070d19; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
    .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 28px; padding: 2.2rem 1.8rem; max-width: 420px; width: 100%; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7); }
    h2 { color: #38bdf8; margin: 0 0 8px 0; font-size: 24px; font-weight: 700; }
    .tag-badge { background: #4f46e5; color: #eef2ff; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; display: inline-block; margin-bottom: 24px; }
    .mic-btn { width: 96px; height: 96px; border-radius: 50%; background: #4f46e5; color: white; border: none; font-size: 40px; cursor: pointer; margin: 15px auto; display: flex; align-items: center; justify-content: center; transition: transform 0.15s ease; box-shadow: 0 10px 25px rgba(79, 70, 229, 0.4); outline: none; -webkit-tap-highlight-color: transparent; }
    .mic-btn:active { transform: scale(0.94); }
    .mic-btn.recording { background: #ef4444; box-shadow: 0 0 30px rgba(239, 68, 68, 0.8); animation: pulse 1.4s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
    #status { font-size: 15px; font-weight: 600; color: #94a3b8; margin-top: 10px; min-height: 22px; }
    .box { background: #030712; border-radius: 16px; padding: 16px; font-size: 14px; line-height: 1.6; text-align: left; margin-top: 24px; border: 1px solid #1e293b; min-height: 130px; white-space: pre-wrap; word-break: break-word; color: #e2e8f0; }
    .label { color: #818cf8; font-weight: 700; font-size: 12px; text-transform: uppercase; }
    .diag { color: #f87171; font-size: 12px; margin-top: 12px; line-height: 1.4; word-break: break-all; }
    audio { width: 100%; margin-top: 18px; border-radius: 8px; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Malayalam Companion</h2>
    <div class="tag-badge">SARVAM ASR + CHAT REASONING</div>
    
    <div>
      <button id="micBtn" class="mic-btn">🎙️</button>
      <div id="status">Tap mic to speak</div>
    </div>

    <div class="box" id="logs">Ready. Tap microphone, speak naturally in Malayalam, and tap again when done.</div>
    <div id="diag" class="diag"></div>
    <audio id="audioPlayer" controls style="display:none;"></audio>
  </div>

  <script>
    const micBtn = document.getElementById("micBtn");
    const status = document.getElementById("status");
    const logs = document.getElementById("logs");
    const diag = document.getElementById("diag");
    const player = document.getElementById("audioPlayer");

    let isRecording = false;
    let audioCtx = null;
    let micStream = null;
    let processor = null;
    let pcmChunks = [];

    function encodeWAV(samples, sampleRate) {
      const buffer = new ArrayBuffer(44 + samples.length * 2);
      const view = new DataView(buffer);

      function writeStr(offset, str) {
        for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
      }

      writeStr(0, "RIFF");
      view.setUint32(4, 36 + samples.length * 2, true);
      writeStr(8, "WAVE");
      writeStr(12, "fmt ");
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, 1, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * 2, true);
      view.setUint16(32, 2, true);
      view.setUint16(34, 16, true);
      writeStr(36, "data");
      view.setUint32(40, samples.length * 2, true);

      let offset = 44;
      for (let i = 0; i < samples.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      }
      return new Blob([view], { type: "audio/wav" });
    }

    async function startWavRecording() {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: 16000 } });
      audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const source = audioCtx.createMediaStreamSource(micStream);
      
      processor = audioCtx.createScriptProcessor(4096, 1, 1);
      pcmChunks = [];

      processor.onaudioprocess = (e) => {
        if (!isRecording) return;
        pcmChunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);
    }

    async function stopWavRecording() {
      if (processor) processor.disconnect();
      if (micStream) micStream.getTracks().forEach(t => t.stop());
      if (audioCtx) await audioCtx.close();

      let totalLen = pcmChunks.reduce((acc, c) => acc + c.length, 0);
      let merged = new Float32Array(totalLen);
      let offset = 0;
      for (let c of pcmChunks) {
        merged.set(c, offset);
        offset += c.length;
      }
      return encodeWAV(merged, 16000);
    }

    micBtn.onclick = async () => {
      player.load();
      diag.textContent = "";

      if (!isRecording) {
        try {
          await startWavRecording();
          isRecording = true;
          micBtn.classList.add("recording");
          status.textContent = "Listening... Tap to stop";
          logs.textContent = "സംസാരിക്കുക (Speaking in Malayalam)...";
        } catch (e) {
          diag.textContent = "Mic access error: " + e.message;
        }
      } else {
        isRecording = false;
        micBtn.classList.remove("recording");
        status.textContent = "Analyzing with Sarvam AI...";
        logs.textContent = "Transcribing and interpreting emotion...";

        const wavBlob = await stopWavRecording();
        const formData = new FormData();
        formData.append("audio_file", wavBlob, "input.wav");

        try {
          const res = await fetch("/api/process-audio", {
            method: "POST",
            body: formData
          });
          const data = await res.json();

          if (data.error_msg) {
            diag.textContent = data.error_msg;
          }

          let logHtml = 
            "<span class='label'>🗣️ Malayalam Transcription:</span>\\n\\"" + (data.transcription || "(none)") + "\\"\\n\\n" +
            "<span class='label'>🧠 Sarvam Intent Detection:</span> " + data.label;

          if (data.stream_url) {
            logHtml += "\\n<span class='label'>🔊 Audio Response:</span> " + data.clip_name;
            player.src = data.stream_url + "?t=" + Date.now();
            player.style.display = "block";
            player.play().catch(e => console.warn(e));
          }

          logs.innerHTML = logHtml;
          status.textContent = data.label;
        } catch (err) {
          diag.textContent = "Upload error: " + err.message;
          status.textContent = "Request failed";
        }
      }
    };
  </script>
</body>
</html>
    """

@app.get("/cdn/audio/{filename}")
async def get_audio(filename: str):
    path = os.path.join("voice_bank", filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path, media_type="audio/mpeg")

@app.post("/api/process-audio")
async def process_audio(audio_file: UploadFile = File(...)):
    audio_bytes = await audio_file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio payload")

    # Step 1: Speech-to-Text via Sarvam Saaras v3
    transcription, error_msg = query_sarvam_asr(audio_bytes)
    print(f"\n[SARVAM ASR]: '{transcription}' | Err: {error_msg}")

    # Step 2: Contextual Intent & Emotion Detection via Sarvam-2B LLM
    matched_tag = query_sarvam_chat_emotion(transcription) if transcription else "neutral"
    print(f"[SARVAM CHAT CLASSIFICATION]: {matched_tag}")

    clip = VOICE_CATALOG.get(matched_tag, "clip_happy.mp3")

    return {
        "transcription": transcription,
        "error_msg": error_msg,
        "label": LABEL_DETAILS.get(matched_tag, LABEL_DETAILS["neutral"]),
        "clip_name": clip,
        "stream_url": f"/cdn/audio/{clip}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
