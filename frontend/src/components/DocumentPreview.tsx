import { useEffect, useState } from 'react'
import { fetchDocumentContentBlob } from '../api'
import { EmptyState } from './EmptyState'
import { ErrorPanel } from './ErrorPanel'
import { LoadingState } from './LoadingState'

interface DocumentPreviewProps {
  documentId: string
  mediaType?: string | null
  filename?: string | null
  sizeBytes?: number | null
}

export function DocumentPreview({
  documentId,
  mediaType,
  filename,
  sizeBytes,
}: DocumentPreviewProps) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null)
  const [textBody, setTextBody] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [resolvedType, setResolvedType] = useState<string | null>(mediaType ?? null)

  useEffect(() => {
    let cancelled = false
    let createdUrl: string | null = null

    setLoading(true)
    setError(null)
    setTextBody(null)
    setObjectUrl(null)

    void fetchDocumentContentBlob(documentId)
      .then(async ({ blob, mediaType: contentType }) => {
        if (cancelled) {
          return
        }
        const type = contentType || mediaType || blob.type || 'application/octet-stream'
        setResolvedType(type)
        if (type.startsWith('text/') || type === 'application/json') {
          setTextBody(await blob.text())
          return
        }
        createdUrl = URL.createObjectURL(blob)
        setObjectUrl(createdUrl)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load document content',
          )
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl)
      }
    }
  }, [documentId, mediaType])

  const type = resolvedType ?? mediaType ?? 'unknown'
  const isPdf = type.includes('pdf')
  const isImage = type.startsWith('image/')

  return (
    <section className="panel">
      <h2>Document</h2>
      <p className="form-hint">
        {filename ?? 'Stored document'} · {type}
        {typeof sizeBytes === 'number' ? ` · ${sizeBytes} bytes` : ''}
        {objectUrl ? (
          <>
            {' '}
            ·{' '}
            <a href={objectUrl} download={filename ?? undefined}>
              Download
            </a>
          </>
        ) : null}
      </p>
      {loading ? <LoadingState label="Loading document content…" /> : null}
      {error ? <ErrorPanel title="Document content" message={error} /> : null}
      {!loading && !error && textBody !== null ? (
        <pre className="document-preview-text">{textBody}</pre>
      ) : null}
      {!loading && !error && objectUrl && isPdf ? (
        <iframe
          className="document-preview-frame"
          title="Document PDF preview"
          src={objectUrl}
        />
      ) : null}
      {!loading && !error && objectUrl && isImage ? (
        <img
          className="document-preview-image"
          src={objectUrl}
          alt={filename ?? 'Uploaded document'}
        />
      ) : null}
      {!loading && !error && objectUrl && !isPdf && !isImage ? (
        <EmptyState message="Preview is not available for this media type. Use Download." />
      ) : null}
      {!loading && !error && textBody === null && !objectUrl ? (
        <EmptyState message="Document content is not available." />
      ) : null}
    </section>
  )
}
