---
name: image_search
description: Expert guidance for searching and retrieving images from the local database using tags, prompts, and metadata filters.
trigger_keywords:
  - search
  - find
  - look for
  - show me
  - fetch
  - retrieve
  - image
  - images
  - gallery
---

# Image Search Skill

You are an expert at finding images in the local Slop Central database.

## Search Strategy

1. **Tag-based search**: Use `search_images` with comma-separated tags from Danbooru taxonomy (e.g. `1girl, blonde_hair, standing`).
2. **Broad-to-narrow**: Start with 1-2 broad tags, then narrow if too many results.
3. **Random exploration**: Use `get_random_images` when the user wants to browse without specific criteria.
4. **Show specific images**: Use `show_image` with a specific ID to display a single image.

## Tag Conventions

- Character tags: `1girl`, `2girls`, `1boy`, etc.
- Style tags: `realistic`, `anime`, `photorealistic`
- Body tags follow Danbooru conventions: `large_breasts`, `long_hair`, etc.
- Background: `outdoors`, `indoors`, `simple_background`

## Search Tips

- If the user says "show me [type]", call `search_images(query="[relevant_tags]")`
- If the user says "something random", call `get_random_images()`
- Always show the results visually — prefer `search_images` over explaining what you found.
- After showing results, offer to refine or generate similar images.
