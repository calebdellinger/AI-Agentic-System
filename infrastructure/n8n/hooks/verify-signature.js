/**
 * Rationale: Webhook authenticity prevents unauthorized work orders.
 *
 * How:
 * - Validate shared secret from Trinity against expected local secret.
 * - Support common header key variations for compatibility.
 *
 * Contracts:
 * - Expects `X-WorkOrder-Secret` (or similar header) from Trinity.
 * - Does not log secrets; only logs event-level metadata.
 */

export function verifyWorkOrderSignature({ headers, body, expectedSecret }) {
  void body;

  if (!expectedSecret || typeof expectedSecret !== "string") {
    return false;
  }

  const normalizedHeaders = normalizeHeaders(headers);
  const incoming =
    normalizedHeaders["x-workorder-secret"] ||
    normalizedHeaders["x_workorder_secret"] ||
    normalizedHeaders["x-trinity-workorder-secret"] ||
    "";

  if (typeof incoming !== "string" || incoming.length === 0) {
    return false;
  }

  return timingSafeEqual(incoming, expectedSecret);
}

function normalizeHeaders(headers) {
  if (!headers || typeof headers !== "object") {
    return {};
  }
  const out = {};
  for (const [key, value] of Object.entries(headers)) {
    out[String(key).toLowerCase()] = String(value);
  }
  return out;
}

function timingSafeEqual(a, b) {
  const aBytes = new TextEncoder().encode(a);
  const bBytes = new TextEncoder().encode(b);

  if (aBytes.length !== bBytes.length) {
    return false;
  }

  let diff = 0;
  for (let i = 0; i < aBytes.length; i += 1) {
    diff |= aBytes[i] ^ bBytes[i];
  }
  return diff === 0;
}

