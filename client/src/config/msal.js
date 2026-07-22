import { PublicClientApplication } from "@azure/msal-browser";

export const msalConfig = {
    auth: {
        clientId: import.meta.env.VITE_AZURE_AD_CLIENT_ID || "",
        authority: `https://login.microsoftonline.com/${import.meta.env.VITE_AZURE_AD_TENANT_ID || "common"}`,
        redirectUri: window.location.origin,
    },
    cache: {
        cacheLocation: "sessionStorage",
        storeAuthStateInCookie: false,
    }
};

export let msalInstance;

try {
    msalInstance = new PublicClientApplication(msalConfig);
} catch (error) {
    console.warn("MSAL.js no pudo inicializarse (Contexto HTTP no seguro):", error);
    // Proveer un mock de compatibilidad mínimo para evitar errores de renderizado en React
    msalInstance = {
        initialize: () => Promise.resolve(),
        addEventCallback: () => 0,
        removeEventCallback: () => {},
        handleRedirectPromise: () => Promise.resolve(null),
        getAllAccounts: () => [],
        getActiveAccount: () => null,
        setActiveAccount: () => {},
        loginRedirect: () => Promise.reject("Autenticación Microsoft no disponible en conexiones HTTP inseguras. Habilite HTTPS o configure un Túnel."),
        logoutRedirect: () => Promise.resolve(),
        getLogger: () => ({ 
            error: () => {}, 
            warning: () => {}, 
            info: () => {}, 
            verbose: () => {} 
        })
    };
}

export const loginRequest = {
    scopes: ["User.Read"]
};
