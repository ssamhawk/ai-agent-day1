# Day 12 - Voice Agent (Speech → LLM → Text)

**Voice-driven AI agent з speech-to-text через OpenAI Whisper API**

## 🎯 Завдання - ПОВНІСТЮ ВИКОНАНО

✅ Voice input через мікрофон
✅ Speech-to-text з OpenAI Whisper API
✅ Інтеграція з існуючим LLM pipeline
✅ Text response від AI
✅ Протестовано з різними типами запитів

## 🚀 Ключові фічі

### **1. Voice Recording**
- 🎤 Кнопка для запису голосу
- ⏱️ Таймер запису в реальному часі
- 📊 Візуальний індикатор запису
- 🛑 Кнопка зупинки запису

### **2. Speech-to-Text (Whisper API)**
- 🗣️ Високоточне розпізнавання через OpenAI Whisper
- 🌍 Автоматичне визначення мови (українська, англійська, російська)
- 📝 Конвертація аудіо → текст
- ✅ Валідація аудіо файлів (формат, розмір)

### **3. LLM Integration**
- 💬 Автоматична вставка тексту в chat input
- 🔗 Використання існуючого pipeline (Smart Mode, Pipeline Mode)
- 💾 Збереження в memory/conversations
- 📊 Compression та persistent storage

### **4. UX Features**
- 🎨 Красивий gradient UI для voice button
- ⏳ "Processing..." індикатор під час розпізнавання
- ✅ Success/Error notifications
- 📱 Mobile-responsive дизайн

## 📊 Як це працює

```
User натискає "🎤 Voice"
    ↓
Browser записує аудіо (MediaRecorder API)
    ↓
Натискає "Stop" → створюється audio blob
    ↓
Відправка на /api/speech-to-text
    ↓
Whisper API → розпізнавання → повертає текст
    ↓
Текст вставляється в input field
    ↓
User відправляє → LLM обробляє → text response
```

## 🏗️ Архітектура

### **Backend:**
```
day12/
├── speech_service.py       # Whisper API integration
├── routes.py               # +/api/speech-to-text endpoint
├── app.py                  # +speech_service config
└── ...existing day11 files
```

### **Frontend:**
```
day12/static/
├── voice-ui.js            # Audio recording + transcription
├── voice-ui.css           # Voice button styles
└── ...existing files

day12/templates/
└── index.html             # +voice button + recording indicator
```

### **API Endpoints:**
```
POST   /api/speech-to-text     # Whisper transcription
POST   /api/chat               # Existing chat (receives text)
POST   /api/pipeline/execute   # Existing pipeline mode
```

## 🔧 Установка

```bash
cd day12
python -m venv venv
source venv/bin/activate  # Linux/Mac
# або venv\Scripts\activate  # Windows

pip install openai flask flask-socketio flask-limiter flask-wtf python-dotenv
cp .env.example .env
```

## 📝 Конфігурація .env

```env
# OpenAI API Key (для GPT + Whisper)
OPENAI_API_KEY=sk-...your-key...

# Flask Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5010

# Secret Key
SECRET_KEY=...random-string...
```

**Важливо:** Той самий `OPENAI_API_KEY` працює для:
- ✅ GPT-4 / GPT-3.5 (chat)
- ✅ **Whisper API** (speech-to-text)

## ▶️ Запуск

```bash
python app.py
```

Відкрий: **http://127.0.0.1:5010**

## 🧪 Тестування

### **Test 1: Розрахунки (українською)**
```
🎤 "Розрахуй п'ять плюс сім помножити на три"
→ Whisper: "Розрахуй п'ять плюс сім помножити на три"
→ LLM: "Результат: 5 + (7 × 3) = 5 + 21 = 26"
```

### **Test 2: Визначення (англійською)**
```
🎤 "Give me a definition of quantum computing"
→ Whisper: "Give me a definition of quantum computing"
→ LLM: "Quantum computing is a type of computation..."
```

### **Test 3: Жарт (англійською)**
```
🎤 "Tell me a joke about programming"
→ Whisper: "Tell me a joke about programming"
→ LLM: "Why do programmers prefer dark mode? Because light attracts bugs!"
```

### **Test 4: Pipeline Mode + Voice**
```
🎤 "Search for latest Python news and save to file"
→ Whisper: "Search for latest Python news and save to file"
→ Pipeline Agent:
   Step 1: [MCP_SEARCH: latest Python news]
   Step 2: [MCP_WRITE_FILE: ~/python_news.md | ...]
   Step 3: [MCP_DONE] "Saved Python news to file!"
```

## 🎤 Підтримувані аудіо формати

Whisper API приймає:
- ✅ **webm** (браузерний MediaRecorder)
- ✅ mp3, mp4, mpeg, mpga
- ✅ m4a, wav, ogg

Максимальний розмір: **25MB**

## 💰 Ціна Whisper API

- **$0.006 за хвилину** аудіо
- Приклад:
  - 10 секунд = $0.001
  - 1 хвилина = $0.006
  - 100 запитів по 10 сек = $0.10

Дуже дешево для тестування!

## 🔒 Security Features

- ✅ CSRF protection на /api/speech-to-text
- ✅ Rate limiting (20 requests/minute)
- ✅ File validation (розмір, формат)
- ✅ Temporary file cleanup
- ✅ Microphone permission handling

## 🆚 Day 11 vs Day 12

| Фіча | Day 11 | Day 12 |
|------|--------|--------|
| **Input** | Text only | Text + Voice ✅ |
| **Speech-to-Text** | ❌ | Whisper API ✅ |
| **Voice UI** | ❌ | Recording button ✅ |
| **Audio formats** | ❌ | webm/mp3/wav ✅ |
| **Memory** | SQLite | SQLite (same) |
| **Pipeline** | MCP tools | MCP tools (same) |

## 📁 Нові файли (Day 12)

```
day12/
├── speech_service.py          # NEW - Whisper API
├── static/
│   ├── voice-ui.js           # NEW - Recording logic
│   └── voice-ui.css          # NEW - Voice button styles
├── routes.py                 # UPDATED - +speech endpoint
├── app.py                    # UPDATED - +speech config
├── templates/
│   └── index.html            # UPDATED - +voice button
└── README.md                 # NEW - Day 12 docs
```

## 🎨 Voice UI Components

### **Voice Button**
- Gradient purple background
- Hover animation (lift effect)
- Recording state: pink gradient + pulse
- Processing state: light gradient + disabled

### **Recording Indicator**
- Fixed at top center
- Shows recording time (00:00)
- Blinking red dot animation
- Auto-hide when stopped

### **Notifications**
- Success: green gradient
- Error: red gradient
- Auto-dismiss after 3s

## 🐛 Troubleshooting

### **Problem: Microphone access denied**
```
Solution: Дозволь доступ до мікрофону в браузері
Chrome: Settings → Privacy → Microphone → Allow
```

### **Problem: MediaRecorder not supported**
```
Solution: Використовуй сучасний браузер
✅ Chrome, Edge, Firefox (останні версії)
❌ IE, старі браузери
```

### **Problem: Whisper API error**
```
Check:
1. OPENAI_API_KEY в .env
2. API key валідний і має кредити
3. Аудіо файл < 25MB
4. Формат підтримується
```

### **Problem: Audio too quiet**
```
Solution: Говори голосніше або ближче до мікрофону
Whisper API добре працює навіть з тихим аудіо
```

### **Problem: Запис починається із запізненням (1-3 секунди)**
```
✅ ВИПРАВЛЕНО! Тепер:
1. При першому кліку де завгодно - мікрофон преініціалізується
2. При натисканні Voice - запис починається МИТТЄВО
3. Stream зберігається між записами = 0 затримка

Якщо все ще бачиш затримку:
- Перезавантаж сторінку (Ctrl+R)
- При першому запиті дай дозвіл на мікрофон
- Наступні записи будуть миттєві!
```

### **Problem: Whisper розпізнає "you" замість цифр**
```
✅ ВИПРАВЛЕНО! Додано:
- Prompt для Whisper API про цифри
- Краща якість аудіо (echoCancellation, noiseSuppression)

Поради:
- Говори мінімум 2-3 секунди
- Використовуй фрази: "calculate five plus seven"
- Замість "п'ять" → "number five"
```

## 🏆 Success Criteria

✅ Voice button працює
✅ Запис аудіо через браузер
✅ Whisper API розпізнає мову
✅ Текст вставляється в input
✅ LLM обробляє запит
✅ Response повертається як текст
✅ Протестовано 3+ сценарії

**Day 12 - ПОВНІСТЮ РЕАЛІЗОВАНО! 🎉**

## 📚 Додаткові можливості

### **Майбутні покращення:**
- 🔊 Text-to-Speech для відповідей (OpenAI TTS)
- 🌍 Вибір мови розпізнавання
- 📝 Історія voice queries
- 🎚️ Регулювання sensitivity
- 📊 Візуалізація аудіо хвилі

### **Інтеграція з Pipeline Mode:**
```
Voice: "Find information about Flask and create a summary"
→ Pipeline:
  1. [MCP_SEARCH: Flask framework]
  2. [MCP_WEB_FETCH: https://flask.palletsprojects.com]
  3. [MCP_WRITE_FILE: ~/flask_summary.md | ...]
  4. [MCP_DONE] "Summary created!"
```

---

## 📖 Documentation Links

- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [MediaRecorder API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

---

**Day 12 Challenge Complete! 🎊**
Voice-driven AI agent готовий до використання!
