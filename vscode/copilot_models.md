Here’s a concise summary of the available models based on the raw API response:

---

### Model Overview
- **Total Models:** 44  
- **Chat Models:** 40  
- **Completion Models:** 1  
- **Embedding Models:** 3  
- **Premium Models (require paid plan):** 21  
- **Preview Models:** 7  
- **Default Chat Model:** `gpt-5-mini`  
- **Fallback Chat Model:** `gpt-4.1`

---

### Notable Models by Vendor

#### Anthropic
- **Claude Opus 4.6 (fast mode)** – premium, high multiplier (30), 200k context, supports reasoning.
- **Claude Opus 4.6** – premium (multiplier 3), same limits.
- **Claude Sonnet 4.6** – premium (multiplier 1), 200k context, 5 images.
- **Claude Haiku 4.5** – premium (multiplier 0.33), 200k context.
- Legacy Claude Sonnet 4/4.5 and Opus 4.5 are also listed but disabled in picker.

#### OpenAI
- **GPT-5.3‑Codex** – premium, 400k context, supports `reasoning_effort` up to `xhigh`.
- **GPT-5.4** – premium, same high limits.
- **GPT-5.4 mini** – premium (multiplier 0.33), lightweight category.
- **GPT-5.2** – premium, versatile, 264k context.
- **GPT-5.1, 5.1‑Codex, 5.1‑Codex‑Mini, 5.1‑Codex‑Max** – all have deprecation notices in April 2026.
- **GPT-5 mini** – free, default model, 264k context, supports reasoning and vision.
- **GPT‑4.1** – free, fallback model, 128k context, vision.
- **GPT‑4o** – free, versatile, 128k context, vision.

#### Google
- **Gemini 3.1 Pro** – premium preview, 128k context, supports reasoning.
- **Gemini 3 Flash** – premium preview, lightweight, 128k context.
- **Gemini 2.5 Pro** – premium, powerful category, 128k context.

#### xAI
- **Grok Code Fast 1** – premium (multiplier 0.25), lightweight, 128k context, no vision.

#### Microsoft / Azure
- **Goldeneye** (free preview) – 400k context, vision, only `/responses` endpoint.
- **Raptor mini (Preview)** – free, versatile, 264k context, vision.

---

### Pricing & Access
- **Free models:** GPT‑5 mini, GPT‑4.1, GPT‑4o, Raptor mini, older GPT‑4/3.5 models, embedding models.
- **Premium models** have multipliers ranging from 0.25 (Grok) to 30 (Claude Opus 4.6 fast).  
- Some premium models are restricted to specific subscription tiers (e.g., `pro_plus`, `enterprise`).

---

### Deprecations
- **GPT‑5.1‑Codex**, **GPT‑5.1‑Codex‑Mini**, and **GPT‑5.1‑Codex‑Max** are scheduled for deprecation on **2026‑04‑01**.
- **GPT‑5.1** is scheduled for deprecation on **2026‑04‑15**.

---

### Capabilities Highlights
- Most new models support **tool calls**, **streaming**, and **structured outputs**.
- **Vision** is supported by many models (Claude Sonnet 4.6, GPT‑5.2, Gemini 2.5 Pro, etc.) with limits on image count and size.
- **Reasoning / thinking** is supported in Claude models (adaptive thinking budget up to 32k tokens) and GPT‑5 models (`reasoning_effort` parameter).

---

Let me know if you need a deeper breakdown of any specific model or category.
