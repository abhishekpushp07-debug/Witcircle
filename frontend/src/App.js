import React,{lazy,Suspense,useEffect} from 'react';
import {BrowserRouter,Routes,Route,useLocation,Navigate} from 'react-router-dom';
import {Toaster} from 'sonner';
import {AuthProvider,useAuth} from './lib/auth';
import {Header,Footer,Loading,Empty} from './components/Shared';
import Landing from './features/Landing';
import './App.css';
const Auth=lazy(()=>import('./features/Auth'));
const Exams=lazy(()=>import('./features/Exams'));
const Home=lazy(()=>import('./features/Home'));
const SetDetail=lazy(()=>import('./features/SetDetail'));
const Player=lazy(()=>import('./features/Player'));
const Results=lazy(()=>import('./features/Results'));
const Studio=lazy(()=>import('./features/Studio'));
const StudioEditor=lazy(()=>import('./features/StudioEditor'));
const Info=lazy(()=>import('./features/Info'));
function Protected({children,staff=false}){const {user,checking}=useAuth();const loc=useLocation();if(checking)return <Loading/>;if(!user)return <Navigate to={'/login?next='+encodeURIComponent(loc.pathname+loc.search)} replace/>;if(staff&&!['owner','reviewer'].includes(user.role))return <Empty title="A workspace for authorized reviewers">Your student account cannot access private source documents.</Empty>;return children;}
class Boundary extends React.Component{state={error:false};static getDerivedStateFromError(){return {error:true};}render(){return this.state.error?<div className="container section"><h1>We couldn’t open this screen.</h1><p>Your saved attempts are retained. Reload to try again.</p><button className="btn btn-primary" data-testid="reload-app" onClick={()=>window.location.reload()}>Reload screen</button></div>:this.props.children;}}
function Shell(){const loc=useLocation();const player=loc.pathname.startsWith('/attempts/');useEffect(()=>{if(!loc.hash)window.scrollTo(0,0);},[loc.pathname,loc.hash]);return <><a className="skip-link" href="#main" data-testid="skip-content">Skip to content</a>{!player&&<Header/>}<main id="main"><Suspense fallback={<Loading/>}><Routes><Route path="/" element={<Landing/>}/><Route path="/exams" element={<Exams/>}/><Route path="/login" element={<Auth/>}/><Route path="/signup" element={<Auth signup/>}/><Route path="/home" element={<Protected><Home/></Protected>}/><Route path="/sets/:id" element={<SetDetail/>}/><Route path="/attempts/:id" element={<Protected><Player/></Protected>}/><Route path="/results/:id" element={<Protected><Results/></Protected>}/><Route path="/studio" element={<Protected staff><Studio/></Protected>}/><Route path="/studio/:id" element={<Protected staff><StudioEditor/></Protected>}/><Route path="/privacy" element={<Info/>}/><Route path="/accessibility" element={<Info/>}/><Route path="*" element={<Empty title="This page isn’t here">Use Explore exams to find an available practice set.</Empty>}/></Routes></Suspense></main>{!player&&<Footer/>}<Toaster position="top-center" richColors/></>}
export default function App(){return <Boundary><BrowserRouter><AuthProvider><Shell/></AuthProvider></BrowserRouter></Boundary>}
