export const Constants = {
    app: {
        name: 'Semantic Workbench',
        defaultTheme: 'light',
        defaultBrand: 'local',
        autoScrollThreshold: 100,
        maxContentWidth: 900,
        maxInputLength: 2000000, // 2M tokens, effectively unlimited
        minChatWidthPercent: 20,
        defaultChatWidthPercent: 33,
        maxFileAttachmentsPerMessage: 10,
        loaderDelayMs: 100,
        responsiveBreakpoints: {
            interactCanvas: '900px',
        },
        speechIdleTimeoutMs: 4000,
        azureSpeechTokenRefreshIntervalMs: 540000, // 540000 ms = 9 minutes
    },
    workflow: {
        maxOutlets: 5,
    },
    service: {
        defaultEnvironmentId: 'local',
        environments: [
            {
                id: 'local',
                name: 'Semantic Workbench backend service on localhost or GitHub Codespaces',
                // Can be overridden by env var VITE_SEMANTIC_WORKBENCH_SERVICE_URL
                url: import.meta.env.VITE_SEMANTIC_WORKBENCH_SERVICE_URL || 'http://localhost:3000',
                brand: 'light',
            },
            // {
            //     id: 'remote',
            //     name: 'Remote',
            //     url: 'https://<YOUR WORKBENCH DEPLOYMENT>.azurewebsites.net',
            //     brand: 'orange',
            // },
        ],
    },
    assistantCategories: {
        Recommended: [''],
        'Example Implementations': [
            'python-01-echo-bot.workbench-explorer',
            'python-02-simple-chatbot.workbench-explorer',
            'python-03-multimodel-chatbot.workbench-explorer',
            'canonical-assistant.semantic-workbench',
        ],
        Experimental: [''],
    },
    msal: {
        method: 'redirect', // 'redirect' | 'popup'
        auth: {
            // Semantic Workbench GitHub sample app registration
            // The same value is set also in AuthSettings in
            // "semantic_workbench_service.config.py" in the backend
            // Can be overridden by env var VITE_SEMANTIC_WORKBENCH_CLIENT_ID
            clientId: import.meta.env.VITE_SEMANTIC_WORKBENCH_CLIENT_ID || '22cb77c3-ca98-4a26-b4db-ac4dcecba690',

            // Specific tenant only:     'https://login.microsoftonline.com/<tenant>/',
            // Personal accounts only:   'https://login.microsoftonline.com/consumers',
            // Work + School accounts:   'https://login.microsoftonline.com/organizations',
            // Work + School + Personal: 'https://login.microsoftonline.com/common'
            // Can be overridden by env var VITE_SEMANTIC_WORKBENCH_AUTHORITY
            authority: import.meta.env.VITE_SEMANTIC_WORKBENCH_AUTHORITY || 'https://login.microsoftonline.com/common',
        },
        cache: {
            cacheLocation: 'localStorage',
            storeAuthStateInCookie: false,
        },
        // Enable the ones you need
        msGraphScopes: [
            // 'Calendars.ReadWrite',
            // 'Calendars.Read.Shared',
            // 'ChannelMessage.Read.All',
            // 'Chat.Read',
            // 'Contacts.Read',
            // 'Contacts.Read.Shared',
            // 'email',
            // 'Files.Read',
            // 'Files.Read.All',
            // 'Files.Read.Selected',
            // 'Group.Read.All',
            // 'Mail.Read',
            // 'Mail.Read.Shared',
            // 'MailboxSettings.Read',
            // 'Notes.Read',
            // 'Notes.Read.All',
            // 'offline_access',
            // 'OnlineMeetingArtifact.Read.All',
            // 'OnlineMeetings.Read',
            'openid',
            // 'People.Read',
            // 'Presence.Read.All',
            'offline_access',
            'profile',
            // 'Sites.Read.All',
            // 'Tasks.Read',
            // 'Tasks.Read.Shared',
            // 'TeamSettings.Read.All',
            'User.Read',
            // 'User.Read.all',
            // 'User.ReadBasic.All',
        ],
    },
    debug: {
        root: 'semantic-workbench',
    },
};
