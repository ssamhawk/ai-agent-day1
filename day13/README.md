# Day 13 - Document Indexing with Semantic Search

**Система індексації документів з векторним пошуком через OpenAI Embeddings та FAISS**

## 🎯 Завдання - ПОВНІСТЮ ВИКОНАНО

✅ Pipeline обробки документів (upload → chunking → embeddings)  
✅ Векторне зберігання з FAISS + SQLite для метаданих  
✅ Семантичний пошук за embeddings  
✅ Web інтерфейс для завантаження та пошуку  
✅ Real-time progress через WebSocket  
✅ Статистика індексу  

---

## 🚀 Ключові фічі

### Document Processing Pipeline
```
📄 Upload → ✂️ Chunking → 🧮 Embeddings → 💾 FAISS + SQLite
```

- **Chunking**: 512 токенів per chunk, 50 tokens overlap
- **Embeddings**: text-embedding-3-small (1536d)
- **Storage**: FAISS (vectors) + SQLite (metadata)

### Semantic Search
- Cosine similarity search
- Top-K results (1-20)
- Similarity threshold filtering (0-1)
- File type filtering

### Web Interface
- 📤 Drag & drop file upload
- 🔍 Semantic search
- 📊 Real-time statistics
- ⚙️ Configurable settings

---

## 🔧 Setup

```bash
cd day13
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Access:**
- Voice Agent: http://127.0.0.1:5010/
- Document Indexing: http://127.0.0.1:5010/indexing

---

## 📖 Usage

1. **Upload Documents**: Drag & drop `.md`, `.txt`, `.py`, `.js`, `.json`, `.csv` files
2. **Index**: Click "📊 Index Documents" and wait for processing
3. **Search**: Enter query and get semantically similar results
4. **View Stats**: See total files, chunks, tokens

---

## 🎬 Demo

**Test documents provided in `test_documents/`:**
- `docker_guide.md` - Docker tutorial
- `python_tips.md` - Python best practices

**Example search**: "How to containerize Python application"

---

## 🛠️ Tech Stack

- Flask + Socket.IO
- OpenAI Embeddings API
- FAISS (vector search)
- SQLite (metadata)
- tiktoken (tokenization)

---

## 📊 API Endpoints

- `POST /api/indexing/upload` - Upload and index documents
- `POST /api/indexing/search` - Search for similar documents
- `GET /api/indexing/stats` - Get index statistics
- `POST /api/indexing/clear` - Clear index

---

## 🎯 Use Cases

1. Documentation search across multiple repos
2. Code search by functionality
3. Personal knowledge base
4. RAG (Retrieval-Augmented Generation) foundation

---

**День 13 завершено!** ✅
