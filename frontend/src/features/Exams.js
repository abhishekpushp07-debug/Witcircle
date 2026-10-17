import React,{useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {ArrowUpRight,BookOpen,Clock3,FileCheck2,Search,ShieldCheck,ArrowRight} from 'lucide-react';
import {api} from '../lib/api';
import {useAuth} from '../lib/auth';
import {Badge,ErrorBox,Empty} from '../components/Shared';
import {Button} from '../components/ui/button';
import {Input} from '../components/ui/input';
import {Tabs,TabsList,TabsTrigger} from '../components/ui/tabs';
import {Skeleton} from '../components/ui/skeleton';

export const SetCard=({s})=>{
 const chapter=!!s.chapter_book_id,active=s.attempt?.status==='active',done=s.attempt?.status==='completed';
 return <article className="card set-card chapter-test-card" data-testid={'exams-set-card-'+s.id}>
  <div className="row-between"><Badge>{chapter?s.chapter_subject:s.exam}</Badge><small data-testid={'exam-state-'+s.id}>{active?'In progress':done?'Completed':chapter?'Live':'Practice'}</small></div>
  {chapter&&<span className="eyebrow" data-testid={'exam-chapter-number-'+s.id}>CHAPTER {String(s.chapter_number).padStart(2,'0')}</span>}
  <h3 data-testid={'exam-title-'+s.id}>{s.title}</h3>
  <div className="set-facts" data-testid={'exam-facts-'+s.id}><span><FileCheck2 size={16}/>{s.count} questions</span><span><Clock3 size={16}/>{s.rules.minutes?s.rules.minutes+' min':'Untimed'}</span></div>
  <div className="chapter-card-marks" data-testid={'exam-marks-'+s.id}><strong>+{s.rules.correct}</strong> correct <span>·</span> <strong>{s.rules.wrong}</strong> wrong <span>·</span> {s.maximum} marks</div>
  {chapter?<p className="import-fineprint" data-testid={'exam-expiry-'+s.id}>Available until {new Date(s.end_at*1000).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}</p>:<p>{s.source}</p>}
  <div className="chapter-card-actions"><Button asChild className="btn btn-primary"><Link to={active?'/attempts/'+s.attempt.id:'/sets/'+s.id} data-testid={(active?'exam-resume-':'exam-start-')+s.id}>{active?'Resume test':done?'Attempt again':chapter?'View rules & start':'Open practice'}<ArrowUpRight size={17}/></Link></Button>
  {done&&<Button asChild variant="outline"><Link to={'/results/'+s.attempt.id} data-testid={'exam-results-'+s.id}>View results</Link></Button>}</div>
 </article>;
};

export default function Exams(){
 const {user}=useAuth();const [params,setParams]=useSearchParams();
 const [mode,setMode]=useState(params.get('exam')==='JEE Main'?'all':'chapters');
 const [subject,setSubject]=useState('');const [exam,setExam]=useState(params.get('exam')||'BITSAT');
 const [query,setQuery]=useState('');const [page,setPage]=useState(1);const [data,setData]=useState(null);const [error,setError]=useState('');const [reload,setReload]=useState(0);
 useEffect(()=>{let live=true;const controller=new AbortController();setData(null);setError('');const timer=setTimeout(()=>{
  const url=mode==='chapters'?`${user?'/my':''}/chapter-exams?subject=${encodeURIComponent(subject)}&q=${encodeURIComponent(query)}&page=${page}`:`${user?'/my':''}/sets?exam=${encodeURIComponent(exam)}&q=${encodeURIComponent(query)}&page=${page}`;
  api(url,{signal:controller.signal}).then(d=>{if(live)setData(d)}).catch(e=>{if(live&&!controller.signal.aborted)setError(e.message)});
 },180);return()=>{live=false;clearTimeout(timer);controller.abort()}},[mode,subject,exam,query,page,user?.id,reload]);
 function switchMode(v){setMode(v);setPage(1);setQuery('');setParams(v==='chapters'?{exam:'BITSAT'}:{exam})}
 return <div className="container page chapter-exams" data-testid="chapter-exams-page">
  <div className="chapter-exams-heading"><div><span className="eyebrow">YOUR NEXT FOCUSED SESSION</span><h1 data-testid="exams-title">One chapter.<br/>One focused hour.</h1><p data-testid="exams-description">Choose a chapter, check the rules, and give it your best. Your answers save as you go.</p></div><div className="chapter-rules-panel" data-testid="chapter-exam-rules"><BookOpen size={24}/><strong>50 questions · 60 minutes</strong><span>+3 correct · −1 incorrect · 0 unanswered</span><small>Your personal timer begins only when you start.</small></div></div>
  <Tabs value={mode} onValueChange={switchMode} data-testid="exam-catalog-modes"><TabsList><TabsTrigger value="chapters" data-testid="exam-mode-chapters">Chapter tests</TabsTrigger><TabsTrigger value="all" data-testid="exam-mode-all">All practice sets</TabsTrigger></TabsList></Tabs>
  <div className="chapter-catalog-toolbar">
   {mode==='chapters'?<Tabs value={subject||'all'} onValueChange={v=>{setSubject(v==='all'?'':v);setPage(1)}} data-testid="exam-subject-tabs"><TabsList>{[['all','All subjects'],['Physics','Physics'],['Chemistry','Chemistry'],['Mathematics','Mathematics']].map(([v,label])=><TabsTrigger value={v} key={v} data-testid={'exam-subject-'+v}>{label}{data?.subject_counts&&<span>{v==='all'?Object.values(data.subject_counts).reduce((a,b)=>a+b,0):data.subject_counts[v]||0}</span>}</TabsTrigger>)}</TabsList></Tabs>:<Tabs value={exam} onValueChange={v=>{setExam(v);setParams({exam:v});setPage(1)}}><TabsList>{['JEE Main','BITSAT'].map(v=><TabsTrigger value={v} key={v} data-testid={'exam-tab-'+v}>{v}</TabsTrigger>)}</TabsList></Tabs>}
   <div className="chapter-search"><Search size={18}/><Input value={query} onChange={e=>{setQuery(e.target.value);setPage(1)}} placeholder={mode==='chapters'?'Find a chapter…':'Search practice sets…'} aria-label="Search chapters or practice sets" data-testid="exams-search-input"/></div>
  </div>
  {mode==='chapters'&&<div className="chapter-source-note" data-testid="answer-keys-only-disclosure"><ShieldCheck size={20}/><p><strong>Original questions. Original notation.</strong> Formula-safe PDF images with zoom. Supplied answer keys unlock after submission; these books do not include worked solutions. Custom practice, not official BITSAT papers.</p></div>}
  <ErrorBox error={error} retry={()=>setReload(v=>v+1)}/>
  {!data&&!error?<div className="set-grid" data-testid="exam-catalog-loading">{[1,2,3].map(n=><Skeleton key={n} className="h-64"/>)}</div>:data?.items.length?<><p className="import-fineprint chapter-result-count" data-testid="exam-result-count">{mode==='chapters'?`${data.total} chapter tests${subject?' · '+subject:''}`:'Published practice sets'}</p><div className="set-grid" data-testid="exam-catalog-list">{data.items.map(s=><SetCard key={s.id} s={s}/>)}</div></>:!error&&<Empty title="No matching tests yet." action={<Button variant="outline" onClick={()=>{setQuery('');setSubject('');setPage(1)}} data-testid="exam-reset-filters">Reset filters</Button>}>Try another chapter or subject. Only live, unexpired tests are shown.</Empty>}
  {data&&(page>1||(mode==='chapters'?data.pages>1:data.items.length===20))&&<div className="chapter-pagination"><Button variant="outline" onClick={()=>setPage(p=>p-1)} disabled={page===1} data-testid="catalog-prev">Previous</Button><span data-testid="catalog-page">Page {page}{mode==='chapters'?' of '+data.pages:''}</span><Button variant="outline" onClick={()=>setPage(p=>p+1)} disabled={mode==='chapters'?page>=data.pages:data.items.length<20} data-testid="catalog-next">Next<ArrowRight size={16}/></Button></div>}
 </div>;
}
