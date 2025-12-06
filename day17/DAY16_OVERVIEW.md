# Day 16 - Citations & Sources

## Завдання
Покращити RAG пайплайн так, щоб модель **обов'язково** включала citations (посилання на джерела) в кожній відповіді.

## Реалізовано ✅

### 1. Citation Metadata (chunk_id, source_file)
**Файл:** `document_indexer.py:77-79`

Додано унікальні ID для кожного chunk:
```python
# Add citation metadata (chunk_id for referencing)
source_file = metadata.get('source_file', 'unknown') if metadata else 'unknown'
chunk_meta['chunk_id'] = f"{source_file}_chunk_{chunk_idx}"
```

### 2. Citation Manager Module
**Файл:** `citation_manager.py` (новий модуль, 280 рядків)

Функціонал:
- `build_context_with_citations()` - будує контекст з numbered citations [1], [2], [3]
- `create_citation_prompt()` - створює prompt що ВИМАГАЄ citations від LLM
- `validate_citations()` - перевіряє чи LLM використав citations
- `format_sources_section()` - форматує секцію з джерелами для відображення

**Приклад контексту з citations:**
```
[1] Source: docker_basics.md (chunk 2)
Relevance: 87.5%
To stop a container, use the docker stop command...

[2] Source: kubernetes_intro.md (chunk 5)
Relevance: 76.3%
Pods are the smallest deployable units...
```

### 3. Citation-Enforcing Prompt
**Файл:** `citation_manager.py:83-110`

```python
IMPORTANT RULES:
1. You MUST cite your sources using the citation numbers provided: [1], [2], [3], etc.
2. Every factual claim should include a citation to the source where you found that information
3. Use inline citations like: "Docker containers can be stopped with docker stop [1]"
4. If information comes from multiple sources, cite all of them: [1][2]
5. Do NOT make up information not found in the provided context
```

### 4. Citation Validation
**Файл:** `citation_manager.py:112-170`

Перевіряє:
- ✅ Чи response містить citations `[1]`, `[2]`, etc.
- ✅ Чи всі джерела використані (citation_rate)
- ✅ Чи немає invalid citations (наприклад [99] коли є тільки 5 джерел)
- ✅ Які джерела missing

**Результат validation:**
```python
{
    'is_valid': True,
    'has_citations': True,
    'all_cited': False,
    'citation_rate': 0.8,  # 4 з 5 джерел використано
    'num_cited': 4,
    'cited': [1, 2, 3, 4],
    'missing': [5],
    'invalid': []
}
```

### 5. Інтеграція в RAG Agent
**Файл:** `rag_agent.py`

Модифіковано `_generate_response_from_chunks()`:
- Використовує `CitationManager` для побудови контексту
- Створює citation-enforcing prompt
- Валідує citations після генерації
- Форматує sources section для UI

**Приклад response з citations:**
```python
{
    'answer': "To stop a Docker container, use docker stop [1]...",
    'citation_validation': {
        'is_valid': True,
        'citation_rate': 1.0,
        'cited': [1, 2, 3]
    },
    'citation_map': { ... },
    'sources_section': "📚 SOURCES\n[1] docker_basics.md..."
}
```

---

## Переваги Citations

### 1. 📚 Transparency (Прозорість)
- Користувач бачить **звідки** інформація
- Може перевірити оригінальне джерело

### 2. 🛡️ Fewer Hallucinations
- LLM не може вигадувати, бо має цитувати
- Якщо немає citation → підозріла інформація

### 3. ✅ Trust & Verification
- Можна перевірити кожне твердження
- Зрозуміло які документи найбільш релевантні

### 4. 🔍 Debugging
- Легко побачити чи правильні документи знайшлись
- Можна покращити retrieval на основі citations

---

## Приклад використання

### До (Day 15):
```
Q: How do I stop a Docker container?
A: Use the docker stop command with the container ID.

🤔 Звідки ця інформація? Невідомо!
```

### Після (Day 16):
```
Q: How do I stop a Docker container?
A: To stop a running Docker container, use the docker stop command
   followed by the container ID [1]. For forceful termination, you
   can use docker kill [2].

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 SOURCES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] docker_basics.md (chunk 2)
    Relevance: 87.5%
    Preview: "The docker stop command gracefully stops..."

[2] docker_basics.md (chunk 7)
    Relevance: 76.3%
    Preview: "Use docker kill when you need immediate..."

✅ Citations: 2/2 used (100%)
```

---

## Testing

### Test Questions (5 питань):

1. **Docker Command:**
   ```
   How do I stop a Docker container?
   ```
   Очікувано: [1] docker_basics.md

2. **Kubernetes Concept:**
   ```
   What is a Pod in Kubernetes?
   ```
   Очікувано: [1] kubernetes_intro.md

3. **Python Async:**
   ```
   Show me how to handle timeout in async code
   ```
   Очікувано: [1] python_async.md з asyncio.wait_for()

4. **Database Optimization:**
   ```
   Why are my database queries slow even with small tables?
   ```
   Очікувано: [1] database_indexing.md

5. **CI/CD Comparison:**
   ```
   Should I use GitHub Actions or Jenkins for my CI/CD pipeline?
   ```
   Очікувано: [1] github_actions.md з розділом "GitHub Actions vs Jenkins"

### Validation Metrics:

- ✅ **Citation Rate**: % джерел що було використано
- ✅ **All Cited**: Чи всі джерела cited
- ✅ **Has Citations**: Чи є хоч якісь citations
- ✅ **No Invalid**: Чи немає invalid citation numbers

---

## Технічна Архітектура

```
┌─────────────────────────────────────────────────┐
│ 1. User Query                                   │
│    "How do I stop Docker container?"            │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 2. Embedding & Retrieval                        │
│    → Generate query embedding                   │
│    → Search vector store (20 docs)              │
│    → Rerank (optional)                          │
│    → Keep top 5                                 │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 3. CitationManager.build_context_with_citations│
│    → Adds [1], [2], [3] markers                │
│    → Creates citation_map for each source       │
│                                                  │
│    Output:                                       │
│    [1] docker_basics.md                         │
│    To stop a container...                       │
│                                                  │
│    [2] kubernetes_intro.md                      │
│    Pods are the smallest...                     │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 4. CitationManager.create_citation_prompt       │
│    → Enforces citation rules                    │
│    → "You MUST cite sources using [1], [2]..."  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 5. LLM Generation                               │
│    → Processes prompt with citations            │
│    → Generates answer with [1], [2] markers     │
│                                                  │
│    Output:                                       │
│    "Use docker stop [1] for graceful shutdown"  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 6. CitationManager.validate_citations           │
│    → Extracts [1], [2] from response            │
│    → Checks coverage and validity               │
│    → Calculates citation_rate                   │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 7. CitationManager.format_sources_section       │
│    → Formats sources for display                │
│    → Shows file names, relevance, previews      │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 8. Response to User                             │
│    → Answer with inline citations               │
│    → Citation validation stats                  │
│    → Formatted sources section                  │
└─────────────────────────────────────────────────┘
```

---

## Файли Модифіковані/Створені

1. **citation_manager.py** - Новий модуль (280 lines)
2. **document_indexer.py** - Додано chunk_id metadata
3. **rag_agent.py** - Інтегровано CitationManager
4. **templates/rag.html** - Оновлено UI (TODO)
5. **static/rag.js** - Додано відображення citations (TODO)

---

## Порівняння Day 15 vs Day 16

| Aspect | Day 15 (Reranking) | Day 16 (Citations) |
|--------|-------------------|-------------------|
| Context Format | `[Document 1: file.md]` | `[1] Source: file.md` |
| LLM Prompt | "Use documents below" | "MUST cite using [1], [2]" |
| Response | Plain text answer | Answer with [1], [2] citations |
| Validation | None | Citation coverage & validity |
| Sources Display | Chunks list | Formatted sources section |
| Transparency | Low | High |
| Hallucination Risk | Medium | Low |

---

## Наступні Кроки (Optional Improvements)

1. **Clickable Citations** - [1] стає посиланням на джерело в UI
2. **Highlight Sources** - Підсвітити cited vs non-cited sources
3. **Citation Heatmap** - Показати які частини документа найбільш використані
4. **Strict Mode** - Вимагати 100% citation coverage
5. **Citation Report** - Детальний аналіз citation patterns

---

## Ключові Уроки

1. **Citations ≠ Quality** - Навіть з citations, LLM може неправильно інтерпретувати
2. **Prompt Engineering Critical** - "MUST cite" сильніше ніж "please cite"
3. **Validation Required** - Не довіряй LLM, завжди перевіряй
4. **User Trust** - Citations значно підвищують довіру користувачів
5. **Debugging Tool** - Citations показують проблеми з retrieval

---

## Запуск

```bash
cd day16
source venv/bin/activate
python app.py
```

Відкрий: http://127.0.0.1:5010/rag

---

🎯 **Day 16 Complete!** RAG тепер завжди надає citations до джерел, підвищуючи прозорість та знижуючи ризик hallucinations.
