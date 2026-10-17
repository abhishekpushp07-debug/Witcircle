import React,{useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {ArrowUpRight,Clock3,FileCheck2,Search,ShieldCheck,ArrowRight} from 'lucide-react';
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

const SetRow = ({s}) => {
 const active=s.attempt?.status==='active', done=s.attempt?.status==='completed';
 return <article className="exam-row" data-testid={'exams-set-card-'+s.id}>
  <div className="exam-row-number" data-testid={'exam-chapter-number-'+s.id}>{String(s.chapter_number).padStart(2,'0')}</div>
  <div className="exam-row-main"><div className="exam-row-overline"><span data-testid={'exam-subject-'+s.id}>{s.chapter_subject}</span><span className={active?'exam-state-active':''} data-testid={'exam-state-'+s.id}>{active?'In progress':done?'Completed':'Available'}</span></div><h3 data-testid={'exam-title-'+s.id}>{s.title}</h3><p data-testid={'exam-facts-'+s.id}>{s.count} questions <span>·</span> {s.rules.minutes} min <span>·</span> +{s.rules.correct} / {s.rules.wrong}</p></div>
  <div className="exam-row-validity" data-testid={'exam-expiry-'+s.id}><span>Available until</span><strong>{new Date(s.end_at*1000).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}</strong></div>
  <div className="exam-row-actions">{done&&<Button asChild variant="ghost"><Link to={'/results/'+s.attempt.id} data-testid={'exam-results-'+s.id}>Results</Link></Button>}<Button asChild className="btn btn-primary"><Link to={active?'/attempts/'+s.attempt.id:'/sets/'+s.id} data-testid={(active?'exam-resume-':'exam-start-')+s.id}>{active?'Resume':done?'Retry test':'Start test'}<ArrowUpRight size={16}/></Link></Button></div>
 </article>;
};

export default function Exams(){
 const {user}=useAuth();const userId=user?.id;const [params,setParams]=useSearchParams();
 const [mode,setMode]=useState(params.get('exam')==='JEE Main'?'all':'chapters');
 const [subject,setSubject]=useState('');const [exam,setExam]=useState(params.get('exam')||'BITSAT');
 const [query,setQuery]=useState('');const [page,setPage]=useState(1);const [data,setData]=useState(null);const [error,setError]=useState('');const [reload,setReload]=useState(0);
 useEffect(()=>{let live=true;const controller=new AbortController();setData(null);setError('');const timer=setTimeout(()=>{
  const url=mode==='chapters'?`${userId?'/my':''}/chapter-exams?subject=${encodeURIComponent(subject)}&q=${encodeURIComponent(query)}&page=${page}`:`${userId?'/my':''}/sets?exam=${encodeURIComponent(exam)}&q=${encodeURIComponent(query)}&page=${page}`;
  api(url,{signal:controller.signal}).then(d=>{if(live)setData(d)}).catch(e=>{if(live&&!controller.signal.aborted)setError(e.message)});
 },180);return()=>{live=false;clearTimeout(timer);controller.abort()}},[mode,subject,exam,query,page,userId,reload]);
 function switchMode(v){setMode(v);setPage(1);setQuery('');setParams(v==='chapters'?{exam:'BITSAT'}:{exam})}
 return <div className="container page chapter-exams" data-testid="chapter-exams-page">
  <header className="exam-library-heading"><div><span className="eyebrow" data-testid="exams-eyebrow">THE PRACTICE LIBRARY</span><h1 data-testid="exams-title">Find your next chapter.</h1><p data-testid="exams-description">One focused hour. A clearer picture of what to work on.</p></div><div className="exam-library-rules" data-testid="chapter-exam-rules"><span><FileCheck2 size={16}/>50 questions</span><span><Clock3 size={16}/>60 minutes</span><span>+3 / −1 marks</span></div></header>
  <Tabs value={mode} onValueChange={switchMode} data-testid="exam-catalog-modes"><TabsList><TabsTrigger value="chapters" data-testid="exam-mode-chapters">Chapter tests</TabsTrigger><TabsTrigger value="all" data-testid="exam-mode-all">All practice sets</TabsTrigger></TabsList></Tabs>
  <div className="chapter-catalog-toolbar exam-library-filters" data-testid="exams-catalog-sticky-filterbar">
   {mode==='chapters'?<Tabs value={subject||'all'} onValueChange={v=>{setSubject(v==='all'?'':v);setPage(1)}} data-testid="exam-subject-tabs"><TabsList>{[['all','All subjects'],['Physics','Physics'],['Chemistry','Chemistry'],['Mathematics','Mathematics']].map(([v,label])=><TabsTrigger value={v} key={v} data-testid={'exam-subject-'+v}>{label}{data?.subject_counts&&<span>{v==='all'?Object.values(data.subject_counts).reduce((a,b)=>a+b,0):data.subject_counts[v]||0}</span>}</TabsTrigger>)}</TabsList></Tabs>:<Tabs value={exam} onValueChange={v=>{setExam(v);setParams({exam:v});setPage(1)}}><TabsList>{['JEE Main','BITSAT'].map(v=><TabsTrigger value={v} key={v} data-testid={'exam-tab-'+v}>{v}</TabsTrigger>)}</TabsList></Tabs>}
   <div className="chapter-search"><Search size={18}/><Input value={query} onChange={e=>{setQuery(e.target.value);setPage(1)}} placeholder={mode==='chapters'?'Find a chapter…':'Search practice sets…'} aria-label="Search chapters or practice sets" data-testid="exams-search-input"/></div>
  </div>
  {mode==='chapters'&&<details className="exam-library-disclosure"><summary data-testid="answer-keys-only-disclosure"><ShieldCheck size={16}/><span>Original notation · Answer keys only</span><span className="exam-about-label">About these tests</span></summary><p data-testid="chapter-exam-about">Your personal timer begins when you start. Unanswered questions earn 0. Source images preserve formulas; supplied keys unlock after submission. These books do not include worked solutions. Custom chapter practice, not official BITSAT papers.</p></details>}
  <ErrorBox error={error} retry={()=>setReload(v=>v+1)}/>
  {!data&&!error?<div className={mode==='chapters'?'exam-library-list':'set-grid'} data-testid="exam-catalog-loading">{[1,2,3,4].map(n=><Skeleton key={n} className="h-28"/>)}</div>:data?.items.length?<><div className="exam-library-count"><p data-testid="exam-result-count" aria-live="polite">{mode==='chapters'?`${data.total} chapter tests${subject?' · '+subject:''}`:'Published practice sets'}</p>{(query||subject)&&<Button variant="ghost" onClick={()=>{setQuery('');setSubject('');setPage(1)}} data-testid="exams-catalog-clear-filters-button">Clear filters</Button>}</div><div className={mode==='chapters'?'exam-library-list':'set-grid'} data-testid="exam-catalog-list">{data.items.map(s=>mode==='chapters'?<SetRow key={s.id} s={s}/>:<SetCard key={s.id} s={s}/>)}</div></>:!error&&<Empty title="No matching tests yet." action={<Button variant="outline" onClick={()=>{setQuery('');setSubject('');setPage(1)}} data-testid="exam-reset-filters">Reset filters</Button>}>Try another chapter or subject. Only live, unexpired tests are shown.</Empty>}
  {data&&(page>1||(mode==='chapters'?data.pages>1:data.items.length===20))&&<div className="chapter-pagination"><Button variant="outline" onClick={()=>setPage(p=>p-1)} disabled={page===1} data-testid="catalog-prev">Previous</Button><span data-testid="catalog-page">Page {page}{mode==='chapters'?' of '+data.pages:''}</span><Button variant="outline" onClick={()=>setPage(p=>p+1)} disabled={mode==='chapters'?page>=data.pages:data.items.length<20} data-testid="catalog-next">Next<ArrowRight size={16}/></Button></div>}
 </div>;
}
