import Link from 'next/link';

const features = [
  { icon: '◷', title: 'Registro de ponto', detail: 'Entradas, saídas e horas trabalhadas em um só lugar.' },
  { icon: '▤', title: 'Funcionários', detail: 'Organização da equipe e das classificações profissionais.' },
  { icon: '$', title: 'Pagamentos', detail: 'Resumo de horas e valores para conferência.' },
];
const roles = [
  ['Ajudante', '$20/h'], ['Taper', '$28/h'],
  ['Drywall Nível 1', '$25/h'], ['Drywall Nível 2', '$32/h'],
];
export default function Home() {
  return <main style={{minHeight:'100vh',background:'#f5f7fb',color:'#17243b',fontFamily:'Arial, sans-serif'}}>
    <header style={{maxWidth:1120,margin:'auto',padding:'25px 24px',display:'flex',justifyContent:'space-between',alignItems:'center',gap:12,flexWrap:'wrap'}}>
      <strong style={{fontSize:23,letterSpacing:'-.7px'}}>Paycheck<span style={{color:'#2563eb'}}>RB</span></strong>
      <Link href="/login" style={{textDecoration:'none',background:'#17243b',color:'white',padding:'12px 20px',borderRadius:12,fontWeight:700}}>Entrar</Link>
    </header>
    <section style={{maxWidth:1120,margin:'auto',padding:'70px 24px 48px',display:'grid',gap:22}}>
      <div style={{color:'#2563eb',fontSize:13,fontWeight:800,letterSpacing:2}}>NOVA EXPERIÊNCIA WEB</div>
      <h1 style={{fontSize:'clamp(36px, 7vw, 66px)',lineHeight:1.08,letterSpacing:'-2px',maxWidth:800,margin:0}}>Controle de equipe e pagamentos, sem complicação.</h1>
      <p style={{fontSize:19,lineHeight:1.6,color:'#53627b',maxWidth:670,margin:0}}>Uma nova interface para acompanhar funcionários, registros de ponto e cálculos de pagamento, no celular ou computador.</p>
      <div><Link href="/login" style={{display:'inline-block',textDecoration:'none',background:'#2563eb',color:'white',padding:'16px 26px',borderRadius:13,fontWeight:700}}>Acessar minha conta →</Link></div>
      <p style={{fontSize:13,color:'#6a7890'}}>Versão em desenvolvimento. As operações de ponto e pagamento ainda não estão liberadas.</p>
    </section>
    <section style={{maxWidth:1120,margin:'auto',padding:'25px 24px 65px'}}>
      <h2 style={{fontSize:26,marginBottom:22}}>O que estamos construindo</h2>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit, minmax(220px, 1fr))',gap:16}}>
        {features.map(f=><article key={f.title} style={{background:'white',border:'1px solid #e5eaf2',borderRadius:18,padding:25,boxShadow:'0 6px 25px #182f5110'}}>
          <div style={{fontSize:28,color:'#2563eb',marginBottom:16}}>{f.icon}</div>
          <h3 style={{margin:'0 0 10px'}}>{f.title}</h3><p style={{lineHeight:1.6,color:'#64748b',margin:0}}>{f.detail}</p>
        </article>)}
      </div>
      <h2 style={{fontSize:24,margin:'44px 0 18px'}}>Classificações do sistema original</h2>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit, minmax(180px, 1fr))',gap:12}}>
        {roles.map(([name,rate])=><div key={name} style={{background:'#eaf0fb',borderRadius:12,padding:18}}><div style={{fontWeight:700}}>{name}</div><div style={{color:'#2563eb',marginTop:8}}>{rate}</div></div>)}
      </div>
      <p style={{color:'#64748b',fontSize:13,marginTop:14}}>Valores de referência extraídos do aplicativo original; não representam registros reais de pagamento.</p>
    </section>
  </main>;
}
