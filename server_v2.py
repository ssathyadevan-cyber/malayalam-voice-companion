import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Voice Companion V4 - Stable Mobile")

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
  <title>Voice Companion V4 (ml-IN)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #080e1e; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 16px; box-sizing: border-box; }
    .card { background: #131b2e; border: 1px solid #1e293b; border-radius: 24px; padding: 1.8rem; max-width: 440px; width: 100%; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
    h2 { color: #38bdf8; margin: 0 0 6px 0; }
    .tag-badge { background: #0369a1; color: #e0f2fe; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; display: inline-block; margin-bottom: 15px; }
    .mic-btn { width: 85px; height: 85px; border-radius: 50%; background: #0284c7; color: white; border: none; font-size: 34px; cursor: pointer; margin: 10px 0; transition: all 0.2s; box-shadow: 0 0 20px rgba(2, 132, 199, 0.4); outline: none; }
    .mic-btn.recording { background: #ef4444; box-shadow: 0 0 25px rgba(239, 68, 68, 0.7); animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.06); } 100% { transform: scale(1); } }
    .box { background: #060a14; border-radius: 12px; padding: 14px; font-size: 13.5px; text-align: left; margin-top: 15px; border: 1px solid #1e293b; min-height: 100px; white-space: pre-wrap; word-break: break-word; }
    .label { color: #38bdf8; font-weight: bold; font-size: 12px; }
    audio { width: 100%; margin-top: 15px; }
    .manual-row { margin-top: 14px; display: flex; gap: 8px; }
    .manual-input { flex: 1; padding: 10px 14px; border-radius: 10px; border: 1px solid #334155; background: #0b1120; color: #fff; font-size: 14px; outline: none; }
    .manual-btn { padding: 10px 16px; border-radius: 10px; border: none; background: #0284c7; color: #fff; font-weight: bold; cursor: pointer; font-size: 13px; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Malayalam Companion</h2>
    <div class="tag-badge">MOBILE-V4 RESILIENT</div>
    
    <div>
      <button id="micBtn" class="mic-btn">🎙️</button>
      <div id="status" style="font-size: 14px; font-weight: 600; color: #cbd5e1;">Tap to Start Speaking</div>
    </div>

    <div class="manual-row">
      <input type="text" id="manualText" class="manual-input" placeholder="Or type Malayalam keyword..." />
      <button id="sendBtn" class="manual-btn">Test</button>
    </div>

    <div class="box" id="logs">Ready. Tap microphone to speak, or type a word to test.</div>
    <audio id="audioPlayer" controls style="display:none;"></audio>
  </div>

  <script>
    const micBtn = document.getElementById("micBtn");
    const status = document.getElementById("status");
    const logs = document.getElementById("logs");
    const player = document.getElementById("audioPlayer");
    const manualText = document.getElementById("manualText");
    const sendBtn = document.getElementById("sendBtn");

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    let rec = null;
    let isRecording = false;
    let capturedSegments = [];

    if (!SpeechRec) {
      logs.textContent = "Speech recognition is not supported natively in this browser view. You can type words below to test directly.";
      micBtn.style.opacity = "0.5";
    } else {
      rec = new SpeechRec();
      rec.lang = "ml-IN";
      rec.continuous = true;
      rec.interimResults = true;

      rec.onstart = () => {
        isRecording = true;
        capturedSegments = [];
        micBtn.classList.add("recording");
        status.textContent = "Listening... Tap mic again to Finish";
        logs.textContent = "സംസാരിക്കുക (Speak now)...";
      };

      rec.onresult = (e) => {
        // Clean array deduplication based on result indices
        let transcript = "";
        for (let i = 0; i < e.results.length; ++i) {
          transcript += e.results[i][0].transcript + " ";
        }
        transcript = transcript.trim();
        if (transcript) {
          logs.textContent = transcript;
        }
      };

      rec.onerror = (e) => {
        console.warn("Speech API error:", e.error);
        if (e.error === "not-allowed") {
          status.textContent = "Mic access blocked. Check permissions.";
        }
      };

      rec.onend = () => {
        if (isRecording) {
          // If stopped involuntarily by mobile OS while still intended to record, restart
          try {
            rec.start();
          } catch(err) {}
        } else {
          micBtn.classList.remove("recording");
        }
      };

      async function triggerClassification(textToSubmit) {
        if (!textToSubmit) return;
        status.textContent = "Analyzing emotion...";
        
        try {
          const res = await fetch("/api/classify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: textToSubmit })
          });
          const data = await res.json();

          let logText = 
            "<span class='label'>🗣️ Malayalam Input:</span>\\n\\"" + data.transcription + "\\"\\n\\n" +
            "<span class='label'>🧠 Triggered Emotion:</span> " + data.label;

          if (data.stream_url) {
            logText += "\\n<span class='label'>🔊 Playing Asset:</span> " + data.clip_name;
            player.src = data.stream_url + "?t=" + Date.now();
            player.style.display = "block";
            player.play().catch(err => {
              console.warn("Autoplay notice:", err);
            });
          } else {
            player.pause();
            player.style.display = "none";
          }

          logs.innerHTML = logText;
          status.textContent = data.label;
        } catch (err) {
          logs.textContent = "Error: " + err.message;
          status.textContent = "Classification error";
        }
      }

      micBtn.onclick = () => {
        // Audio pre-unlock for mobile browsers
        player.load();

        if (!isRecording) {
          try {
            rec.start();
          } catch(e) {
            console.warn("Start error:", e);
          }
        } else {
          isRecording = false;
          try { rec.stop(); } catch(e) {}
          micBtn.classList.remove("recording");
          status.textContent = "Stopping...";
          
          setTimeout(() => {
            const raw = logs.textContent.trim();
            if (raw && !raw.startsWith("Ready.") && !raw.startsWith("സംസാരിക്കുക")) {
              triggerClassification(raw);
            } else {
              status.textContent = "No speech detected. Tap to try again.";
            }
          }, 300);
        }
      };

      sendBtn.onclick = () => {
        const text = manualText.value.trim();
        if (text) {
          triggerClassification(text);
          manualText.value = "";
        }
      };
      
      manualText.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          sendBtn.click();
        }
      });
    }
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

@app.post("/api/classify")
async def handle_classify(payload: TextPayload):
    text = payload.text.strip()
    print(f"\n[MALAYALAM INPUT]: '{text}'")

    matched_tag = classify_text(text)
    clip = VOICE_CATALOG.get(matched_tag, None)
    print(f"[DECISION]: Tag='{matched_tag}' -> Clip='{clip}'\n")

    return {
        "transcription": text,
        "label": LABEL_DETAILS.get(matched_tag, LABEL_DETAILS["neutral"]),
        "clip_name": clip,
        "stream_url": f"/cdn/audio/{clip}" if clip else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
