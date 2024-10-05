// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { useGetConversationStateDescriptionsQuery } from '../../../services/workbench';
import { Loading } from '../../App/Loading';
import { AssistantInspectorList } from './AssistantInspectorList';

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

interface AssistantCanvasProps {
    assistant: Assistant;
    conversationId: string;
}

export const AssistantCanvas: React.FC<AssistantCanvasProps> = (props) => {
    const { assistant, conversationId } = props;
    const classes = useClasses();

    const {
        data: stateDescriptions,
        error: stateDescriptionsError,
        isFetching: isFetchingStateDescriptions,
    } = useGetConversationStateDescriptionsQuery({ assistantId: assistant.id, conversationId: conversationId });

    if (stateDescriptionsError) {
        const errorMessage = JSON.stringify(stateDescriptionsError);
        throw new Error(`Error loading assistant state descriptions: ${errorMessage}`);
    }

    // watching fetching instead of load, to avoid passing the old data on assistant id change
    if (isFetchingStateDescriptions) {
        return <Loading />;
    }

    return (
        <div className={classes.inspectors}>
            {!stateDescriptions || stateDescriptions.length === 0 ? (
                <div>No states found for this assistant</div>
            ) : (
                <AssistantInspectorList
                    conversationId={conversationId}
                    assistant={assistant}
                    stateDescriptions={stateDescriptions}
                />
            )}
        </div>
    );
};
