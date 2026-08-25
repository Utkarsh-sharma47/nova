import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ApiClientError,
  getDocument,
  getDocumentDecision,
  getDocumentValidation,
} from '../api'
import type { DecisionResult, ValidationResult } from '../api/types'
import { DecisionPanel } from '../components/DecisionPanel'
import { DocumentPreview } from '../components/DocumentPreview'
import { EmptyState } from '../components/EmptyState'
import { ErrorPanel } from '../components/ErrorPanel'
import { FieldTable } from '../components/FieldTable'
import { LoadingState } from '../components/LoadingState'
import { StatusBadge } from '../components/StatusBadge'
import { ValidationChecks } from '../components/ValidationChecks'
import { useAsync } from '../hooks/useAsync'
import { formatTimestamp } from '../utils/status'

export function DocumentPage() {
  const { documentId = '' } = useParams()
  const [validation, setValidation] = useState<ValidationResult | null>(null)
  const [decision, setDecision] = useState<DecisionResult | null>(null)
  const [subResourceError, setSubResourceError] = useState<string | null>(null)
  const [validationLoading, setValidationLoading] = useState(false)
  const [decisionLoading, setDecisionLoading] = useState(false)

  const loadDocument = useCallback(
    () => getDocument(documentId),
    [documentId],
  )

  const docState = useAsync(loadDocument, [documentId], {
    enabled: Boolean(documentId),
  })

  useEffect(() => {
    if (docState.status !== 'success') {
      setValidation(null)
      setDecision(null)
      setValidationLoading(false)
      setDecisionLoading(false)
      return
    }

    let cancelled = false
    setValidationLoading(true)
    setDecisionLoading(true)
    setSubResourceError(null)
    setValidation(null)
    setDecision(null)

    void Promise.allSettled([
      getDocumentValidation(documentId),
      getDocumentDecision(documentId),
    ]).then(([validationResult, decisionResult]) => {
      if (cancelled) {
        return
      }

      if (validationResult.status === 'fulfilled') {
        setValidation(validationResult.value)
      } else if (
        !(validationResult.reason instanceof ApiClientError &&
          validationResult.reason.status === 404)
      ) {
        setSubResourceError(
          validationResult.reason instanceof Error
            ? validationResult.reason.message
            : 'Failed to load validation',
        )
      }

      if (decisionResult.status === 'fulfilled') {
        setDecision(decisionResult.value)
      } else if (
        !(decisionResult.reason instanceof ApiClientError &&
          decisionResult.reason.status === 404)
      ) {
        setSubResourceError(
          decisionResult.reason instanceof Error
            ? decisionResult.reason.message
            : 'Failed to load decision',
        )
      }

      setValidationLoading(false)
      setDecisionLoading(false)
    })

    return () => {
      cancelled = true
    }
  }, [docState.status, documentId])

  if (!documentId) {
    return <EmptyState message="Document ID is required." />
  }

  if (docState.status === 'loading' || docState.status === 'idle') {
    return <LoadingState label="Loading document…" />
  }

  if (docState.status === 'error') {
    return (
      <ErrorPanel
        title="Failed to load document"
        message={docState.error.message}
        code={
          docState.error instanceof ApiClientError
            ? docState.error.code
            : undefined
        }
        traceId={
          docState.error instanceof ApiClientError
            ? docState.error.traceId
            : undefined
        }
        retryable={
          docState.error instanceof ApiClientError
            ? docState.error.retryable
            : true
        }
        onRetry={() => docState.reload()}
      />
    )
  }

  const doc = docState.data
  const hasUncertainValidation =
    validation?.overall_result === 'UNCERTAIN' ||
    validation?.checks.some((check) => check.result === 'UNCERTAIN')

  return (
    <>
      <h1>Document {doc.document_id}</h1>

      <section className="panel">
        <dl className="meta-list">
          <dt>Status</dt>
          <dd>
            <StatusBadge status={doc.status} showLifecycle />
          </dd>
          <dt>Customer</dt>
          <dd>{doc.customer_id}</dd>
          <dt>Shipment</dt>
          <dd>
            <Link to={`/shipments/${doc.shipment_id}`}>{doc.shipment_id}</Link>
          </dd>
          <dt>Type</dt>
          <dd>{doc.document_type ?? '—'}</dd>
          <dt>Run ID</dt>
          <dd>{doc.run_id ?? '—'}</dd>
          <dt>Created</dt>
          <dd>{formatTimestamp(doc.created_at)}</dd>
          <dt>Updated</dt>
          <dd>{formatTimestamp(doc.updated_at)}</dd>
          {doc.content ? (
            <>
              <dt>Content</dt>
              <dd>
                {doc.content.media_type}, {doc.content.size_bytes} bytes
              </dd>
            </>
          ) : null}
        </dl>
      </section>

      <DocumentPreview
        documentId={doc.document_id}
        mediaType={doc.content?.media_type}
        filename={doc.content?.filename}
        sizeBytes={doc.content?.size_bytes}
      />

      {doc.status === 'FAILED' && doc.failures?.length ? (
        <section className="panel panel--danger">
          <h2>Processing failures</h2>
          <ul>
            {doc.failures.map((failure, index) => (
              <li key={`${failure.code ?? 'failure'}-${index}`}>
                {failure.stage ? `[${failure.stage}] ` : ''}
                {failure.message ?? failure.code ?? 'Unknown failure'}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="panel">
        <h2>Extraction</h2>
        {doc.extraction?.fields?.length ? (
          <FieldTable fields={doc.extraction.fields} />
        ) : (
          <EmptyState message="Extraction not available for this document." />
        )}
      </section>

      {subResourceError ? (
        <ErrorPanel message={subResourceError} title="Sub-resource error" />
      ) : null}

      <section
        className={hasUncertainValidation ? 'panel panel--highlight' : 'panel'}
      >
        {validationLoading ? (
          <LoadingState label="Loading validation…" />
        ) : validation ? (
          <ValidationChecks
            checks={validation.checks}
            overallResult={validation.overall_result}
          />
        ) : (
          <EmptyState
            title="Validation"
            message="Validation results are not yet available."
          />
        )}
      </section>

      <DecisionPanel
        decision={decision}
        loading={decisionLoading}
        notAvailableMessage="Routing decision is not yet available."
      />
    </>
  )
}
