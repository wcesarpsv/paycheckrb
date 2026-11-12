'use client';
import { useEffect,useState } from 'react';
import { createClient } from '@supabase/supabase-js';
const supabase=createClient(process.env.NEXT_PUBLIC_SUPABASE_URL,process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);
export default function Dashboard(){
 const [employee,setEmployee]=useState(null);const [status,setStatus]=useState('Verificando acesso...');
 useEffect(()=>{let alive=true;(async()=>{const {data}=await supabase.auth.getSession();if(!data.session){window.location.replace('/login');return;}
 const r=await fetch('/api/me',{headers:{Authorization:'Bearer '+data.session.access_token},cache:'no-store'});
 if(!alive)return;if(!r.ok){setStatus('Acesso não autorizado.');return;}const j=await r.json();setEmployee(j.employee);setStatus('');})();return()=>{alive=false}},[]);
 async function logout(){await supabase.auth.signOut();window.location.replace('/login')}
 return <main style={{maxWidth:780,margin:'8vh auto',padding:24}}><h1>PaycheckRB</h1>{employee?<><p>Bem-vindo, {employee.name}.</p><p>Perfil: {employee.is_admin?'Administrador':'Funcionário'}</p><p>Os registros de ponto e relatórios estão sendo migrados e ainda não estão disponíveis nesta versão de teste.</p><button onClick={logout}>Sair</button></>:<p>{status}</p>}</main>
}
