// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useParams } from 'react-router-dom';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { CanvasControls } from '../components/Conversations/Canvas/CanvasControls';
import { GeneralCanvas } from '../components/Conversations/Canvas/GeneralCanvas';
import { ConversationShare } from '../components/Conversations/ConversationShare';
import { InteractHistory } from '../components/Conversations/InteractHistory';
import { InteractInput } from '../components/Conversations/InteractInput';
import { WorkbenchEventSource } from '../libs/WorkbenchEventSource';
import { useEnvironment } from '../libs/useEnvironment';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useAppDispatch } from '../redux/app/hooks';
import { setCanvasState } from '../redux/features/app/appSlice';
import {
    useGetAssistantsQuery,
    useGetConversationFilesQuery,
    useGetConversationParticipantsQuery,
    useGetConversationQuery,
} from '../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        width: '100%',
        height: '100%',
    },
    main: {
        position: 'relative',
        display: 'grid',
        gridTemplateColumns: '1fr',
        gridTemplateRows: '1fr auto',
        width: '100%',
        height: '100%',
    },
    history: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        gap: tokens.spacingVerticalM,
    },
    historyContent: {
        // do not use flexbox here, it breaks the virtuoso
        width: '100%',
        maxWidth: `${Constants.app.maxContentWidth}px`,
        ...shorthands.padding(0, tokens.spacingHorizontalXS, 0, 0),
    },
    input: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
        ...shorthands.borderTop(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
        ...shorthands.borderBottom(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
    },
    canvas: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        height: '100%',
    },
    controls: {
        position: 'absolute',
        top: 0,
        right: 0,
    },
});

export const Interact: React.FC = () => {
    const { conversationId } = useParams();
    if (!conversationId) {
        throw new Error('Conversation ID is required');
    }

    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { data: assistants, error: assistantsError, isLoading: isLoadingAssistants } = useGetAssistantsQuery();
    const {
        data: conversation,
        error: conversationError,
        isLoading: isLoadingConversation,
    } = useGetConversationQuery(conversationId);
    const {
        data: conversationParticipants,
        error: conversationParticipantsError,
        isLoading: isLoadingConversationParticipants,
    } = useGetConversationParticipantsQuery(conversationId);
    const {
        data: conversationFiles,
        error: conversationFilesError,
        isLoading: isLoadingConversationFiles,
    } = useGetConversationFilesQuery(conversationId);

    const siteUtility = useSiteUtility();
    const environment = useEnvironment();

    if (assistantsError) {
        const errorMessage = JSON.stringify(assistantsError);
        throw new Error(`Error loading assistants: ${errorMessage}`);
    }

    if (conversationError) {
        const errorMessage = JSON.stringify(conversationError);
        throw new Error(`Error loading conversation: ${errorMessage}`);
    }

    if (conversationParticipantsError) {
        const errorMessage = JSON.stringify(conversationParticipantsError);
        throw new Error(`Error loading participants: ${errorMessage}`);
    }

    if (conversationFilesError) {
        const errorMessage = JSON.stringify(conversationFilesError);
        throw new Error(`Error loading conversation files: ${errorMessage}`);
    }

    if (!isLoadingAssistants && (!assistants || assistants.length === 0)) {
        throw new Error('No assistants found');
    }

    if (!isLoadingConversation && !conversation) {
        const errorMessage = `No conversation loaded for ${conversationId}`;
        throw new Error(errorMessage);
    }

    if (!isLoadingConversationParticipants && !conversationParticipants) {
        const errorMessage = `No participants loaded for ${conversationId}`;
        throw new Error(errorMessage);
    }

    if (!isLoadingConversationFiles && !conversationFiles) {
        const errorMessage = `No conversation files loaded for ${conversationId}`;
        throw new Error(errorMessage);
    }

    React.useEffect(() => {
        if (conversation && conversationParticipants) {
            siteUtility.setDocumentTitle(conversation.title);
        }
    }, [conversation, conversationParticipants, siteUtility]);

    React.useEffect(() => {
        var workbenchEventSource: WorkbenchEventSource | undefined;

        const handleFocusEvent = (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            dispatch(
                setCanvasState({ open: true, assistantId: data['assistant_id'], assistantStateId: data['state_id'] }),
            );
        };

        (async () => {
            workbenchEventSource = await WorkbenchEventSource.createOrUpdate(environment.url, conversationId);
            workbenchEventSource.addEventListener('assistant.state.focus', handleFocusEvent);
        })();

        return () => {
            workbenchEventSource?.removeEventListener('assistant.state.focus', handleFocusEvent);
        };
    }, [environment, conversationId, dispatch]);

    if (
        isLoadingAssistants ||
        isLoadingConversation ||
        isLoadingConversationParticipants ||
        isLoadingConversationFiles ||
        !assistants ||
        !conversation ||
        !conversationParticipants ||
        !conversationFiles
    ) {
        return (
            <AppView title="Interact">
                <Loading />
            </AppView>
        );
    }

    const actions = {
        items: [<ConversationShare key="share" iconOnly conversationId={conversationId} />],
    };

    const conversationAssistants = assistants.filter((assistant) =>
        conversationParticipants.some(
            (conversationParticipant) => conversationParticipant.active && conversationParticipant.id === assistant.id,
        ),
    );

    return (
        <AppView title={conversation.title} actions={actions} fullSizeContent>
            <div className={classes.root}>
                <div className={classes.main}>
                    <div className={classes.history}>
                        <div className={classes.historyContent}>
                            <InteractHistory conversation={conversation} participants={conversationParticipants} />
                        </div>
                    </div>
                    <div className={classes.input}>
                        <InteractInput conversationId={conversationId} />
                    </div>
                </div>
                <div className={classes.canvas}>
                    <div className={classes.controls}>
                        <CanvasControls />
                    </div>
                    <GeneralCanvas
                        conversation={conversation}
                        conversationParticipants={conversationParticipants}
                        conversationFiles={conversationFiles}
                        conversationAssistants={conversationAssistants}
                        preventAssistantModifyOnParticipantIds={conversationParticipants
                            .filter((participant) => participant.active)
                            .map((participant) => participant.id)}
                    />
                </div>
            </div>
        </AppView>
    );
};
