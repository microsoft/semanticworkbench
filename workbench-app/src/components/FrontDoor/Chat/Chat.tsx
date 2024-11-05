// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useGetAssistantCapabilities } from '../../../libs/useAssistantCapabilities';
import { useParticipantUtility } from '../../../libs/useParticipantUtility';
import { Assistant } from '../../../models/Assistant';
import { useAppSelector } from '../../../redux/app/hooks';
import {
    useGetAssistantsInConversationQuery,
    useGetConversationFilesQuery,
    useGetConversationParticipantsQuery,
    useGetConversationQuery,
} from '../../../services/workbench';
import { ExperimentalNotice } from '../../App/ExperimentalNotice';
import { Loading } from '../../App/Loading';
import { ConversationShare } from '../../Conversations/ConversationShare';
import { InteractHistory } from '../../Conversations/InteractHistory';
import { InteractInput } from '../../Conversations/InteractInput';
import { ParticipantAvatarGroup } from '../../Conversations/ParticipantAvatarGroup';
import { ChatCanvas } from './ChatCanvas';
import { ChatControls } from './ChatControls';

const useClasses = makeStyles({
    // centered content, two rows
    // first is for chat history, fills the space and scrolls
    // second is for input, anchored to the bottom
    root: {
        position: 'relative',
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'row',
        height: '100%',
    },
    header: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        pointerEvents: 'none',
        zIndex: tokens.zIndexOverlay,
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        backgroundImage: `linear-gradient(to bottom, ${tokens.colorNeutralBackground1}, ${tokens.colorNeutralBackground1}, transparent, transparent)`,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM, tokens.spacingVerticalXXXL),
    },
    headerControls: {
        position: 'relative',
        pointerEvents: 'auto',
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalM,
        justifyContent: 'center',
        flex: '1 1 auto',
        overflowX: 'hidden',

        '&.before': {
            left: 0,
            flex: '0 0 auto',
        },

        '&.center': {
            overflow: 'visible',
        },

        '&.after': {
            right: 0,
            flex: '0 0 auto',
        },
    },
    centerContent: {
        position: 'absolute',
        top: 0,
        left: tokens.spacingHorizontalM,
        right: tokens.spacingHorizontalM,
    },
    content: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
    },
    canvas: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
    },
    history: {
        flex: '1 1 auto',
        position: 'relative',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        gap: tokens.spacingVerticalM,
    },
    historyContent: {
        // do not use flexbox here, it breaks the virtuoso
        width: '100%',
        maxWidth: '800px',
    },
    historyRoot: {
        paddingTop: tokens.spacingVerticalXXXL,
        boxSizing: 'border-box',
    },
    input: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
        ...shorthands.borderTop(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
    },
});

interface ChatProps {
    conversationId: string;
    headerBefore?: React.ReactNode;
    headerAfter?: React.ReactNode;
}

export const Chat: React.FC<ChatProps> = (props) => {
    const { conversationId, headerBefore, headerAfter } = props;
    const classes = useClasses();
    const { sortParticipants } = useParticipantUtility();
    const localUserId = useAppSelector((state) => state.localUser.id);

    const {
        data: conversation,
        error: conversationError,
        isLoading: conversationIsLoading,
    } = useGetConversationQuery(conversationId, { refetchOnMountOrArgChange: true });
    const {
        data: conversationParticipants,
        error: conversationParticipantsError,
        isLoading: conversationParticipantsIsLoading,
    } = useGetConversationParticipantsQuery(conversationId);
    const {
        data: assistants,
        error: assistantsError,
        isLoading: assistantsIsLoading,
        refetch: assistantsRefetch,
    } = useGetAssistantsInConversationQuery(conversationId);
    const {
        data: conversationFiles,
        error: conversationFilesError,
        isLoading: conversationFilesIsLoading,
    } = useGetConversationFilesQuery(conversationId);

    const { data: assistantCapabilities, isFetching: assistantCapabilitiesIsFetching } =
        useGetAssistantCapabilities(assistants);

    if (conversationError) {
        const errorMessage = JSON.stringify(conversationError);
        throw new Error(`Error loading conversation (${conversationId}): ${errorMessage}`);
    }

    if (conversationParticipantsError) {
        const errorMessage = JSON.stringify(conversationParticipantsError);
        throw new Error(`Error loading conversation participants (${conversationId}): ${errorMessage}`);
    }

    if (assistantsError) {
        const errorMessage = JSON.stringify(assistantsError);
        throw new Error(`Error loading assistants (${conversationId}): ${errorMessage}`);
    }

    if (conversationFilesError) {
        const errorMessage = JSON.stringify(conversationFilesError);
        throw new Error(`Error loading conversation files (${conversationId}): ${errorMessage}`);
    }

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
                assistantsRefetch();
                // Return early to avoid returning an incomplete list of assistants
                return;
            }
        }

        return results.sort((a, b) => a.name.localeCompare(b.name));
    }, [assistants, conversationParticipants, assistantsRefetch]);

    if (
        conversationIsLoading ||
        conversationParticipantsIsLoading ||
        assistantsIsLoading ||
        conversationFilesIsLoading ||
        assistantCapabilitiesIsFetching
    ) {
        return <Loading />;
    }

    if (!conversation) {
        throw new Error(`Conversation (${conversationId}) not found`);
    }

    if (!conversationParticipants) {
        throw new Error(`Conversation participants (${conversationId}) not found`);
    }

    if (!assistants) {
        throw new Error(`Assistants (${conversationId}) not found`);
    }

    if (!conversationFiles) {
        throw new Error(`Conversation files (${conversationId}) not found`);
    }

    const readOnly = conversation.conversationPermission === 'read';

    const otherParticipants = sortParticipants(conversationParticipants).filter(
        (participant) => participant.id !== localUserId,
    );

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <div className={mergeClasses(classes.headerControls, 'before')}>{headerBefore}</div>
                <div className={mergeClasses(classes.headerControls, 'center')}>
                    <ExperimentalNotice className={classes.centerContent} />
                </div>
                <div className={mergeClasses(classes.headerControls, 'after')}>
                    {otherParticipants.length === 1 && (
                        <ParticipantAvatarGroup participants={otherParticipants} layout="spread" />
                    )}
                    {otherParticipants.length > 1 && (
                        <ParticipantAvatarGroup layout="pie" participants={otherParticipants} />
                    )}
                    <ConversationShare iconOnly conversation={conversation} />
                    <ChatControls conversationId={conversation.id} />
                    {headerAfter}
                </div>
            </div>
            <div className={classes.content}>
                <div className={classes.history}>
                    <div className={classes.historyContent}>
                        <InteractHistory
                            className={classes.historyRoot}
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
            <div className={classes.canvas}>
                <ChatCanvas
                    readOnly={readOnly}
                    conversation={conversation}
                    conversationParticipants={conversationParticipants}
                    conversationFiles={conversationFiles}
                    conversationAssistants={conversationAssistants}
                />
            </div>
        </div>
    );
};
