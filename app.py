from io import BytesIO

from flask import Flask, jsonify, render_template_string, request, send_file
from gtts import gTTS
from gtts.lang import tts_langs

app = Flask(__name__)

MAX_CHARS = 5000
LANGS = sorted(tts_langs().items(), key=lambda item: item[1])  # (code, name)

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Text to Speech</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f3f4f6; margin: 0; }
    main { max-width: 640px; margin: 40px auto; background: #fff; padding: 24px;
           border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.08); }
    h1 { margin-top: 0; }
    textarea, select { width: 100%; padding: 10px; font-size: 16px; box-sizing: border-box; }
    textarea { height: 160px; }
    label { display: block; margin: 14px 0 6px; font-weight: bold; }
    .row { display: flex; gap: 16px; align-items: end; }
    .row > div { flex: 1; }
    button { margin-top: 18px; padding: 12px 20px; font-size: 16px; border: 0;
             border-radius: 8px; background: #f97316; color: #fff; cursor: pointer; }
    button:disabled { opacity: .6; cursor: wait; }
    audio { width: 100%; margin-top: 20px; }
    #msg { color: #b91c1c; margin-top: 12px; }
    #dl { display: inline-block; margin-top: 10px; }
  </style>
</head>
<body>
  <main>
    <h1>Text to Speech</h1>
    <p>Type or paste text, choose a language, then listen or download the audio.</p>

    <label for="textBox">Your text</label>
    <textarea id="textBox" placeholder="Type or paste your text here..."></textarea>

    <div class="row">
      <div>
        <label for="langBox">Language</label>
        <select id="langBox">
          {% for code, name in langs %}
          <option value="{{ code }}" {% if code == 'en' %}selected{% endif %}>{{ name }}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label><input type="checkbox" id="slowBox"> Speak slowly</label>
      </div>
    </div>

    <button id="goBtn">Generate speech</button>
    <div id="msg"></div>
    <audio id="player" controls hidden></audio>
    <a id="dl" download="speech.mp3" hidden>Download MP3</a>
  </main>

  <script>
    const textBox = document.getElementById("textBox");
    const langBox = document.getElementById("langBox");
    const slowBox = document.getElementById("slowBox");
    const goBtn = document.getElementById("goBtn");
    const msg = document.getElementById("msg");
    const player = document.getElementById("player");
    const dl = document.getElementById("dl");

    goBtn.onclick = async () => {
      msg.textContent = "";
      goBtn.disabled = true;
      goBtn.textContent = "Generating...";
      try {
        const res = await fetch("/speak", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: textBox.value,
            lang: langBox.value,
            slow: slowBox.checked
          })
        });
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.error || "Something went wrong.");
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        player.src = url;
        player.hidden = false;
        dl.href = url;
        dl.hidden = false;
        player.play();
      } catch (e) {
        msg.textContent = e.message;
      }
      goBtn.disabled = false;
      goBtn.textContent = "Generate speech";
    };
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE, langs=LANGS)


@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    lang = data.get("lang", "en")
    slow = bool(data.get("slow", False))

    if not text:
        return jsonify(error="Please enter some text first."), 400
    if len(text) > MAX_CHARS:
        return jsonify(error=f"Text is too long. Keep it under {MAX_CHARS} characters."), 400
    if lang not in dict(LANGS):
        lang = "en"

    try:
        buffer = BytesIO()
        gTTS(text=text, lang=lang, slow=slow).write_to_fp(buffer)
        buffer.seek(0)
        return send_file(buffer, mimetype="audio/mpeg")
    except Exception:
        return jsonify(error="Could not generate speech. Check your internet connection and try again."), 502


if __name__ == "__main__":
    app.run(debug=False)