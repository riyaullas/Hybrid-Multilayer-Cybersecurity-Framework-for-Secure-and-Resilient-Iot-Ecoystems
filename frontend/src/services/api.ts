const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
let token = sessionStorage.getItem('ms_token') || '';
export function setToken(value:string){token=value; if(value)sessionStorage.setItem('ms_token',value);else sessionStorage.removeItem('ms_token')}
export function getToken(){return token}
export async function api<T=any>(path:string, options:RequestInit={}):Promise<T>{
 const headers:Record<string,string>={'Content-Type':'application/json',...(options.headers as Record<string,string>||{})}; if(token)headers.Authorization=`Bearer ${token}`;
 const res=await fetch(`${BASE}${path}`,{...options,headers}); if(!res.ok){let message=`Request failed (${res.status})`;try{const j=await res.json();message=j.detail||message}catch{} throw new Error(message)}
 return res.json();
}
export async function login(username:string,password:string){const r=await api<any>('/auth/login',{method:'POST',body:JSON.stringify({username,password})});setToken(r.access_token);return r.user}
