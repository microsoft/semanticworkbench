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
import { Dismiss24Regular, SettingsRegular } from '@fluentui/react-icons';
import React from 'react';
import { WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { CommandButton } from '../../App/CommandButton';
import { WorkflowDefinitionEditor } from './WorkflowDefinitionEditor';

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

interface DefinitionPropertiesEditorProps {
    workflowDefinition: WorkflowDefinition;
    onChange: (newValue: WorkflowDefinition) => void;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
}

export const DefinitionPropertiesEditor: React.FC<DefinitionPropertiesEditorProps> = (props) => {
    const { workflowDefinition, onChange, open, onOpenChange } = props;
    const classes = useClasses();
    const [isOpen, setIsOpen] = React.useState(open ?? false);

    React.useEffect(() => {
        setIsOpen(open ?? false);
    }, [open]);

    const handleOpenChange = (newOpen: boolean) => {
        setIsOpen(newOpen);
        if (onOpenChange) {
            onOpenChange(newOpen);
        }
    };

    return (
        <>
            <CommandButton
                description="Edit Workflow Configuration"
                icon={<SettingsRegular />}
                iconOnly
                asToolbarButton
                label="Edit"
                onClick={() => handleOpenChange(true)}
            />
            <Drawer
                type="overlay"
                separator
                size="large"
                open={isOpen}
                onOpenChange={() => handleOpenChange(false)}
                position="end"
                className={classes.drawer}
            >
                <DrawerHeader className={classes.header}>
                    <DrawerHeaderTitle
                        action={
                            <Button
                                appearance="subtle"
                                icon={<Dismiss24Regular />}
                                onClick={() => handleOpenChange(false)}
                            />
                        }
                    >
                        Edit Workflow Configuration
                    </DrawerHeaderTitle>
                </DrawerHeader>
                <DrawerBody>
                    <div className={classes.body}>
                        <WorkflowDefinitionEditor
                            workflowDefinition={workflowDefinition}
                            onChange={(newValue) => {
                                onChange(newValue);
                            }}
                        />
                    </div>
                </DrawerBody>
            </Drawer>
        </>
    );
};
