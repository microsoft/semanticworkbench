// Copyright (c) Microsoft. All rights reserved.

import { InteractCanvasState } from '../../../models/InteractCanvasState';

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
    interactCanvasState: InteractCanvasState;
    userPhoto: {
        src?: string;
        isLoading: boolean;
    };
    isDraggingOverBody?: boolean;
    activeConversationId?: string;
}
