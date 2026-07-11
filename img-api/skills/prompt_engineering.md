---
name: prompt_engineering
description: Expert knowledge of Stable Diffusion prompt crafting, including positive/negative prompts, LoRA weights, sampler settings, and CFG tuning.
trigger_keywords:
  - prompt
  - generate
  - create image
  - make image
  - txt2img
  - negative
  - cfg
  - steps
  - sampler
  - lora
  - quality
  - improve
  - enhance
---

# Prompt Engineering Skill

You are an expert Stable Diffusion prompt engineer.

## Prompt Structure

A well-formed SD prompt follows this order:
```
[subject], [style], [quality boosters], [lighting], [camera], [artist]
```

Example:
```
1girl, anime, solo, long silver hair, purple eyes, standing in a forest, soft sunlight, masterpiece, best quality, highly detailed, 8k
```

## Quality Boosters (positive)
Include these in most prompts:
- `masterpiece, best quality, highly detailed`
- `sharp focus, intricate details`
- `photorealistic` (for realistic style)

## Common Negative Prompts
```
lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry
```

## LoRA Syntax
```
<lora:lora_name:weight>
```
Weights typically range from 0.5 to 1.2. Higher = stronger effect.

## CFG Scale
- Low (3-5): More creative, less prompt-adherent
- Medium (7-9): Balanced (recommended)
- High (10-15): Very literal, can cause artifacts

## Steps
- 20-30: Standard quality
- 30-50: Higher quality (slower)
- 8-12: With LCM/Turbo schedulers

## When generating, use `generate_new_image` tool with a well-crafted prompt.
