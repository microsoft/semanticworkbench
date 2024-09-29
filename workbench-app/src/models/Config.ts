// Copyright (c) Microsoft. All rights reserved.

import { RJSFSchema, UiSchema } from '@rjsf/utils';

export type Config = {
    config: object;
    jsonSchema?: RJSFSchema;
    uiSchema?: UiSchema;
};
