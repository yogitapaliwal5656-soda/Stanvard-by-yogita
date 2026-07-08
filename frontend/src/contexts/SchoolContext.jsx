import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { useAuth } from './AuthContext';

const SchoolContext = createContext(null);

export const SchoolProvider = ({ children }) => {
  const { user } = useAuth();
  const [schools, setSchools] = useState([]);
  const [activeSchoolId, setActiveSchoolId] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadSchools = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const { data } = await api.get('/auth/my-schools');
      setSchools(data);
      const stored = localStorage.getItem('stv_school');
      if (data.find((s) => s.id === stored)) setActiveSchoolId(stored);
      else if (user.school_id && data.find((s) => s.id === user.school_id)) {
        setActiveSchoolId(user.school_id);
        localStorage.setItem('stv_school', user.school_id);
      } else if (data.length) {
        setActiveSchoolId(data[0].id);
        localStorage.setItem('stv_school', data[0].id);
      }
    } finally { setLoading(false); }
  }, [user]);

  useEffect(() => { loadSchools(); }, [loadSchools]);

  const switchSchool = (id) => {
    setActiveSchoolId(id);
    localStorage.setItem('stv_school', id);
    // Force page components to re-fetch by dispatching an event
    window.dispatchEvent(new CustomEvent('stv:school-changed', { detail: id }));
  };

  const activeSchool = schools.find((s) => s.id === activeSchoolId) || null;

  return (
    <SchoolContext.Provider value={{ schools, activeSchool, activeSchoolId, switchSchool, refresh: loadSchools, loading }}>
      {children}
    </SchoolContext.Provider>
  );
};

export const useSchool = () => useContext(SchoolContext);
