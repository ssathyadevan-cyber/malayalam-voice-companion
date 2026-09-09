import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Voice Companion - Real-Time Malayalam Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

DIRECT_MAP = {
    "anger": ["ദേഷ്യം", "ദേഷ്യ", "ദേഷ്യമാണ്", "കോപം", "വെറുപ്പ്", "കലിപ്പ്", "angry", "mad"],
    "anxiety": ["പേടി", "പേടിയാണ്", "ടെൻഷൻ", "ഭയം", "പരിഭ്രാന്തി", "വിറയ്ക്കുന്നു", "panic", "fear"],
    "loneliness": ["ഒറ്റ", "ഒറ്റപ്പെടൽ", "ഒറ്റയ്ക്കാണ്", "ആരുമില്ല", "തനിച്ചാണ്", "തനിയെ", "lonely", "alone"],
    "sadness": ["സങ്കടം", "സങ്കട", "സങ്കടമാണ്", "വിഷമം", "വിഷമമാണ്", "കരച്ചിൽ", "വേദന", "നിരാശ", "sad", "cry"],
    "happy": ["സന്തോഷം", "സന്തോഷ", "സന്തോഷമാണ്", "സന്തോഷമുണ്ട്", "ഹാപ്പി", "ചിരി", "നല്ല", "അടിപൊളി", "സൂപ്പർ", "happy", "joy"],
    "confused": ["ആശയക്കുഴപ്പം", "മനസ്സിലാകുന്നില്ല", "മനസിലാകുന്നില്ല", "എന്ത് ചെയ്യണം", "confused", "lost"],
    "crisis": ["മരിക്കണം", "ജീവിതം മടുത്തു", "ആത്മഹത്യ", "suicide"],
    "neutral": ["നമസ്കാരം", "ഹലോ", "ഹായ്", "hello", "hi"]
}

class TextPayload(BaseModel):
    text: str

def classify_text(text: str) -> str:
    clean = text.lower().replace("്", "").replace("ാ", "").replace("ി", "")
    for emotion, patterns in DIRECT_MAP.items():
        for pat in patterns:
            pat_clean = pat.lower().replace("്", "").replace("ാ", "").replace("ി", "")
            if pat_clean in clean or pat in text.lower():
                return emotion
    return "neutral"

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
    .tag-badge { background: #059669; color: #ecfdf5; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; display: inline-block; margin-bottom: 24px; }
    .mic-btn { width: 96px; height: 96px; border-radius: 50%; background: #0284c7; color: white; border: none; font-size: 40px; cursor: pointer; margin: 15px auto; display: flex; align-items: center; justify-content: center; transition: transform 0.15s ease; box-shadow: 0 10px 25px rgba(2, 132, 199, 0.4); outline: none; -webkit-tap-highlight-color: transparent; }
    .mic-btn:active { transform: scale(0.94); }
    .mic-btn.listening { background: #ef4444; box-shadow: 0 0 30px rgba(239, 68, 68, 0.8); animation: pulse 1.4s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
    #status { font-size: 15px; font-weight: 600; color: #94a3b8; margin-top: 10px; min-height: 22px; }
    .box { background: #030712; border-radius: 16px; padding: 16px; font-size: 14px; line-height: 1.6; text-align: left; margin-top: 24px; border: 1px solid #1e293b; min-height: 130px; white-space: pre-wrap; word-break: break-word; color: #e2e8f0; }
    .label { color: #38bdf8; font-weight: 700; font-size: 12px; text-transform: uppercase; }
    audio { width: 100%; margin-top: 18px; border-radius: 8px; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Malayalam Companion</h2>
    <div class="tag-badge">REAL-TIME INSTANT ENGINE</div>
    
    <div>
      <button id="micBtn" class="mic-btn">🎙️</button>
      <div id="status">Tap mic to speak</div>
    </div>

    <div class="box" id="logs">Tap mic and speak in Malayalam. Speech is detected and evaluated in real time without serverless lag.</div>
    <audio id="audioPlayer" controls style="display:none;"></audio>
  </div>

  <script>
    const micBtn = document.getElementById("micBtn");
    const status = document.getElementById("status");
    const logs = document.getElementById("logs");
    const player = document.getElementById("audioPlayer");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isListening = false;

    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.lang = "ml-IN";
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => {
        isListening = true;
        micBtn.classList.add("listening");
        status.textContent = "Listening to Malayalam...";
        logs.textContent = "സംസാരിക്കുക...";
      };

      recognition.onresult = async (event) => {
        const text = event.results[0][0].transcript.trim();
        logs.textContent = "Processing: " + text;
        status.textContent = "Evaluating emotion...";

        try {
          const res = await fetch("/api/evaluate-emotion", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
          });

          const data = await res.json();
          let logHtml = 
            "<span class='label'>🗣️ Malayalam Input:</span>\\n\\"" + text + "\\"\\n\\n" +
            "<span class='label'>🧠 Triggered Emotion:</span> " + data.label;

          if (data.stream_url) {
            logHtml += "\\n<span class='label'>🔊 Audio Response:</span> " + data.clip_name;
            player.src = data.stream_url + "?t=" + Date.now();
            player.style.display = "block";
            player.play().catch(e => console.warn(e));
          }

          logs.innerHTML = logHtml;
          status.textContent = data.label;
        } catch (err) {
          logs.textContent = "Server error: " + err.message;
        }
      };

      recognition.onerror = (e) => {
        status.textContent = "Recognition error: " + e.error;
        logs.textContent = "Error code: " + e.error + ". Please tap the mic and try again.";
        micBtn.classList.remove("listening");
        isListening = false;
      };

      recognition.onend = () => {
        micBtn.classList.remove("listening");
        isListening = false;
      };
    } else {
      status.textContent = "Unsupported Browser";
      logs.textContent = "Speech recognition is not supported on this browser. Please open in Google Chrome on Android or Desktop.";
    }

    micBtn.onclick = () => {
      player.load();
      if (!recognition) return;
      if (!isListening) {
        recognition.start();
      } else {
        recognition.stop();
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

@app.post("/api/evaluate-emotion")
async def evaluate_emotion(payload: TextPayload):
    text = payload.text.strip()
    matched_tag = classify_text(text) if text else "neutral"
    clip = VOICE_CATALOG.get(matched_tag, "clip_happy.mp3")

    return {
        "text": text,
        "emotion": matched_tag,
        "label": LABEL_DETAILS.get(matched_tag, LABEL_DETAILS["neutral"]),
        "clip_name": clip,
        "stream_url": f"/cdn/audio/{clip}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
