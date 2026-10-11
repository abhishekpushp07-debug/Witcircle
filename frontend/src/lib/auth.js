import React,{createContext,useContext,useEffect,useState} from 'react';
import {api,post} from './api';
const AuthContext=createContext();
export function AuthProvider({children}){
 const [user,setUser]=useState(null);const [checking,setChecking]=useState(true);
 useEffect(()=>{api('/auth/me').catch(()=>post('/auth/refresh')).then(setUser).catch(()=>setUser(null)).finally(()=>setChecking(false));},[]);
 const logout=async()=>{await post('/auth/logout');Object.keys(localStorage).filter(k=>k.startsWith('tejas-draft-')).forEach(k=>localStorage.removeItem(k));setUser(null);};
 return <AuthContext.Provider value={{user,setUser,checking,logout}}>{children}</AuthContext.Provider>;
}
export const useAuth=()=>useContext(AuthContext);
