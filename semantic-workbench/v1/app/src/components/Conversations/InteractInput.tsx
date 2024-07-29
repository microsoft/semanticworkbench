// Copyright (c) Microsoft. All rights reserved.

import {
    ChatInput,
    ChatInputEntityNode,
    ChatInputSubmitEvents,
    ChatInputTokenNode,
    ChatInputValueData,
    LexicalEditor,
    LexicalEditorRefPlugin,
} from '@fluentui-copilot/react-copilot';
import { Dropdown, Option, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { getEncoding } from 'js-tiktoken';
import { CLEAR_EDITOR_COMMAND } from 'lexical';
import React from 'react';
import { Constants } from '../../Constants';
import { useLocalUserAccount } from '../../libs/useLocalUserAccount';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppDispatch } from '../../redux/app/hooks';
import {
    updateGetConversationMessagesQueryData,
    useCreateConversationMessageMutation,
    useGetConversationMessagesQuery,
    useGetConversationParticipantsQuery,
} from '../../services/workbench';
import { ClearEditorPlugin } from './ChatInputPlugins/ClearEditorPlugin';
import { ParticipantMentionsPlugin } from './ChatInputPlugins/ParticipantMentionsPlugin';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
        gap: tokens.spacingVerticalS,
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'stretch',
        width: '100%',
        maxWidth: `${Constants.app.maxContentWidth}px`,
        gap: tokens.spacingVerticalS,
        ...shorthands.padding(0, tokens.spacingHorizontalXXL, 0, tokens.spacingHorizontalM),
        boxSizing: 'border-box',
    },
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        width: '100%',
        gap: tokens.spacingHorizontalS,
    },
    rowEnd: {
        justifyContent: 'end',
    },
    fullWidth: {
        width: '100%',
        maxWidth: '100%',
    },
    commandTextbox: {
        '& [role=textbox]': {
            fontFamily: 'monospace',
        },
    },
});

const directedAtDefaultKey = 'all';
const directedAtDefaultValue = 'All assistants';

interface InteractInputProps {
    conversationId: string;
    additionalContent?: React.ReactNode;
}

export const InteractInput: React.FC<InteractInputProps> = (props) => {
    const { conversationId, additionalContent } = props;
    const classes = useClasses();
    const [createMessage] = useCreateConversationMessageMutation();
    const [messageTypeValue, setMessageTypeValue] = React.useState<'Chat' | 'Command'>('Chat');
    const [tokenCount, setTokenCount] = React.useState(0);
    const [directedAtId, setDirectedAtId] = React.useState<string>(directedAtDefaultKey);
    const [directedAtName, setDirectedAtName] = React.useState<string>(directedAtDefaultValue);
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const editorRef = React.useRef<LexicalEditor | null>();
    const dispatch = useAppDispatch();
    const localUserAccount = useLocalUserAccount();
    const userId = localUserAccount.getUserId();

    const {
        data: conversationMessages,
        isLoading: isConversationMessagesLoading,
        error: conversationMessagesError,
    } = useGetConversationMessagesQuery(conversationId);

    const {
        data: participants,
        isLoading: isParticipantsLoading,
        error: participantsError,
    } = useGetConversationParticipantsQuery(conversationId);

    if (conversationMessagesError) {
        const errorMessage = JSON.stringify(conversationMessagesError);
        console.error(`Failed to load conversation messages: ${errorMessage}`);
    }

    if (participantsError) {
        const errorMessage = JSON.stringify(participantsError);
        console.error(`Failed to load conversation participants: ${errorMessage}`);
    }

    const tokenizer = React.useMemo(() => getEncoding('cl100k_base'), []);

    if (isConversationMessagesLoading || isParticipantsLoading) {
        return null;
    }

    const handleSend = (_event: ChatInputSubmitEvents, data: ChatInputValueData) => {
        if (data.value.trim() === '' || isSubmitting) {
            return;
        }

        (async () => {
            setIsSubmitting(true);
            const content = data.value.trim();
            let metadata: Record<string, any> | undefined =
                directedAtId === directedAtDefaultKey ? undefined : { directed_at: directedAtId };

            const messageType = messageTypeValue.toLowerCase() as 'chat' | 'command';

            const mentions: string[] = [];
            const nodes = editorRef.current?.getEditorState()._nodeMap;
            if (nodes) {
                for (const node of nodes.values()) {
                    if (node.__type !== 'entity') continue;
                    try {
                        const nodeData = (node as any).__data as { type: string; participant: ConversationParticipant };
                        if (nodeData.type === 'mention') {
                            mentions.push(nodeData.participant.id);
                        }
                    } catch (error) {
                        // ignore, not a mention
                    }
                }
            }

            if (mentions.length > 0) {
                if (!metadata) {
                    metadata = {};
                }
                metadata.mentions = mentions;
            }

            // optimistically update the UI
            // this will be replaced by the actual message when the mutation completes
            // need to define the extra fields for the message such as sender, timestamp, etc.
            // so that the message can be rendered correctly
            dispatch(
                updateGetConversationMessagesQueryData(conversationId, [
                    ...(conversationMessages ?? []),
                    {
                        id: 'optimistic',
                        sender: {
                            participantId: userId,
                            participantRole: 'user',
                        },
                        timestamp: new Date().toISOString(),
                        messageType,
                        content,
                        contentType: 'text/plain',
                        filenames: [],
                        metadata,
                    },
                ]),
            );

            editorRef.current?.dispatchCommand(CLEAR_EDITOR_COMMAND, undefined);

            await createMessage({
                conversationId,
                content,
                messageType,
                metadata,
            });

            // reset for the next message
            setMessageTypeValue('Chat');

            setIsSubmitting(false);
        })();
    };

    const updateInput = (newInput: string) => {
        const newMessageType = newInput.startsWith('/') ? 'Command' : 'Chat';
        if (newMessageType !== messageTypeValue) {
            setMessageTypeValue(newMessageType);
        }

        const tokens = tokenizer.encode(newInput);
        setTokenCount(tokens.length);
    };

    return (
        <div className={classes.root}>
            <div className={classes.content}>
                {/* // this is for injecting controls for supporting features like workflow */}
                {additionalContent}
                <div className={classes.row}>
                    <div className={classes.row}>Message type: {messageTypeValue}</div>
                    <div className={mergeClasses(classes.row, classes.rowEnd)}>
                        <div>Directed to:</div>
                        <div>
                            <Dropdown
                                disabled={
                                    participants?.filter((participant) => participant.role === 'assistant').length ===
                                        0 || messageTypeValue !== 'Command'
                                }
                                className={classes.fullWidth}
                                placeholder="Select participant"
                                value={directedAtName}
                                selectedOptions={[directedAtId]}
                                onOptionSelect={(_event, data) => {
                                    setDirectedAtId(data.optionValue as string);
                                    setDirectedAtName(data.optionText as string);
                                }}
                            >
                                <Option key={directedAtDefaultKey} value={directedAtDefaultKey}>
                                    {directedAtDefaultValue}
                                </Option>
                                {participants
                                    ?.filter((participant) => participant.role === 'assistant')
                                    .map((participant) => (
                                        <Option key={participant.id} value={participant.id}>
                                            {participant.name}
                                        </Option>
                                    ))}
                            </Dropdown>
                        </div>
                    </div>
                </div>
                <ChatInput
                    className={mergeClasses(
                        classes.fullWidth,
                        messageTypeValue === 'Command' ? classes.commandTextbox : '',
                    )}
                    onChange={(_event, data) => updateInput(data.value)}
                    maxLength={Constants.app.maxInputLength}
                    characterCount={tokenCount}
                    count={<span>{tokenCount} tokens</span>}
                    placeholderValue="Ask a question or request assistance or type / to enter a command."
                    customNodes={[ChatInputTokenNode, ChatInputEntityNode]}
                    onSubmit={handleSend}
                    trimWhiteSpace
                    showCount
                    disableSend={isSubmitting}
                >
                    <ClearEditorPlugin />
                    {participants && (
                        <ParticipantMentionsPlugin
                            participants={participants.filter((participant) => participant.id !== userId)}
                            parent={document.getElementById('app')}
                        />
                    )}
                    <LexicalEditorRefPlugin editorRef={editorRef} />
                </ChatInput>
            </div>
        </div>
    );
};
