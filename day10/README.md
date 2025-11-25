# Day 10 - MCP Pipeline Agent

**Automated MCP pipeline where tools are combined into a sequence and executed step by step**

## 🎯 Requirements - FULLY MET

✅ Multiple MCP tools (search, read_file, write_file, list_files)
✅ Agent that chains tools into pipeline
✅ Automated step-by-step execution

## 🚀 Key Features

- **Autonomous Agent** - AI decides which tools to use and when
- **Sequential Execution** - One tool at a time, results feed next step
- **Tool Chaining** - Output of step N becomes input for step N+1
- **Language Detection** - Responds in same language as query
- **Error Handling** - Graceful failure recovery

## 📊 How It Works

**Pipeline Execution Example:**

Query: "List day10 files, read pipeline_agent.py, save summary"

```
Step 1: [MCP_LIST_FILES: day10] → Returns file list
Step 2: [MCP_READ_FILE: pipeline_agent.py] → Returns code
Step 3: [MCP_WRITE_FILE: summary.md | ...] → Saves analysis
Result: ✅ Complete!
```

---

## 🔧 Installation & Setup

### 1. Install dependencies
```bash
cd day10
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY (required)
# - BRAVE_API_KEY (optional, for web search)
```

### 3. Run application
```bash
python app.py
```

Open: http://127.0.0.1:5010

---

## 🧪 Testing

### Run automated tests:
```bash
python test_pipeline_local.py   # Simple test
python test_full_pipeline.py    # Full chain test
```

### Manual testing in UI:
1. Open http://127.0.0.1:5010
2. Enable **🔗 Pipeline Mode** in settings
3. Try these examples:

**Example 1 - Simple File Creation:**
```
Create a TODO list at ~/todo.txt with: 1. Learn MCP 2. Build pipeline 3. Test
```

**Example 2 - Multi-step Analysis:**
```
List files in ~/projects, read the main .py file, and save analysis to ~/analysis.md
```

**Example 3 - Research & Save** (requires Brave API):
```
Search for Flask best practices and save top 5 tips to ~/flask_tips.md
```

---

## 🆚 Day 8 vs Day 10

| Feature | Day 8 | Day 10 |
|---------|-------|--------|
| **Execution** | All tools at once | Step-by-step iterative |
| **Planning** | User pre-defines | AI decides dynamically |
| **Chaining** | Independent tools | Results feed next step |
| **Write files** | ❌ No | ✅ Yes |
| **Autonomous** | Semi-autonomous | Fully autonomous |
| **Example** | Search OR read | Search → analyze → save |

---

## 📁 Project Structure

```
day10/
├── app.py                    # Main application
├── pipeline_agent.py         # 🆕 Pipeline Agent implementation
├── ai_service.py             # AI response generation
├── mcp_client.py             # MCP client (+ write_file tool)
├── compression.py            # Conversation compression
├── routes.py                 # API routes (+ pipeline endpoint)
├── config.py                 # Configuration
├── .env                      # Environment variables (gitignored)
├── .env.example              # 🆕 Example configuration
├── requirements.txt          # Dependencies
├── templates/
│   └── index.html            # 🆕 Updated UI with Pipeline Mode
├── static/
│   ├── script.js             # 🆕 Pipeline UI logic
│   ├── style.css             # Styles
│   └── utils.js              # Utilities
├── test_outputs/             # 🆕 Pipeline test outputs
│   ├── test_write.txt
│   ├── simple_test.txt
│   └── pipeline_analysis.md
├── test_pipeline.py          # 🆕 Test scripts
├── test_pipeline_local.py
└── test_full_pipeline.py
```

---

## 🆚 Day 8 vs Day 10

| Feature | Day 8 | Day 10 |
|---------|-------|--------|
| **Execution** | All tools at once | Step-by-step iterative |
| **Planning** | User pre-defines | AI decides dynamically |
| **Chaining** | Independent tools | Results feed next step |
| **Write files** | ❌ No | ✅ Yes |
| **Example** | Search OR read | Search → analyze → save |

---

## 🏆 Success

Day 10 requirements fully implemented and tested.
