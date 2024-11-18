// Copyright (c) Microsoft. All rights reserved.

import { DialogOpenChangeData, DialogOpenChangeEvent } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { DialogControl } from '../App/DialogControl';
import { AssistantServiceMetadata } from './AssistantServiceMetadata';

interface AssistantServiceInfoDialogProps {
    assistant?: Assistant;
    open: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const AssistantServiceInfoDialog: React.FC<AssistantServiceInfoDialogProps> = (props) => {
    const { assistant, open, onOpenChange } = props;

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title={assistant && `"${assistant?.name}" Service Info`}
            content={assistant && <AssistantServiceMetadata assistantServiceId={assistant.assistantServiceId} />}
            closeLabel="Close"
        />
    );
};
