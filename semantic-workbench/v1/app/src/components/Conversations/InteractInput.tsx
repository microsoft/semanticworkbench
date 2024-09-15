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
import { Button, Tooltip, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { Attach20Regular, DocumentRegular, Mic20Regular } from '@fluentui/react-icons';
import { getEncoding } from 'js-tiktoken';
import { CLEAR_EDITOR_COMMAND, COMMAND_PRIORITY_LOW, DRAGOVER_COMMAND, DROP_COMMAND, PASTE_COMMAND } from 'lexical';
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
import { InputOptionsControl } from './InputOptionsControl';

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
    const [directedAtId, setDirectedAtId] = React.useState<string>();
    const [attachmentFiles, setAttachmentFiles] = React.useState<File[]>([]);
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [isListening, setIsListening] = React.useState(false);
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const [editorIsInitialized, setEditorIsInitialized] = React.useState(false);
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

    const editorRefCallback = React.useCallback((editor: LexicalEditor) => {
        editorRef.current = editor;

        // set the editor as initialized
        setEditorIsInitialized(true);
    }, []);

    React.useEffect(() => {
        if (!editorIsInitialized) return;

        if (!editorRef.current) {
            console.error('Failed to get editor reference after initialization');
            return;
        }
        const editor = editorRef.current;

        const removePasteListener = editor.registerCommand(
            PASTE_COMMAND,
            (event: ClipboardEvent) => {
                console.log('paste event', event);

                const clipboardItems = event.clipboardData?.items;
                if (!clipboardItems) return false;

                for (const item of clipboardItems) {
                    if (item.kind === 'file') {
                        // limit the number of attachments to the maximum allowed
                        if (attachmentFiles.length >= Constants.app.maxFileAttachmentsPerMessage) {
                            dispatch(
                                addError({
                                    title: 'Attachment limit reached',
                                    message: `Only ${Constants.app.maxFileAttachmentsPerMessage} files can be attached per message`,
                                }),
                            );
                            return true;
                        }

                        const file = item.getAsFile();
                        if (file) {
                            // ensure the filename is unique by appending a timestamp before the extension
                            const timestamp = new Date().getTime();
                            const filename = `${file.name.replace(/\.[^/.]+$/, '')}_${timestamp}${file.name.match(
                                /\.[^/.]+$/,
                            )}`;

                            // file.name is read-only, so create a new file object with the new name
                            // make sure to use the same file contents, content type, etc.
                            const updatedFile =
                                filename !== file.name ? new File([file], filename, { type: file.type }) : file;

                            // add the file to the list of attachments
                            setAttachmentFiles((prevFiles) => [...prevFiles, updatedFile]);

                            // Prevent default paste for file items
                            event.preventDefault();
                            event.stopPropagation();

                            // Indicate command was handled
                            return true;
                        }
                    }
                }

                // Allow default handling for non-file paste
                return false;
            },
            COMMAND_PRIORITY_LOW,
        );

        const removeDragOverListener = editor.registerCommand(
            DRAGOVER_COMMAND,
            (event: DragEvent) => {
                console.log('dragover event', event);

                // Prevent default dragover behavior
                event.preventDefault();
                event.stopPropagation();
                return true;
            },
            COMMAND_PRIORITY_LOW,
        );

        const removeDropListener = editor.registerCommand(
            DROP_COMMAND,
            (event: DragEvent) => {
                console.log('drop event', event);

                const files = event.dataTransfer?.files;
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

                // Prevent default drop behavior
                event.preventDefault();
                event.stopPropagation();

                // Indicate command was handled
                return true;
            },
            COMMAND_PRIORITY_LOW,
        );

        return () => {
            // Clean up listeners on unmount
            removePasteListener();
            removeDragOverListener();
            removeDropListener();
        };
    }, [attachmentFiles, dispatch, editorIsInitialized, editorRef, setAttachmentFiles]);

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
            let metadata: Record<string, any> | undefined = directedAtId ? undefined : { directed_at: directedAtId };

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
                <InputOptionsControl
                    messageTypeValue={messageTypeValue}
                    participants={participants}
                    onDirectedAtChange={setDirectedAtId}
                />
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
                    <LexicalEditorRefPlugin editorRef={editorRefCallback} />
                </ChatInput>
            </div>
        </div>
    );
};
