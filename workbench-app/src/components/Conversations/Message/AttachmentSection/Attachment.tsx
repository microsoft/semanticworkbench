import { Attach24Regular } from '@fluentui/react-icons';
import React from 'react';

interface AttachmentProps {
    media: React.ReactNode;
    content: string;
    onDismiss?: () => void;
}

/**
 * Renders an attachment UI component with optional dismiss functionality.
 *
 * @param media - The media or icon to display alongside the attachment.
 * @param content - The textual content of the attachment.
 * @param onDismiss - Optional callback invoked when the dismiss icon is clicked.
 */
export const Attachment: React.FC<AttachmentProps> = ({ media, content, onDismiss }) => {
    return (
        <div className="attachment">
            {media}
            <span>{content}</span>
            {onDismiss && <Attach24Regular onClick={onDismiss} />}
        </div>
    );
};
