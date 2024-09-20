// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    SelectTabData,
    SelectTabEvent,
    SelectTabEventHandler,
    Tab,
    TabList,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { BookInformation24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useCanvasController } from '../../../libs/useCanvasController';
import { AssistantStateDescription } from '../../../models/AssistantStateDescription';
import { useAppSelector } from '../../../redux/app/hooks';
import { AssistantInspector } from './AssistantInspector';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateColumns: '1fr',
        gridTemplateRows: 'auto 1fr',
        height: '100%',
    },
    header: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    headerContent: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: tokens.spacingHorizontalM,
        ...shorthands.padding(tokens.spacingVerticalS),
        ...shorthands.borderBottom(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
    },
    body: {
        overflowY: 'auto',
        height: '100%',
        maxHeight: '100%',
    },
});

interface AssistantInspectorListProps {
    conversationId: string;
    stateDescriptions: AssistantStateDescription[];
    hideCloseButton?: boolean;
}

export const AssistantInspectorList: React.FC<AssistantInspectorListProps> = (props) => {
    const { conversationId, stateDescriptions, hideCloseButton } = props;
    const classes = useClasses();
    const { conversationCanvasState } = useAppSelector((state) => state.app);
    const canvasController = useCanvasController();

    const onTabSelect: SelectTabEventHandler = (_event: SelectTabEvent, data: SelectTabData) => {
        canvasController.transitionToState({ assistantStateId: data.value as string });
    };

    const selectedTab = conversationCanvasState?.assistantStateId ?? stateDescriptions[0].id;
    const selectedStateDescription = stateDescriptions.find((stateDescription) => stateDescription.id === selectedTab);

    if (!conversationCanvasState?.assistantId) return null;

    if (stateDescriptions.length === 0) {
        return (
            <div className={classes.root}>
                <div className={classes.header}>
                    <div className={classes.headerContent}>
                        <div>No assistant state inspectors available</div>
                        {!hideCloseButton && (
                            <Button
                                appearance="secondary"
                                icon={<BookInformation24Regular />}
                                onClick={() => canvasController.transitionToState({ open: false })}
                            />
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <div className={classes.headerContent}>
                    <TabList selectedValue={selectedTab} onTabSelect={onTabSelect} size="small">
                        {stateDescriptions
                            .filter((stateDescription) => stateDescription.id !== 'config')
                            .map((stateDescription) => (
                                <Tab key={stateDescription.id} value={stateDescription.id}>
                                    {stateDescription.displayName}
                                </Tab>
                            ))}
                    </TabList>
                    {!hideCloseButton && (
                        <Button
                            appearance="secondary"
                            icon={<BookInformation24Regular />}
                            onClick={() => canvasController.transitionToState({ open: false })}
                        />
                    )}
                </div>
            </div>
            {selectedStateDescription && (
                <div className={classes.body}>
                    <AssistantInspector
                        assistantId={conversationCanvasState?.assistantId}
                        conversationId={conversationId}
                        stateDescription={selectedStateDescription}
                    />
                </div>
            )}
        </div>
    );
};
