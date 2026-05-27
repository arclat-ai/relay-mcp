import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(req: NextRequest) {
  const token = req.cookies.get('sb-access-token');
  const { pathname } = req.nextUrl;

  const protectedRoutes = ['/upload', '/dashboard'];

  // Check if trying to access a protected route without a token
  if (!token && protectedRoutes.some(route => pathname.startsWith(route))) {
    const url = req.nextUrl.clone();
    url.pathname = '/auth/login';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
