import os
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Voice Companion - HuggingFace Audio Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "").strip()
# Updated to Hugging Face's official Inference Router domain
HF_ASR_URL = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3"

VOICE_CATALOG = {
    "anger": "clip_anger.mp3",
    "anxiety": "clip_anxiety.mp3",
    "loneliness": "clip_loneliness.mp3",
    "sadness": "clip_sadness.mp3",
    "happy": "clip_happy.mp3",
    "confused": "clip_confused.mp3",
    "crisis": "clip_crisis.mp3"
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

DIRECT_MAP = {
    "anger": [
        "ദേഷ്യം", "ദേഷ്യ", "ദേഷ്യമാണ്", "ദേഷ്യപ്പെടുന്നു", "ദേഷ്യം വരുന്നു", "ദേഷ്യമായി",
        "കോപം", "കോപ", "വെറുപ്പ്", "വെറുത്തു", "ചതി", "ചതിച്ചു", "സഹിക്കാൻ വയ്യ",
        "കലിപ്പ്", "കലിപ്പാണ്", "കലിപ്പ് വരുന്നു", "ദേഷ്യമുണ്ട്", "angry", "mad", "hate"
    ],
    "anxiety": [
        "പേടി", "പേടിയാണ്", "പേടിയാകുന്നു", "പേടിയാവുന്നു", "പേടിയുണ്ട്", "പേടിച്ചു",
        "ടെൻഷൻ", "ടെൻഷനാണ്", "ടെന്ഷന്", "ടെൻഷൻ ആകുന്നു", "ഭയം", "ഭയമാണ്",
        "പരിഭ്രാന്തി", "പരിഭ്രമം", "ശ്വാസം മുട്ടൽ", "ശ്വാസമെടുക്കാൻ പറ്റുന്നില്ല",
        "നെഞ്ചിടിപ്പ്", "നെഞ്ച് ഇടിക്കുന്നു", "വിറയ്ക്കുന്നു", "panic", "fear", "scared"
    ],
    "loneliness": [
        "ഒറ്റ", "ഒറ്റപ്പെടൽ", "ഒറ്റയ്ക്കാണ്", "ഒറ്റക്ക്", "ഒറ്റപ്പെട്ടു", "ഒറ്റയ്ക്കായി",
        "ആരുമില്ല", "ആരും കൂടെയില്ല", "തനിച്ചാണ്", "തനിച്ചായി", "തനിയെ", "തനിച്ചു",
        "മനസ്സ് തുറന്ന്", "മനസ്സു തുറന്ന്", "മനസ് തുറന്ന്", "സംസാരിക്കാൻ തോന്നുന്നു", "സംസാരിക്കാൻ ആരുമില്ല",
        "കേൾക്കാൻ ആരുമില്ല", "കൂട്ടില്ല", "കൂട്ടിന് ആരുമില്ല", "lonely", "alone", "isolated"
    ],
    "sadness": [
        "സങ്കടം", "സങ്കട", "സങ്കടമാണ്", "സങ്കടമുണ്ട്", "സങ്കടപ്പെടുന്നു", "സങ്കടമായി",
        "വിഷമം", "വിഷമ", "വിഷമമാണ്", "വിഷമമുണ്ട്", "വിഷമമായി",
        "കരച്ചിൽ", "കരയുന്നു", "കരഞ്ഞു", "കരയാൻ വരുന്നു", "കണ്ണീർ",
        "വേദന", "വേദനിക്കുന്നു", "മനസ്സു തകർന്നു", "മനസ്സ് തകർന്നു", "ഹൃദയം തകർന്നു",
        "തകർന്നുപോയി", "നിരാശ", "നിരാശയാണ്", "sad", "sadness", "cry", "crying", "grief"
    ],
    "happy": [
        "സന്തോഷം", "സന്തോഷ", "സന്തോഷമാണ്", "സന്തോഷമുണ്ട്", "സന്തോഷമായി", "സന്തോഷപ്പെടുന്നു",
        "ഹാപ്പി", "ഹാപ്പിയാണ്", "ചിരി", "നല്ല ദിവസം", "നല്ലൊരു ദിവസം", "അടിപൊളി",
        "സൂപ്പർ", "ആഹ്ലാദം", "ഉത്സാഹം", "രസം", "നന്ദി", "സുഖം", "സുഖമാണ്",
        "happy", "joy", "joyful", "glad", "great", "wonderful", "smile"
    ],
    "confused": [
        "ആശയക്കുഴപ്പം", "ആശയക്കുഴപ്പമാണ്", "ആശയക്കുഴപ്പമുണ്ട്", "മനസ്സിലാകുന്നില്ല", "മനസിലാകുന്നില്ല",
        "എന്ത് ചെയ്യണം", "എന്താ ചെയ്യേണ്ടത്", "എന്ത് ചെയ്യണമെന്ന് അറിയില്ല", "ഒരു എത്തും പിടിയും",
        "തലപുകയുന്നു", "ഒന്നും തിരിയുന്നില്ല", "confused", "confusion", "lost"
    ],
    "crisis": [
        "മരിക്കണം", "മരിക്കാൻ തോന്നുന്നു", "മരിച്ചാൽ മതി", "ജീവനൊടുക്കാൻ", "ജീവനൊടുക്കും",
        "ജീവിതം അവസാനിപ്പിക്കാൻ", "ജീവിതം മടുത്തു", "ഇനി ജീവിക്കേണ്ട", "ആത്മഹത്യ", "suicide"
    ],
    "neutral": [
        "നമസ്കാരം", "നമസ്തെ", "ഹലോ", "ഹായ്", "സുഖമാണോ", "വിശേഷങ്ങൾ",
        "hello", "hi", "hey"
    ]
}

def classify_text(text: str) -> str:
    clean = text.lower().replace("്", "").replace("ാ", "").replace("ി", "")
    for emotion, patterns in DIRECT_MAP.items():
        for pat in patterns:
            pat_clean = pat.lower().replace("്", "").replace("ാ", "").replace("ി", "")
            if pat_clean in clean or pat in text.lower():
                return emotion
    return "neutral"

def query_hf_asr(audio_bytes: bytes, mime_type: str = "audio/webm"):
    token = os.environ.get("HF_API_TOKEN", "").strip()
    if not token:
        print("[HF ASR Error]: HF_API_TOKEN is empty in environment variables.")
        return ""

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": mime_type
    }

    try:
        response = requests.post(
            HF_ASR_URL,
            headers=headers,
            data=audio_bytes,
            timeout=30
        )
        if response.status_code != 200:
            print(f"[HF ASR Error] Status {response.status_code}: {response.text[:200]}")
            return ""

        res_json = response.json()
        return res_json.get("text", "").strip()
    except Exception as e:
        print(f"[HF ASR Exception]: {e}")
        return ""

@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Malayalam Voice Companion</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #070d19; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
    .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 28px; padding: 2.2rem 1.8rem; max-width: 420px; width: 100%; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7); }
    h2 { color: #38bdf8; margin: 0 0 8px 0; font-size: 24px; font-weight: 700; }
    .tag-badge { background: #0284c7; color: #f0f9ff; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; display: inline-block; margin-bottom: 24px; }
    .mic-btn { width: 96px; height: 96px; border-radius: 50%; background: #0284c7; color: white; border: none; font-size: 40px; cursor: pointer; margin: 15px auto; display: flex; align-items: center; justify-content: center; transition: transform 0.15s ease; box-shadow: 0 10px 25px rgba(2, 132, 199, 0.4); outline: none; -webkit-tap-highlight-color: transparent; }
    .mic-btn:active { transform: scale(0.94); }
    .mic-btn.recording { background: #ef4444; box-shadow: 0 0 30px rgba(239, 68, 68, 0.8); animation: pulse 1.4s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
    #status { font-size: 15px; font-weight: 600; color: #94a3b8; margin-top: 10px; min-height: 22px; }
    .box { background: #030712; border-radius: 16px; padding: 16px; font-size: 14px; line-height: 1.6; text-align: left; margin-top: 24px; border: 1px solid #1e293b; min-height: 130px; white-space: pre-wrap; word-break: break-word; color: #e2e8f0; }
    .label { color: #38bdf8; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    audio { width: 100%; margin-top: 18px; border-radius: 8px; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Malayalam Companion</h2>
    <div class="tag-badge">SERVER-ASR AUDIO PIPELINE</div>
    
    <div>
      <button id="micBtn" class="mic-btn">🎙️</button>
      <div id="status">Tap mic to speak</div>
    </div>

    <div class="box" id="logs">Ready. Tap the microphone once to record, speak your Malayalam sentence, and tap again when finished.</div>
    <audio id="audioPlayer" controls style="display:none;"></audio>
  </div>

  <script>
    const micBtn = document.getElementById("micBtn");
    const status = document.getElementById("status");
    const logs = document.getElementById("logs");
    const player = document.getElementById("audioPlayer");

    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

    async function setupRecorder() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        let mime = "audio/webm";
        if (!MediaRecorder.isTypeSupported("audio/webm")) {
          if (MediaRecorder.isTypeSupported("audio/mp4")) {
            mime = "audio/mp4";
          } else {
            mime = "";
          }
        }
        
        mediaRecorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          micBtn.classList.remove("recording");
          status.textContent = "Processing speech...";
          logs.textContent = "Uploading audio to AI model for transcription...";

          const chosenType = mediaRecorder.mimeType || "audio/webm";
          const audioBlob = new Blob(audioChunks, { type: chosenType });
          audioChunks = [];

          const formData = new FormData();
          formData.append("audio_file", audioBlob, "recording.webm");
          formData.append("mime_type", chosenType);

          try {
            const res = await fetch("/api/process-audio", {
              method: "POST",
              body: formData
            });

            const data = await res.json();
            if (!data.transcription) {
              status.textContent = "Could not detect clear speech. Tap to retry.";
              logs.textContent = "No Malayalam words recognized. Please speak clearly closer to the microphone.";
              return;
            }

            let logHtml = 
              "<span class='label'>🗣️ Malayalam Transcription:</span>\\n\\"" + data.transcription + "\\"\\n\\n" +
              "<span class='label'>🧠 Triggered Emotion:</span> " + data.label;

            if (data.stream_url) {
              logHtml += "\\n<span class='label'>🔊 Audio Response:</span> " + data.clip_name;
              player.src = data.stream_url + "?t=" + Date.now();
              player.style.display = "block";
              player.play().catch(err => console.warn(err));
            } else {
              player.pause();
              player.style.display = "none";
            }

            logs.innerHTML = logHtml;
            status.textContent = data.label;
          } catch (err) {
            logs.textContent = "Error processing audio: " + err.message;
            status.textContent = "Server communication error";
          }
        };
      } catch (err) {
        status.textContent = "Microphone access denied";
        logs.textContent = "Please grant microphone permissions to use voice interaction.";
      }
    }

    micBtn.onclick = async () => {
      player.load();

      if (!mediaRecorder) {
        await setupRecorder();
      }

      if (!mediaRecorder) return;

      if (!isRecording) {
        audioChunks = [];
        mediaRecorder.start();
        isRecording = true;
        micBtn.classList.add("recording");
        status.textContent = "Recording... Tap again to finish";
        logs.textContent = "സംസാരിക്കുക (Speaking)...";
      } else {
        isRecording = false;
        mediaRecorder.stop();
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
async def process_audio(
    audio_file: UploadFile = File(...),
    mime_type: str = "audio/webm"
):
    audio_bytes = await audio_file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio payload")

    transcription = query_hf_asr(audio_bytes, mime_type=mime_type)
    print(f"\n[ASR TRANSCRIPT]: '{transcription}'")

    matched_tag = classify_text(transcription) if transcription else "neutral"
    clip = VOICE_CATALOG.get(matched_tag, None)
    print(f"[DECISION]: Emotion='{matched_tag}' -> Clip='{clip}'\n")

    return {
        "transcription": transcription,
        "label": LABEL_DETAILS.get(matched_tag, LABEL_DETAILS["neutral"]),
        "clip_name": clip,
        "stream_url": f"/cdn/audio/{clip}" if clip else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
