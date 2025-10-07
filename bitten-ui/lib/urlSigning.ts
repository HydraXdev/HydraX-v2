// Secret key for URL signing - in production, this should be from environment
const SIGNING_SECRET = process.env.URL_SIGNING_SECRET || 'bitten-secure-url-signing-key-2025';

// Web Crypto API compatible HMAC function for Edge Runtime
async function createHMAC(secret: string, message: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const messageData = encoder.encode(message);

  const key = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign('HMAC', key, messageData);
  const hashArray = Array.from(new Uint8Array(signature));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

export interface SignedURLParams {
  uid: string;
  path: string;
  t: number; // timestamp
  sig: string; // signature
  [key: string]: any; // additional params like missionId, ticketId
}

/**
 * Sign a URL with HMAC_SHA256 for secure access
 */
export async function signURL(uid: string, path: string, additionalParams: Record<string, any> = {}): Promise<string> {
  const timestamp = Math.floor(Date.now() / 1000);

  // Create signature payload: uid|path|timestamp
  const payload = `${uid}|${path}|${timestamp}`;
  const signature = await createHMAC(SIGNING_SECRET, payload);

  // Build URL with all parameters
  const params = new URLSearchParams({
    uid,
    t: timestamp.toString(),
    sig: signature,
    ...additionalParams
  });

  return `${path}?${params.toString()}`;
}

/**
 * Verify a signed URL
 */
export async function verifySignedURL(searchParams: URLSearchParams, requestPath: string): Promise<{ valid: boolean; uid?: string; expired?: boolean }> {
  const uid = searchParams.get('uid');
  const timestamp = searchParams.get('t');
  const signature = searchParams.get('sig');

  if (!uid || !timestamp || !signature) {
    return { valid: false };
  }

  // Check if expired (5 minutes = 300 seconds)
  const now = Math.floor(Date.now() / 1000);
  const urlTime = parseInt(timestamp);
  const expired = (now - urlTime) > 300;

  if (expired) {
    return { valid: false, expired: true };
  }

  // Verify signature
  const payload = `${uid}|${requestPath}|${urlTime}`;
  const expectedSignature = await createHMAC(SIGNING_SECRET, payload);

  const valid = signature === expectedSignature;
  return { valid, uid: valid ? uid : undefined, expired: false };
}

/**
 * Create a Telegram deep link with signed parameters
 */
export function createTelegramDeepLink(uid: string, page: string, params: Record<string, any> = {}): string {
  const baseURL = process.env.NEXT_PUBLIC_BASE_URL || 'http://134.199.204.67:3000';
  const signedURL = signURL(uid, page, params);
  return `${baseURL}${signedURL}`;
}

/**
 * Validate mission access for user
 */
export async function validateMissionAccess(uid: string, missionId: string): Promise<boolean> {
  // TODO: Implement actual mission validation against database
  // For now, return true for development
  return true;
}

/**
 * Validate ticket access for user
 */
export async function validateTicketAccess(uid: string, ticketId: string): Promise<boolean> {
  // TODO: Implement actual ticket validation against database
  // For now, return true for development
  return true;
}

/**
 * Get latest active mission for user
 */
export async function getLatestMissionForUser(uid: string): Promise<string | null> {
  // TODO: Implement actual mission lookup from database
  // For now, return a sample mission ID
  return `msn-${uid}-${Date.now()}`;
}

/**
 * Get user's active trades
 */
export async function getActiveTradesForUser(uid: string): Promise<string[]> {
  // TODO: Implement actual trade lookup from database
  // For now, return sample ticket IDs
  return [`84231197`, `84231198`];
}