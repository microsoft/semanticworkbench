// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Title3, tokens } from '@fluentui/react-components';
import React from 'react';
import { useParams } from 'react-router-dom';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { InteractCanvas } from '../components/Conversations/Canvas/InteractCanvas';
import { ConversationRename } from '../components/Conversations/ConversationRename';
import { ConversationShare } from '../components/Conversations/ConversationShare';
import { InteractHistory } from '../components/Conversations/InteractHistory';
import { InteractInput } from '../components/Conversations/InteractInput';
import { useGetAssistantCapabilities } from '../libs/useAssistantCapabilities';
import { useSiteUtility } from '../libs/useSiteUtility';
import { Assistant } from '../models/Assistant';
import { useAppSelector } from '../redux/app/hooks';
import {
    useGetAssistantsInConversationQuery,
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
        // to let the controls anchor to the corner
        position: 'relative',
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
    title: {
        color: tokens.colorNeutralForegroundOnBrand,
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
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
        refetch: refetchAssistants,
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
    const localUserId = useAppSelector((state) => state.localUser.id);
    const { data: assistantCapabilities, isFetching: isFetchingAssistantCapabilities } = useGetAssistantCapabilities(
        assistants ?? [],
        { skip: isLoadingAssistants || assistantsError !== undefined },
    );

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

    const conversationAssistants = React.useMemo(() => {
        const results: Assistant[] = [];

        // If the conversation or assistants are not loaded, return early
        if (!conversationParticipants || !assistants) {
            return results;
        }

        for (let conversationParticipant of conversationParticipants) {
            // Only include active assistants
            if (!conversationParticipant.active || conversationParticipant.role !== 'assistant') continue;

            // Find the assistant in the list of assistants
            const assistant = assistants.find((assistant) => assistant.id === conversationParticipant.id);

            if (assistant) {
                // If the assistant is found, add it to the list of assistants
                results.push(assistant);
            } else {
                // If the assistant is not found, refetch the assistants
                refetchAssistants();
                // Return early to avoid returning an incomplete list of assistants
                return;
            }
        }

        return results.sort((a, b) => a.name.localeCompare(b.name));
    }, [assistants, conversationParticipants, refetchAssistants]);

    if (
        isLoadingAssistants ||
        isLoadingConversation ||
        isLoadingConversationParticipants ||
        isLoadingConversationFiles ||
        isFetchingAssistantCapabilities ||
        !assistants ||
        !assistantCapabilities ||
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
    const readOnly = conversation.conversationPermission === 'read';

    const actions = {
        items: [<ConversationShare key="share" iconOnly conversation={conversation} />],
    };

    return (
        <AppView
            title={
                <div className={classes.title}>
                    <ConversationRename
                        id={conversation.id}
                        value={conversation.title}
                        disabled={conversation.ownerId !== localUserId}
                        iconOnly
                    />
                    <Title3>{conversation.title}</Title3>
                </div>
            }
            actions={actions}
            fullSizeContent
        >
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
                        <InteractInput
                            readOnly={readOnly}
                            conversationId={conversationId}
                            assistantCapabilities={assistantCapabilities}
                        />
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
