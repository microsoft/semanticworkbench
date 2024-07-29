// Copyright (c) Microsoft. All rights reserved.

import { Flowchart24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Link } from 'react-router-dom';
import { Assistant } from '../../models/Assistant';
import { CommandButton } from '../App/CommandButton';

interface AssistantWorkflowProps {
    assistant: Assistant;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantWorkflow: React.FC<AssistantWorkflowProps> = (props) => {
    const { assistant, iconOnly, asToolbarButton } = props;

    return (
        <Link to={`/workflow/${assistant.id}`}>
            <CommandButton
                description="Edit assistant workflow"
                icon={<Flowchart24Regular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label="Workflow"
            />
        </Link>
    );
};
