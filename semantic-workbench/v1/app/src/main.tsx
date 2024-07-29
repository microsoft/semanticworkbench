import { AuthenticationResult, EventType, PublicClientApplication } from '@azure/msal-browser';
import { AuthenticatedTemplate, MsalProvider, UnauthenticatedTemplate } from '@azure/msal-react';
import { CopilotProvider } from '@fluentui-copilot/react-copilot';
import { FluentProvider } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import { Constants } from './Constants';
import { Root } from './Root';
import './index.css';
import { AuthHelper } from './libs/AuthHelper';
import { getCustomTheme } from './libs/useCustomTheme';
import { getEnvironment } from './libs/useEnvironment';
import { store } from './redux/app/store';
import { AcceptTerms } from './routes/AcceptTerms';
import { AssistantEditor } from './routes/AssistantEditor';
import { AssistantServiceRegistrationEditor } from './routes/AssistantServiceRegistrationEditor';
import { Dashboard } from './routes/Dashboard';
import { ErrorPage } from './routes/ErrorPage';
import { Interact } from './routes/Interact';
import { Login } from './routes/Login';
import { Settings } from './routes/Settings';
import { WorkflowEditor } from './routes/WorkflowEditor';
import { WorkflowInteract } from './routes/WorkflowInteract';
import { WorkflowRunEditor } from './routes/WorkflowRunEditor';

if (!localStorage.getItem('debug')) {
    localStorage.setItem('debug', `${Constants.debug.root}:*`);
}

const log = debug(Constants.debug.root).extend('main');

const unauthenticatedRouter = createBrowserRouter([
    {
        path: '/',
        element: <Root />,
        errorElement: <ErrorPage />,
        children: [
            {
                index: true,
                element: <Login />,
            },
            {
                path: '/terms',
                element: <AcceptTerms />,
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
                element: <Dashboard />,
            },
            {
                path: '/settings',
                element: <Settings />,
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
                path: '/workflow/:workflowDefinitionId',
                element: <WorkflowRunEditor />,
            },
            {
                path: '/workflow/:workflowDefinitionId/edit',
                element: <WorkflowEditor />,
            },
            {
                path: '/workflow/:workflowDefinitionId/run/:workflowRunId',
                element: <WorkflowInteract />,
            },
            {
                path: '/conversation/:conversationId',
                element: <Interact />,
            },
            {
                path: '/terms',
                element: <AcceptTerms />,
            },
        ],
    },
]);

const msalInstance = new PublicClientApplication(AuthHelper.msalConfig);

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

const customTheme = getCustomTheme('light', getEnvironment(store.getState().settings.environmentId)?.brand);

let container: HTMLElement | null = null;
document.addEventListener('DOMContentLoaded', () => {
    if (!container) {
        container = document.getElementById('root');
        if (!container) {
            throw new Error('Could not find root element');
        }
        const root = ReactDOM.createRoot(container);
        log('starting app');
        root.render(
            <React.StrictMode>
                <Provider store={store}>
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
                </Provider>
            </React.StrictMode>,
        );
    }
});
