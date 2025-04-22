// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { useGetConversationStateDescriptionsQuery } from '../../../services/workbench';
import { ErrorMessageBar } from '../../App/ErrorMessageBar';
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
    const [stateDescriptionsErrorMessage, setStateDescriptionsErrorMessage] = React.useState<string>();

    const {
        data: stateDescriptions,
        error: stateDescriptionsError,
        isLoading: isLoadingStateDescriptions,
    } = useGetConversationStateDescriptionsQuery({ assistantId: assistant.id, conversationId: conversationId });

    React.useEffect(() => {
        const errorMessage = stateDescriptionsError ? JSON.stringify(stateDescriptionsError) : undefined;
        if (stateDescriptionsErrorMessage !== errorMessage) {
            setStateDescriptionsErrorMessage(errorMessage);
        }
    }, [stateDescriptionsError, stateDescriptionsErrorMessage]);

    // watching fetching instead of load, to avoid passing the old data on assistant id change
    if (isLoadingStateDescriptions && !stateDescriptionsErrorMessage) {
        return <Loading />;
    }

    const enabledStateDescriptions = stateDescriptions?.filter((stateDescription) => stateDescription.enabled) || [];

    return (
        <div className={classes.inspectors}>
            {enabledStateDescriptions.length === 0 ? (
                stateDescriptionsErrorMessage ? (
                    <ErrorMessageBar title="Failed to load assistant states" error={stateDescriptionsErrorMessage} />
                ) : (
                    <div>No states found for this assistant</div>
                )
            ) : (
                <AssistantInspectorList
                    conversationId={conversationId}
                    assistant={assistant}
                    stateDescriptions={enabledStateDescriptions}
                />
            )}
        </div>
    );
};
