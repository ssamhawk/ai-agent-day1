# Day 19 — Vision QA Agent (Quality & Style Compliance)

Automated quality assurance for generated images using Vision API. Evaluates images against checklists and filters low-quality results.

## What's New in Day 19?

### 🔍 Vision-Based QA Agent
- **Automated quality control** for generated images
- **Dual-mode evaluation**:
  1. Text-based checklist (preset styles)
  2. Visual comparison (reference images)
- **Detailed scoring** on 6 quality dimensions
- **Smart filtering** with configurable thresholds

### 📊 Quality Checklist

Every image is evaluated on:
1. **Color Palette** (0-10): Matches expected colors?
2. **Visual Style** (0-10): Correct artistic style (3D, realistic, etc)?
3. **Mood** (0-10): Right atmosphere/feeling?
4. **Composition** (0-10): Good framing and layout?
5. **Subject Match** (0-10): Contains what was requested?
6. **Quality** (0-10): Sharp, clear, no artifacts?

**Overall Score** = Average of all checks

---

## Architecture

```
User Request
     ↓
Generate Image (fal.ai)
     ↓
QA Evaluation (Vision API) ← Optional: Reference Image
     ├─ Color Palette ✓
     ├─ Visual Style ✓
     ├─ Mood ✓
     ├─ Composition ✓
     ├─ Subject Match ✓
     └─ Quality ✓
     ↓
Score ≥ Threshold?
     ├─ YES → ✅ Save & Return
     └─ NO  → ❌ Flag/Discard
```

---

## Quick Start

### 1. Install & Setup

```bash
cd day19
source venv/bin/activate

# Copy and configure .env
cp .env.example .env
# Add your keys: OPENAI_API_KEY, FAL_KEY
```

### 2. Configure QA Threshold

In `.env`:
```bash
QA_THRESHOLD=7.0  # Images below this score are flagged
```

**Recommended thresholds:**
- **Strict** (8.0-10.0): Only best images pass
- **Balanced** (7.0): Good quality images (default)
- **Permissive** (5.0-6.0): Most images pass

### 3. Start Server

```bash
python app.py
```

Access: http://127.0.0.1:5010

---

## Usage Examples

### Example 1: Text-based QA (Preset Styles)

**Request:**
```json
POST /api/image/generate
{
  "prompt": "a cat wearing sunglasses",
  "model": "flux-schnell",
  "size": "square",
  "enable_qa": true,
  "qa_threshold": 7.0,
  "qa_checklist": {
    "color_palette": ["#FF006E", "#00F0FF", "#8338EC"],
    "visual_style": "cyberpunk, neon lights, futuristic",
    "mood": "edgy, energetic, mysterious"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "image_url": "...",
    "qa_check": {
      "overall_score": 8.5,
      "passed": true,
      "checks": {
        "color_palette": {"score": 9.0, "feedback": "Neon pink and cyan present"},
        "visual_style": {"score": 8.5, "feedback": "Strong cyberpunk aesthetic"},
        "mood": {"score": 8.0, "feedback": "Captures edgy vibe well"},
        "composition": {"score": 9.0, "feedback": "Well-centered, clean"},
        "subject_match": {"score": 10.0, "feedback": "Cat with sunglasses visible"},
        "quality": {"score": 7.5, "feedback": "Sharp, minor grain"}
      },
      "suggestions": "Could improve sharpness slightly",
      "comparison_mode": "text"
    }
  }
}
```

---

## How It Works

### Text-Based QA (Preset Styles)

Vision API evaluates image against text checklist:
- Reads checklist requirements
- Analyzes generated image
- Scores each criterion (0-10)
- Provides detailed feedback

### Visual Comparison QA (Reference Images)

Vision API sees BOTH images:
- Reference image (target style)
- Generated image (to evaluate)
- Compares them visually
- More accurate than text-based

**Example:** "Does this generated robot match the blue metallic style of the reference robot?"

---

## Day 19 Tasks Completed

✅ Integrate vision model (GPT-4o-mini with vision)
✅ Send generated images for evaluation
✅ Define quality checklist (6 criteria)
✅ Implement generate → analyze → score pipeline
✅ Discard/flag images below threshold
✅ Support both text-based and visual comparison QA
✅ Detailed feedback and suggestions

