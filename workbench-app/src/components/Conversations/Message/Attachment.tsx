import { Attach24Regular } from '@fluentui/react-icons';
import React from 'react';

interface AttachmentProps {
    media: React.ReactNode;
    content: string;
    onDismiss?: () => void;
}

export const Attachment: React.FC<AttachmentProps> = (props) => {
    const { media, content, onDismiss } = props;

    return (
        <div className="attachment">
            {media}
            <span>{content}</span>
            {onDismiss && <Attach24Regular onClick={onDismiss} />}
        </div>
    );
};
