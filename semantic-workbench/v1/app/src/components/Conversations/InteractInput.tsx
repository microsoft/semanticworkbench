// Copyright (c) Microsoft. All rights reserved.

import { Attachment, AttachmentList } from '@fluentui-copilot/react-attachments';
import {
    $createTextNode,
    $getRoot,
    ChatInput,
    ChatInputEntityNode,
    ChatInputSubmitEvents,
    ChatInputTokenNode,
    ChatInputValueData,
    EditorState,
    LexicalEditor,
    LexicalEditorRefPlugin,
    TextNode,
} from '@fluentui-copilot/react-copilot';
import { Button, Tooltip, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { Attach20Regular, DocumentRegular } from '@fluentui/react-icons';
import debug from 'debug';
import { getEncoding } from 'js-tiktoken';
import {
    $createLineBreakNode,
    CLEAR_EDITOR_COMMAND,
    COMMAND_PRIORITY_LOW,
    LineBreakNode,
    PASTE_COMMAND,
} from 'lexical';
import React from 'react';
import { Constants } from '../../Constants';
import { useLocalUserAccount } from '../../libs/useLocalUserAccount';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppDispatch } from '../../redux/app/hooks';
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
import { SpeechButton } from './SpeechButton';

const log = debug(Constants.debug.root).extend('InteractInput');

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
    dragTarget: {
        transition: 'border 0.3s',
        border: `2px dashed transparent`,
    },
    dragOver: {
        border: `2px dashed ${tokens.colorPaletteGreenBorderActive}`,
        borderRadius: tokens.borderRadiusLarge,
    },
});

interface InteractInputProps {
    conversationId: string;
    additionalContent?: React.ReactNode;
}

class TemporaryTextNode extends TextNode {
    static getType() {
        return 'temporary';
    }

    static clone(node: TemporaryTextNode) {
        return new TemporaryTextNode(node.__text, node.__key);
    }
}

export const InteractInput: React.FC<InteractInputProps> = (props) => {
    const { conversationId, additionalContent } = props;
    const classes = useClasses();
    const [createMessage] = useCreateConversationMessageMutation();
    const [uploadConversationFiles] = useUploadConversationFilesMutation();
    const [messageTypeValue, setMessageTypeValue] = React.useState<'Chat' | 'Command'>('Chat');
    const [tokenCount, setTokenCount] = React.useState(0);
    const [directedAtId, setDirectedAtId] = React.useState<string>();
    const [isDraggingOver, setIsDraggingOver] = React.useState(false);
    const [attachmentFiles, setAttachmentFiles] = React.useState<File[]>([]);
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [isListening, setIsListening] = React.useState(false);
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
                log('paste event', event);

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

        return () => {
            // Clean up listeners on unmount
            removePasteListener();
        };
    }, [attachmentFiles, dispatch, editorIsInitialized, editorRef, setAttachmentFiles]);

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

    // update the listening state when the speech recognizer starts or stops
    // so that we can disable the input send while listening
    const handleListeningChange = (listening: boolean) => {
        setIsListening(listening);
    };

    // update the editor with the in-progress recognized text while the speech recognizer is recognizing,
    // which is not the final text yet, but it will give the user an idea of what is being recognized
    const handleSpeechRecognizing = (text: string) => {
        const editor = editorRef.current;
        if (!editor) {
            console.error('Failed to get editor reference');
            return;
        }

        editor.update(() => {
            // get the editor state
            const editorState: EditorState = editor.getEditorState();

            // check if there is a temporary text node in the editor
            // if found, update the text content of the temporary text node
            let foundTemporaryNode = false;
            editorState._nodeMap.forEach((node) => {
                if (node instanceof TemporaryTextNode) {
                    node.setTextContent(text);
                    foundTemporaryNode = true;
                }
            });

            // get the root node of the editor
            const root = $getRoot();

            // if no temporary text node was found, insert a new temporary text node at the end of the editor
            if (!foundTemporaryNode) {
                const selection = root.selectEnd();
                if (!selection) {
                    console.error('Failed to get selection');
                    return;
                }

                // insert a line break before the temporary text node if the editor is not empty
                if (root.getTextContentSize() > 0) {
                    selection.insertNodes([$createLineBreakNode()]);
                }

                // insert the temporary text node at the end of the editor
                selection.insertNodes([new TemporaryTextNode(text)]);
            }

            // select the end of the editor to ensure the temporary text node is visible
            root.selectEnd();
        });
    };

    // update the editor with the final recognized text when the speech recognizer has recognized the speech
    // this will replace the in-progress recognized text in the editor
    const handleSpeechRecognized = (text: string) => {
        const editor = editorRef.current;
        if (!editor) {
            console.error('Failed to get editor reference');
            return;
        }

        editor.update(() => {
            // get the editor state
            const editorState: EditorState = editor.getEditorState();

            // remove any temporary text nodes from the editor
            editorState._nodeMap.forEach((node) => {
                if (node instanceof TemporaryTextNode) {
                    node.remove();
                }
            });

            // get the root node of the editor
            const root = $getRoot();

            // insert the recognized text as a text node at the end of the editor
            const selection = root.selectEnd();
            if (!selection) {
                console.error('Failed to get selection');
                return;
            }
            selection.insertNodes([$createTextNode(text)]);

            // select the end of the editor to ensure the text node is visible
            root.selectEnd();
        });
    };

    const handleDrop = (event: React.DragEvent) => {
        log('drop event', event);
        event.preventDefault();
        event.stopPropagation();
        setIsDraggingOver(false);

        const files = event.dataTransfer.files;
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

    const handleDragOver = (event: React.DragEvent) => {
        // log('dragover event', event);
        event.preventDefault();
        event.stopPropagation();
    };

    const handleDragEnter = (event: React.DragEvent) => {
        log('dragenter event', event);
        setIsDraggingOver(true);
        event.preventDefault();
        event.stopPropagation();
    };

    const handleDragLeave = (event: React.DragEvent) => {
        event.preventDefault();
        event.stopPropagation();
        const relatedTarget = event.relatedTarget as HTMLElement;
        if (event.currentTarget.contains(relatedTarget)) {
            return;
        }
        log('dragleave event', event);
        setIsDraggingOver(false);
    };

    const disableInputs = isSubmitting || isListening;

    return (
        <div
            className={classes.root}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
        >
            <div className={classes.content}>
                {/* // this is for injecting controls for supporting features like workflow */}
                {additionalContent}
                <InputOptionsControl
                    messageTypeValue={messageTypeValue}
                    participants={participants}
                    onDirectedAtChange={setDirectedAtId}
                />
                <div className={mergeClasses(classes.row, classes.dragTarget, isDraggingOver ? classes.dragOver : '')}>
                    <ChatInput
                        className={mergeClasses(
                            classes.fullWidth,
                            messageTypeValue === 'Command' ? classes.commandTextbox : '',
                        )}
                        onChange={(_event, data) => updateInput(data.value)}
                        maxLength={Constants.app.maxInputLength}
                        characterCount={tokenCount}
                        count={
                            <span>
                                {tokenCount} tokens / {attachmentFiles.length} attachments (max{' '}
                                {Constants.app.maxFileAttachmentsPerMessage})
                            </span>
                        }
                        placeholderValue="Ask a question or request assistance or type / to enter a command."
                        customNodes={[ChatInputTokenNode, ChatInputEntityNode, LineBreakNode, TemporaryTextNode]}
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
                                    <SpeechButton
                                        disabled={disableInputs}
                                        onListeningChange={handleListeningChange}
                                        onSpeechRecognizing={handleSpeechRecognizing}
                                        onSpeechRecognized={handleSpeechRecognized}
                                    />
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
        </div>
    );
};
