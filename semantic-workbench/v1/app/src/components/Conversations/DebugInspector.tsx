// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Tooltip,
    makeStyles,
} from '@fluentui/react-components';
import { Info16Regular } from '@fluentui/react-icons';
import React from 'react';
import { CodeContentRenderer } from './ContentRenderers/CodeContentRenderer';
import { ContentRenderer } from './ContentRenderers/ContentRenderer';

const useClasses = makeStyles({
    root: {
        maxWidth: 'calc(100vw - 32px)',
        minWidth: 'min(600px, 100vw)',
        width: 'fit-content',
    },
});

interface DebugInspectorProps {
    debug?: { [key: string]: any };
    trigger?: JSX.Element;
}

export const DebugInspector: React.FC<DebugInspectorProps> = (props) => {
    const { debug, trigger } = props;
    const classes = useClasses();

    if (!debug) {
        return null;
    }

    return (
        <Dialog>
            <DialogTrigger>
                {trigger || (
                    <Tooltip
                        content="Display debug information to indicate how this content was created."
                        relationship="label"
                    >
                        <Button appearance="subtle" size="small" icon={<Info16Regular />} />
                    </Tooltip>
                )}
            </DialogTrigger>
            <DialogSurface className={classes.root}>
                <DialogBody>
                    <DialogTitle>Debug Inspection</DialogTitle>
                    <DialogContent>
                        {debug.content ? (
                            <ContentRenderer content={debug.content} contentType={debug.contentType} />
                        ) : (
                            <CodeContentRenderer content={JSON.stringify(debug, null, 2)} language="json" />
                        )}
                    </DialogContent>
                    <DialogActions>
                        <DialogTrigger disableButtonEnhancement>
                            <Button appearance="primary">Close</Button>
                        </DialogTrigger>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
