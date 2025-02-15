import { AiGeneratedDisclaimer, Attachment, AttachmentList } from '@fluentui-copilot/react-copilot';
import React from 'react';
import { ConversationFileIcon } from '../ConversationFileIcon';
import { TooltipWrapper } from './AttachmentSection/TooltipWrapper';

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
                    <TooltipWrapper content={filename} key={filename}>
                        <Attachment
                            media={<ConversationFileIcon file={filename} />}
                            content={filename}

                        />
                    </TooltipWrapper>
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
