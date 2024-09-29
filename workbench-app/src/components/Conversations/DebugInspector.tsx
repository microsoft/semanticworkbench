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
import { JSONTree } from 'react-json-tree';
import { ContentRenderer } from './ContentRenderers/ContentRenderer';

const useClasses = makeStyles({
    root: {
        maxWidth: 'calc(100vw - 32px)',
        minWidth: 'min(600px, 100vw)',
        width: 'fit-content',
    },
    content: {
        height: 'calc(100vh - 150px)',
        width: 'calc(100vw - 100px)',
        paddingRight: '8px',
        boxSizing: 'border-box',
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
                            <div className={classes.content}>
                                <JSONTree
                                    data={debug}
                                    hideRoot
                                    invertTheme
                                    collectionLimit={10}
                                    shouldExpandNodeInitially={(keyPath /*, data, level*/) => {
                                        // Leave any of the following keys collapsed
                                        const keepCollapsed = ['content_safety', 'image_url'];
                                        return !keepCollapsed.includes(String(keyPath[0]));
                                    }}
                                    theme={{
                                        base00: '#000000',
                                        base01: '#303030',
                                        base02: '#505050',
                                        base03: '#b0b0b0',
                                        base04: '#d0d0d0',
                                        base05: '#e0e0e0',
                                        base06: '#f5f5f5',
                                        base07: '#ffffff',
                                        base08: '#fb0120',
                                        base09: '#fc6d24',
                                        base0A: '#fda331',
                                        base0B: '#a1c659',
                                        base0C: '#76c7b7',
                                        base0D: '#6fb3d2',
                                        base0E: '#d381c3',
                                        base0F: '#be643c',
                                    }}
                                />
                            </div>
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
