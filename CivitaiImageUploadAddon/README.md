# Civitai Image Upload Addon for Firefox

This addon automatically handles uploading images from your local computer to Civitai posts (on `civitai.com` or `civitai.red`) using a file path passed in the `path` query parameter.

## How it works
1. When you navigate to `https://civitai.red/posts/create?path=C:/path/to/your/image.png` (or `civitai.com`), the content script reads the `path` query parameter.
2. It fetches the image bytes from your local Pinthesis/Slop Central backend (`http://localhost:8000/view-local-file?path=...`).
3. It converts the retrieved image bytes into a `File` object and injects it directly into the page's file input.
4. It triggers a `change` event so that the website's upload interface automatically starts the upload process.

## Installation in Firefox (Temporary Extension)
1. Open Firefox.
2. Type `about:debugging` in the address bar and press Enter.
3. Click on **This Firefox** on the left menu.
4. Click on the **Load Temporary Add-on...** button.
5. Navigate to the `CivitaiImageUploadAddon/` directory and select the `manifest.json` file.
6. The addon is now loaded and will work for the current browser session.
