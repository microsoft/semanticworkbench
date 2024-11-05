// Copyright (c) Microsoft. All rights reserved.

export interface ConversationMessageDebug {
    id: string;
    debugData: {
        [key: string]: any;
    };
}

export const conversationMessageDebugFromJSON = (json: any): ConversationMessageDebug => {
    return {
        id: json.id,
        debugData: json.debug_data,
    };
};
