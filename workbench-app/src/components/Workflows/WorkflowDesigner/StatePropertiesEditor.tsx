// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Drawer,
    DrawerBody,
    DrawerHeader,
    DrawerHeaderTitle,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { Dismiss24Regular } from '@fluentui/react-icons';
import React from 'react';
import { WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { WorkflowStateEditor } from './WorkflowStateEditor';

const useClasses = makeStyles({
    drawer: {
        '& > .fui-DrawerBody': {
            backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
            backgroundSize: '100%',
        },
    },
    header: {
        ...shorthands.borderBottom(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
    },
    body: {
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
});

interface StatePropertiesEditorProps {
    workflowDefinition: WorkflowDefinition;
    stateIdToEdit?: string;
    onChange: (newValue: WorkflowDefinition) => void;
    onClose: () => void;
}

export const StatePropertiesEditor: React.FC<StatePropertiesEditorProps> = (props) => {
    const { workflowDefinition, stateIdToEdit, onChange, onClose } = props;
    const classes = useClasses();

    return (
        <Drawer
            type="overlay"
            separator
            size="large"
            open={!!stateIdToEdit}
            onOpenChange={onClose}
            position="end"
            className={classes.drawer}
        >
            <DrawerHeader className={classes.header}>
                <DrawerHeaderTitle
                    action={<Button appearance="subtle" icon={<Dismiss24Regular />} onClick={onClose} />}
                >
                    Edit State Configuration
                </DrawerHeaderTitle>
            </DrawerHeader>
            <DrawerBody>
                <div className={classes.body}>
                    {stateIdToEdit && (
                        <WorkflowStateEditor
                            workflowDefinition={workflowDefinition}
                            stateIdToEdit={stateIdToEdit}
                            onChange={(newValue) => {
                                onChange(newValue);
                            }}
                        />
                    )}
                </div>
            </DrawerBody>
        </Drawer>
    );
};
