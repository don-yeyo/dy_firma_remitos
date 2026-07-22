import React, { createContext, useContext, useState, useEffect } from 'react';
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { loginRequest } from "./msal";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const { instance, accounts } = useMsal();
    const isMsAuthenticated = useIsAuthenticated();

    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);

    // 1. Seteo del estado ante Autenticación con Microsoft Real
    useEffect(() => {
        if (isMsAuthenticated && accounts.length > 0) {
            setIsAuthenticated(true);
            setUser({
                name: accounts[0].name,
                email: accounts[0].username,
                provider: 'microsoft',
                avatar: null
            });
        } else {
            // Solo limpiar si no estamos en bypass Mock
            if (import.meta.env.VITE_MOCK_AUTH !== 'true') {
                setIsAuthenticated(false);
                setUser(null);
            }
        }
    }, [isMsAuthenticated, accounts]);

    // 2. BYPASS DE AUTENTICACION
    useEffect(() => {
        if (import.meta.env.VITE_MOCK_AUTH === 'true') {
            const mockEmail = import.meta.env.VITE_MOCK_AUTH_EMAIL;

            if (!mockEmail) {
                alert("⚠️ Error: VITE_MOCK_AUTH está activo pero falta setear VITE_MOCK_AUTH_EMAIL en el archivo .env");
                console.error("VITE_MOCK_AUTH está activo pero falta setear VITE_MOCK_AUTH_EMAIL");
                setIsAuthenticated(false);
                setUser(null);
                return;
            }

            if (!user || (user.provider !== 'microsoft' && user.email !== mockEmail)) {
                console.log(`⚠️ MODO MOCK ACTIVADO: Entrando como ${mockEmail}`);
                setIsAuthenticated(true);
                setUser({
                    name: "Usuario Mock",
                    email: mockEmail,
                    provider: 'mock',
                    avatar: null
                });
            }
        }
    }, [user, isMsAuthenticated]);

    const loginMicrosoft = () => {
        instance.loginRedirect(loginRequest).catch(e => console.error(e));
    };

    const logout = () => {
        if (user?.provider === 'microsoft') {
            instance.logoutRedirect().catch(e => console.error(e));
        } else {
            // Limpieza local del estado mock
            setIsAuthenticated(false);
            setUser(null);
        }
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
