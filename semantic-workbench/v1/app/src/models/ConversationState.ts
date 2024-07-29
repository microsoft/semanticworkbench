// Copyright (c) Microsoft. All rights reserved.

import { RJSFSchema, UiSchema } from '@rjsf/utils';

export type ConversationState = {
    id: string;
    data: object;
    jsonSchema?: RJSFSchema;
    uiSchema?: UiSchema;
};
