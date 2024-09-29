// Copyright (c) Microsoft. All rights reserved.

import { EditRegular } from '@fluentui/react-icons';
import React from 'react';
import { Link } from 'react-router-dom';
import { WorkflowDefinition } from '../../models/WorkflowDefinition';
import { CommandButton } from '../App/CommandButton';

interface WorkflowEditProps {
    workflowDefinition: WorkflowDefinition;
    label?: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const WorkflowEdit: React.FC<WorkflowEditProps> = (props) => {
    const { workflowDefinition, label, iconOnly, asToolbarButton } = props;

    return (
        <Link to={`/workflow/${workflowDefinition.id}/edit`}>
            <CommandButton
                description="Edit workflow definition"
                icon={<EditRegular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label={label ?? 'Edit'}
            />
        </Link>
    );
};
