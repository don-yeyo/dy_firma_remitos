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
    // Proveer un mock de compatibilidad basado en Proxy para evitar excepciones por métodos no implementados
    const baseMock = {
        initialize: () => Promise.resolve(),
        addEventCallback: () => 0,
        removeEventCallback: () => {},
        handleRedirectPromise: () => Promise.resolve(null),
        getAllAccounts: () => [],
        getActiveAccount: () => null,
        setActiveAccount: () => {},
        loginRedirect: () => Promise.reject("Autenticación Microsoft no disponible en conexiones HTTP inseguras. Habilite HTTPS o configure un Túnel."),
        logoutRedirect: () => Promise.resolve(),
        getNavigationClient: () => ({
            navigateInternal: () => Promise.resolve(true),
            navigateExternal: () => Promise.resolve(true),
        }),
        getLogger: () => {
            const loggerInstance = {
                error: () => {}, 
                warning: () => {}, 
                info: () => {}, 
                verbose: () => {},
                isLevel: () => false,
                clone: () => loggerInstance
            };
            return loggerInstance;
        }
    };

    msalInstance = new Proxy(baseMock, {
        get: (target, prop) => {
            if (prop in target) {
                return target[prop];
            }
            // Si el componente de Microsoft accede a algún método interno no documentado,
            // devolvemos una función segura vacía para no romper el ciclo de vida de React
            return () => {};
        }
    });
}

export const loginRequest = {
    scopes: ["User.Read"]
};
