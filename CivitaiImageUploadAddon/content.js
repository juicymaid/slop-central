(async function() {
  const urlParams = new URLSearchParams(window.location.search);
  const imagePath = urlParams.get('path');

  if (!imagePath) {
    console.log("[Civitai Upload Helper] No 'path' query parameter found. Doing nothing.");
    return;
  }

  console.log("[Civitai Upload Helper] Found path to upload:", imagePath);

  // Create UI overlay
  const overlay = document.createElement('div');
  overlay.style.position = 'fixed';
  overlay.style.bottom = '20px';
  overlay.style.right = '20px';
  overlay.style.padding = '15px 25px';
  overlay.style.backgroundColor = '#1a1b1e';
  overlay.style.color = '#fff';
  overlay.style.border = '1px solid #373a40';
  overlay.style.borderRadius = '8px';
  overlay.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.5)';
  overlay.style.fontFamily = 'sans-serif';
  overlay.style.zIndex = '999999';
  overlay.style.display = 'flex';
  overlay.style.flexDirection = 'column';
  overlay.style.gap = '8px';
  overlay.style.fontSize = '14px';

  const title = document.createElement('div');
  title.style.fontWeight = 'bold';
  title.textContent = 'Civitai Image Upload Helper';
  overlay.appendChild(title);

  const status = document.createElement('div');
  status.textContent = 'Preparing...';
  status.style.color = '#a6a7ab';
  overlay.appendChild(status);

  document.body.appendChild(overlay);

  function updateStatus(text, color = '#a6a7ab') {
    status.textContent = text;
    status.style.color = color;
    console.log("[Civitai Upload Helper]", text);
  }

  // Helper to wait for the input element
  function waitForInput(selector, timeout = 15000) {
    return new Promise((resolve, reject) => {
      const el = document.querySelector(selector);
      if (el) return resolve(el);

      const observer = new MutationObserver(() => {
        const el = document.querySelector(selector);
        if (el) {
          resolve(el);
          observer.disconnect();
        }
      });
      observer.observe(document.documentElement, { childList: true, subtree: true });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`Timeout waiting for file input "${selector}"`));
      }, timeout);
    });
  }

  try {
    // 1. Fetch file from local backend
    updateStatus(`Fetching file from backend: ${imagePath}`);
    const backendUrl = `http://localhost:8000/view-local-file?path=${encodeURIComponent(imagePath)}`;
    const response = await fetch(backendUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch file from local backend: ${response.statusText} (${response.status})`);
    }

    const blob = await response.blob();
    const filename = imagePath.split(/[/\\]/).pop() || 'image.png';
    const mimeType = response.headers.get('content-type') || blob.type || 'image/png';
    const file = new File([blob], filename, { type: mimeType });

    updateStatus(`Fetched file: ${filename} (${(blob.size / 1024 / 1024).toFixed(2)} MB). Waiting for file input...`);

    // 2. Wait for the upload input
    const inputSelector = 'input[type="file"][accept*="image"]';
    const fileInput = await waitForInput(inputSelector);

    updateStatus('Input element found. Injecting file...', '#4dabf7');

    // 3. Set files on input
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;

    // 4. Trigger change events to notify React/Mantine
    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
    fileInput.dispatchEvent(new Event('input', { bubbles: true }));

    updateStatus('Upload triggered successfully!', '#40c057');
    setTimeout(() => {
      overlay.style.transition = 'opacity 1s';
      overlay.style.opacity = '0';
      setTimeout(() => overlay.remove(), 1000);
    }, 3000);

  } catch (error) {
    updateStatus(`Error: ${error.message}`, '#fa5252');
  }
})();
