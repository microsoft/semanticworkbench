// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, makeStyles, Text } from '@fluentui/react-components';

import { diffJson } from 'diff';
import React from 'react';
import { Utility } from '../../libs/Utility';
import { CommandButton } from '../App/CommandButton';
import { DiffRenderer } from '../Conversations/ContentRenderers/DiffRenderer';

const useClasses = makeStyles({
    dialogSurface: {
        maxWidth: 'calc(100vw - 32px)',
        minWidth: 'min(600px, 100vw)',
        width: 'fit-content',
    },
    dialogContent: {
        height: 'calc(100vh - 150px)',
        width: 'calc(100vw - 100px)',
        paddingRight: '8px',
        boxSizing: 'border-box',
    },
    configDiff: {
        maxHeight: 'calc(100vh - 250px)',
        overflowY: 'auto',
    },
    diffView: {
        width: '100%',
    },
});

interface ApplyConfigButtonProps {
    label?: string;
    confirmMessage?: string;
    currentConfig?: object;
    newConfig: object;
    onApply?: (config: object) => void;
}

export const ApplyConfigButton: React.FC<ApplyConfigButtonProps> = (props) => {
    const { label, confirmMessage, currentConfig, newConfig, onApply } = props;
    const classes = useClasses();
    const [diffCount, setDiffCount] = React.useState<number>(0);

    React.useEffect(() => {
        if (currentConfig && newConfig) {
            const changes = diffJson(currentConfig, newConfig);
            // Count the number of changed values in the configuration diff
            // Note that the diff is a nested dictionary of changed values
            // that contain any combination of the oldValue and/or newValue
            // so we are really just counting if either oldValue or newValue is present
            // but do not count them twice if both are present
            const changeCount = changes.reduce((count, change) => count + (change.added ? 1 : 0), 0);
            setDiffCount(changeCount);
        }
    }, [currentConfig, newConfig]);

    const handleApply = React.useCallback(() => {
        onApply?.(newConfig);
    }, [newConfig, onApply]);

    const defaultLabel = 'Apply configuration';
    const title = `${label ?? defaultLabel}: ${diffCount} changes`;

    return (
        <>
            <CommandButton
                disabled={diffCount === 0}
                description="Apply configuration"
                label={title}
                dialogContent={{
                    title,
                    content: (
                        <>
                            <p>
                                <Text>{confirmMessage || 'Are you sure you want to apply the configuration?'}</Text>
                            </p>
                            <p>
                                <Text>The following values will be affected:</Text>
                            </p>
                            <div className={classes.configDiff}>
                                <DiffRenderer
                                    source={{
                                        content: JSON.stringify(Utility.sortKeys(currentConfig), null, 2),
                                        label: 'Current',
                                    }}
                                    compare={{
                                        content: JSON.stringify(Utility.sortKeys(newConfig), null, 2),
                                        label: 'New',
                                    }}
                                    wrapLines
                                />
                            </div>
                        </>
                    ),
                    closeLabel: 'Cancel',
                    additionalActions: [
                        <DialogTrigger key="apply" disableButtonEnhancement>
                            <Button appearance="primary" onClick={handleApply}>
                                Confirm
                            </Button>
                        </DialogTrigger>,
                    ],
                    classNames: { dialogSurface: classes.dialogSurface, dialogContent: classes.dialogContent },
                }}
            />
        </>
    );
};
