// Copyright (c) Microsoft. All rights reserved.

import { Attachment, AttachmentList } from '@fluentui-copilot/react-attachments';
import {
    $createParagraphNode,
    $createTextNode,
    $getRoot,
    $getSelection,
    ChatInput,
    ChatInputEntityNode,
    ChatInputSubmitEvents,
    ChatInputTokenNode,
    ChatInputValueData,
    LexicalEditor,
    LexicalEditorRefPlugin,
} from '@fluentui-copilot/react-copilot';
import {
    Button,
    Dropdown,
    Option,
    Tooltip,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { Attach20Regular, DocumentRegular, Mic20Regular } from '@fluentui/react-icons';
import { getEncoding } from 'js-tiktoken';
import { CLEAR_EDITOR_COMMAND } from 'lexical';
import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import React from 'react';
import { Constants } from '../../Constants';
import { useLocalUserAccount } from '../../libs/useLocalUserAccount';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { addError } from '../../redux/features/app/appSlice';
import {
    updateGetConversationMessagesQueryData,
    useCreateConversationMessageMutation,
    useGetConversationMessagesQuery,
    useGetConversationParticipantsQuery,
    useUploadConversationFilesMutation,
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
    const { speechKey, speechRegion } = useAppSelector((state) => state.settings);
    const [createMessage] = useCreateConversationMessageMutation();
    const [uploadConversationFiles] = useUploadConversationFilesMutation();
    const [messageTypeValue, setMessageTypeValue] = React.useState<'Chat' | 'Command'>('Chat');
    const [tokenCount, setTokenCount] = React.useState(0);
    const [directedAtId, setDirectedAtId] = React.useState<string>(directedAtDefaultKey);
    const [directedAtName, setDirectedAtName] = React.useState<string>(directedAtDefaultValue);
    const [attachmentFiles, setAttachmentFiles] = React.useState<File[]>([]);
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [isListening, setIsListening] = React.useState(false);
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const editorRef = React.useRef<LexicalEditor | null>();
    const attachmentInputRef = React.useRef<HTMLInputElement>(null);
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

    React.useEffect(() => {
        if (recognizer) return;
        if (!speechKey || !speechRegion) return;

        const speechConfig = speechSdk.SpeechConfig.fromSubscription(speechKey, speechRegion);
        const speechRecognizer = new speechSdk.SpeechRecognizer(speechConfig);
        setRecognizer(speechRecognizer);
    }, [recognizer, speechKey, speechRegion]);

    const tokenizer = React.useMemo(() => getEncoding('cl100k_base'), []);

    if (isConversationMessagesLoading || isParticipantsLoading) {
        return null;
    }

    const handleSend = (_event: ChatInputSubmitEvents, data: ChatInputValueData) => {
        if (data.value.trim() === '' || isSubmitting || isListening) {
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

            // upload attachments
            const filenames = attachmentFiles.length > 0 ? attachmentFiles.map((file) => file.name) : undefined;
            const files = attachmentFiles.length > 0 ? [...attachmentFiles] : undefined;
            // reset the attachment files so that the same files are not uploaded again
            setAttachmentFiles([]);
            if (files) {
                await uploadConversationFiles({ conversationId, files });
            }

            // create the message
            await createMessage({
                conversationId,
                content,
                messageType,
                filenames,
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

    const onAttachment = () => {
        attachmentInputRef.current?.click();
    };

    const onAttachmentChanged = () => {
        const files = attachmentInputRef.current?.files;
        if (files) {
            const filesSet = new Set<File>(attachmentFiles);
            for (let i = 0; i < Math.min(files.length, Constants.app.maxFileAttachmentsPerMessage); i++) {
                filesSet.add(files[i]);
            }
            setAttachmentFiles(Array.from(filesSet));

            if (files.length > Constants.app.maxFileAttachmentsPerMessage) {
                // show a warning that only the first N files were attached
                dispatch(
                    addError({
                        title: 'Attachment limit reached',
                        message: `Only the first ${Constants.app.maxFileAttachmentsPerMessage} files were attached`,
                    }),
                );
            }
        }
    };

    const onRecordSpeech = async () => {
        if (!recognizer || isListening) return;

        setIsListening(true);
        recognizer.recognizeOnceAsync((result) => {
            if (result.reason === speechSdk.ResultReason.Canceled) {
                const cancellationDetails = result.errorDetails;
                if (cancellationDetails) {
                    console.error(`Speech recognition canceled: ${cancellationDetails}`);
                }
                setIsListening(false);
                return;
            }

            if (result.reason === speechSdk.ResultReason.NoMatch) {
                setIsListening(false);
                return;
            }

            const text = result.text;

            if (text.trim() === '') {
                setIsListening(false);
                return;
            }

            editorRef.current?.update(() => {
                const root = $getRoot();
                if (root.getTextContent().length > 0) {
                    // there is already text, so insert a new paragraph
                    const paragraph = $createParagraphNode();
                    paragraph.append($createTextNode(text));
                    root.append(paragraph);
                } else {
                    // no text yet, but we don't want to insert a new paragraph
                    // so set the selection to the end of the root node and then
                    // we can use that to insert the text directly
                    root.selectEnd();
                    const selection = $getSelection();
                    if (!selection) {
                        console.error('Failed to get selection');
                        setIsListening(false);
                        return;
                    }
                    selection.insertText(text);
                }
                // select the end of the root node so that the user can continue typing
                root.selectEnd();
            });

            setIsListening(false);
        });
    };

    const disableInputs = isSubmitting || isListening;

    const innerSpeechButton = (
        <Button
            appearance="transparent"
            disabled={disableInputs || !recognizer}
            style={{ color: isListening ? 'red' : undefined }}
            icon={<Mic20Regular />}
            onClick={onRecordSpeech}
        />
    );
    const speechButton = recognizer ? (
        innerSpeechButton
    ) : (
        <Tooltip content="Enable speech in settings" relationship="label">
            {innerSpeechButton}
        </Tooltip>
    );

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
                                    ?.slice()
                                    .sort((a, b) => a.name.localeCompare(b.name))
                                    .filter((participant) => participant.role === 'assistant')
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
                    disableSend={disableInputs}
                    actions={
                        <span style={{ display: 'flex', alignItems: 'center' }}>
                            <span>
                                <input
                                    hidden
                                    ref={attachmentInputRef}
                                    type="file"
                                    onChange={onAttachmentChanged}
                                    multiple
                                />
                                <Button
                                    appearance="transparent"
                                    disabled={disableInputs}
                                    icon={<Attach20Regular />}
                                    onClick={onAttachment}
                                />
                                {speechButton}
                            </span>
                        </span>
                    }
                    attachments={
                        <AttachmentList>
                            {attachmentFiles.map((file, index) => (
                                <Tooltip content={file.name} key={index} relationship="label">
                                    <Attachment
                                        id={file.name}
                                        key={index}
                                        media={<DocumentRegular />}
                                        primaryAction={{ as: 'span' }}
                                        dismissButton={{
                                            onClick: () =>
                                                setAttachmentFiles(attachmentFiles.filter((f) => f !== file)),
                                        }}
                                    >
                                        {file.name}
                                    </Attachment>
                                </Tooltip>
                            ))}
                        </AttachmentList>
                    }
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
