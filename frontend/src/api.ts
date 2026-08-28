export type User = {id:number; username:string; email:string; display_name:string; avatar_url:string; role:'USER'|'CREATOR'};
export type Session = {id:number; creator:{id:number; display_name:string; avatar_url:string}; title:string; description:string; starts_at:string; capacity:number; status:string; active_booking_count:number};
export type Booking = {id:number; session:Session; status:string; booked_at:string};
let accessToken: string | null = null;

const wakeRetryDelays = [2000, 4000, 8000, 12000, 16000, 20000];
const transientGatewayStatuses = new Set([502, 503, 504]);

function cookie(name:string) { return document.cookie.split('; ').find(row => row.startsWith(name + '='))?.split('=')[1]; }

function wait(milliseconds:number) {
  return new Promise(resolve => window.setTimeout(resolve, milliseconds));
}

async function fetchWithWakeRetry(url:string, init:RequestInit, canRetry:boolean) {
  for (let attempt = 0; ; attempt += 1) {
    const response = await fetch(url, init);
    if (!canRetry || !transientGatewayStatuses.has(response.status) || attempt >= wakeRetryDelays.length) {
      return response;
    }
    await wait(wakeRetryDelays[attempt]);
  }
}

export async function ensureCsrf() { await api('/auth/csrf/'); }
export async function api<T>(path:string, init:RequestInit = {}): Promise<T> {
  const method = (init.method || 'GET').toUpperCase();
  const headers = new Headers(init.headers);
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  if (!['GET','HEAD','OPTIONS'].includes(method)) headers.set('X-CSRFToken', decodeURIComponent(cookie('csrftoken') || ''));
  if (init.body) headers.set('Content-Type', 'application/json');
  const response = await fetchWithWakeRetry(
    '/api' + path,
    {...init, method, headers, credentials:'include'},
    ['GET','HEAD','OPTIONS'].includes(method),
  );
  if (!response.ok) { const data = await response.json().catch(() => ({})); throw new Error(data.detail || Object.values(data).flat().join(' ') || `Request failed (${response.status})`); }
  return response.status === 204 ? undefined as T : response.json();
}
export async function restoreSession(): Promise<User | null> { try { const data = await api<{access:string;user:User}>('/auth/refresh/', {method:'POST'}); accessToken=data.access; return data.user; } catch { return null; } }
export async function login() { const {authorization_url} = await api<{authorization_url:string}>('/auth/github/start/'); window.location.assign(authorization_url); }
export async function logout() { await api('/auth/logout/', {method:'POST'}); accessToken=null; }
