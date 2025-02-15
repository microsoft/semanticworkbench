import { makeStyles, mergeClasses } from '@fluentui/react-components';
import React from 'react';
import { CopyButton } from '../../App/CopyButton';
import { DebugInspector } from '../DebugInspector';
import { MessageDelete } from '../MessageDelete';
import { MessageLink } from '../MessageLink';
import { RewindConversation } from '../RewindConversation';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        width: '100%',
    },
});

interface MessageActionsProps {
    className?: string;
    readOnly: boolean;
    message: any;
    conversation: any;
    debugData: any;
    isLoadingDebugData: boolean;
    isUninitializedDebugData: boolean;
    onRewind?: (message: any, redo: boolean) => void;
    setSkipDebugLoad: React.Dispatch<React.SetStateAction<boolean>>;
}

export const MessageActions: React.FC<MessageActionsProps> = (props) => {
    const {
        className,
        readOnly,
        message,
        conversation,
        debugData,
        isLoadingDebugData,
        isUninitializedDebugData,
        onRewind,
        setSkipDebugLoad,
    } = props;

    const classes = useClasses();

    return (
        <div className={mergeClasses(classes.root, className)}>
            {!readOnly && <MessageLink conversation={conversation} messageId={message.id} />}
            <DebugInspector
                debug={message.hasDebugData ? debugData?.debugData || { loading: true } : undefined}
                loading={isLoadingDebugData || isUninitializedDebugData}
                onOpen={() => {
                    setSkipDebugLoad(false);
                }}
            />
            <CopyButton data={message.content} tooltip="Copy message" size="small" appearance="transparent" />
            {!readOnly && (
                <>
                    <MessageDelete conversationId={conversation.id} message={message} />
                    <RewindConversation onRewind={(redo) => onRewind?.(message, redo)} />
                </>
            )}
        </div>
    );
};
