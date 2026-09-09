import os
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="De-Addiction Voice Companion")

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
    "craving": "clip_craving.mp3",
    "stigma": "clip_stigma.mp3",
    "crisis": "clip_crisis.mp3",
    "neutral": "clip_happy.mp3"
}

LABEL_DETAILS = {
    "anger": "🔥 AGITATION / ANGER (ദേഷ്യം / അസ്വസ്ഥത)",
    "anxiety": "⚠️ WITHDRAWAL / ANXIETY (വിറയൽ / പരിഭ്രാന്തി)",
    "loneliness": "🫂 ISOLATION (ഏകാന്തത)",
    "sadness": "💧 RELAPSE GUILT (സങ്കടം / കുറ്റബോധം)",
    "happy": "✨ RECOVERY PROGRESS (സന്തോഷം / പുരോഗതി)",
    "craving": "⚡ INTENSE CRAVING (തീവ്രമായ കൊതി / ആഗ്രഹം)",
    "stigma": "🛡️ FEAR OF STIGMA / TREATMENT (ചികിത്സാ ഭയം / നാണക്കേട്)",
    "crisis": "🚨 CRISIS INTERVENTION (അടിയന്തിര സഹായം)",
    "neutral": "🌿 GENERAL SUPPORT (പൊതുവായ പിന്തുണ)"
}

EMOTION_KEYWORDS = {
    "crisis": ["മരിക്കണം", "ജീവിതം മടുത്തു", "ആത്മഹത്യ", "suicide", "അവസാനിപ്പിക്കാൻ", "ജീവനൊടുക്കാൻ"],
    "stigma": ["റീഹാബ്", "നാണക്കേട്", "പോലീസ് കേസ്", "ഡോക്ടറെ കാണാൻ", "മുദ്രകുത്തുമോ", "ജോലി പോകും", "സമൂഹം", "നാട്ടുകാർ"],
    "craving": ["കൊതി", "ഉപയോഗിക്കാൻ തോന്നുന്നു", "ഇപ്പോൾ തന്നെ വേണം", "പിടിച്ചുനിൽക്കാൻ പറ്റുന്നില്ല", "കൈവിട്ടുപോകും", "craving", "urge"],
    "anxiety": [
        "വിറയ്ക്കുന്നു", "വിറയൽ", "സഹിക്കാൻ പറ്റുന്നില്ല", "പേടി", "പേടിയാണ്", "ടെൻഷൻ", 
        "ഉറങ്ങാൻ പറ്റിയില്ല", "നെഞ്ചിടിപ്പ്", "ശ്വാസം മുട്ടൽ", "withdrawal", "panic"
    ],
    "sadness": [
        "വീണുപോയി", "പഴയ ശീലം", "കുറ്റബോധം", "തോറ്റുപോയി", "തോൽപ്പിച്ചു", "വിഷമം", 
        "സങ്കടം", "കരച്ചിൽ", "വേദന", "നിരാശ", "relapse", "sad"
    ],
    "loneliness": [
        "ആരുമില്ല", "ഒറ്റപ്പെട്ടു", "ഒറ്റയ്ക്കാണ്", "ഏകാന്തത", "തനിച്ചാണ്", "തനിയെ", "കൂട്ടില്ല", "alone", "isolated"
    ],
    "anger": ["ദേഷ്യം", "വെറുപ്പ്", "ഉപദേശിക്കാൻ", "വെറുതെ വിട്ടേക്ക്", "കലിപ്പ്", "കോപം", "angry", "mad"],
    "happy": ["തൊട്ടിട്ടില്ല", "മാറ്റം", "നല്ല ദിവസം", "സന്തോഷം", "ആശ്വാസം", "ജയിച്ചു", "അഭിമാനം", "happy", "clean"]
}

def fast_local_classify(text: str):
    clean = text.lower()
    for emotion, patterns in EMOTION_KEYWORDS.items():
        for pat in patterns:
            if pat in clean:
                return emotion
    return None

def query_sarvam_asr(audio_bytes: bytes):
    key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not key:
        return "", "SARVAM_API_KEY missing in environment."

    headers = {"api-subscription-key": key}
    files = {"file": ("input.wav", audio_bytes, "audio/wav")}
    data = {
        "model": "saaras:v3",
        "language_code": "ml-IN",
        "mode": "transcribe"
    }

    try:
        res = requests.post(SARVAM_ASR_URL, headers=headers, files=files, data=data, timeout=15)
        if res.status_code != 200:
            return "", f"Sarvam ASR HTTP {res.status_code}: {res.text[:140]}"
        return res.json().get("transcript", "").strip(), None
    except Exception as e:
        return "", f"ASR connection error: {str(e)}"

def query_sarvam_chat_emotion(transcript: str) -> str:
    local_tag = fast_local_classify(transcript)
    if local_tag:
        return local_tag

    key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not key or not transcript:
        return "neutral"

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": key
    }

    prompt = (
        "You are an empathetic addiction recovery classifier. "
        "Classify the user's emotional state from this Malayalam speech into EXACTLY one category: "
        "[anger, anxiety, loneliness, sadness, happy, craving, stigma, crisis, neutral].\n"
        f"User text: \"{transcript}\"\n"
        "Return ONLY the single lowercased word."
    )

    payload = {
        "model": "sarvam-105b-conversations",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 8
    }

    try:
        res = requests.post(SARVAM_CHAT_URL, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"].strip().lower()
            for tag in VOICE_CATALOG.keys():
                if tag in content:
                    return tag
    except Exception:
        pass

    return "neutral"

@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>De-Addiction Voice Companion</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #070d19; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
    .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 28px; padding: 2.2rem 1.8rem; max-width: 440px; width: 100%; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7); }
    h2 { color: #38bdf8; margin: 0 0 8px 0; font-size: 22px; font-weight: 700; }
    .tag-badge { background: #0284c7; color: #f0f9ff; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; display: inline-block; margin-bottom: 24px; }
    .mic-btn { width: 96px; height: 96px; border-radius: 50%; background: #0284c7; color: white; border: none; font-size: 40px; cursor: pointer; margin: 20px auto; display: flex; align-items: center; justify-content: center; transition: transform 0.15s ease; box-shadow: 0 10px 25px rgba(2, 132, 199, 0.4); outline: none; -webkit-tap-highlight-color: transparent; }
    .mic-btn:active { transform: scale(0.94); }
    .mic-btn.recording { background: #ef4444; box-shadow: 0 0 30px rgba(239, 68, 68, 0.8); animation: pulse 1.4s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
    #status { font-size: 15px; font-weight: 600; color: #94a3b8; margin-top: 10px; min-height: 22px; }
    .box { background: #030712; border-radius: 16px; padding: 16px; font-size: 14px; line-height: 1.6; text-align: left; margin-top: 24px; border: 1px solid #1e293b; min-height: 130px; white-space: pre-wrap; word-break: break-word; color: #e2e8f0; }
    .label { color: #38bdf8; font-weight: 700; font-size: 12px; text-transform: uppercase; }
    .diag { color: #f87171; font-size: 12px; margin-top: 12px; line-height: 1.4; word-break: break-all; }
    audio { width: 100%; margin-top: 18px; border-radius: 8px; }
  </style>
</head>
<body>
  <div class="card">
    <h2>De-Addiction Voice Companion</h2>
    <div class="tag-badge">AI RECOVERY SUPPORT</div>

    <div>
      <button id="micBtn" class="mic-btn">🎙️</button>
      <div id="status">Ready</div>
    </div>

    <div class="box" id="logs">ഹലോ! ഇന്ന് നിങ്ങളെ എങ്ങനെ സഹായിക്കാം? നിങ്ങളുടെ മനസ്സിലുള്ളത് എന്തും ഇവിടെ തുറന്നു സംസാരിക്കാം. ഞങ്ങൾ കൂടെയുണ്ട്.</div>
    <div id="diag" class="diag"></div>
    <audio id="audioPlayer" controls style="display:none;"></audio>
  </div>

  <script>
    const micBtn = document.getElementById("micBtn");
    const status = document.getElementById("status");
    const logs = document.getElementById("logs");
    const diag = document.getElementById("diag");
    const player = document.getElementById("audioPlayer");

    let initialWelcomePlayed = false;
    let isRecording = false;
    let audioCtx = null;
    let micStream = null;
    let processor = null;
    let pcmChunks = [];

    // Attempt autoplay immediately on script evaluation
    function tryPlayWelcome() {
      if (initialWelcomePlayed) return;
      player.src = "/cdn/audio/clip_welcome.mp3?t=" + Date.now();
      player.style.display = "block";
      player.play().then(() => {
        initialWelcomePlayed = true;
      }).catch(err => {
        // Autoplay blocked by browser policy; will play on first click
        console.log("Autoplay waiting for first gesture:", err.message);
      });
    }

    window.addEventListener("DOMContentLoaded", tryPlayWelcome);
    window.addEventListener("load", tryPlayWelcome);

    // If blocked, any first tap/click anywhere on page immediately triggers it
    document.addEventListener("click", () => {
      if (!initialWelcomePlayed) {
        tryPlayWelcome();
      }
    }, { once: true });

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
      // If the welcome note has not yet played due to autoplay block, play it and don't record yet
      if (!initialWelcomePlayed) {
        tryPlayWelcome();
        return;
      }

      player.load();
      diag.textContent = "";

      if (!isRecording) {
        try {
          await startWavRecording();
          isRecording = true;
          micBtn.classList.add("recording");
          status.textContent = "Listening... Tap to send";
          logs.textContent = "സംസാരിക്കുക (Speaking in Malayalam)...";
        } catch (e) {
          diag.textContent = "Mic access error: " + e.message;
        }
      } else {
        isRecording = false;
        micBtn.classList.remove("recording");
        status.textContent = "Processing with Sarvam AI...";
        logs.textContent = "Analyzing speech...";

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
            "<span class='label'>🧠 Evaluated State:</span> " + data.label;

          if (data.stream_url) {
            logHtml += "\\n<span class='label'>🔊 Support Response:</span> " + data.clip_name;
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

    transcription, error_msg = query_sarvam_asr(audio_bytes)
    print(f"\n[SARVAM ASR]: '{transcription}' | Err: {error_msg}")

    matched_tag = query_sarvam_chat_emotion(transcription) if transcription else "neutral"
    print(f"[RECOVERY TAG]: {matched_tag}")

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
