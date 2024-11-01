// Copyright (c) Microsoft. All rights reserved.

import { InteractCanvasState } from '../../../models/InteractCanvasState';
import { User } from '../../../models/User';

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
    interactCanvasState?: InteractCanvasState;
    activeConversationId?: string;
    user?: User;
}
