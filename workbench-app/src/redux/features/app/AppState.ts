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
    isDraggingOverBody?: boolean;
    activeConversationId?: string;
}
