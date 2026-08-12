const MB = 1024 * 1024

export const UPLOAD_LIMITS = {
  defaultMaxBytes: 8 * MB,
  imageMaxBytes: 8 * MB,
  avatarMaxBytes: 5 * MB,
  maxAttachments: 8,
  allowedExtensions: ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.pdf'],
  allowedMimePrefixes: ['image/', 'application/pdf'],
}

export function formatFileSize(bytes = 0) {
  const size = Number(bytes) || 0
  if (size < 1024) return `${size} B`
  if (size < MB) return `${Math.round(size / 1024)} KB`
  return `${(size / MB).toFixed(1)} MB`
}

export function fileExtension(name = '') {
  const match = String(name || '').toLowerCase().match(/(\.[a-z0-9]+)$/)
  return match?.[1] || ''
}

export function isAllowedUpload(file, limits = UPLOAD_LIMITS) {
  const ext = fileExtension(file?.name)
  const mime = String(file?.type || '').toLowerCase()
  const allowedExt = limits.allowedExtensions.includes(ext)
  const allowedMime = limits.allowedMimePrefixes.some((prefix) => mime.startsWith(prefix))
  return allowedExt || allowedMime
}

export function validateUploadFile(file, limits = UPLOAD_LIMITS) {
  if (!file) {
    return 'فایلی انتخاب نشده است.'
  }
  if (!isAllowedUpload(file, limits)) {
    return 'فقط تصویر (JPG، PNG، WEBP) یا PDF مجاز است.'
  }
  const maxBytes = limits.defaultMaxBytes || UPLOAD_LIMITS.defaultMaxBytes
  if (Number(file.size || 0) > maxBytes) {
    return `حجم فایل نباید بیشتر از ${formatFileSize(maxBytes)} باشد.`
  }
  return ''
}

export async function compressImageFile(
  file,
  { maxWidth = 1920, maxHeight = 1920, quality = 0.84, targetMaxBytes = 4 * MB } = {},
) {
  if (!file || !String(file.type || '').startsWith('image/')) return file
  if (file.size <= targetMaxBytes) return file

  return new Promise((resolve) => {
    const objectUrl = URL.createObjectURL(file)
    const image = new Image()

    image.onload = () => {
      URL.revokeObjectURL(objectUrl)
      const ratio = Math.min(maxWidth / image.width, maxHeight / image.height, 1)
      const width = Math.max(1, Math.round(image.width * ratio))
      const height = Math.max(1, Math.round(image.height * ratio))
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const context = canvas.getContext('2d')
      if (!context) {
        resolve(file)
        return
      }
      context.drawImage(image, 0, 0, width, height)
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            resolve(file)
            return
          }
          const nextName = String(file.name || 'attachment').replace(/\.[^.]+$/, '') + '.jpg'
          const compressed = new File([blob], nextName, {
            type: 'image/jpeg',
            lastModified: Date.now(),
          })
          resolve(compressed.size < file.size ? compressed : file)
        },
        'image/jpeg',
        quality,
      )
    }

    image.onerror = () => {
      URL.revokeObjectURL(objectUrl)
      resolve(file)
    }

    image.src = objectUrl
  })
}

export async function prepareUploadFile(file, limits = UPLOAD_LIMITS) {
  const validationError = validateUploadFile(file, limits)
  if (validationError) {
    throw new Error(validationError)
  }
  const prepared = await compressImageFile(file, {
    targetMaxBytes: Math.min(limits.imageMaxBytes || limits.defaultMaxBytes, 4 * MB),
  })
  const postValidationError = validateUploadFile(prepared, limits)
  if (postValidationError) {
    throw new Error(postValidationError)
  }
  return prepared
}
