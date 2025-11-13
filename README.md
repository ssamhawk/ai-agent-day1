# AI Agent Challenge

Multi-day AI agent development challenge with progressive feature additions.

## Project Structure

```
ai-challange/
├── day1/              # Day 1 - Basic AI Agent
│   ├── app.py         # Flask app (port 5001)
│   ├── templates/
│   ├── static/
│   └── README.md
├── day2/              # Day 2 - AI Configuration
│   ├── app.py         # Flask app (port 5002)
│   ├── templates/
│   ├── static/
│   └── README.md
├── .env               # Shared environment variables
├── requirements.txt   # Shared dependencies
└── venv/             # Shared virtual environment
```

## Quick Start

### Installation

1. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create `.env` file:**
```bash
touch .env
```

4. **Add your OpenAI API key to `.env`:**
```env
OPENAI_API_KEY=your_actual_api_key_here

# Optional configuration
FLASK_DEBUG=False
FLASK_HOST=127.0.0.1
SECRET_KEY=your_secret_key_here
```

### Running Different Days

Each day is an independent application that can be run separately:

**Day 1 - Basic AI Agent:**
```bash
python day1/app.py
# Opens on http://127.0.0.1:5001
```

**Day 2 - AI Configuration:**
```bash
python day2/app.py
# Opens on http://127.0.0.1:5002
```

You can run multiple days simultaneously since they use different ports!

## Challenge Progress

### ✅ Day 1 - Basic AI Agent
- Modern web interface with dark/light theme
- Conversation history (10 messages)
- Rate limiting and security features
- Markdown support

### 🚧 Day 2 - AI Configuration
- Structured response format
- Parseable AI outputs
- Custom prompt engineering

### 📅 Day 3 - Coming Soon

## Technologies

- **Backend:** Flask 3.0.0, Python 3.9+
- **AI Model:** OpenAI GPT-4o-mini
- **Frontend:** Vanilla JavaScript, CSS3, HTML5
- **Security:** Flask-Limiter, secure sessions

## License

This project is part of the AI Agent Challenge.

## Credits

Powered by OpenAI GPT-4o-mini API
