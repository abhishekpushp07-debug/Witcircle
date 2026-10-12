import React,{createContext,useCallback,useContext,useEffect,useMemo,useRef,useState} from 'react';
import {api,post} from './api';
const AuthContext=createContext();
export function AuthProvider({children}){
 const [user,commitUser]=useState(null);const [checking,setChecking]=useState(true);const generation=useRef(0);const mounted=useRef(true);const bootstrap=useRef(null);
 const setUser=useCallback(next=>{generation.current+=1;bootstrap.current?.abort();commitUser(next);setChecking(false);},[]);
 useEffect(()=>{mounted.current=true;const controller=new AbortController();bootstrap.current=controller;const epoch=generation.current;
  api('/auth/session',{signal:controller.signal}).then(data=>{if(mounted.current&&epoch===generation.current){commitUser(data.user);setChecking(false);}}).catch(()=>{if(mounted.current&&!controller.signal.aborted&&epoch===generation.current){commitUser(null);setChecking(false);}});
  return()=>{mounted.current=false;controller.abort();};
 },[]);
 const logout=useCallback(async()=>{generation.current+=1;bootstrap.current?.abort();await post('/auth/logout');Object.keys(localStorage).filter(k=>k.startsWith('tejas-draft-')).forEach(k=>localStorage.removeItem(k));if(mounted.current){commitUser(null);setChecking(false);}},[]);
 const value=useMemo(()=>({user,setUser,checking,logout}),[user,setUser,checking,logout]);
 return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export const useAuth=()=>useContext(AuthContext);
