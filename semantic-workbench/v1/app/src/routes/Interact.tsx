// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useParams } from 'react-router-dom';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { InteractCanvas } from '../components/Conversations/Canvas/InteractCanvas';
import { ConversationShare } from '../components/Conversations/ConversationShare';
import { InteractHistory } from '../components/Conversations/InteractHistory';
import { InteractInput } from '../components/Conversations/InteractInput';
import { useSiteUtility } from '../libs/useSiteUtility';
import {
    useGetAssistantsInConversationQuery,
    useGetConversationFilesQuery,
    useGetConversationParticipantMeQuery,
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
});

export const Interact: React.FC = () => {
    const { conversationId } = useParams();
    if (!conversationId) {
        throw new Error('Conversation ID is required');
    }

    const classes = useClasses();
    const {
        data: assistants,
        error: assistantsError,
        isLoading: isLoadingAssistants,
    } = useGetAssistantsInConversationQuery(conversationId);
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
    const {
        currentData: participantMe,
        isLoading: isLoadingParticipantMe,
        error: participantMeError,
    } = useGetConversationParticipantMeQuery(conversationId);

    const siteUtility = useSiteUtility();

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

    if (participantMeError) {
        const errorMessage = JSON.stringify(participantMeError);
        throw new Error(`Error loading participant: ${errorMessage}`);
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

    if (
        isLoadingAssistants ||
        isLoadingConversation ||
        isLoadingConversationParticipants ||
        isLoadingConversationFiles ||
        isLoadingParticipantMe ||
        !assistants ||
        !conversation ||
        !conversationParticipants ||
        !conversationFiles ||
        !participantMe
    ) {
        return (
            <AppView title="Interact">
                <Loading />
            </AppView>
        );
    }

    const readOnly = participantMe.conversationPermission === 'read';

    const conversationAssistants = assistants.filter((assistant) =>
        conversationParticipants.some(
            (conversationParticipant) => conversationParticipant.active && conversationParticipant.id === assistant.id,
        ),
    );
    const actions = {
        items: [<ConversationShare key="share" iconOnly conversation={conversation} />],
    };

    return (
        <AppView title={conversation.title} actions={actions} fullSizeContent>
            <div className={classes.root}>
                <div className={classes.main}>
                    <div className={classes.history}>
                        <div className={classes.historyContent}>
                            <InteractHistory
                                readOnly={readOnly}
                                conversation={conversation}
                                participants={conversationParticipants}
                            />
                        </div>
                    </div>
                    <div className={classes.input}>
                        <InteractInput readOnly={readOnly} conversationId={conversationId} />
                    </div>
                </div>
                <InteractCanvas
                    readOnly={readOnly}
                    conversation={conversation}
                    conversationParticipants={conversationParticipants}
                    conversationFiles={conversationFiles}
                    conversationAssistants={conversationAssistants}
                />
            </div>
        </AppView>
    );
};
