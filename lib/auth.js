import { createClient } from '@supabase/supabase-js';
import { getServerDatabase } from './supabase';

// Verify every request with Supabase Auth, never trust a client-supplied employee ID.
export async function getCurrentEmployee(request) {
  const header = request.headers.get('authorization') || '';
  const match = /^Bearer (.+)$/.exec(header);
  if (!match) return null;
  const url = process.env.SUPABASE_URL;
  const publishable = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!url || !publishable) throw new Error('Supabase Auth not configured');
  const authClient = createClient(url, publishable, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: { user }, error } = await authClient.auth.getUser(match[1]);
  if (error || !user) return null;
  const db = getServerDatabase();
  const { data: employee, error: employeeError } = await db.from('employees')
    .select('id,name,email,is_admin,active,role_id').eq('id', user.id).maybeSingle();
  if (employeeError) throw employeeError;
  if (!employee?.active) return null;
  return employee;
}
