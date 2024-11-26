import { AuthenticationResult, EventType, PublicClientApplication } from '@azure/msal-browser';
import { AuthenticatedTemplate, MsalProvider, UnauthenticatedTemplate } from '@azure/msal-react';
import { CopilotProvider } from '@fluentui-copilot/react-copilot';
import { FluentProvider } from '@fluentui/react-components';
import { initializeFileTypeIcons } from '@fluentui/react-file-type-icons';
import debug from 'debug';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider as ReduxProvider } from 'react-redux';
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import { Constants } from './Constants';
import { Root } from './Root';
import './index.css';
import { AuthHelper } from './libs/AuthHelper';
import { Theme } from './libs/Theme';
import { getEnvironment } from './libs/useEnvironment';
import { store } from './redux/app/store';
import { AcceptTerms } from './routes/AcceptTerms';
import { AssistantEditor } from './routes/AssistantEditor';
import { AssistantServiceRegistrationEditor } from './routes/AssistantServiceRegistrationEditor';
import { Dashboard } from './routes/Dashboard';
import { ErrorPage } from './routes/ErrorPage';
import { FrontDoor } from './routes/FrontDoor';
import { Login } from './routes/Login';
import { Settings } from './routes/Settings';
import { ShareRedeem } from './routes/ShareRedeem';
import { Shares } from './routes/Shares';

// Enable debug logging for the app
localStorage.setItem('debug', `${Constants.debug.root}:*`);

const log = debug(Constants.debug.root).extend('main');

const unauthenticatedRouter = createBrowserRouter([
    {
        path: '/',
        element: <Root />,
        errorElement: <ErrorPage />,
        children: [
            {
                // This is the default route, it should not include a path
                index: true,
                element: <Login />,
            },
            {
                path: '/terms',
                element: <AcceptTerms />,
            },
            {
                // This is the catch-all route, it should be the last route
                path: '/*',
                element: <Login />,
            },
        ],
    },
]);

const authenticatedRouter = createBrowserRouter([
    {
        path: '/',
        element: <Root />,
        errorElement: <ErrorPage />,
        children: [
            {
                index: true,
                element: <FrontDoor />,
            },
            {
                path: '/:conversationId?',
                element: <FrontDoor />,
            },
            {
                path: '/dashboard',
                element: <Dashboard />,
            },
            {
                path: '/settings',
                element: <Settings />,
            },
            {
                path: '/shares',
                element: <Shares />,
            },
            {
                path: '/assistant/:assistantId/edit',
                element: <AssistantEditor />,
            },
            {
                path: '/assistant-service-registration/:assistantServiceRegistrationId/edit',
                element: <AssistantServiceRegistrationEditor />,
            },
            {
                path: '/conversation-share/:conversationShareId/redeem',
                element: <ShareRedeem />,
            },
            {
                path: '/terms',
                element: <AcceptTerms />,
            },
        ],
    },
]);

const msalInstance = new PublicClientApplication(AuthHelper.getMsalConfig());

const accounts = msalInstance.getAllAccounts();
if (accounts.length > 0) {
    msalInstance.setActiveAccount(accounts[0]);
}

msalInstance.addEventCallback((event) => {
    if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
        const payload = event.payload as AuthenticationResult;
        msalInstance.setActiveAccount(payload.account);
    }
});

export const getMsalInstance = async () => {
    await msalInstance.initialize();
    return msalInstance;
};

const customTheme = Theme.getCustomTheme('light', getEnvironment(store.getState().settings.environmentId)?.brand);

initializeFileTypeIcons();

let container: HTMLElement | null = null;
document.addEventListener('DOMContentLoaded', () => {
    if (!container) {
        container = document.getElementById('root');
        if (!container) {
            throw new Error('Could not find root element');
        }
        const root = ReactDOM.createRoot(container);

        const app = (
            <ReduxProvider store={store}>
                <MsalProvider instance={msalInstance}>
                    <FluentProvider className="app-container" theme={customTheme}>
                        <CopilotProvider mode="canvas">
                            <UnauthenticatedTemplate>
                                <RouterProvider router={unauthenticatedRouter} />
                            </UnauthenticatedTemplate>
                            <AuthenticatedTemplate>
                                <RouterProvider router={authenticatedRouter} />
                            </AuthenticatedTemplate>
                        </CopilotProvider>
                    </FluentProvider>
                </MsalProvider>
            </ReduxProvider>
        );

        // NOTE: React.StrictMode is used to help catch common issues in the app but will also double-render
        // components.If you want to verify that any double rendering is coming from this, you can disable
        // React.StrictMode by setting the env var VITE_DISABLE_STRICT_MODE = true. Please note that this
        // will also disable the double-render check, so only use this for debugging purposes and make sure
        // to test with React.StrictMode enabled before committing any changes.

        // Can be overridden by env var VITE_DISABLE_STRICT_MODE
        const disableStrictMode = import.meta.env.VITE_DISABLE_STRICT_MODE === 'true';

        let startLogMessage = 'starting app';
        if (import.meta.env.DEV) {
            startLogMessage = `${startLogMessage} in development mode`;
            startLogMessage = `${startLogMessage} [strict mode: ${disableStrictMode ? 'disabled' : 'enabled'}]`;
        }

        log(startLogMessage);
        root.render(disableStrictMode ? app : <React.StrictMode>{app}</React.StrictMode>);
    }
});
