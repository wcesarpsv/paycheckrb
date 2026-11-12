import { NextResponse } from 'next/server';
import { getCurrentEmployee } from '../../../lib/auth';

export async function GET(request) {
  try {
    const employee = await getCurrentEmployee(request);
    if (!employee) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    return NextResponse.json({ employee });
  } catch (error) {
    console.error('Auth verification error', error.message);
    return NextResponse.json({ error: 'Service unavailable' }, { status: 503 });
  }
}
