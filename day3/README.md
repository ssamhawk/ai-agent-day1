# AI Agent - Day 2 Challenge: AI Configuration

A smart AI agent with structured response format that can be correctly parsed by the application. Built on Day 1 foundation with enhanced AI configuration capabilities.

## Features

✨ **Modern UI/UX**
- 🌓 Dark/Light theme toggle with localStorage persistence
- 📱 Responsive design (up to 1400px width)
- 🎨 Gradient backgrounds and smooth animations
- ⌨️ Markdown support (**bold**, *italic*, `code`, lists, etc.)

🤖 **AI Capabilities**
- 💬 Conversation history (remembers last 10 messages)
- 🔄 Context-aware responses
- ⏳ Typing indicator animation
- 📋 Copy response to clipboard

🔒 **Security & Performance**
- 🛡️ Rate limiting (10 requests/minute, 200/day, 50/hour)
- ✅ Input validation (max 2000 characters)
- 🔐 Secure session management
- 📝 Error logging without exposing sensitive data
- 🚫 Protected API keys with `.gitignore`

## Installation

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
FLASK_PORT=5001
SECRET_KEY=your_secret_key_here
```

## Usage

**Start the server:**
```bash
python day2/app.py
```

**Open your browser:**
```
http://127.0.0.1:5002
```

**Chat with the AI:**
1. Type your question in the input field
2. Press "Send" or hit Enter
3. Get AI-powered responses with context awareness
4. Use the 🗑️ Clear button to reset conversation history
5. Toggle between 🌙 Dark and ☀️ Light themes

## API Endpoints

### `POST /api/chat`
Send a message to the AI agent.

**Request:**
```json
{
  "message": "Your question here"
}
```

**Response:**
```json
{
  "response": "AI response here",
  "success": true
}
```

**Rate Limit:** 10 requests per minute

### `POST /api/clear`
Clear conversation history.

**Response:**
```json
{
  "success": true,
  "message": "Conversation history cleared"
}
```

## Project Structure

```
ai-challange/
├── app.py                 # Flask backend with OpenAI integration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── .gitignore            # Git ignore rules
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── style.css         # CSS with theme support
│   └── script.js         # Frontend JavaScript
└── venv/                 # Virtual environment (not in git)
```

## Technologies

- **Backend:** Flask 3.0.0, Python 3.9+
- **AI Model:** OpenAI GPT-4o-mini
- **Frontend:** Vanilla JavaScript, CSS3, HTML5
- **Styling:** CSS Custom Properties (CSS Variables)
- **Security:** Flask-Limiter, secure sessions
- **Fonts:** Inter (Google Fonts)

## Configuration

Environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *required* | Your OpenAI API key |
| `FLASK_DEBUG` | `False` | Enable debug mode |
| `FLASK_HOST` | `127.0.0.1` | Server host |
| `FLASK_PORT` | `5002` | Server port (Day 2) |
| `SECRET_KEY` | *auto-generated* | Flask session secret |

## Security Features

- ✅ API key protection with `.gitignore`
- ✅ Rate limiting to prevent abuse
- ✅ Input validation (length limits)
- ✅ Secure error handling (no data exposure)
- ✅ HttpOnly and SameSite cookies
- ✅ Debug mode disabled by default
- ✅ Localhost-only binding

## Development

**Enable debug mode:**
```bash
# In .env file
FLASK_DEBUG=True
```

**Check logs:**
Server logs include structured logging with timestamps for debugging.

## Day 2 Goals

- ✅ Specify the desired output structure directly in the prompt
- ✅ Provide an example of the expected output format
- ✅ Response from LLM can be correctly parsed by the application

## License

This project is part of the AI Agent Challenge - Day 2.

## Credits

Powered by OpenAI GPT-4o-mini API
