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
import { useCanvasController } from '../../libs/useCanvasController';
import { AssistantStateDescription } from '../../models/AssistantStateDescription';
import { useAppSelector } from '../../redux/app/hooks';
import { Inspector } from './Inspector';

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

interface InspectorListProps {
    conversationId: string;
    stateDescriptions: AssistantStateDescription[];
    hideCloseButton?: boolean;
}

export const InspectorList: React.FC<InspectorListProps> = (props) => {
    const { conversationId, stateDescriptions, hideCloseButton } = props;
    const classes = useClasses();
    const { conversationCanvasState } = useAppSelector((state) => state.app);
    const canvasController = useCanvasController();

    const onTabSelect: SelectTabEventHandler = (_event: SelectTabEvent, data: SelectTabData) =>
        canvasController.transitionToState({ assistantStateId: data.value as string });

    const selectedTab = conversationCanvasState?.assistantStateId ?? stateDescriptions[0].id;
    const selectedStateDescription = stateDescriptions.find((stateDescription) => stateDescription.id === selectedTab);

    if (!conversationCanvasState?.assistantId) return null;

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
                    <Inspector
                        assistantId={conversationCanvasState?.assistantId}
                        conversationId={conversationId}
                        stateDescription={selectedStateDescription}
                    />
                </div>
            )}
        </div>
    );
};
