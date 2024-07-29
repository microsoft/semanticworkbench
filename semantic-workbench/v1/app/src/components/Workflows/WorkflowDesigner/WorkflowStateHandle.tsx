// Copyright (c) Microsoft. All rights reserved.

import { Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { Handle, Position } from 'reactflow';
import { OutletData } from '../../../models/WorkflowDefinition';

const useClasses = makeStyles({
    outlet: {
        position: 'relative',
        textAlign: 'right',
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.padding(tokens.spacingVerticalXXS, tokens.spacingHorizontalS),
    },
    outletLabel: {
        whiteSpace: 'nowrap',
        backgroundColor: tokens.colorNeutralBackground4,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.padding(tokens.spacingVerticalXXS, tokens.spacingHorizontalS),
    },
});

export interface WorkflowStateHandleProps {
    outlet: OutletData;
    handleClassName?: string;
}

export const WorkflowStateHandle: React.FC<WorkflowStateHandleProps> = (props) => {
    const { outlet, handleClassName } = props;
    const classes = useClasses();

    return (
        <div className={classes.outlet}>
            <Text className={classes.outletLabel}>{outlet.label}</Text>
            <Handle className={handleClassName} id={outlet.id} type="source" position={Position.Right} />
        </div>
    );
};
