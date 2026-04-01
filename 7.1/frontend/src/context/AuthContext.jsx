import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for saved token in localStorage on mount
    const savedUser = localStorage.getItem('rrhh_user');
    const token = localStorage.getItem('rrhh_token');
    
    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = (userData, token) => {
    localStorage.setItem('rrhh_user', JSON.stringify(userData));
    localStorage.setItem('rrhh_token', token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('rrhh_user');
    localStorage.removeItem('rrhh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
        {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
