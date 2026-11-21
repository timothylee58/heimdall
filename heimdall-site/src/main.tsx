import React,{useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {motion,MotionConfig} from 'framer-motion';
import {ArrowUpRight,ArrowRight,Check,CheckCircle2,Pause,OctagonX,FileText,Layers,GitBranch,Fingerprint,ChevronDown,Plus,RotateCcw,Activity,Terminal,Eye,LockKeyhole} from 'lucide-react';
import {ui,capabilities,verdicts,departments,tiers,tour,scenarios,components,faqs,evidence,type Lang,type Words} from './content';
import {canRecord,validateRequest} from './session';
import './style.css';
const languages:Lang[]=['en','bm','zh'];
type Event={scenario:number;state:'reviewed'|'approved'|'denied'|'suggested'};
type Translator=(words:Words)=>string;
const statusWords={reviewed:ui.reviewed,approved:ui.approved,denied:ui.denied,suggested:ui.suggested};
function Badge({code}:{code:string}){const Icon=code==='BLOCK'?OctagonX:code==='HOLD'?Pause:code==='ALLOW'?CheckCircle2:FileText;return <span className={`badge ${code.toLowerCase()}`}><Icon size={13}/>{code}</span>}
function Brand(){return <a className="brand" href="#/" aria-label="Heimdall"><span className="brand-icon"><i/><i/><i/></span>heimdall<span className="brand-dot">®</span></a>}
function Language({lang,setLang}:{lang:Lang;setLang:(l:Lang)=>void}){return <div className="language" aria-label="EN / BM / 中文">{languages.map((l,i)=><button key={l} onClick={()=>setLang(l)} aria-pressed={lang===l} lang={l==='bm'?'ms':l==='zh'?'zh-CN':'en'} className={lang===l?'selected':''}>{['EN','BM','中文'][i]}</button>)}</div>}
function LinkButton({href,children,secondary=false}:{href:string;children:React.ReactNode;secondary?:boolean}){return <a className={`button ${secondary?'secondary':''}`} href={href}>{children}<ArrowUpRight size={17}/></a>}
function Label({children}:{children:React.ReactNode}){return <div className="eyebrow">{children}</div>}
function Flow({t,compact=false}:{t:Translator;compact?:boolean}){return <div className={`flow ${compact?'compact':''}`}>{[ui.proposal,ui.classify,ui.policy,ui.verdict,ui.audit,ui.briefing].map((a,i)=><React.Fragment key={i}><div><span className="mono">0{i+1}</span><p>{t(a)}</p>{i===2?<GitBranch size={22}/>:i===4?<Fingerprint size={22}/>:<Layers size={22}/>}</div>{i<5&&<ArrowRight className="flow-arrow" size={18}/>}</React.Fragment>)}</div>}
function Policy({t}:{t:Translator}){return <><div className="verdict-list">{verdicts.map((v,i)=><div key={v.code}><span className="index mono">0{i+1}</span><Badge code={v.code}/><p>{t(v.desc)}</p><span className="mono type-tag">{i<3?t(ui.verdict):t(ui.assistance)}</span></div>)}</div><div className="mapping"><Label>{t(ui.mapping)}</Label><div className="mapping-codes"><span>ALLOW <ArrowRight size={16}/> ALLOW</span><span>APPROVE <ArrowRight size={16}/> HOLD</span><span>NEVER <ArrowRight size={16}/> BLOCK</span></div><p>{t(ui.assistNote)}</p></div></>}
function Evidence({t}:{t:Translator}){return <><div className="evidence-columns"><div><CheckCircle2 size={24}/><h3>{t(ui.implemented)}</h3><p>{t(ui.implCopy)}</p></div><div><Eye size={24}/><h3>{t(ui.illustrative)}</h3><p>{t(ui.uiCopy)}</p></div><div><GitBranch size={24}/><h3>{t(ui.planned)}</h3><p>{t(ui.integrationCopy)}</p></div></div><div className="evidence-metrics">{[[ui.metrics,evidence.metrics],[ui.kit,evidence.kit],[ui.intercept,evidence.interception]].map(([a,b],i)=><div key={i}><span>{t(a)}</span><strong><span className="status-dot"/>{t(b)}</strong></div>)}</div></>}
function Teaser({t}:{t:Translator}){const s=scenarios[2];return <a href="#/demo" className="teaser console-surface"><div className="console-top"><span><Activity size={15}/>{t(ui.console)}</span><ArrowUpRight size={18}/></div><div className="teaser-content"><div className="tiny-label">{t(ui.synthetic)}</div><div className="agent-line"><span className="agent-avatar"><GitBranch size={18}/></span>{t(departments[2])}<span className="mono">R18</span></div><p className="teaser-action">{t(s.action)}</p><div className="teaser-divider"/><div className="between"><span className="tiny-label">{t(ui.verdict)}</span><Badge code="BLOCK"/></div><p className="console-muted">{t(s.reason)}</p><div className="suggestion-preview"><FileText size={16}/><span>REWRITE</span><span>{t(ui.assistance)}</span><ArrowRight size={15}/></div><div className="teaser-foot"><span className="mono">data/lumen_public.json</span><Fingerprint size={18}/></div></div><div className="console-bottom">{t(ui.view)}<ArrowRight size={16}/></div></a>}
function Contact({t}:{t:Translator}){const [values,setValues]=useState({name:'',email:'',company:'',message:''});const [errors,setErrors]=useState<Record<string,'required'|'invalidEmail'>>({});const [success,setSuccess]=useState(false);return <section id="walkthrough" className="contact section"><div><Label>06 / {t(ui.walk)}</Label><h2>{t(ui.contactTitle)}</h2><p>{t(ui.contactCopy)}</p><div className="contact-symbol"><GitBranch size={90} strokeWidth={.65}/></div></div><form noValidate onSubmit={e=>{e.preventDefault();const next=validateRequest(values);setErrors(next);if(!Object.keys(next).length)setSuccess(true);}}>{success?<div className="form-success" role="status"><CheckCircle2 size={34}/><h3>{t(ui.success)}</h3><p>{t(ui.contactCopy)}</p><button type="button" className="button secondary" onClick={()=>setSuccess(false)}>{t(ui.edit)}<ArrowRight size={16}/></button></div>:<><div className="form-row">{(['name','email'] as const).map(key=><div key={key}><label htmlFor={key}>{t(ui[key])}</label><input id={key} type={key==='email'?'email':'text'} autoComplete={key} value={values[key]} onChange={e=>setValues({...values,[key]:e.target.value})} aria-invalid={!!errors[key]} aria-describedby={errors[key]?`${key}-error`:undefined}/>{errors[key]&&<small id={`${key}-error`} className="error">{t(ui[errors[key]])}</small>}</div>)}</div><label htmlFor="company">{t(ui.company)}</label><input id="company" autoComplete="organization" value={values.company} onChange={e=>setValues({...values,company:e.target.value})}/><label htmlFor="message">{t(ui.message)}</label><textarea id="message" rows={4} value={values.message} onChange={e=>setValues({...values,message:e.target.value})} aria-invalid={!!errors.message} aria-describedby={errors.message?'message-error':undefined}/>{errors.message&&<small className="error" id="message-error">{t(ui.required)}</small>}<button className="button" type="submit">{t(ui.submit)}<ArrowUpRight size={17}/></button><small className="form-note">{t(ui.local)}</small></>}</form></section>}
function Home({t}:{t:Translator}){return <><section className="hero"><motion.div initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:.6}}><Label>{t(ui.eyebrow)}</Label><h1>{t(ui.hero)}<br/><span>{t(ui.hero2)}</span></h1><p className="hero-intro">{t(ui.intro)}</p><div className="actions"><LinkButton href="#/demo">{t(ui.open)}</LinkButton><LinkButton href="#/walkthrough" secondary>{t(ui.walk)}</LinkButton></div><div className="hero-note"><span className="status-dot"/>{t(ui.local)}</div></motion.div><motion.div className="hero-console" initial={{opacity:0,y:24}} animate={{opacity:1,y:0}} transition={{duration:.7,delay:.12}}><Teaser t={t}/><div className="console-anchor"><span>01 — 05</span><span>{t(ui.proposal)} → {t(ui.verdict)}</span></div></motion.div><div className="hero-bottom"><span className="mono">HEIMDALL / LOCAL TRUST LAYER</span><a href="#/how">{t(ui.how)}<ChevronDown size={15}/></a></div></section><section id="how" className="section"><Label>01 / {t(ui.policy)}</Label><div className="section-heading"><h2>{t(ui.how)}</h2><p>{t(ui.howSub)}</p></div><Flow t={t}/><div className="capabilities">{capabilities.map((c,i)=><div key={i}><span className="mono">0{i+1}</span><p>{t(c)}</p><Check size={15}/></div>)}</div><p className="small-note">{t(ui.implCopy)}</p></section><section id="policy" className="section"><Label>02 / {t(ui.verdict)}</Label><h2>{t(ui.boundaries)}</h2><Policy t={t}/></section><section id="audit" className="section audit-section"><div><Label>03 / {t(ui.audit)}</Label><h2>{t(ui.auditTitle)}</h2><p>{t(ui.auditCopy)}</p><LinkButton href="#/docs" secondary>{t(ui.docs)}</LinkButton></div><div className="audit-example"><div className="sample-ledger console-surface"><div className="console-top"><span><Fingerprint size={16}/>{t(ui.audit)}</span><span className="tiny-label">{t(ui.synthetic)}</span></div><div className="ledger-line"><span className="mono">01 / R18</span><Badge code="BLOCK"/></div><pre>{'event → previous_digest → digest\ndata/lumen_public.json\n[event_digest]'}</pre></div><div className="brief-card"><Label><FileText size={15}/> {t(ui.briefing)}</Label><p>{t(ui.summary)}</p><span className="small-note">{t(ui.synthetic)}</span></div></div></section><section id="evidence" className="section"><Label>04 / {t(ui.status)}</Label><h2>{t(ui.evidenceTitle)}</h2><Evidence t={t}/></section><section className="section integration-section"><div><Label>05 / {t(ui.planned)}</Label><h2>{t(ui.integrations)}</h2></div><div><p className="large-copy">{t(ui.integrationCopy)}</p><div className="integration-lines">{[components[4].name,wLocal('Authenticated approvals','Kelulusan disahkan','身份认证审批'),wLocal('External audit anchor','Penambat audit luaran','外部审计锚点')].map((n,i)=><div key={i}><span>{t(n)}</span><span className="planned-tag">{t(ui.planned)}</span></div>)}</div><p>{t(ui.readNote)}</p></div></section><Contact t={t}/><section className="section faq-section"><div><Label>07 / FAQ</Label><h2>{t(ui.faq)}</h2></div><div>{faqs.map((f,i)=><details key={i}><summary>{t(f.q)}<Plus size={19}/></summary><p>{t(f.a)}</p></details>)}</div></section></>}
const wLocal=(a:string,b:string,c:string):Words=>[a,b,c];
function Demo({t}:{t:Translator}){const [step,setStep]=useState(0);const [selected,setSelected]=useState(0);const guide=tour.steps[step];function navigate(next:number){setStep(next);const scenario=tour.steps[next].scenario;if(scenario!==undefined)setSelected(scenario);}const [events,setEvents]=useState<Event[]>([]);const [states,setStates]=useState<Record<number,Event['state']>>({});const [assists,setAssists]=useState<Record<number,boolean>>({});const [brief,setBrief]=useState(false);const s=scenarios[selected];const reviewed=!!states[selected];function record(state:Event['state']){if(!canRecord(events,selected,state))return;setEvents(prev=>canRecord(prev,selected,state)?[...prev,{scenario:selected,state}]:prev);setStates(prev=>({...prev,[selected]:state}));setBrief(false);}function reset(){setEvents([]);setStates({});setAssists({});setBrief(false);navigate(0);}const decisions=events.filter(e=>e.state==='approved'||e.state==='denied');return <div className="demo-page">
<section className="page-heading">
<Label>{t(ui.synthetic)}</Label>
<h1>{t(ui.demoTitle)}</h1>
<p>{t(ui.demoIntro)}</p>
<div className="between">
<span className="small-note">
<LockKeyhole size={14}/>{t(ui.local)}</span>
<button className="text-button" onClick={reset}>
<RotateCcw size={14}/>{t(ui.reset)}</button>
</div>
</section>
<section className="demo-guide" aria-label={t(tour.title)}>
<Label>{t(tour.title)}</Label>
<ol>{tour.steps.map((item,i)=><li key={i}><button onClick={()=>navigate(i)} aria-current={step===i?'step':undefined}><span className="mono">0{i+1}</span>{t(item.title)}</button></li>)}</ol>
<div className="guide-copy" aria-live="polite"><h2>{t(guide.title)}</h2><p>{t(guide.copy)}</p></div>
<div className="guide-actions"><button className="button secondary" disabled={step===0} onClick={()=>navigate(step-1)}>{t(tour.back)}</button><a className="text-button" href={`#${guide.target}`} onClick={e=>{e.preventDefault();document.getElementById(guide.target)?.focus();document.getElementById(guide.target)?.scrollIntoView({behavior:'instant',block:'start'});}}>{t(guide.title)}<ArrowRight size={16}/></a><button className="button secondary" disabled={step===tour.steps.length-1} onClick={()=>navigate(step+1)}>{t(tour.next)}<ArrowRight size={16}/></button></div>
</section>
<section id="demo-console" tabIndex={-1} className="demo-workspace console-surface">
<div className="workspace-title">
<span>
<Terminal size={17}/> HEIMDALL / {t(ui.console)}</span>
<span className="tiny-label">{t(ui.synthetic)}</span>
</div>
<div className="workspace-grid">
<aside className="scenario-nav">
<Label>{t(ui.scenarios)}</Label>{scenarios.map((item,i)=>
<button key={item.id} className={selected===i?'active':''} onClick={()=>setSelected(i)} aria-pressed={selected===i}>
<span className="scenario-number mono">0{i+1}</span>
<span>
<small>{t(departments[item.agent])}</small>
<strong>{t(item.title)}</strong>
</span>
<Badge code={item.verdict}/>
</button>)}</aside>
<div className="action-panel">
<div className="between">
<span className="agent-line">
<span className="agent-avatar">
<GitBranch size={17}/>
</span>{t(departments[s.agent])}</span>
<span className="mono">0{selected+1} / 05</span>
</div>
<h2>{t(s.title)}</h2>
<Label>{t(ui.proposal)}</Label>
<p className="proposed-action">{t(s.action)}</p>
<div className="metadata">
<div>
<Label>{t(ui.classify)}</Label>
<span>
<Layers size={14}/>{t(tiers[s.tier])}</span>
</div>
<div>
<Label>{t(ui.rule)}</Label>
<code>{s.rule}</code>
</div>
<div className="path-row">
<Label>{t(ui.path)}</Label>
<code>{s.path}</code>
</div>
</div>{!reviewed?<button className="button light" onClick={()=>record('reviewed')}>{t(ui.review)}<ArrowRight size={16}/>
</button>:<motion.div key={selected} initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:.25}} className="verdict-result" aria-live="polite">
<div className="between">
<Label>{t(ui.verdict)}</Label>
<Badge code={s.verdict}/>
</div>
<h3>{t(ui.reason)}</h3>
<p>{t(s.reason)}</p>{s.verdict==='HOLD'&&<div className="approval">
<p>{t(states[selected]==='approved'?ui.approved:states[selected]==='denied'?ui.denied:ui.pendingOwner)}</p>{states[selected]==='reviewed'&&<div className="actions">
<button className="button light" onClick={()=>record('approved')}>
<Check size={16}/>{t(ui.approve)}</button>
<button className="button dark-secondary" onClick={()=>record('denied')}>
<OctagonX size={16}/>{t(ui.deny)}</button>
</div>}</div>}{s.assistance&&<div className="assistance-box">
<div className="between">
<Badge code={s.assistance}/>
<button className="text-button" disabled={assists[selected]} onClick={()=>{setAssists({...assists,[selected]:true});record('suggested');}}>{t(ui.showAssist)}<ArrowRight size={14}/>
</button>
</div>{assists[selected]&&<>
<p>{t(s.assistance==='REWRITE'?ui.rewriteText:ui.redactText)}</p>
<p className="console-muted">{t(ui.assistNote)}</p>
<Badge code="BLOCK"/>
</>}</div>}</motion.div>}</div>
</div>
<div className="workspace-footer">
<Fingerprint size={14}/>{t(ui.exampleRules)}</div>
</section>
<section className="demo-results">
<div id="demo-audit" tabIndex={-1} className="session-audit">
<div className="between">
<h2>{t(ui.audit)}</h2>
<Fingerprint size={22}/>
</div>
<Label>{t(ui.synthetic)}</Label>
<div className="audit-events" aria-live="polite">{!events.length?<p className="empty">{t(ui.empty)}</p>:events.map((e,i)=>
<div key={i}>
<span className="mono">{String(i+1).padStart(2,'0')}</span>
<div>
<strong>{t(scenarios[e.scenario].title)}</strong>
<small>{t(statusWords[e.state])}</small>
<code>{scenarios[e.scenario].rule} / {scenarios[e.scenario].path}</code>
</div>
<Badge code={scenarios[e.scenario].verdict}/>
</div>)}</div>
</div>
<div id="demo-briefing" tabIndex={-1} className="owner-panel">
<div className="between">
<h2>{t(ui.briefing)}</h2>
<FileText size={22}/>
</div>
<Label>{t(ui.synthetic)}</Label>{brief?<div className="generated" role="status">
<p>{t(ui.briefLead)}</p>{Object.keys(states).map(key=>{const n=Number(key);return <div key={key}>
<Badge code={scenarios[n].verdict}/>
<p>{t(scenarios[n].reason)}</p>{decisions.filter(e=>e.scenario===n).map((e,i)=>
<p key={i}>{t(statusWords[e.state])}</p>)}</div>})}</div>:<p className="empty">{t(ui.briefEmpty)}</p>}<button className="button secondary" disabled={!events.length} onClick={()=>setBrief(true)}>{t(ui.generate)}<ArrowRight size={16}/>
</button>
</div>
</section>
<div className="demo-cta">
<p>{t(ui.contactTitle)}</p>
<LinkButton href="#/walkthrough">{t(ui.walk)}</LinkButton>
</div>
</div>}
function Docs({t}:{t:Translator}){return <div className="docs-page"><section className="page-heading"><Label>HEIMDALL / {t(ui.docs)}</Label><h1>{t(ui.docsTitle)}</h1><p>{t(ui.docsIntro)}</p></section><div className="docs-layout"><aside className="docs-nav">{[['system',ui.overview],['components',ui.components],['rules',ui.rulesTitle],['integrity',ui.audit],['scope',ui.intercept],['limitations',ui.evidenceTitle]].map(([id,a])=><a key={id as string} href={`#/docs/${id}`}>{t(a as Words)}<ArrowUpRight size={13}/></a>)}</aside><div className="docs-content"><section id="system"><Label>01 / {t(ui.overview)}</Label><h2>{t(ui.how)}</h2><Flow t={t} compact/><p>{t(ui.readNote)}</p></section><section id="components"><Label>02 / {t(ui.components)}</Label><h2>{t(ui.components)}</h2><div className="component-table"><div className="table-heading"><span>{t(ui.components)}</span><span>{t(ui.inputs)}</span><span>{t(ui.status)}</span></div>{components.map((c,i)=><div className="component-row" key={i}><strong>{t(c.name)}</strong><p>{t(c.desc)}</p><span className="planned-tag">{t(c.planned?ui.planned:ui.implemented)}</span></div>)}</div></section><section id="rules"><Label>03 / {t(ui.rulesTitle)}</Label><h2>{t(ui.boundaries)}</h2><Policy t={t}/><p className="small-note">{t(ui.exampleRules)}</p><div className="rule-reference">{scenarios.map((s,i)=><div key={s.id}><div className="between"><code>{s.rule}</code><Badge code={s.verdict}/></div><h3>{t(s.title)}</h3><Label>{t(ui.classify)} / {t(tiers[s.tier])}</Label><p>{t(s.reason)}</p><code>{s.path}</code><span className="small-note">{String(i+1).padStart(2,'0')} / {t(ui.synthetic)}</span></div>)}</div></section><section id="integrity"><Label>04 / {t(ui.audit)}</Label><h2>{t(ui.auditDesign)}</h2><p>{t(ui.auditDesignText)}</p><div className="chain"><Fingerprint size={24}/><code>event → previous_digest → digest</code><LockKeyhole size={22}/></div><h3>{t(ui.briefing)}</h3><p>{t(ui.briefDesign)}</p></section><section id="scope"><Label>05 / {t(ui.intercept)}</Label><h2>{t(ui.integrations)}</h2><p>{t(ui.readNote)}</p><p>{t(ui.integrationCopy)}</p></section><section id="limitations"><Label>06 / {t(ui.evidenceTitle)}</Label><h2>{t(ui.evidenceTitle)}</h2><Evidence t={t}/><div className="limitation-note"><LockKeyhole size={23}/><p>{t(ui.limits)}</p></div><p className="small-note">{t(ui.sourceNote)}</p></section><div className="demo-cta"><LinkButton href="#/demo">{t(ui.open)}</LinkButton><LinkButton href="#/walkthrough" secondary>{t(ui.walk)}</LinkButton></div></div></div></div>}
function App(){const [lang,setLang]=useState<Lang>(()=>{try{const x=localStorage.getItem('heimdall-language');return languages.includes(x as Lang)?x as Lang:'en';}catch{return 'en';}});const [hash,setHash]=useState(location.hash||'#/');const [menu,setMenu]=useState(false);const t:Translator=x=>x[lang==='en'?0:lang==='bm'?1:2];useEffect(()=>{try{localStorage.setItem('heimdall-language',lang);}catch{}document.documentElement.lang=lang==='bm'?'ms':lang==='zh'?'zh-CN':'en';},[lang]);useEffect(()=>{const change=()=>{setHash(location.hash||'#/');setMenu(false);};window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change);},[]);const page=hash.startsWith('#/demo')?'demo':hash.startsWith('#/docs')?'docs':'home';useEffect(()=>{const id=page==='docs'?hash.split('/')[2]:hash.slice(2);requestAnimationFrame(()=>{if(id)document.getElementById(id)?.scrollIntoView({behavior:'instant'});else window.scrollTo({top:0,behavior:'instant'});});document.title=`Heimdall | ${t(ui[page])}`;},[hash,page,lang]);return <MotionConfig reducedMotion="user"><a className="skip-link" href="#main">{t(ui.skip)}</a><header><div className="header-inner"><Brand/><nav className={menu?'open':''} aria-label={t(ui.home)}>{(['home','demo','docs'] as const).map(p=><a key={p} aria-current={page===p?'page':undefined} className={page===p?'current':''} href={p==='home'?'#/':`#/${p}`}>{t(ui[p])}</a>)}</nav><div className="header-actions"><Language lang={lang} setLang={setLang}/><a className="header-cta" href="#/walkthrough">{t(ui.walk)}<ArrowUpRight size={15}/></a><button className="menu-toggle" aria-expanded={menu} aria-label={t(ui.home)} onClick={()=>setMenu(!menu)}><Layers size={22}/></button></div></div></header><main id="main" tabIndex={-1}>{page==='home'?<Home t={t}/>:page==='demo'?<Demo t={t}/>:<Docs t={t}/>}</main><footer><div className="footer-top"><div><Brand/><p>{t(ui.footer)}</p></div><div className="footer-links">{(['home','demo','docs'] as const).map(p=><a key={p} href={p==='home'?'#/':`#/${p}`}>{t(ui[p])}<ArrowUpRight size={14}/></a>)}<a href="#/walkthrough">{t(ui.walk)}<ArrowUpRight size={14}/></a></div></div><div className="footer-bottom"><span>{t(ui.local)}</span><Language lang={lang} setLang={setLang}/><span className="mono">HEIMDALL / 2026</span></div></footer></MotionConfig>}
createRoot(document.getElementById('root')!).render(<App/>);
