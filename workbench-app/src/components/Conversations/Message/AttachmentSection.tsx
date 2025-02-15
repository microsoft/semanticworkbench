import { AiGeneratedDisclaimer, Attachment, AttachmentList } from '@fluentui-copilot/react-copilot';
import { Tooltip } from '@fluentui/react-components';
import { Attach24Regular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationFileIcon } from '../ConversationFileIcon';

interface AttachmentSectionProps {
    filenames?: string[];
    message?: any;
    generatedClass: string;
    footerItems?: string | string[];
}

export const AttachmentSection: React.FC<AttachmentSectionProps> = (props) => {
    const { filenames, message, generatedClass, footerItems } = props;
    const attachmentList =
        filenames && filenames.length > 0 ? (
            <AttachmentList>
                {filenames.map((filename) => (
                    <Tooltip content={filename} key={filename} relationship="label">
                        <Attachment
                            media={<ConversationFileIcon file={filename} />}
                            content={filename}
                            dismissIcon={<Attach24Regular />}
                        />
                    </Tooltip>
                ))}
            </AttachmentList>
        ) : null;

    const aiGeneratedDisclaimer =
        message && message.metadata?.['generated_content'] === false ? null : (
            <AiGeneratedDisclaimer className={generatedClass}>
                AI-generated content may be incorrect
            </AiGeneratedDisclaimer>
        );

    return (
        <>
            {aiGeneratedDisclaimer}
            {footerItems}
            {attachmentList}
        </>
    );
};
