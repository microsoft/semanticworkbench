// Copyright (c) Microsoft. All rights reserved.

export interface AppState {
    // persisted
    devMode: boolean;
    completedFirstRun: {
        app: boolean;
        experimental: boolean;
    };
    hideExperimentalNotice: boolean;
    chatWidthPercent: number;
    globalContentOpen: boolean;
    // transient
    isDraggingOverBody?: boolean;
    activeConversationId?: string;
    errors: {
        id: string;
        title?: string;
        message?: string;
    }[];
}
