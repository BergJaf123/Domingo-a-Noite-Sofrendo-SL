import base64
import json
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

# Dicionário de tipos MIME para conversão de arquivos
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

def file_to_data_uri(uploaded_file, fallback_mime="application/octet-stream"):
    """Converte um arquivo enviado pelo Streamlit em Data URI para uso no navegador."""
    if uploaded_file is None:
        return ""
    suffix = Path(uploaded_file.name).suffix.lower()
    mime = MIME_BY_SUFFIX.get(suffix, fallback_mime)
    payload = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    return f"data:{mime};base64,{payload}"

st.title("Domingo de Noite Sofrendo — 100% Streamlit")
st.write(
    "Esta versão agora remove o fundo verde dos sprites automaticamente! "
    "Use os controles na barra lateral para ajustar a sensibilidade do Chroma Key."
)

with st.sidebar:
    st.header("🎮 Configurações")
    
    audio_file = st.file_uploader(
        "Música do jogo",
        type=["mp3", "wav", "ogg"],
        help="Envie seu arquivo de áudio (ex: musica.mp3).",
    )

    st.divider()
    st.subheader("🖼️ Sprites & Chroma Key")
    chroma_sensitivity = st.slider("Sensibilidade do Verde", 0, 255, 100, help="Aumente se o fundo verde ainda aparecer.")
    
    col1, col2 = st.columns(2)
    with col1:
        idle_sprite = st.file_uploader("Idle (Parado)", type=["png", "jpg", "jpeg", "webp", "gif"], key="idle")
        down_sprite = st.file_uploader("Baixo", type=["png", "jpg", "jpeg", "webp", "gif"], key="down")
        right_sprite = st.file_uploader("Direita", type=["png", "jpg", "jpeg", "webp", "gif"], key="right")
    with col2:
        left_sprite = st.file_uploader("Esquerda", type=["png", "jpg", "jpeg", "webp", "gif"], key="left")
        up_sprite = st.file_uploader("Cima", type=["png", "jpg", "jpeg", "webp", "gif"], key="up")

    st.divider()
    st.subheader("⚙️ Dificuldade")
    bpm = st.slider("BPM", min_value=60, max_value=240, value=172)
    note_speed = st.slider("Velocidade das notas", min_value=100, max_value=800, value=300)
    note_freq = st.slider("Densidade de notas", min_value=0.2, max_value=3.0, value=1.0)
    seed = st.number_input("Seed do mapa", min_value=1, value=12345)

# Preparar assets para o JavaScript
assets = {
    "audio": file_to_data_uri(audio_file, "audio/mpeg"),
    "sprites": {
        "idle": file_to_data_uri(idle_sprite, "image/png"),
        "left": file_to_data_uri(left_sprite, "image/png"),
        "down": file_to_data_uri(down_sprite, "image/png"),
        "up": file_to_data_uri(up_sprite, "image/png"),
        "right": file_to_data_uri(right_sprite, "image/png"),
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
        <span id="game-status">Aguardando início...</span>
    </div>
    <canvas id="gameCanvas" width="{WIDTH}" height="{HEIGHT}" tabindex="0"></canvas>
</div>

<style>
    #game-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: white;
    }}
    .controls {{
        width: {WIDTH}px;
        max-width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}
    #start-btn {{
        padding: 10px 20px;
        background-color: #ff4b4b;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
    }}
    #start-btn:hover {{ background-color: #ff3333; }}
    #game-status {{ color: #888; }}
    #gameCanvas {{
        background-color: #146464;
        border: 4px solid #262730;
        border-radius: 10px;
        outline: none;
        max-width: 100%;
        height: auto;
    }}
    #gameCanvas:focus {{ border-color: #ff4b4b; }}
</style>

<script>
(() => {{
    const assets = {config_json};
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const startBtn = document.getElementById('start-btn');
    const statusTxt = document.getElementById('game-status');

    // Constantes de Estilo
    const COLORS = {{
        bg: '#146464',
        dark: '#141428',
        gray: '#3c3c50',
        white: '#ffffff',
        hitLine: '#c8c8ff',
        perfect: '#ffdc32',
        good: '#50dc78',
        miss: '#dc3c3c',
        combo: '#ffb400',
        lanes: ['#ffffff', '#ffa032', '#3cffff', '#f0a0f0']
    }};

    const GAME_CFG = {{
        laneCount: 4,
        laneWidth: 60,
        gap: 12,
        startX: 30,
        hitY: {HEIGHT} - 100,
        noteH: 24,
        charX: 630,
        charY: {HEIGHT} - 80,
        spriteH: 350
    }};

    const KEY_MAP = {{
        'ArrowLeft': 0, 'ArrowDown': 1, 'ArrowUp': 2, 'ArrowRight': 3,
        'a': 0, 'A': 0, 's': 1, 'S': 1, 'j': 2, 'J': 2, 'k': 3, 'K': 3
    }};

    // Função para remover fundo verde (Chroma Key)
    function removeGreenBackground(img) {{
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = img.width;
        tempCanvas.height = img.height;
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.drawImage(img, 0, 0);
        
        const imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
        const data = imageData.data;
        const sensitivity = assets.config.chromaSensitivity;

        for (let i = 0; i < data.length; i += 4) {{
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Lógica de Chroma Key: se o verde for dominante e acima da sensibilidade
            if (g > sensitivity && g > r && g > b) {{
                data[i + 3] = 0; // Torna o pixel transparente
            }}
        }}
        tempCtx.putImageData(imageData, 0, 0);
        const newImg = new Image();
        newImg.src = tempCanvas.toDataURL();
        return newImg;
    }}

    // Gerenciador de Assets
    const sprites = {{}};
    const spritePromises = Object.entries(assets.sprites).map(([name, src]) => {{
        if (!src) return Promise.resolve();
        return new Promise(resolve => {{
            const img = new Image();
            img.onload = () => {{ 
                sprites[name] = removeGreenBackground(img);
                resolve(); 
            }};
            img.src = src;
        }});
    }});

    let audio = null;
    if (assets.audio) {{
        audio = new Audio(assets.audio);
    }}

    // Lógica de Jogo
    class RhythmGame {{
        constructor() {{
            this.reset();
        }}

        reset() {{
            this.running = false;
            this.score = 0;
            this.combo = 0;
            this.maxCombo = 0;
            this.health = 100;
            this.feedback = "";
            this.fbTimer = 0;
            this.pose = "idle";
            this.poseTimer = 0;
            this.keyFlash = [0, 0, 0, 0];
            this.startTime = 0;
            this.gameOver = false;
            this.finished = false;
            
            this.rng = assets.config.seed;
            this.chart = this.generateChart();
            
            if (audio) {{
                audio.pause();
                audio.currentTime = 0;
            }}
        }}

        random() {{
            this.rng = (this.rng * 1664525 + 1013904223) >>> 0;
            return this.rng / 4294967296;
        }}

        generateChart() {{
            const notes = [];
            const duration = audio?.duration || 90;
            const beatInterval = 60 / assets.config.bpm;
            let t = 3.0;
            
            while (t < duration - 1.0) {{
                const lane = Math.floor(this.random() * 4);
                notes.push({{ lane, time: t, hit: false, miss: false }});
                
                if (this.random() < 0.2) {{
                    const other = (lane + 1 + Math.floor(this.random() * 3)) % 4;
                    notes.push({{ lane: other, time: t, hit: false, miss: false }});
                }}
                
                const steps = [0.5, 1.0, 1.0, 1.0, 2.0];
                t += beatInterval * steps[Math.floor(this.random() * steps.length)] * assets.config.noteFreq;
            }}
            return notes.sort((a, b) => a.time - b.time);
        }}

        start() {{
            this.reset();
            this.running = true;
            this.startTime = performance.now();
            statusTxt.textContent = "JOGANDO! Use as setas ou A S J K.";
            if (audio) audio.play().catch(e => console.error("Erro ao tocar áudio:", e));
        }}

        update(now) {{
            if (!this.running || this.gameOver || this.finished) return;
            
            const ct = (now - this.startTime) / 1000;
            const dt = 1/60;

            for (const n of this.chart) {{
                if (!n.hit && !n.miss && n.time < ct - 0.25) {{
                    n.miss = true;
                    this.triggerMiss();
                }}
            }}

            if (this.fbTimer > 0) this.fbTimer -= dt;
            if (this.poseTimer > 0) this.poseTimer -= dt; else this.pose = "idle";
            for (let i=0; i<4; i++) if (this.keyFlash[i] > 0) this.keyFlash[i] -= dt;

            if (this.health <= 0) {{
                this.gameOver = true;
                this.running = false;
                if (audio) audio.pause();
                statusTxt.textContent = "GAME OVER! Clique em Reiniciar.";
            }}

            const totalTime = (audio?.duration || 90) + 1;
            if (ct > totalTime || this.chart.every(n => n.hit || n.miss)) {{
                this.finished = true;
                this.running = false;
                statusTxt.textContent = "CONCLUÍDO! Score: " + this.score;
            }}
        }}

        triggerMiss() {{
            this.combo = 0;
            this.feedback = "MISS";
            this.fbTimer = 0.4;
            this.health = Math.max(0, this.health - 8);
        }}

        handleInput(key) {{
            if (!this.running || this.gameOver || this.finished) return;
            const lane = KEY_MAP[key];
            if (lane === undefined) return;

            const ct = (performance.now() - this.startTime) / 1000;
            let best = null;
            let minDiff = 999;

            for (const n of this.chart) {{
                if (n.hit || n.miss || n.lane !== lane) continue;
                const diff = Math.abs(n.time - ct);
                if (diff < minDiff) {{
                    minDiff = diff;
                    best = n;
                }}
            }}

            if (!best || minDiff > 0.25) return;

            this.keyFlash[lane] = 0.15;
            const poses = ["left", "down", "up", "right"];
            this.pose = poses[lane];
            this.poseTimer = 0.25;

            if (minDiff < 0.06) {{
                best.hit = true;
                this.score += 300 + this.combo * 10;
                this.combo++;
                this.feedback = "PERFECT";
                this.fbTimer = 0.6;
                this.health = Math.min(100, this.health + 5);
            }} else if (minDiff < 0.15) {{
                best.hit = true;
                this.score += 100;
                this.combo++;
                this.feedback = "GOOD";
                this.fbTimer = 0.5;
                this.health = Math.min(100, this.health + 2);
            }} else {{
                best.miss = true;
                this.triggerMiss();
            }}
            this.maxCombo = Math.max(this.maxCombo, this.combo);
        }}

        draw() {{
            ctx.fillStyle = COLORS.bg;
            ctx.fillRect(0, 0, {WIDTH}, {HEIGHT});
            
            const ct = this.running ? (performance.now() - this.startTime) / 1000 : 0;

            ctx.strokeStyle = COLORS.gray;
            ctx.beginPath(); ctx.moveTo(370, 0); ctx.lineTo(370, {HEIGHT}); ctx.stroke();

            for (let i=0; i<4; i++) {{
                const x = GAME_CFG.startX + i * (GAME_CFG.laneWidth + GAME_CFG.gap);
                ctx.fillStyle = COLORS.dark;
                ctx.fillRect(x, 0, GAME_CFG.laneWidth, {HEIGHT});
                ctx.strokeStyle = COLORS.lanes[i];
                ctx.strokeRect(x, 0, GAME_CFG.laneWidth, {HEIGHT});
            }}

            ctx.strokeStyle = COLORS.hitLine;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(GAME_CFG.startX - 5, GAME_CFG.hitY);
            ctx.lineTo(GAME_CFG.startX + 4 * (GAME_CFG.laneWidth + GAME_CFG.gap), GAME_CFG.hitY);
            ctx.stroke();
            ctx.lineWidth = 1;

            for (const n of this.chart) {{
                if (n.hit || n.miss) continue;
                const tDiff = n.time - ct;
                if (tDiff > 2 || tDiff < -0.5) continue;
                const y = GAME_CFG.hitY - tDiff * assets.config.noteSpeed - GAME_CFG.noteH / 2;
                const x = GAME_CFG.startX + n.lane * (GAME_CFG.laneWidth + GAME_CFG.gap);
                ctx.fillStyle = COLORS.lanes[n.lane];
                this.roundRect(x + 4, y, GAME_CFG.laneWidth - 8, GAME_CFG.noteH, 5, true);
                ctx.strokeStyle = COLORS.white;
                this.roundRect(x + 4, y, GAME_CFG.laneWidth - 8, GAME_CFG.noteH, 5, false);
            }}

            const labels = ["◄", "▼", "▲", "►"];
            for (let i=0; i<4; i++) {{
                const x = GAME_CFG.startX + i * (GAME_CFG.laneWidth + GAME_CFG.gap);
                const flash = this.keyFlash[i];
                ctx.fillStyle = flash > 0 ? COLORS.lanes[i] : COLORS.gray;
                this.roundRect(x + 4, GAME_CFG.hitY - 18, GAME_CFG.laneWidth - 8, 36, 8, true);
                ctx.fillStyle = COLORS.lanes[i];
                ctx.font = "bold 20px monospace";
                ctx.textAlign = "center";
                ctx.fillText(labels[i], x + GAME_CFG.laneWidth/2, GAME_CFG.hitY + 7);
            }}

            const img = sprites[this.pose] || sprites.idle;
            if (img) {{
                const ratio = GAME_CFG.spriteH / img.height;
                const w = img.width * ratio;
                ctx.drawImage(img, GAME_CFG.charX - w/2, GAME_CFG.charY - GAME_CFG.spriteH, w, GAME_CFG.spriteH);
            }} else {{
                ctx.strokeStyle = "white"; ctx.lineWidth = 5;
                ctx.beginPath();
                ctx.arc(GAME_CFG.charX, GAME_CFG.charY - 150, 30, 0, Math.PI*2);
                ctx.moveTo(GAME_CFG.charX, GAME_CFG.charY - 120); ctx.lineTo(GAME_CFG.charX, GAME_CFG.charY - 40);
                ctx.stroke();
            }}

            ctx.textAlign = "left";
            ctx.fillStyle = "white";
            ctx.font = "bold 24px monospace";
            ctx.fillText("SCORE: " + String(this.score).padStart(8, '0'), 400, 50);
            
            if (this.combo >= 3) {{
                ctx.fillStyle = COLORS.combo;
                ctx.fillText(this.combo + "x COMBO", 400, 85);
            }}

            if (this.fbTimer > 0) {{
                ctx.globalAlpha = Math.min(1, this.fbTimer / 0.2);
                ctx.fillStyle = this.feedback === "PERFECT" ? COLORS.perfect : (this.feedback === "GOOD" ? COLORS.good : COLORS.miss);
                ctx.font = "bold 40px monospace";
                ctx.fillText(this.feedback, GAME_CFG.startX, GAME_CFG.hitY - 60);
                ctx.globalAlpha = 1;
            }}

            const hpW = 300;
            ctx.fillStyle = COLORS.gray;
            this.roundRect(400, {HEIGHT} - 50, hpW, 20, 10, true);
            ctx.fillStyle = this.health > 50 ? COLORS.good : (this.health > 25 ? COLORS.perfect : COLORS.miss);
            this.roundRect(400, {HEIGHT} - 50, hpW * (this.health/100), 20, 10, true);
            ctx.strokeStyle = "white";
            this.roundRect(400, {HEIGHT} - 50, hpW, 20, 10, false);
            ctx.fillStyle = "white"; ctx.font = "16px monospace";
            ctx.fillText("HP", 400 + hpW + 10, {HEIGHT} - 35);

            if (this.gameOver) this.drawOverlay("GAME OVER", COLORS.miss);
            if (this.finished) this.drawOverlay("CLEAR!", COLORS.perfect);
            if (!this.running && !this.gameOver && !this.finished) {{
                this.drawOverlay("PRONTO?", COLORS.white, "Clique em JOGAR para começar");
            }}
        }}

        drawOverlay(txt, color, sub = "") {{
            ctx.fillStyle = "rgba(0,0,0,0.7)";
            ctx.fillRect(0, 0, {WIDTH}, {HEIGHT});
            ctx.textAlign = "center";
            ctx.fillStyle = color;
            ctx.font = "bold 60px monospace";
            ctx.fillText(txt, {WIDTH}/2, {HEIGHT}/2);
            if (sub) {{
                ctx.fillStyle = "white";
                ctx.font = "20px monospace";
                ctx.fillText(sub, {WIDTH}/2, {HEIGHT}/2 + 50);
            }}
        }}

        roundRect(x, y, w, h, r, fill) {{
            ctx.beginPath();
            ctx.moveTo(x+r, y);
            ctx.arcTo(x+w, y, x+w, y+h, r);
            ctx.arcTo(x+w, y+h, x, y+h, r);
            ctx.arcTo(x, y+h, x, y, r);
            ctx.arcTo(x, y, x+w, y, r);
            ctx.closePath();
            if (fill) ctx.fill(); else ctx.stroke();
        }}
    }}

    const game = new RhythmGame();

    function gameLoop(now) {{
        game.update(now);
        game.draw();
        requestAnimationFrame(gameLoop);
    }}

    startBtn.onclick = () => {{
        canvas.focus();
        game.start();
    }};

    canvas.onkeydown = (e) => {{
        if (e.key === 'Enter' && !game.running) game.start();
        if (KEY_MAP[e.key] !== undefined) {{
            e.preventDefault();
            game.handleInput(e.key);
        }}
    }};

    Promise.all(spritePromises).then(() => {{
        requestAnimationFrame(gameLoop);
        statusTxt.textContent = "Arquivos carregados. Clique em JOGAR.";
    }});
}})();
</script>
"""

# Renderizar o componente
components.html(html_code, height=800, scrolling=False)

st.divider()
st.markdown("""
### ⌨️ Controles
- **Setas** ou **A S J K** para as notas.
- **ENTER** ou botão para iniciar/reiniciar.
- Clique no quadro do jogo para ativar o teclado.
""")
