import { createClient } from '@supabase/supabase-js';

// Only import this module from server code. Never expose the secret key in NEXT_PUBLIC variables.
export function getServerDatabase() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SECRET_KEY;
  if (!url || !key) throw new Error('Missing Supabase server configuration');
  return createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false }, db: { schema: 'paycheckrb' } });
}
