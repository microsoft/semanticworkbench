import React from 'react';
import { CopyButton } from '../../App/CopyButton';
import { DebugInspector } from '../DebugInspector';
import { MessageDelete } from '../MessageDelete';
import { MessageLink } from '../MessageLink';
import { RewindConversation } from '../RewindConversation';

interface ActionsProps {
    conversation: any;
    message: any;
    readOnly: boolean;
    debugData: any;
    isLoadingDebugData: boolean;
    isUninitializedDebugData: boolean;
    onRewind?: (message: any, redo: boolean) => void;
}

export const MessageActions: React.FC<ActionsProps> = ({
    conversation,
    message,
    readOnly,
    debugData,
    isLoadingDebugData,
    isUninitializedDebugData,
    onRewind,
}) => (
    <>
        {!readOnly && <MessageLink conversation={conversation} messageId={message.id} />}
        <DebugInspector
            debug={message.hasDebugData ? debugData?.debugData || { loading: true } : undefined}
            loading={isLoadingDebugData || isUninitializedDebugData}
            onOpen={() => {} /* Hook logic for handling onOpen */}
        />
        <CopyButton data={message.content} tooltip="Copy message" size="small" appearance="transparent" />
        {!readOnly && (
            <>
                <MessageDelete conversationId={conversation.id} message={message} />
                <RewindConversation onRewind={(redo) => onRewind?.(message, redo)} />
            </>
        )}
    </>
);
