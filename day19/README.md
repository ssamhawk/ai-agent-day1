# Day 14 - First RAG Query

RAG (Retrieval-Augmented Generation) comparison tool that demonstrates the difference between AI responses with and without document context.

## What is RAG?

**Retrieval-Augmented Generation (RAG)** is a technique that enhances LLM responses by:
1. **Retrieving** relevant documents from your knowledge base
2. **Augmenting** the LLM prompt with this context
3. **Generating** a response based on both the query and retrieved documents

### Why RAG?

- **Factual Accuracy**: LLM can cite specific documents instead of relying on training data
- **Up-to-date Information**: Use your latest documents, not just training cutoff data
- **Domain Expertise**: Provide domain-specific knowledge the LLM wasn't trained on
- **Transparency**: See which documents were used to generate the response

## Features

### 🔍 RAG Comparison
- **Compare Mode**: Side-by-side comparison of responses with/without RAG
- **With RAG**: Query uses retrieved document context
- **Without RAG**: Query uses only LLM's general knowledge

### 📊 Response Analysis
- **Token Usage**: Compare token consumption
- **Source Files**: See which documents were used
- **Chunk Preview**: View retrieved document chunks
- **Similarity Scores**: See relevance scores for each chunk

### ⚙️ Customizable Options
- **Top K**: Number of chunks to retrieve (1-10)
- **Min Similarity**: Filter chunks by relevance (0.0-1.0)
- **Temperature**: Control response creativity (0.0-2.0)

## Architecture

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ├──────────┬────────────┐
       │          │            │
       v          v            v
┌──────────┐  ┌─────────┐  ┌─────────┐
│  Without │  │  With   │  │ Compare │
│   RAG    │  │   RAG   │  │  Both   │
└─────┬────┘  └────┬────┘  └────┬────┘
      │            │             │
      v            v             v
┌───────────────────────────────────┐
│         RAG Agent                 │
│  • query_without_rag()            │
│  • query_with_rag()               │
│  • compare_responses()            │
└─────────┬─────────────────────────┘
          │
          v
┌─────────────────────────────────┐
│     Vector Store Search         │
│  • Generate query embedding     │
│  • Search FAISS index           │
│  • Retrieve top K chunks        │
└─────────┬───────────────────────┘
          │
          v
┌─────────────────────────────────┐
│   Build Augmented Prompt        │
│  • System prompt                │
│  • Retrieved documents          │
│  • User question                │
└─────────┬───────────────────────┘
          │
          v
┌─────────────────────────────────┐
│      OpenAI LLM (gpt-4o-mini)   │
│  • Generate response            │
└─────────┬───────────────────────┘
          │
          v
     ┌────────┐
     │Response│
     └────────┘
```

## Usage

### 1. Start the Server

```bash
cd day14
source venv/bin/activate
python app.py
```

Access at: http://127.0.0.1:5010

### 2. Upload Documents

Before using RAG, you need indexed documents:

1. Go to **Document Indexing** page: http://127.0.0.1:5010/indexing
2. Upload documents (.md, .txt, .py, .js, .json, .csv)
3. Click **"📊 Index Documents"**
4. Wait for indexing to complete

### 3. Test RAG Comparison

1. Go to **RAG Comparison** page: http://127.0.0.1:5010/rag
2. Enter a question (e.g., "How to containerize a Python application with Docker?")
3. Click **"⚖️ Compare Responses"**
4. Compare the two responses side-by-side

### Demo Queries

Use these questions with the demo documents (from `/demo_documents`):

1. **Docker Containerization**
   ```
   How to containerize a Python application with Docker?
   ```
   - **Without RAG**: Generic Docker advice from training data
   - **With RAG**: Specific steps from docker_guide.md

2. **API Development**
   ```
   How to build a REST API with authentication?
   ```
   - **Without RAG**: General REST API concepts
   - **With RAG**: FastAPI + JWT implementation from your docs

3. **Performance Optimization**
   ```
   How to optimize Python code performance?
   ```
   - **Without RAG**: Common optimization tips
   - **With RAG**: Specific techniques from python_best_practices.md

4. **Async Programming**
   ```
   How to write asynchronous code in Python?
   ```
   - **Without RAG**: General async/await explanation
   - **With RAG**: Examples from your FastAPI tutorial

## API Endpoints

### Query with RAG

```http
POST /api/rag/query
Content-Type: application/json

{
  "question": "How to containerize a Python app?",
  "mode": "compare",  // "compare" | "with_rag" | "without_rag"
  "top_k": 5,
  "min_similarity": 0.0,
  "temperature": 0.7
}
```

Response:
```json
{
  "question": "...",
  "without_rag": {
    "answer": "...",
    "tokens_used": 150,
    "mode": "without_rag"
  },
  "with_rag": {
    "answer": "...",
    "tokens_used": 250,
    "mode": "with_rag",
    "chunks_used": [
      {
        "source_file": "docker_guide.md",
        "text": "...",
        "similarity": 0.89,
        "chunk_index": 0,
        "token_count": 512
      }
    ],
    "source_files": ["docker_guide.md"],
    "num_chunks": 5
  }
}
```

## Navigation

- **AI Agent**: http://127.0.0.1:5010/ - Voice-driven AI agent
- **Document Indexing**: http://127.0.0.1:5010/indexing - Upload and index documents
- **RAG Comparison**: http://127.0.0.1:5010/rag - Compare RAG vs non-RAG responses

## Technical Details

### RAG Agent (`rag_agent.py`)

**Core Methods:**
- `query_without_rag(question, temperature)`: Direct LLM query
- `query_with_rag(question, top_k, min_similarity, temperature)`: RAG-enhanced query
- `compare_responses(question, ...)`: Get both responses

**Prompt Engineering:**

Without RAG:
```
System: You are a helpful assistant. Answer based on your general knowledge.
User: {question}
```

With RAG:
```
System: Answer questions based on the provided documents.
        Use the documents to support your answer.
        Cite which document(s) you used.

User: Based on the following documents, answer this question:

      Question: {question}

      Documents:
      [Document 1: docker_guide.md (relevance: 89%)]
      {chunk_text}

      [Document 2: fastapi_tutorial.md (relevance: 85%)]
      {chunk_text}

      Answer:
```

### Components

1. **Vector Store** (`vector_store.py`)
   - FAISS index for similarity search
   - SQLite for metadata storage
   - Cosine similarity scoring

2. **Document Indexer** (`document_indexer.py`)
   - Text chunking (512 tokens, 50 overlap)
   - Embedding generation (text-embedding-3-small)

3. **RAG Agent** (`rag_agent.py`)
   - Query routing
   - Context retrieval
   - Prompt augmentation

## When RAG Helps vs Doesn't Help

### ✅ RAG is Beneficial When:

- Questions about **specific documents** in your knowledge base
- Requests for **domain-specific information** not in training data
- Need for **citations** and source references
- Questions about **recent updates** or internal documentation
- Technical details from **your codebase**

### ❌ RAG May Not Help When:

- **General knowledge questions** (e.g., "What is Python?")
- Questions **unrelated to indexed documents**
- Very **broad topics** without specific document matches
- Documents retrieved have **low similarity scores**
- Questions requiring **reasoning** rather than facts

## Configuration

Edit `app.py` to customize:

```python
# RAG Agent configuration
rag_agent = RAGAgent(
    client=client,
    vector_store=vector_store,
    embedding_generator=document_indexer.embedding_generator,
    model="gpt-4o-mini"  # Change LLM model
)
```

## Files Added

- `rag_agent.py` - RAG logic
- `rag_routes.py` - API endpoints
- `templates/rag.html` - RAG UI
- `static/rag.css` - RAG styles
- `static/rag.js` - RAG frontend logic

## Comparison with Day 13

| Day 13 | Day 14 |
|--------|--------|
| Document indexing only | Document indexing + RAG queries |
| Vector search UI | RAG comparison UI |
| Show similar chunks | Show LLM responses with context |
| Manual document review | AI-generated answers |

## Future Enhancements

- [ ] Conversation history with RAG
- [ ] Multi-turn RAG conversations
- [ ] Citation highlighting in responses
- [ ] RAG confidence scoring
- [ ] Hybrid search (keyword + semantic)
- [ ] Response quality metrics
- [ ] A/B testing framework
- [ ] Streaming RAG responses
