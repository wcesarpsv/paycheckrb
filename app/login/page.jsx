'use client';
import { useState } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);
export default function Login() {
  const [email,setEmail]=useState(''); const [password,setPassword]=useState('');
  const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  async function submit(e){
    e.preventDefault();setBusy(true);setError('');
    try {
      const {data,error:authError}=await supabase.auth.signInWithPassword({email,password});
      if(authError) throw new Error('E-mail ou senha inválidos.');
      const response=await fetch('/api/me',{headers:{Authorization:'Bearer '+data.session.access_token},cache:'no-store'});
      if(!response.ok){await supabase.auth.signOut();throw new Error('Usuário sem acesso ativo ao PaycheckRB.');}
      window.location.assign('/dashboard');
    }catch(err){setError(err.message)}finally{setBusy(false)}
  }
  return <main style={{maxWidth:420,margin:'10vh auto',padding:28,background:'white',borderRadius:16,boxShadow:'0 8px 30px #0001'}}>
    <h1>PaycheckRB</h1><p>Acesse sua conta para registrar seu ponto.</p>
    <form onSubmit={submit} style={{display:'grid',gap:14}}>
      <label>E-mail<input type="email" required autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} style={{display:'block',width:'100%',padding:12,boxSizing:'border-box'}} /></label>
      <label>Senha<input type="password" required autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} style={{display:'block',width:'100%',padding:12,boxSizing:'border-box'}} /></label>
      {error&&<p role="alert" style={{color:'#b42318'}}>{error}</p>}
      <button disabled={busy} style={{padding:14,border:0,borderRadius:8,background:'#2055ca',color:'white'}}>{busy?'Entrando...':'Entrar'}</button>
    </form><p style={{fontSize:12,color:'#667085'}}>Contas são cadastradas pelo administrador.</p>
  </main>;
}
