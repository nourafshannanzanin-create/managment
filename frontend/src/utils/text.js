export function cleanDisplayText(value) {
  return String(value ?? '')
    .replace(/\s+/g, ' ')
    .replace(/\s*[-–—]+\s*/g, ' - ')
    .replace(/\s*[·•]+\s*/g, ' · ')
    .trim()
}

export function joinDisplayParts(parts, separator = ' - ') {
  return (parts || [])
    .map((item) => cleanDisplayText(item))
    .filter(Boolean)
    .join(separator)
}
