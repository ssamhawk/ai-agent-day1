# 🧪 Тестові Питання для Day 16 - Citations

## Інструкція по тестуванню

1. Відкрий http://127.0.0.1:5010/rag
2. Завантаж всі 8 документів через "📤 Manage Documents"
3. Задай кожне питання нижче
4. Перевір:
   - ✅ Чи є citations [1], [2], [3] в відповіді
   - ✅ Чи citation_rate > 0.7 (70%+)
   - ✅ Чи sources_section показує правильні файли
   - ✅ Чи відповідь не містить hallucinations

---

## 📋 8 Тестових Питань (по 1 на кожен файл)

### ❓ Питання 1: Docker Basics
**Файл:** `docker_basics.md`

```
How do I stop a running Docker container?
```

**Очікувана відповідь:**
- ✅ Має містити `docker stop` command
- ✅ Citation [1] на docker_basics.md
- ✅ Можливо додаткова інформація про `docker kill`
- ✅ Citation rate: 100% (1/1 або 2/2)

**Приклад правильної відповіді:**
```
To stop a running Docker container, use the docker stop command
followed by the container ID or name [1]. For forceful termination,
you can use docker kill [1].

📚 SOURCES
[1] docker_basics.md (chunk 2)
    "The docker stop command gracefully stops..."
```

---

### ❓ Питання 2: Kubernetes
**Файл:** `kubernetes_intro.md`

```
What is a Pod in Kubernetes and how is it different from a container?
```

**Очікувана відповідь:**
- ✅ Пояснення що Pod - це smallest deployable unit
- ✅ Pod може містити multiple containers
- ✅ Citation [1] на kubernetes_intro.md
- ✅ Citation rate: 100%

**Приклад правильної відповіді:**
```
A Pod is the smallest deployable unit in Kubernetes that can contain
one or more containers [1]. Unlike a single container, a Pod can run
multiple containers that share the same network namespace and storage
volumes [1].

📚 SOURCES
[1] kubernetes_intro.md (chunk 5)
    "Pods are the smallest deployable units..."
```

---

### ❓ Питання 3: Python Async
**Файл:** `python_async.md`

```
Show me how to handle timeouts in Python async code
```

**Очікувана відповідь:**
- ✅ Має містити `asyncio.wait_for()` приклад
- ✅ Citation [1] на python_async.md
- ✅ Код приклад з timeout parameter
- ✅ Citation rate: 100%

**Приклад правильної відповіді:**
```
You can handle timeouts in Python async code using asyncio.wait_for() [1].
Here's an example:

```python
result = await asyncio.wait_for(some_coroutine(), timeout=5.0)
```

This will raise asyncio.TimeoutError if the operation takes longer than
5 seconds [1].

📚 SOURCES
[1] python_async.md (chunk 8)
    "Use asyncio.wait_for() to add timeout..."
```

---

### ❓ Питання 4: Database Indexing
**Файл:** `database_indexing.md`

```
Why are my database queries slow even with small tables?
```

**Очікувана відповідь:**
- ✅ Пояснення про missing indexes
- ✅ B-tree index structure explanation
- ✅ Citation [1] на database_indexing.md
- ✅ Можливо EXPLAIN ANALYZE command
- ✅ Citation rate: 100%

**Приклад правильної відповіді:**
```
Even with small tables, queries can be slow without proper indexes [1].
The database performs a sequential scan through all rows instead of
using an index lookup [1]. You should create indexes on columns used
in WHERE clauses and JOINs [1].

Use EXPLAIN ANALYZE to check if your queries are using indexes [1].

📚 SOURCES
[1] database_indexing.md (chunk 3)
    "Without indexes, the database scans all rows..."
```

---

### ❓ Питання 5: GitHub Actions
**Файл:** `github_actions.md`

```
Should I use GitHub Actions or Jenkins for my CI/CD pipeline?
```

**Очікувана відповідь:**
- ✅ Порівняння GitHub Actions vs Jenkins
- ✅ Pros and cons кожного
- ✅ Citation [1] на github_actions.md
- ✅ Можливо use cases для кожного
- ✅ Citation rate: 100%

**Приклад правильної відповіді:**
```
GitHub Actions is better for projects already hosted on GitHub, offering
seamless integration and no server maintenance [1]. Jenkins provides more
flexibility and plugins but requires self-hosting and maintenance [1].

Choose GitHub Actions if:
- Your code is on GitHub
- You want zero setup [1]

Choose Jenkins if:
- You need complex custom pipelines
- You're already invested in Jenkins ecosystem [1]

📚 SOURCES
[1] github_actions.md (chunk 7)
    "GitHub Actions vs Jenkins: GitHub Actions offers..."
```

---

### ❓ Питання 6: Machine Learning
**Файл:** `machine_learning_basics.md`

```
What's the difference between supervised and unsupervised learning?
```

**Очікувана відповідь:**
- ✅ Supervised - має labels
- ✅ Unsupervised - немає labels
- ✅ Examples для кожного типу
- ✅ Citation [1] на machine_learning_basics.md
- ✅ Citation rate: 100%

**Приклад правильної відповіді:**
```
Supervised learning uses labeled data to train models, where each input
has a known output [1]. For example, email spam classification where
emails are labeled as spam or not spam [1].

Unsupervised learning works with unlabeled data to find patterns [1].
Examples include clustering customers into segments or dimensionality
reduction [1].

📚 SOURCES
[1] machine_learning_basics.md (chunk 2)
    "Supervised learning requires labeled data..."
```

---

### ❓ Питання 7: REST API Design
**Файл:** `rest_api_design.md`

```
What's the difference between PUT and PATCH in REST APIs?
```

**Очікувана відповідь:**
- ✅ PUT - replaces entire resource
- ✅ PATCH - partial update
- ✅ Citation [1] на rest_api_design.md
- ✅ Code examples для обох
- ✅ Citation rate: 100%

**Приклад правильної відповіді:**
```
PUT replaces the entire resource with the new data you provide [1].
If you omit a field, it will be removed or set to default [1].

PATCH performs a partial update, modifying only the fields you specify [1].
Other fields remain unchanged [1].

Example:
PUT /users/123 - sends complete user object [1]
PATCH /users/123 - sends only {email: "new@email.com"} [1]

📚 SOURCES
[1] rest_api_design.md (chunk 4)
    "PUT vs PATCH: PUT replaces the entire resource..."
```

---

### ❓ Питання 8: Testing Strategies
**Файл:** `testing_strategies.md`

```
What are common mistakes when writing tests?
```

**Очікувана відповідь:**
- ✅ Testing implementation details
- ✅ Flaky tests
- ✅ Too many mocks
- ✅ Citation [1] на testing_strategies.md
- ✅ Citation rate: 100%

**Приклад правильної відповіді:**
```
Common testing mistakes include [1]:

1. Testing implementation details instead of behavior [1]
2. Writing flaky tests that randomly fail [1]
3. Over-mocking, which makes tests fragile [1]
4. Not testing edge cases and error conditions [1]
5. Making tests too dependent on each other [1]

Focus on testing what the code does, not how it does it [1].

📚 SOURCES
[1] testing_strategies.md (chunk 9)
    "Common Testing Mistakes: Testing implementation..."
```

---

## 🎯 Cross-Document Питання (Advanced)

### ❓ Питання 9: Multi-Source (Docker + Kubernetes)

```
How do I deploy a Docker container to Kubernetes?
```

**Очікувана відповідь:**
- ✅ Інформація з docker_basics.md про containers
- ✅ Інформація з kubernetes_intro.md про Pods/Deployments
- ✅ Citations [1] docker_basics.md + [2] kubernetes_intro.md
- ✅ Citation rate: > 70%

**Приклад правильної відповіді:**
```
First, containerize your application using Docker [1]. Then create
a Kubernetes Deployment manifest that specifies your Docker image [2].

Steps:
1. Build Docker image: docker build -t myapp:v1 [1]
2. Push to registry: docker push myapp:v1 [1]
3. Create Kubernetes Deployment with image: myapp:v1 [2]
4. Kubernetes will pull and run your container in Pods [2]

📚 SOURCES
[1] docker_basics.md (chunk 1)
    "Building Docker images with docker build..."
[2] kubernetes_intro.md (chunk 3)
    "Deployments specify which container images to run..."
```

---

### ❓ Питання 10: Multi-Source (Testing + CI/CD)

```
How do I run tests automatically when code is pushed to GitHub?
```

**Очікувана відповідь:**
- ✅ Інформація з testing_strategies.md про test commands
- ✅ Інформація з github_actions.md про workflows
- ✅ Citations [1] testing + [2] github_actions
- ✅ Citation rate: > 70%

**Приклад правильної відповіді:**
```
Set up a GitHub Actions workflow that triggers on push events [1].
Configure it to run your test suite automatically [2].

Example workflow:
```yaml
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: npm test
```

This will run your tests (unit, integration, E2E) [2] every time
code is pushed to the repository [1].

📚 SOURCES
[1] github_actions.md (chunk 4)
    "Workflows trigger on events like push..."
[2] testing_strategies.md (chunk 2)
    "Run tests in CI/CD pipeline automatically..."
```

---

## ✅ Критерії Успіху

### Per-Question Success:
- ✅ Response має 1+ citations
- ✅ Citation rate >= 70%
- ✅ No invalid citations (e.g., [99] when only 5 sources)
- ✅ Response відповідає на питання
- ✅ Sources section показує правильні файли

### Overall Success (8 питань):
- ✅ 8/8 питань мають citations (100%)
- ✅ Average citation rate >= 80%
- ✅ No hallucinations (всі facts з документів)
- ✅ Sources properly formatted

---

## 📊 Як Перевірити

### 1. Citation Presence:
```
✅ GOOD: "Use docker stop [1] to stop containers"
❌ BAD:  "Use docker stop to stop containers" (no citation!)
```

### 2. Citation Rate:
```
✅ GOOD: 5/5 sources cited = 100% citation rate
⚠️  OK:   4/5 sources cited = 80% citation rate
❌ BAD:  1/5 sources cited = 20% citation rate
```

### 3. Invalid Citations:
```
Sources provided: [1], [2], [3]
✅ GOOD: Response uses [1], [2]
❌ BAD:  Response uses [1], [5] (5 doesn't exist!)
```

### 4. Source Accuracy:
```
Question about Docker
✅ GOOD: [1] docker_basics.md
❌ BAD:  [1] kubernetes_intro.md (wrong file!)
```

---

## 🐛 Debugging Tips

### Якщо citation rate низький:
- Перевір чи prompt містить "MUST cite sources"
- Перевір чи context має [1], [2] markers
- Спробуй stronger prompt: "ALWAYS cite, NEVER skip"

### Якщо hallucinations:
- Citations допомагають, але не гарантують
- Перевір чи LLM invented facts not in sources
- Порівняй response з actual source text

### Якщо invalid citations:
- Bug в citation validation regex
- LLM invented citation numbers
- Check: чи context містив ці номери?

---

## 🎓 Висновок

Після тестування всіх 8 питань ти маєш побачити:

1. **Every response has citations** - [1], [2], [3] в тексті
2. **High citation rates** - 80%+ sources використано
3. **Accurate sources** - правильні файли в sources_section
4. **No hallucinations** - всі facts з документів
5. **Trust & Transparency** - можна перевірити кожне твердження

Citations **значно покращують** якість RAG відповідей! 🎯
