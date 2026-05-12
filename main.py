import base64
import json
import os
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# Configuração da página Streamlit
st.set_page_config(
    page_title="Domingo de Noite Sofrendo",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dimensões do jogo
WIDTH = 1280
HEIGHT = 720

# Dicionário de tipos MIME
MIME_BY_SUFFIX = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

def get_local_file_as_data_uri(file_path):
    """Lê um arquivo local e converte para Data URI."""
    if not os.path.exists(file_path):
        return ""
    suffix = Path(file_path).suffix.lower()
    mime = MIME_BY_SUFFIX.get(suffix, "application/octet-stream")
    with open(file_path, "rb") as f:
        payload = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{payload}"

def file_to_data_uri(uploaded_file, local_path, fallback_mime="application/octet-stream"):
    """Prioriza o arquivo enviado por upload; se não houver, tenta o arquivo local."""
    if uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix.lower()
        mime = MIME_BY_SUFFIX.get(suffix, fallback_mime)
        payload = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        return f"data:{mime};base64,{payload}"
    return get_local_file_as_data_uri(local_path)

st.title("Domingo de Noite Sofrendo — Carregamento Automático")
st.write(
    "Este jogo agora carrega automaticamente os arquivos `musica.mp3` e os sprites se eles estiverem na mesma pasta do script! "
    "Você ainda pode usar a barra lateral para trocar os arquivos em tempo real."
)

with st.sidebar:
    st.header("🎮 Configurações")
    
    audio_file = st.file_uploader(
        "Trocar Música (Opcional)",
        type=["mp3", "wav", "ogg"],
        help="Se você não enviar nada, ele tentará carregar 'musica.mp3' da pasta.",
    )

    st.divider()
    st.subheader("🖼️ Sprites & Chroma Key")
    chroma_sensitivity = st.slider("Sensibilidade do Verde", 0, 255, 100)
    
    st.caption("Envie arquivos para substituir os locais (sprite_p.png, etc):")
    col1, col2 = st.columns(2)
    with col1:
        u_idle = st.file_uploader("Idle", type=["png", "jpg", "webp"], key="u_idle")
        u_down = st.file_uploader("Baixo", type=["png", "jpg", "webp"], key="u_down")
        u_right = st.file_uploader("Direita", type=["png", "jpg", "webp"], key="u_right")
    with col2:
        u_left = st.file_uploader("Esquerda", type=["png", "jpg", "webp"], key="u_left")
        u_up = st.file_uploader("Cima", type=["png", "jpg", "webp"], key="u_up")

    st.divider()
    st.subheader("⚙️ Dificuldade")
    bpm = st.slider("BPM", min_value=60, max_value=240, value=172)
    note_speed = st.slider("Velocidade das notas", min_value=100, max_value=800, value=300)
    note_freq = st.slider("Densidade de notas", min_value=0.2, max_value=3.0, value=1.0)
    seed = st.number_input("Seed do mapa", min_value=1, value=12345)

# Mapeamento de assets (Prioriza Upload > Local)
assets = {
    "audio": file_to_data_uri(audio_file, "musica.mp3", "audio/mpeg"),
    "sprites": {
        "idle": file_to_data_uri(u_idle, "sprite_p.png", "image/png"),
        "left": file_to_data_uri(u_left, "sprite_e.png", "image/png"),
        "down": file_to_data_uri(u_down, "sprite_b.png", "image/png"),
        "up": file_to_data_uri(u_up, "sprite_c.png", "image/png"),
        "right": file_to_data_uri(u_right, "sprite_d.png", "image/png"),
    },
    "config": {
        "width": WIDTH,
        "height": HEIGHT,
        "bpm": bpm,
        "noteSpeed": note_speed,
        "noteFreq": note_freq,
        "seed": int(seed),
        "chromaSensitivity": chroma_sensitivity
    },
}

config_json = json.dumps(assets, ensure_ascii=False)

# Código HTML/JS do jogo
html_code = f"""
<div id="game-container">
    <div class="controls">
        <button id="start-btn">JOGAR / REINICIAR</button>
        <span id="game-status">Carregando assets...</span>
    </div>
    <canvas id="gameCanvas" width="{WIDTH}" height="{HEIGHT}" tabindex="0"></canvas>
</div>

<style>
    #game-container {{ display: flex; flex-direction: column; align-items: center; font-family: sans-serif; color: white; }}
    .controls {{ width: {WIDTH}px; max-width: 100%; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
    #start-btn {{ padding: 10px 20px; background: #ff4b4b; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }}
    #gameCanvas {{ background: #146464; border: 4px solid #262730; border-radius: 10px; outline: none; max-width: 100%; height: auto; }}
    #gameCanvas:focus {{ border-color: #ff4b4b; }}
</style>

<script>
(() => {{
    const assets = {config_json};
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const startBtn = document.getElementById('start-btn');
    const statusTxt = document.getElementById('game-status');

    const COLORS = {{
        bg: '#146464', dark: '#141428', gray: '#3c3c50', white: '#ffffff',
        hitLine: '#c8c8ff', perfect: '#ffdc32', good: '#50dc78', miss: '#dc3c3c',
        combo: '#ffb400', lanes: ['#ffffff', '#ffa032', '#3cffff', '#f0a0f0']
    }};

    const GAME_CFG = {{
        laneCount: 4, laneWidth: 60, gap: 12, startX: 30,
        hitY: {HEIGHT} - 100, noteH: 24, charX: 630, charY: {HEIGHT} - 80, spriteH: 350
    }};

    const KEY_MAP = {{ 'ArrowLeft': 0, 'ArrowDown': 1, 'ArrowUp': 2, 'ArrowRight': 3, 'a': 0, 's': 1, 'j': 2, 'k': 3 }};

    function removeGreen(img) {{
        const c = document.createElement('canvas');
        c.width = img.width; c.height = img.height;
        const x = c.getContext('2d');
        x.drawImage(img, 0, 0);
        const d = x.getImageData(0, 0, c.width, c.height);
        const s = assets.config.chromaSensitivity;
        for (let i=0; i<d.data.length; i+=4) {{
            if (d.data[i+1] > s && d.data[i+1] > d.data[i] && d.data[i+1] > d.data[i+2]) d.data[i+3] = 0;
        }}
        x.putImageData(d, 0, 0);
        const n = new Image(); n.src = c.toDataURL(); return n;
    }}

    const sprites = {{}};
    const spritePromises = Object.entries(assets.sprites).map(([name, src]) => {{
        if (!src) return Promise.resolve();
        return new Promise(r => {{
            const i = new Image(); i.onload = () => {{ sprites[name] = removeGreen(i); r(); }}; i.src = src;
        }});
    }});

    const audio = assets.audio ? new Audio(assets.audio) : null;

    class Game {{
        constructor() {{ this.reset(); }}
        reset() {{
            this.running = false; this.score = 0; this.combo = 0; this.health = 100;
            this.feedback = ""; this.fbT = 0; this.pose = "idle"; this.poseT = 0;
            this.flash = [0,0,0,0]; this.gameOver = false; this.finished = false;
            this.rng = assets.config.seed; this.chart = this.genChart();
            if (audio) {{ audio.pause(); audio.currentTime = 0; }}
        }}
        random() {{ this.rng = (this.rng * 1664525 + 1013904223) >>> 0; return this.rng / 4294967296; }}
        genChart() {{
            const n = []; const dur = audio?.duration || 90; const bi = 60 / assets.config.bpm;
            let t = 3.0;
            while (t < dur - 1.0) {{
                const l = Math.floor(this.random() * 4); n.push({{ lane: l, time: t, hit: false, miss: false }});
                if (this.random() < 0.2) n.push({{ lane: (l+1)%4, time: t, hit: false, miss: false }});
                t += bi * [0.5, 1, 1, 1, 2][Math.floor(this.random()*5)] * assets.config.noteFreq;
            }}
            return n.sort((a,b) => a.time - b.time);
        }}
        start() {{ this.reset(); this.running = true; this.startTime = performance.now(); if (audio) audio.play(); statusTxt.textContent = "JOGANDO!"; }}
        update(now) {{
            if (!this.running || this.gameOver || this.finished) return;
            const ct = (now - this.startTime) / 1000;
            for (const n of this.chart) if (!n.hit && !n.miss && n.time < ct - 0.25) {{ n.miss = true; this.combo = 0; this.health -= 8; this.feedback = "MISS"; this.fbT = 0.4; }}
            if (this.fbT > 0) this.fbT -= 1/60;
            if (this.poseT > 0) this.poseT -= 1/60; else this.pose = "idle";
            for (let i=0; i<4; i++) if (this.flash[i] > 0) this.flash[i] -= 1/60;
            if (this.health <= 0) {{ this.gameOver = true; this.running = false; statusTxt.textContent = "GAME OVER"; }}
            if (ct > (audio?.duration || 90) + 1) {{ this.finished = true; this.running = false; statusTxt.textContent = "FIM!"; }}
        }}
        handle(key) {{
            const l = KEY_MAP[key]; if (l === undefined || !this.running) return;
            const ct = (performance.now() - this.startTime) / 1000;
            let b = null; let d = 999;
            for (const n of this.chart) if (!n.hit && !n.miss && n.lane === l) {{ const df = Math.abs(n.time - ct); if (df < d) {{ d = df; b = n; }} }}
            if (!b || d > 0.25) return;
            this.flash[l] = 0.15; this.pose = ["left", "down", "up", "right"][l]; this.poseT = 0.25;
            if (d < 0.08) {{ b.hit = true; this.score += 300; this.combo++; this.feedback = "PERFECT"; this.fbT = 0.6; this.health = Math.min(100, this.health+5); }}
            else {{ b.hit = true; this.score += 100; this.combo++; this.feedback = "GOOD"; this.fbT = 0.5; this.health = Math.min(100, this.health+2); }}
        }}
        draw() {{
            ctx.fillStyle = COLORS.bg; ctx.fillRect(0, 0, {WIDTH}, {HEIGHT});
            const ct = this.running ? (performance.now() - this.startTime) / 1000 : 0;
            ctx.strokeStyle = COLORS.gray; ctx.beginPath(); ctx.moveTo(370, 0); ctx.lineTo(370, {HEIGHT}); ctx.stroke();
            for (let i=0; i<4; i++) {{
                const x = GAME_CFG.startX + i * (GAME_CFG.laneWidth + GAME_CFG.gap);
                ctx.fillStyle = COLORS.dark; ctx.fillRect(x, 0, GAME_CFG.laneWidth, {HEIGHT});
                ctx.strokeStyle = COLORS.lanes[i]; ctx.strokeRect(x, 0, GAME_CFG.laneWidth, {HEIGHT});
            }}
            ctx.strokeStyle = COLORS.hitLine; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(GAME_CFG.startX-5, GAME_CFG.hitY); ctx.lineTo(GAME_CFG.startX+288, GAME_CFG.hitY); ctx.stroke(); ctx.lineWidth = 1;
            for (const n of this.chart) {{
                if (n.hit || n.miss) continue;
                const td = n.time - ct; if (td > 2 || td < -0.5) continue;
                const y = GAME_CFG.hitY - td * assets.config.noteSpeed - 12;
                const x = GAME_CFG.startX + n.lane * 72;
                ctx.fillStyle = COLORS.lanes[n.lane]; ctx.fillRect(x+4, y, 52, 24);
            }}
            for (let i=0; i<4; i++) {{
                const x = GAME_CFG.startX + i * 72;
                ctx.fillStyle = this.flash[i] > 0 ? COLORS.lanes[i] : COLORS.gray;
                ctx.fillRect(x+4, GAME_CFG.hitY-18, 52, 36);
            }}
            const img = sprites[this.pose] || sprites.idle;
            if (img) {{ const r = 350/img.height; ctx.drawImage(img, 630-img.width*r/2, {HEIGHT}-80-350, img.width*r, 350); }}
            ctx.fillStyle = "white"; ctx.font = "bold 24px monospace"; ctx.fillText("SCORE: " + this.score, 400, 50);
            if (this.fbT > 0) {{ ctx.fillStyle = COLORS.perfect; ctx.fillText(this.feedback, GAME_CFG.startX, GAME_CFG.hitY-60); }}
            ctx.fillStyle = COLORS.gray; ctx.fillRect(400, {HEIGHT}-50, 300, 20);
            ctx.fillStyle = COLORS.good; ctx.fillRect(400, {HEIGHT}-50, 300*(this.health/100), 20);
            if (!this.running) {{ ctx.fillStyle = "rgba(0,0,0,0.5)"; ctx.fillRect(0,0,{WIDTH},{HEIGHT}); ctx.fillStyle="white"; ctx.textAlign="center"; ctx.fillText("PRONTO?", {WIDTH}/2, {HEIGHT}/2); }}
        }}
    }}

    const game = new Game();
    function loop(n) {{ game.update(n); game.draw(); requestAnimationFrame(loop); }}
    startBtn.onclick = () => {{ canvas.focus(); game.start(); }};
    canvas.onkeydown = (e) => game.handle(e.key);
    Promise.all(spritePromises).then(() => {{ requestAnimationFrame(loop); statusTxt.textContent = "Pronto!"; }});
}})();
</script>
"""

# Renderizar o componente
components.html(html_code, height=800, scrolling=False)

st.divider()
st.markdown("""
### 📂 Como usar no GitHub / Streamlit Cloud
Para que o jogo carregue tudo sozinho, coloque os arquivos com estes nomes exatos na mesma pasta:
- `musica.mp3`
- `sprite_p.png` (Parado)
- `sprite_e.png` (Esquerda)
- `sprite_b.png` (Baixo)
- `sprite_c.png` (Cima)
- `sprite_d.png` (Direita)
""")
