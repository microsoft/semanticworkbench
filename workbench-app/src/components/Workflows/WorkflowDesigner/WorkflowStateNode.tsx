// Copyright (c) Microsoft. All rights reserved.

import { Button, Card, Text, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { ErrorCircleRegular, Settings24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Handle, NodeProps, Position } from 'reactflow';
import { WorkflowState } from '../../../models/WorkflowDefinition';
import { isValidWorkflowStateData } from './WorkflowStateEditor';
import { WorkflowStateHandle } from './WorkflowStateHandle';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#fff',
        overflow: 'visible',
        gap: 0,
        ...shorthands.padding(0),
        ...shorthands.border(tokens.strokeWidthThin, 'solid', tokens.colorBrandForegroundInverted),
        // when the parent is selected
        ':global(.selected >)': {
            ...shorthands.border(tokens.strokeWidthThick, 'solid', tokens.colorBrandForegroundInverted),
        },
    },
    error: {
        color: tokens.colorPaletteRedForeground1,
    },
    heading: {
        borderRadius: `${tokens.borderRadiusMedium} ${tokens.borderRadiusMedium} 0 0`,
        overflow: 'hidden',
        width: '100%',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundImage: `linear-gradient(to bottom right, ${tokens.colorNeutralBackground1}, ${tokens.colorNeutralBackground6})`,
        boxSizing: 'border-box',
        gap: tokens.spacingHorizontalXXS,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    startHeading: {
        backgroundImage: `linear-gradient(to bottom right, ${tokens.colorPaletteGreenBackground1}, ${tokens.colorPaletteGreenBackground2})`,
    },
    errorHeading: {
        backgroundImage: `linear-gradient(to bottom right, ${tokens.colorPaletteRedBackground1}, ${tokens.colorPaletteRedBackground2})`,
    },
    body: {
        display: 'grid',
        gridTemplateColumns: 'auto 1fr',
        width: '100%',
    },
    actions: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    outlets: {
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyItems: 'end',
        ...shorthands.borderLeft(tokens.strokeWidthThin, 'solid', tokens.colorNeutralBackground4),
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(tokens.spacingVerticalM, 0),
    },
    handle: {
        backgroundColor: tokens.colorNeutralBackground4,
        ...shorthands.borderColor(tokens.colorBrandForegroundInverted),
    },
});

export interface WorkflowStateNodeData extends WorkflowState {
    isStart?: boolean;
    onEdit?: () => void;
}

export const WorkflowStateNode: React.FC<NodeProps<WorkflowStateNodeData>> = (props) => {
    const { data, isConnectable } = props;
    const { isStart, label, outlets, onEdit } = data;
    const classes = useClasses();

    const checkIsValid = isValidWorkflowStateData(data);

    return (
        <Card className={classes.root} onDoubleClick={onEdit}>
            <div
                className={mergeClasses(
                    classes.heading,
                    isStart && classes.startHeading,
                    !checkIsValid.isValid && classes.errorHeading,
                )}
            >
                {!checkIsValid.isValid && <ErrorCircleRegular className={classes.error} />}
                <Text>{label}</Text>
            </div>
            <div className={classes.body}>
                <div className={classes.actions}>
                    {!isStart && (
                        <Handle
                            className={classes.handle}
                            type="target"
                            position={Position.Left}
                            isConnectable={isConnectable}
                        />
                    )}
                    <Button appearance="outline" size="small" icon={<Settings24Regular />} onClick={onEdit} />
                </div>
                <div className={classes.outlets}>
                    {outlets.map((outlet) => (
                        <WorkflowStateHandle key={outlet.id} handleClassName={classes.handle} outlet={outlet} />
                    ))}
                </div>
            </div>
        </Card>
    );
};
