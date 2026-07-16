import React, { createContext, useContext, useState, useEffect } from 'react';
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { loginRequest } from "./msal";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const { instance, accounts } = useMsal();
    const isMsAuthenticated = useIsAuthenticated();

    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);

    useEffect(() => {
        // BYPASS DE AUTENTICACION PARA DESARROLLO LOCAL
        if (import.meta.env.DEV && import.meta.env.VITE_MOCK_AUTH === 'true') {
            const mockEmail = import.meta.env.VITE_MOCK_AUTH_EMAIL || "operador.mock@donyeyo.com.ar";
            setIsAuthenticated(true);
            setUser({
                name: "Operador de Pruebas (Mock)",
                email: mockEmail,
                provider: 'mock',
                avatar: null
            });
            return;
        }

        if (isMsAuthenticated && accounts.length > 0) {
            setIsAuthenticated(true);
            setUser({
                name: accounts[0].name,
                email: accounts[0].username,
                provider: 'microsoft',
                avatar: null
            });
        } else {
            setIsAuthenticated(false);
            setUser(null);
        }
    }, [isMsAuthenticated, accounts]);

    const loginMicrosoft = () => {
        // En modo mock no redirigir a Microsoft
        if (import.meta.env.DEV && import.meta.env.VITE_MOCK_AUTH === 'true') {
            return;
        }
        instance.loginRedirect(loginRequest).catch(e => console.error("MSAL Login Error:", e));
    };

    const logout = () => {
        if (import.meta.env.DEV && import.meta.env.VITE_MOCK_AUTH === 'true') {
            setIsAuthenticated(false);
            setUser(null);
            return;
        }
        instance.logoutRedirect().catch(e => console.error("MSAL Logout Error:", e));
    };

    return (
        <AuthContext.Provider value={{
            isAuthenticated,
            user,
            loginMicrosoft,
            logout
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
