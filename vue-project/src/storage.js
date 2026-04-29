import { apiUrl } from './api'

export async function saveToFile(data, filename) {
  if (data == null) return

  const jsonBlob = new Blob([JSON.stringify(data)], { type: 'application/json' })
  const formData = new FormData()
  formData.append('file', jsonBlob, filename)

  await fetch(`${apiUrl}/save-file?filename=${encodeURIComponent(filename)}`, {
    method: 'POST',
    body: formData,
  })
}

export async function loadFromFile(filename) {
  const response = await fetch(`${apiUrl}/storage-files/${encodeURIComponent(filename)}`)
  if (!response.ok) {
    console.error('Failed to load file:', response.statusText)
    return null
  }
  return await response.json()
}
