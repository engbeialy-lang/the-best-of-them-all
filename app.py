
import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import matplotlib.pyplot as plt
import io, re, json, html, ast, operator
from datetime import date
from deep_translator import GoogleTranslator
from groq import Groq

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None


st.set_page_config(
    page_title="CODEleader Universe",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

PROJECTS = [
    {"name":"Weather App","icon":"🌦️","category":"Daily Tools","desc":"Weather forecasts and climate information."},
    {"name":"Snake Ultimate","icon":"🐍","category":"Games","desc":"Classic Snake game with advanced features."},
    {"name":"Translator App","icon":"🌍","category":"AI & Language","desc":"Translate text between multiple languages."},
    {"name":"Summarizer App","icon":"📄","category":"AI Tools","desc":"Summarize documents and long texts."},
    {"name":"Audio & Video Transcription","icon":"🎙️","category":"AI & Media","desc":"Extract text from audio and video."},
    {"name":"Study AI","icon":"📝","category":"Education","desc":"Create quizzes and study materials."},
    {"name":"My Chatbot","icon":"🤖","category":"AI Tools","desc":"Your personal AI chatbot."},
    {"name":"AI Student Assistant","icon":"🎒","category":"Education","desc":"A collection of smart student tools."},
    {"name":"AI English Teacher","icon":"🇬🇧","category":"Education","desc":"Practice English with an AI teacher."},
    {"name":"Smart School AI","icon":"🎓","category":"Education","desc":"Your smart school study assistant."},
    {"name":"Python Code Playground","icon":"🐍","category":"Education","desc":"Write Python and try safe learning examples."},
    {"name":"Math Solver","icon":"🔢","category":"Education","desc":"Understand math problems step by step."},
    {"name":"Smart Planner","icon":"📅","category":"Daily Tools","desc":"Organize tasks, dates and priorities."},
]

CATEGORIES = [
    "All Projects", "AI Tools", "Education",
    "AI & Language", "AI & Media", "Daily Tools", "Games"
]

DEFAULTS = {
    "selected_project": None,
    "category": "All Projects",
    "weather_data": None,
    "weather_city": "Cairo",
    "chat_history": [],
    "english_history": [],
    "school_history": [],
    "quiz_questions": [],
    "quiz_answers": {},
    "summary_result": "",
    "translation_result": "",
    "transcription_result": "",
    "planner_tasks": [],
    "python_code": "print('Hello, CODEleader!')\nname = 'Student'\nprint('Welcome', name)",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# GROQ

def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY", None)
    return Groq(api_key=api_key) if api_key else None


def ask_groq(
    prompt,
    system="You are a helpful educational assistant.",
    model="openai/gpt-oss-120b",
    max_tokens=1200
):
    client = get_groq_client()

    if client is None:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to Streamlit secrets."
        )

    result = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.3
    )

    return result.choices[0].message.content


# DESIGN

st.markdown('''<style>
.stApp {
    background:
        radial-gradient(ellipse at 10% 0%,#25205b 0%,transparent 35%),
        radial-gradient(ellipse at 90% 15%,#102d54 0%,transparent 35%),
        #090d19;
    color: #f5f6ff;
}

.block-container {
    padding-top: 2rem;
    max-width: 1450px;
}

[data-testid="stSidebar"] {
    background: #101629;
    border-right: 1px solid #28324d;
}

.project-card {
    background: linear-gradient(145deg,#171f35,#11182a);
    border: 1px solid #303c5d;
    border-radius: 18px;
    padding: 22px;
    min-height: 190px;
    margin-bottom: 10px;
}

.project-card:hover {
    border-color: #8b7cff;
    transform: translateY(-3px);
}

.project-icon {
    font-size: 35px;
    margin-bottom: 12px;
}

.project-title {
    font-size: 19px;
    font-weight: 750;
    color: white;
}

.project-desc {
    color: #aab5d0;
    font-size: 13px;
    margin-top: 8px;
    min-height: 38px;
}

.category-label {
    color: #a99cff;
    font-size: 12px;
    margin-top: 12px;
}

div.stButton > button {
    border-radius: 10px;
    border: 1px solid #55558f;
    background: #252650;
    color: white;
    font-weight: 600;
}

div.stButton > button:hover {
    border-color: #a99cff;
    background: #37336e;
    color: white;
}

/* TEXT INPUTS AND PYTHON EDITOR */

.stTextArea textarea,
.stTextInput input,
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: #202434 !important;
    -webkit-text-fill-color: #202434 !important;
    caret-color: #202434 !important;
    border: 1px solid #aeb8cc !important;
    border-radius: 8px !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: #687386 !important;
    -webkit-text-fill-color: #687386 !important;
    opacity: 1 !important;
}

/* DROPDOWNS AND DATE FIELDS */

[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {
    background: #ffffff !important;
    color: #202434 !important;
    -webkit-text-fill-color: #202434 !important;
}

[data-baseweb="select"] input,
[data-baseweb="select"] span {
    color: #202434 !important;
    -webkit-text-fill-color: #202434 !important;
}

[data-baseweb="popover"] [role="option"] {
    color: #202434 !important;
    background: #ffffff !important;
}

/* CODE OUTPUT */

[data-testid="stCodeBlock"] pre,
[data-testid="stCodeBlock"] code {
    background: #f3f5f9 !important;
    color: #202434 !important;
    -webkit-text-fill-color: #202434 !important;
}

</style>''', unsafe_allow_html=True)


def render_project_card(project):
    card = f'''<div class="project-card">
    <div class="project-icon">{html.escape(project["icon"])}</div>
    <div class="project-title">{html.escape(project["name"])}</div>
    <div class="project-desc">{html.escape(project["desc"])}</div>
    <div class="category-label">{html.escape(project["category"])}</div>
    </div>'''

    st.markdown(card, unsafe_allow_html=True)


# 1 WEATHER

def get_weather(city):
    """Fetch weather from Open-Meteo."""

    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        },
        timeout=20
    )

    geo_response.raise_for_status()
    geo_data = geo_response.json()

    if not geo_data.get("results"):
        raise ValueError(f"City not found: {city}")

    place = geo_data["results"][0]

    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,visibility",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,temperature_2m_mean",
            "forecast_days": 3,
            "timezone": "auto"
        },
        timeout=20
    )

    weather_response.raise_for_status()

    data = weather_response.json()
    current = data["current"]
    daily = data["daily"]

    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Heavy thunderstorm"
    }

    current_condition = [{
        "temp_C": str(round(current["temperature_2m"])),
        "FeelsLikeC": str(round(current["apparent_temperature"])),
        "humidity": str(current["relative_humidity_2m"]),
        "windspeedKmph": str(round(current["wind_speed_10m"])),
        "visibility": str(round(current.get("visibility", 0) / 1000)),
        "weatherDesc": [{
            "value": descriptions.get(
                current["weather_code"],
                "Weather information"
            )
        }]
    }]

    forecast = []

    for i, forecast_date in enumerate(daily["time"]):
        forecast.append({
            "date": forecast_date,
            "maxtempC": str(round(daily["temperature_2m_max"][i])),
            "mintempC": str(round(daily["temperature_2m_min"][i])),
            "avgtempC": str(round(daily["temperature_2m_mean"][i]))
        })

    return {
        "current_condition": current_condition,
        "nearest_area": [{
            "areaName": [{"value": place["name"]}],
            "country": [{"value": place.get("country", "")}]
        }],
        "weather": forecast
    }


def render_weather():
    st.markdown("## 🌦️ Weather Dashboard")

    city = st.text_input(
        "Enter City",
        value=st.session_state.weather_city,
        key="weather_city_entry"
    )

    if st.button("Search Weather") and city.strip():
        try:
            with st.spinner("Loading weather..."):
                st.session_state.weather_data = get_weather(city.strip())
                st.session_state.weather_city = city.strip()

        except Exception as e:
            st.error(f"Weather Error: {e}")

    st.markdown("### ⭐ Favorite Cities")

    cols = st.columns(5)

    for i, fav in enumerate(["Cairo", "Alexandria", "London", "Paris", "Tokyo"]):
        with cols[i]:
            if st.button(fav, key=f"weather_fav_{fav}"):
                try:
                    st.session_state.weather_data = get_weather(fav)
                    st.session_state.weather_city = fav

                except Exception as e:
                    st.error(f"Weather Error: {e}")

    data = st.session_state.weather_data

    if not data:
        st.info("Search for a city to view its weather.")
        return

    try:
        current = data["current_condition"][0]
        location = data["nearest_area"][0]

        st.markdown(
            f"### 📍 {location['areaName'][0]['value']}, "
            f"{location['country'][0]['value']}"
        )

        st.title(f"{current['temp_C']}°C")
        st.caption(current["weatherDesc"][0]["value"])

        cols = st.columns(4)

        for col, label, value in zip(
            cols,
            ["Feels Like", "Humidity", "Wind", "Visibility"],
            [
                f"{current['FeelsLikeC']}°C",
                f"{current['humidity']}%",
                f"{current['windspeedKmph']} km/h",
                f"{current['visibility']} km"
            ]
        ):
            col.metric(label, value)

        forecast = data["weather"][:3]

        df = pd.DataFrame([
            {
                "Date": d["date"],
                "Maximum °C": d["maxtempC"],
                "Minimum °C": d["mintempC"],
                "Average °C": d["avgtempC"]
            }
            for d in forecast
        ])

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        fig, ax = plt.subplots(figsize=(10, 4))

        dates = [d["date"] for d in forecast]

        ax.plot(
            dates,
            [int(d["maxtempC"]) for d in forecast],
            marker="o",
            label="Maximum"
        )

        ax.plot(
            dates,
            [int(d["mintempC"]) for d in forecast],
            marker="o",
            label="Minimum"
        )

        ax.set_ylabel("Temperature °C")
        ax.legend()
        ax.grid(alpha=.2)

        st.pyplot(fig)
        plt.close(fig)

    except (KeyError, IndexError, TypeError, ValueError) as e:
        st.error(f"Weather display error: {e}")


# 2 SNAKE

def render_snake():
    st.markdown("## 🐍 Snake Ultimate")
    st.caption("Play directly inside CODEleader Universe!")

    game_html = r'''<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}
body{margin:0;background:#090d19;color:white;font-family:Arial;text-align:center}
.game{max-width:520px;margin:auto;padding:15px}
canvas{width:100%;max-width:440px;background:#101629;border:2px solid #55558f;border-radius:12px;display:block;margin:15px auto}
.score{font-size:23px;color:#a99cff;font-weight:bold;margin:12px}
button{background:#252650;color:white;border:1px solid #7772c9;padding:12px 20px;border-radius:10px;margin:5px;font-size:17px;cursor:pointer;touch-action:manipulation}
.controls{display:grid;grid-template-columns:repeat(3,65px);justify-content:center;gap:5px;margin-top:10px}
#message{color:#ffcc66;min-height:25px;font-weight:bold}
</style>
</head>
<body>
<div class="game">
<div class="score">
Score: <span id="score">0</span> |
Speed: <span id="speed">1</span> |
Best: <span id="best">0</span>
</div>
<canvas id="board" width="440" height="440"></canvas>
<div id="message">Press Start to play!</div>
<button onclick="startGame()">▶ Start / Restart</button>
<button onclick="pauseGame()">⏸ Pause</button>
<div class="controls">
<div></div>
<button onclick="changeDirection('UP')">⬆️</button>
<div></div>
<button onclick="changeDirection('LEFT')">⬅️</button>
<button onclick="changeDirection('DOWN')">⬇️</button>
<button onclick="changeDirection('RIGHT')">➡️</button>
</div>
<p>Use Arrow Keys or WASD to move.</p>
</div>

<script>
const canvas=document.getElementById('board');
const ctx=canvas.getContext('2d');
const size=22;
const cells=20;

let snake=[];
let food={};
let direction='RIGHT';
let nextDirection='RIGHT';
let score=0;
let speed=1;
let timer=null;
let running=false;
let gameOver=false;
let best=0;

try {
    best=Number(localStorage.getItem('snakeBest')||0);
} catch(e) {}

document.getElementById('best').textContent=best;

function randomFood(){
    let p;
    do {
        p={
            x:Math.floor(Math.random()*cells),
            y:Math.floor(Math.random()*cells)
        };
    } while(snake.some(s=>s.x===p.x&&s.y===p.y));
    return p;
}

function startGame(){
    clearInterval(timer);
    snake=[
        {x:10,y:10},
        {x:9,y:10},
        {x:8,y:10}
    ];
    direction='RIGHT';
    nextDirection='RIGHT';
    score=0;
    speed=1;
    running=true;
    gameOver=false;
    food=randomFood();
    updateInfo();
    document.getElementById('message').textContent='';
    draw();
    runTimer();
}

function runTimer(){
    clearInterval(timer);
    timer=setInterval(()=>{
        if(running&&!gameOver){
            update();
            draw();
        }
    },Math.max(65,160-(speed-1)*10));
}

function changeDirection(d){
    const opposite={
        UP:'DOWN',
        DOWN:'UP',
        LEFT:'RIGHT',
        RIGHT:'LEFT'
    };
    if(d!==opposite[direction]){
        nextDirection=d;
    }
}

document.addEventListener('keydown',e=>{
    const k=e.key.toLowerCase();
    const keys={
        arrowup:'UP',
        arrowdown:'DOWN',
        arrowleft:'LEFT',
        arrowright:'RIGHT',
        w:'UP',
        s:'DOWN',
        a:'LEFT',
        d:'RIGHT'
    };
    if(keys[k]){
        e.preventDefault();
        changeDirection(keys[k]);
    }
});

function update(){
    direction=nextDirection;
    const head={...snake[0]};

    if(direction==='UP')head.y--;
    if(direction==='DOWN')head.y++;
    if(direction==='LEFT')head.x--;
    if(direction==='RIGHT')head.x++;

    const eating=head.x===food.x&&head.y===food.y;
    const body=eating?snake:snake.slice(0,-1);

    if(
        head.x<0||
        head.y<0||
        head.x>=cells||
        head.y>=cells||
        body.some(p=>p.x===head.x&&p.y===head.y)
    ){
        endGame();
        return;
    }

    snake.unshift(head);

    if(eating){
        score+=10;

        if(score>best){
            best=score;
            try{
                localStorage.setItem('snakeBest',String(best));
            }catch(e){}
        }

        const old=speed;
        speed=Math.min(10,1+Math.floor(score/50));
        food=randomFood();
        updateInfo();

        if(speed!==old)runTimer();
    }else{
        snake.pop();
    }
}

function updateInfo(){
    document.getElementById('score').textContent=score;
    document.getElementById('speed').textContent=speed;
    document.getElementById('best').textContent=best;
}

function endGame(){
    gameOver=true;
    running=false;
    clearInterval(timer);
    document.getElementById('message').textContent=
        'Game Over! Final Score: '+score;
    updateInfo();
}

function pauseGame(){
    if(gameOver||snake.length===0)return;
    running=!running;
    document.getElementById('message').textContent=
        running?'':'Game Paused';
}

function draw(){
    ctx.fillStyle='#101629';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.strokeStyle='#202b42';

    for(let i=0;i<=cells;i++){
        ctx.beginPath();
        ctx.moveTo(i*size,0);
        ctx.lineTo(i*size,canvas.height);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(0,i*size);
        ctx.lineTo(canvas.width,i*size);
        ctx.stroke();
    }

    if(!snake.length)return;

    ctx.fillStyle='#ff5757';
    ctx.beginPath();
    ctx.arc(
        food.x*size+size/2,
        food.y*size+size/2,
        size/2-3,
        0,
        Math.PI*2
    );
    ctx.fill();

    snake.forEach((p,i)=>{
        ctx.fillStyle=i===0?'#a99cff':'#45d483';
        ctx.fillRect(
            p.x*size+2,
            p.y*size+2,
            size-4,
            size-4
        );
    });
}

draw();
</script>
</body>
</html>'''

    components.html(
        game_html,
        height=720,
        scrolling=False
    )


# 3 TRANSLATOR

LANGUAGES = {
    "Auto Detect": "auto",
    "English": "en",
    "Arabic": "ar",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Italian": "it",
    "Turkish": "tr",
    "Chinese": "zh-CN",
    "Japanese": "ja",
    "Russian": "ru",
    "Portuguese": "pt",
    "Hindi": "hi",
    "Korean": "ko",
    "Dutch": "nl",
    "Urdu": "ur"
}


def render_translator():
    st.markdown("## 🌍 Translator App")

    c1, c2 = st.columns(2)

    with c1:
        source = st.selectbox("From", list(LANGUAGES.keys()))

    with c2:
        target = st.selectbox(
            "To",
            [x for x in LANGUAGES if x != "Auto Detect"],
            index=1
        )

    text = st.text_area("Enter text", height=180)

    if st.button("Translate"):
        if not text.strip():
            st.warning("Enter text first.")
        else:
            try:
                st.session_state.translation_result = GoogleTranslator(
                    source=LANGUAGES[source],
                    target=LANGUAGES[target]
                ).translate(text)
            except Exception as e:
                st.error(f"Translation failed: {e}")

    if st.session_state.translation_result:
        st.text_area(
            "Translated text",
            value=st.session_state.translation_result,
            height=180
        )

        st.download_button(
            "Download Translation",
            st.session_state.translation_result,
            file_name="translation.txt"
        )


# 4 SUMMARIZER

def render_summarizer():
    st.markdown("## 📄 Summarizer App")

    uploaded = st.file_uploader(
        "Upload TXT or PDF",
        type=["txt", "pdf"]
    )

    extracted = ""

    if uploaded:
        try:
            if uploaded.name.lower().endswith(".txt"):
                extracted = uploaded.getvalue().decode(
                    "utf-8",
                    errors="ignore"
                )
            elif PdfReader is None:
                st.error("Install pypdf to read PDF files.")
            else:
                extracted = "\n".join(
                    p.extract_text() or ""
                    for p in PdfReader(uploaded).pages
                )
        except Exception as e:
            st.error(f"File reading error: {e}")

    text = st.text_area(
        "Text to summarize",
        value=extracted,
        height=250
    )

    length = st.selectbox(
        "Summary length",
        ["Short", "Medium", "Detailed"]
    )

    if st.button("Summarize"):
        if not text.strip():
            st.warning("Enter or upload text first.")
        else:
            try:
                with st.spinner("Creating summary..."):
                    st.session_state.summary_result = ask_groq(
                        f"Create a {length.lower()} summary of this text:\n\n{text}"
                    )
            except Exception as e:
                st.error(str(e))

    if st.session_state.summary_result:
        st.markdown("### Summary")
        st.write(st.session_state.summary_result)

        st.download_button(
            "Download Summary",
            st.session_state.summary_result,
            file_name="summary.txt"
        )


# 5 TRANSCRIPTION

def render_transcription():
    st.markdown("## 🎙️ Audio & Video Transcription")
    st.write("Upload an audio file to convert speech into text.")

    uploaded = st.file_uploader(
        "Upload audio",
        type=["mp3", "wav", "m4a", "ogg", "webm", "mp4"]
    )

    if st.button("Transcribe"):
        if not uploaded:
            st.warning("Upload a file first.")
            return

        client = get_groq_client()

        if client is None:
            st.error("GROQ_API_KEY is missing.")
            return

        try:
            with st.spinner("Transcribing..."):
                result = client.audio.transcriptions.create(
                    file=(
                        uploaded.name,
                        uploaded.getvalue(),
                        uploaded.type or "application/octet-stream"
                    ),
                    model="whisper-large-v3",
                    response_format="text"
                )

                st.session_state.transcription_result = (
                    result.text if hasattr(result, "text") else str(result)
                )

        except Exception as e:
            st.error(f"Transcription failed: {e}")

    if st.session_state.transcription_result:
        st.text_area(
            "Transcription",
            value=st.session_state.transcription_result,
            height=250
        )

        st.download_button(
            "Download TXT",
            st.session_state.transcription_result,
            file_name="transcription.txt"
        )


# 6 STUDY AI

def render_study_ai():
    st.markdown("## 📝 Study AI")
    st.write("Generate practice questions and check your understanding.")

    subject = st.selectbox(
        "Subject",
        ["English", "Science", "Math", "History", "Computer Science"]
    )

    topic = st.text_input("Topic")
    count = st.slider("Number of questions", 3, 10, 5)

    if st.button("Generate Quiz"):
        if not topic.strip():
            st.warning("Enter a topic.")
        else:
            try:
                prompt = f'''Create exactly {count} multiple-choice questions about {topic} in {subject}.
Return valid JSON only:
[{{"question":"Question","options":["A","B","C","D"],"answer":"A","explanation":"Explanation"}}]'''

                with st.spinner("Preparing your quiz..."):
                    raw = ask_groq(
                        prompt,
                        system="You are an educational quiz generator. Return valid JSON only."
                    )

                match = re.search(r"\[.*\]", raw, re.S)

                if not match:
                    raise ValueError(
                        "The AI did not return valid quiz data."
                    )

                questions = json.loads(match.group())

                if not isinstance(questions, list) or not questions:
                    raise ValueError("No questions were generated.")

                st.session_state.quiz_questions = questions
                st.session_state.quiz_answers = {}

            except Exception as e:
                st.error(f"Quiz generation failed: {e}")

    questions = st.session_state.quiz_questions

    if questions:
        st.divider()
        st.markdown("### Your Quiz")

        for i, q in enumerate(questions):
            st.markdown(f"**{i+1}. {q['question']}**")

            st.session_state.quiz_answers[i] = st.radio(
                "Choose an answer",
                q["options"],
                key=f"quiz_answer_{i}",
                index=None
            )

        if st.button("Check Answers"):
            score = 0

            for i, q in enumerate(questions):
                if st.session_state.quiz_answers.get(i) == q["answer"]:
                    score += 1
                    st.success(f"Question {i+1}: Correct!")
                else:
                    st.error(
                        f"Question {i+1}: Correct answer: {q['answer']}"
                    )

                st.caption(q.get("explanation", ""))

            st.metric(
                "Your Score",
                f"{score} / {len(questions)}"
            )


# 7 CHATBOT

def render_chatbot():
    st.markdown("## 🤖 My Chatbot")
    st.write("Ask questions and have a conversation with AI.")

    if st.button("New Conversation"):
        st.session_state.chat_history = []
        st.rerun()

    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    prompt = st.chat_input("Write your message...")

    if prompt:
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.write(prompt)

        try:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = ask_groq(
                        prompt,
                        system="You are a helpful and friendly AI assistant."
                    )
                    st.write(answer)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:
            st.error(str(e))


# 8 STUDENT ASSISTANT

def render_student_assistant():
    st.markdown("## 🎒 AI Student Assistant")

    tool = st.selectbox(
        "Choose a tool",
        ["Ask AI", "Image Filters", "Image OCR"]
    )

    if tool == "Ask AI":
        question = st.text_area("What do you need help with?")

        if st.button("Ask Student Assistant") and question.strip():
            try:
                st.markdown("### Answer")
                st.write(
                    ask_groq(
                        question,
                        system="You are a helpful school student assistant. Explain clearly and encourage learning."
                    )
                )
            except Exception as e:
                st.error(str(e))

    elif tool == "Image Filters":
        if Image is None:
            st.error("Install Pillow to use image filters.")
            return

        uploaded = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg"]
        )

        name = st.selectbox(
            "Filter",
            ["Original", "Vintage", "B&W", "Sharpen", "Warm", "Cinema"]
        )

        if uploaded:
            image = Image.open(uploaded).convert("RGB")

            if name == "Vintage":
                image = ImageEnhance.Color(image).enhance(.6)
                image = ImageEnhance.Contrast(image).enhance(1.2)

            elif name == "B&W":
                image = image.convert("L").convert("RGB")

            elif name == "Sharpen":
                image = image.filter(ImageFilter.SHARPEN)

            elif name == "Warm":
                r, g, b = image.split()
                image = Image.merge(
                    "RGB",
                    (
                        ImageEnhance.Brightness(r).enhance(1.12),
                        g,
                        ImageEnhance.Brightness(b).enhance(.85)
                    )
                )

            elif name == "Cinema":
                image = ImageEnhance.Contrast(image).enhance(1.35)
                image = ImageEnhance.Color(image).enhance(.75)

            st.image(
                image,
                caption=name,
                use_container_width=True
            )

            buf = io.BytesIO()
            image.save(buf, format="PNG")

            st.download_button(
                "Download Image",
                buf.getvalue(),
                file_name="edited_image.png",
                mime="image/png"
            )

    else:
        if Image is None or pytesseract is None:
            st.error(
                "Install Pillow and pytesseract. Tesseract OCR must also be installed."
            )
            return

        uploaded = st.file_uploader(
            "Upload image",
            type=["png", "jpg", "jpeg"]
        )

        lang = st.selectbox(
            "OCR Language",
            ["eng", "ara", "eng+ara"]
        )

        if uploaded:
            image = Image.open(uploaded)
            st.image(image, use_container_width=True)

            if st.button("Extract Text"):
                try:
                    result = pytesseract.image_to_string(
                        image,
                        lang=lang
                    )

                    st.text_area(
                        "Extracted Text",
                        result,
                        height=250
                    )

                    st.download_button(
                        "Download Text",
                        result,
                        file_name="extracted_text.txt"
                    )

                except Exception as e:
                    st.error(f"OCR error: {e}")


# 9 ENGLISH TEACHER

def render_english_teacher():
    st.markdown("## 🇬🇧 AI English Teacher")

    mode = st.selectbox(
        "Learning Mode",
        [
            "Normal Conversation",
            "Correct My English",
            "Grammar Explanation",
            "Vocabulary"
        ]
    )

    if st.button("Clear Conversation"):
        st.session_state.english_history = []
        st.rerun()

    for m in st.session_state.english_history:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    prompt = st.chat_input("Speak or type in English or Arabic...")

    if prompt:
        st.session_state.english_history.append({
            "role": "user",
            "content": prompt
        })

        system = f'''You are an AI English teacher.
Learning mode: {mode}.
The student may use English or Arabic.
Understand both languages.
Reply in English unless Arabic explanation is requested.
Correct clear English mistakes politely.
Do not invent mistakes.
In grammar mode, answer grammar questions directly.
In vocabulary mode, explain meaning and provide examples.
Avoid generic questions about hobbies or free time.
Keep responses clear and suitable for school learners.'''

        try:
            with st.chat_message("assistant"):
                with st.spinner("Preparing your lesson..."):
                    answer = ask_groq(prompt, system=system)
                    st.write(answer)

            st.session_state.english_history.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:
            st.error(str(e))


# 10 SMART SCHOOL

def render_smart_school():
    st.markdown("## 🎓 Smart School AI")

    grade = st.selectbox(
        "Grade",
        ["Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9"]
    )

    subject = st.selectbox(
        "Subject",
        [
            "English",
            "Mathematics",
            "Science",
            "Social Studies",
            "Religious Studies"
        ]
    )

    language = st.selectbox(
        "Answer Language",
        ["English", "Arabic"]
    )

    if st.button("Clear School Chat"):
        st.session_state.school_history = []
        st.rerun()

    for m in st.session_state.school_history:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    question = st.chat_input("Ask your school question...")

    if question:
        st.session_state.school_history.append({
            "role": "user",
            "content": question
        })

        system = (
            f"You are Smart School AI. Student grade: {grade}. "
            f"Subject: {subject}. Reply language: {language}. "
            "Explain at the student's grade level. "
            "Show steps for mathematical problems. "
            "Encourage understanding rather than memorization."
        )

        try:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = ask_groq(question, system=system)
                    st.write(answer)

            st.session_state.school_history.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:
            st.error(str(e))


# 11 PYTHON CODE PLAYGROUND

def safe_python_run(source):
    # A deliberately small educational interpreter.
    # It never calls exec() or eval().

    allowed_bin = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow
    }

    allowed_unary = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg
    }

    env = {}
    output = []

    def expr(node):
        if isinstance(node, ast.Constant) and isinstance(
            node.value, (int, float, str, bool)
        ):
            return node.value

        if isinstance(node, ast.Name) and node.id in env:
            return env[node.id]

        if isinstance(node, ast.BinOp) and type(node.op) in allowed_bin:
            left, right = expr(node.left), expr(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError(
                    "Power is limited in this learning playground."
                )

            return allowed_bin[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_unary:
            return allowed_unary[type(node.op)](
                expr(node.operand)
            )

        if isinstance(node, (ast.List, ast.Tuple)):
            return [expr(x) for x in node.elts]

        raise ValueError(
            "This example uses a Python feature that is not supported in the safe playground."
        )

    tree = ast.parse(source)

    if len(tree.body) > 100:
        raise ValueError("Please keep examples under 100 lines.")

    for statement in tree.body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            env[statement.targets[0].id] = expr(statement.value)

        elif (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "print"
        ):
            if statement.value.keywords:
                raise ValueError(
                    "print keyword arguments are not supported."
                )

            output.append(
                " ".join(str(expr(a)) for a in statement.value.args)
            )

        elif isinstance(statement, ast.Expr):
            output.append(str(expr(statement.value)))

        else:
            raise ValueError(
                "Supported statements: variable assignments, expressions, and print()."
            )

    return (
        "\n".join(output)
        if output
        else "Program finished. No output was produced."
    )


def render_python_playground():
    st.markdown("## 🐍 Python Code Playground")
    st.write(
        "Write Python code and try a small set of safe learning examples."
    )

    examples = {
        "Hello World": "print('Hello, world!')",

        "Variables": (
            "name = 'CODEleader'\n"
            "age = 12\n"
            "print('Welcome', name)\n"
            "print('Age:', age)"
        ),

        "Math Operations": (
            "a = 12\n"
            "b = 5\n"
            "print(a + b)\n"
            "print(a * b)"
        ),

        "Simple Calculation": (
            "price = 25\n"
            "quantity = 4\n"
            "print('Total:', price * quantity)"
        )
    }

    choice = st.selectbox(
        "Load an example",
        ["Choose an example"] + list(examples.keys())
    )

    if choice != "Choose an example":
        st.session_state.python_code = examples[choice]

    st.session_state.python_code = st.text_area(
        "Python Editor",
        value=st.session_state.python_code,
        height=260,
        key="python_editor"
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button("▶ Run Code", use_container_width=True):
            try:
                with st.spinner("Running your example..."):
                    st.session_state.python_output = safe_python_run(
                        st.session_state.python_code
                    )
            except Exception as e:
                st.session_state.python_output = f"Error: {e}"

    with c2:
        st.download_button(
            "⬇ Download .py",
            st.session_state.python_code,
            file_name="my_python_code.py",
            mime="text/x-python",
            use_container_width=True
        )

    if "python_output" in st.session_state:
        st.markdown("### Output")
        st.code(st.session_state.python_output)

    st.info(
        "This is a safe beginner playground, not a full Python interpreter. "
        "Loops, imports, file access and arbitrary code execution are intentionally disabled."
    )


# 12 MATH SOLVER

def render_math_solver():
    st.markdown("## 🔢 Math Solver")
    st.write("Enter a math problem and get a step-by-step explanation.")

    level = st.selectbox(
        "Level",
        ["Primary", "Preparatory", "Secondary", "Advanced"]
    )

    language = st.selectbox(
        "Explanation language",
        ["English", "Arabic"]
    )

    problem = st.text_area(
        "Write your math problem",
        height=140,
        placeholder="Example: Solve 3x + 7 = 22"
    )

    if st.button("Solve Problem", use_container_width=True):
        if not problem.strip():
            st.warning("Enter a math problem first.")
        else:
            try:
                prompt = (
                    f"Solve this math problem step by step: {problem}\n"
                    f"Use clear numbered steps, verify the result, "
                    f"and explain why each step is valid. "
                    f"Student level: {level}. Reply in: {language}. "
                    f"If information is missing, say what is missing instead of guessing."
                )

                with st.spinner("Solving and explaining..."):
                    st.session_state.math_result = ask_groq(
                        prompt,
                        system=(
                            "You are a careful mathematics tutor. "
                            "Show accurate steps, check arithmetic, "
                            "and help the student understand rather than only giving the final answer."
                        ),
                        max_tokens=1500
                    )

            except Exception as e:
                st.error(str(e))

    if st.session_state.get("math_result"):
        st.markdown("### Solution")
        st.markdown(st.session_state.math_result)


# 13 SMART PLANNER

def render_smart_planner():
    st.markdown("## 📅 Smart Planner")
    st.write("Organize your tasks and follow your progress.")

    with st.form("add_planner_task", clear_on_submit=True):
        title = st.text_input(
            "Task name",
            placeholder="Example: Finish science homework"
        )

        c1, c2 = st.columns(2)

        with c1:
            due = st.date_input("Due date", value=date.today())

        with c2:
            priority = st.selectbox(
                "Priority",
                ["High", "Medium", "Low"],
                index=1
            )

        submitted = st.form_submit_button(
            "＋ Add Task",
            use_container_width=True
        )

    if submitted:
        if title.strip():
            st.session_state.planner_tasks.append({
                "title": title.strip(),
                "due": due.isoformat(),
                "priority": priority,
                "done": False
            })
            st.success("Task added.")
        else:
            st.warning("Enter a task name.")

    tasks = st.session_state.planner_tasks
    total = len(tasks)
    completed = sum(t["done"] for t in tasks)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tasks", total)
    c2.metric("Completed", completed)
    c3.metric("Remaining", total - completed)

    st.progress(completed / total if total else 0)

    if not tasks:
        st.info("Your planner is empty. Add your first task above.")
        return

    st.markdown("### Your Tasks")

    for i, task in enumerate(tasks):
        c1, c2, c3, c4 = st.columns([4, 2, 1.5, 1])

        with c1:
            st.checkbox(
                task["title"],
                value=task["done"],
                key=f"planner_done_{i}",
                on_change=lambda idx=i: st.session_state.planner_tasks[idx].update(
                    done=not st.session_state.planner_tasks[idx]["done"]
                )
            )

        with c2:
            st.caption(f"📅 {task['due']}")

        with c3:
            st.caption(f"Priority: {task['priority']}")

        with c4:
            if st.button("🗑️", key=f"planner_delete_{i}"):
                st.session_state.planner_tasks.pop(i)
                st.rerun()

    if st.button("Clear Completed Tasks"):
        st.session_state.planner_tasks = [
            t for t in tasks if not t["done"]
        ]
        st.rerun()


# SIDEBAR

with st.sidebar:
    st.markdown("## 🌌 CODEleader")
    st.caption("UNIVERSE PLATFORM")
    st.divider()
    st.markdown("### Navigation")

    for category in CATEGORIES:
        if st.button(
            category,
            key=f"cat_{category}",
            use_container_width=True
        ):
            st.session_state.category = category
            st.session_state.selected_project = None
            st.rerun()

    st.divider()
    st.caption("13 Projects • Growing Universe")


# PROJECT ROUTER

def open_project(name):
    routes = {
        "Weather App": render_weather,
        "Snake Ultimate": render_snake,
        "Translator App": render_translator,
        "Summarizer App": render_summarizer,
        "Audio & Video Transcription": render_transcription,
        "Study AI": render_study_ai,
        "My Chatbot": render_chatbot,
        "AI Student Assistant": render_student_assistant,
        "AI English Teacher": render_english_teacher,
        "Smart School AI": render_smart_school,
        "Python Code Playground": render_python_playground,
        "Math Solver": render_math_solver,
        "Smart Planner": render_smart_planner,
    }

    routes[name]()


# PROJECT DETAILS / DASHBOARD

if st.session_state.selected_project:
    project = next(
        (p for p in PROJECTS if p["name"] == st.session_state.selected_project),
        None
    )

    if project is None:
        st.session_state.selected_project = None
        st.rerun()

    if st.button("← Back to Dashboard"):
        st.session_state.selected_project = None
        st.rerun()

    st.title(f"{project['icon']} {project['name']}")
    st.caption(project["category"])
    st.write(project["desc"])
    st.divider()

    open_project(project["name"])

else:
    st.markdown("## Explore Your Universe")

    search = st.text_input(
        "🔎 Search projects",
        placeholder="Find your next experience..."
    )

    filtered = [
        p for p in PROJECTS
        if (
            st.session_state.category == "All Projects"
            or p["category"] == st.session_state.category
        )
        and (
            search.lower() in p["name"].lower()
            or search.lower() in p["desc"].lower()
        )
    ]

    st.caption(f"{len(filtered)} projects available")

    cols = st.columns(3)

    for index, project in enumerate(filtered):
        with cols[index % 3]:
            render_project_card(project)

            if st.button(
                "Explore Project →",
                key=f"open_{project['name']}",
                use_container_width=True
            ):
                st.session_state.selected_project = project["name"]
                st.rerun()

    st.divider()

    st.markdown(
        "<div style='text-align:center;color:#8993ad;'>CODEleader Universe © 2026</div>",
        unsafe_allow_html=True
    )
