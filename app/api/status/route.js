import { NextResponse } from 'next/server';
import { getServerDatabase } from '../../../lib/supabase';
export async function GET() {
  try {
    const db = getServerDatabase();
    const { error } = await db.from('roles').select('id', { head: true, count: 'exact' });
    if (error) throw error;
    return NextResponse.json({ app: 'PaycheckRB', database: 'connected' });
  } catch (e) {
    console.error('Database health check failed', e.message);
    return NextResponse.json({ app: 'PaycheckRB', database: 'unavailable' }, { status: 503 });
  }
}
