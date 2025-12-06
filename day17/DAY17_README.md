# Day 17 — Image Generation

AI-powered image generation integrated into Day 16 Knowledge Base UI.

## Features

### 🎨 Image Generation
- Generate images using fal.ai API
- Multiple models: Flux Pro/Dev/Schnell, SDXL
- Full parameter control:
  - **Prompt**: Text description
  - **Model**: 4 models with different speed/quality/cost
  - **Size**: 6 aspect ratios (landscape, portrait, square)
  - **Steps**: Quality control (inference steps)
  - **Seed**: Reproducibility

### 📊 Logging & Stats
- Every generation logged with:
  - Model name and ID
  - All parameters
  - Response latency
  - Cost estimate
  - Success/failure status
- Aggregated statistics
- Recent logs view

## Quick Start

```bash
cd day17
python3 app.py
```

Open: http://127.0.0.1:5010/rag

## Usage

1. **Switch to Image Mode**
   - Click "🎨 Generate Image" tab

2. **Enter Prompt**
   ```
   a cute cat wearing sunglasses on a beach, sunset, highly detailed
   ```

3. **Configure Options** (optional)
   - Model: flux-schnell (default, fast & cheap)
   - Size: landscape_4_3 (default)
   - Steps: 0 = model default
   - Seed: enable for reproducible results

4. **Generate**
   - Click "🎨 Generate Image"
   - Wait 5-30 seconds
   - View result with metadata

5. **View Stats**
   - Click "📊 View Stats"
   - See total generations, costs, latency

## Models

| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| `flux-schnell` | ⚡⚡⚡ Fastest | Good | $0.003 |
| `flux-dev` | ⚡⚡ Fast | Great | $0.025 |
| `flux-pro` | ⚡ Slower | Best | $0.055 |
| `sdxl` | ⚡⚡⚡ Very Fast | Good | $0.002 |

## Size Options

- `landscape_4_3`: 1024×768 (default)
- `landscape_16_9`: 1024×576
- `square`: 512×512
- `square_hd`: 1024×1024
- `portrait_4_3`: 768×1024
- `portrait_16_9`: 576×1024

## API Endpoints

### Generate Image
```http
POST /api/image/generate
Content-Type: application/json

{
  "prompt": "a beautiful sunset over mountains",
  "model": "flux-schnell",
  "size": "landscape_4_3",
  "steps": 20,
  "seed": 42
}
```

### Get Statistics
```http
GET /api/image/stats
```

### Get Logs
```http
GET /api/image/logs?limit=10
```

### List Models
```http
GET /api/image/models
```

## Files Added

- `image_generator.py` - Core image generation logic
- `logger.py` - Generation logging system
- `image_routes.py` - API endpoints
- `static/image-gen.js` - Frontend JavaScript
- `static/rag.css` - Updated styles with image mode

## Configuration

API key is in `.env`:
```
FAL_KEY=your_api_key_here
```

## Integration

Image generation is integrated into the Knowledge Base page:
- **Mode Selector**: Switch between RAG Search and Image Generation
- **Shared UI**: Uses same layout and styling
- **Independent**: RAG and Image modes work separately

## Example Prompts

```
a cute cat wearing sunglasses on a beach, sunset
cyberpunk city at night with neon lights, highly detailed
abstract geometric art with vibrant colors
futuristic robot in a neon city, cinematic lighting
oil painting of a medieval castle, detailed
```

## Tips

1. **Start with flux-schnell** for fast iteration
2. **Use seed** for reproducible results
3. **Check stats** to monitor usage and costs
4. **Higher steps** = better quality but slower
5. **Try different models** for different use cases

## Requirements

- Python 3.9+
- fal.ai API key (configured in `.env`)
- All dependencies from `requirements.txt`

## Navigation

- **Voice Agent**: http://127.0.0.1:5010/
- **Knowledge Base + Image Gen**: http://127.0.0.1:5010/rag

## Day 17 Tasks Completed

✅ Connect to image model (fal.ai)
✅ Implement parameters: prompt, size, quality/steps, seed
✅ Log for each request:
  - Model name
  - Input parameters
  - Response latency
  - Cost estimate
✅ UI integration with mode selector
✅ Statistics and history tracking
