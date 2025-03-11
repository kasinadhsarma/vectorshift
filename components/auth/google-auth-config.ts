// Google OAuth configuration
export const GOOGLE_CONFIG = {
  client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
  redirect_uri: 'http://localhost:8000/auth/google/callback',
  scope: 'openid email profile',
  response_type: 'code',
  access_type: 'offline',
  prompt: 'consent'
}
