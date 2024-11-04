// Copyright (c) Microsoft. All rights reserved.

export interface AppState {
    devMode: boolean;
    errors: {
        id: string;
        title?: string;
        message?: string;
    }[];
    completedFirstRun: {
        app: boolean;
        experimental: boolean;
        workflow: boolean;
    };
    chatWidthPercent: number;
    localUser?: {
        id: string;
        name: string;
        email: string;
        avatar: {
            name: string;
            image?: {
                src: string;
            };
        };
    };
    userPhoto: {
        src?: string;
        isLoading: boolean;
    };
    isDraggingOverBody?: boolean;
    activeConversationId?: string;
}
