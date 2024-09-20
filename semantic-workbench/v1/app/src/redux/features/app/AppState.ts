// Copyright (c) Microsoft. All rights reserved.

export interface AppState {
    devMode?: boolean;
    isDraggingOverBody?: boolean;
    errors?: {
        id: string;
        title?: string;
        message?: string;
    }[];
    completedFirstRun?: {
        app?: boolean;
        experimental?: boolean;
        workflow?: boolean;
    };
    chatWidthPercent: number;
    canvasState?: {
        open?: boolean;
        mode?: 'conversation' | 'assistant';
        assistantId?: string;
        assistantStateId?: string;
    };
}
