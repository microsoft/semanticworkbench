// Copyright (c) Microsoft. All rights reserved.

import { ConversationCanvasState } from '../../../models/ConversationCanvasState';

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
    conversationCanvasState?: ConversationCanvasState;
}
