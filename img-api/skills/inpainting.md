---
name: inpainting
description: Expert guidance for inpainting and modifying existing images using SAM segmentation and diffusion models.
trigger_keywords:
  - inpaint
  - edit
  - modify
  - change
  - replace
  - remove
  - add to
  - alter
  - fix
---

# Inpainting Skill

You are an expert at using the inpainting pipeline to modify existing images.

## Inpainting Workflow

Use `inpaint_image(image_id, sam_prompt, prompt)`:

1. **image_id**: The ID of the image to modify (from search results or user context).
2. **sam_prompt**: A description of the **region** to replace (e.g. `"clothes"`, `"hair"`, `"background"`, `"face"`, `"hands"`). This drives SAM segmentation.
3. **prompt**: What to replace that region **with** (e.g. `"red dress"`, `"blue short hair"`, `"beach background"`).

## SAM Prompt Tips

- Keep sam_prompt simple and anatomically clear: `"shirt"`, `"pants"`, `"background"`.
- Avoid compound descriptions for sam_prompt — SAM works best with single object labels.
- The generation prompt should describe the full desired result in that region.

## Example

User: "Change her outfit to a bikini"
```
inpaint_image(
  image_id="abc123",
  sam_prompt="clothes",
  prompt="bikini, string bikini, blue, detailed fabric"
)
```

## Best Practices

- Before inpainting, show the original image with `show_image` so the user confirms.
- Use detailed, positive-only prompts for the replacement region.
- If the user says "fix" something, first identify what needs fixing, then inpaint.
