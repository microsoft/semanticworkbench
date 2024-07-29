// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { AssistantStateDescription } from '../../models/AssistantStateDescription';
import { useGetConversationStateDescriptionsQuery } from '../../services/workbench';
import { InspectorList } from './InspectorList';

const useClasses = makeStyles({
    inspectors: {
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        height: '100%',
        maxHeight: '100%',
        overflowY: 'auto',
        overflowX: 'hidden',
    },
});

interface InteractInspectorsProps {
    assistant: Assistant;
    conversationId: string;
    onOpenChange?: (open: boolean) => void;
}

export const InteractInspectors: React.FC<InteractInspectorsProps> = (props) => {
    const { assistant, conversationId, onOpenChange } = props;
    const classes = useClasses();
    const [filteredStateDescriptions, setFilteredStateDescriptions] = React.useState<AssistantStateDescription[]>([]);

    const {
        data: stateDescriptions,
        error: stateDescriptionsError,
        isLoading: isLoadingStateDescriptions,
    } = useGetConversationStateDescriptionsQuery({ assistantId: assistant.id, conversationId: conversationId });

    if (stateDescriptionsError) {
        const errorMessage = JSON.stringify(stateDescriptionsError);
        throw new Error(`Error loading assistant state descriptions: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (isLoadingStateDescriptions) return;
        setFilteredStateDescriptions(
            stateDescriptions?.filter((stateDescription) => stateDescription.id !== 'config') ?? [],
        );
    }, [isLoadingStateDescriptions, stateDescriptions]);

    if (filteredStateDescriptions.length === 0) return null;

    return (
        <div className={classes.inspectors}>
            <InspectorList
                assistantId={assistant.id}
                conversationId={conversationId}
                stateDescriptions={filteredStateDescriptions}
                onOpenChange={onOpenChange}
            />
        </div>
    );
};
