import { Attachment, AttachmentList } from '@fluentui-copilot/react-copilot';
import { makeStyles, mergeClasses, tokens } from '@fluentui/react-components';
import React from 'react';
import { TooltipWrapper } from '../../App/TooltipWrapper';
import { ConversationFileIcon } from '../ConversationFileIcon';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
        marginTop: tokens.spacingVerticalS,
    },
});

interface AttachmentSectionProps {
    filenames?: string[];
    className?: string;
}

export const AttachmentSection: React.FC<AttachmentSectionProps> = (props) => {
    const { filenames, className } = props;
    const classes = useClasses();

    const attachmentList =
        filenames && filenames.length > 0 ? (
            <AttachmentList>
                {filenames.map((filename) => (
                    <TooltipWrapper content={filename} key={filename}>
                        <Attachment media={<ConversationFileIcon file={filename} />} content={filename} />
                    </TooltipWrapper>
                ))}
            </AttachmentList>
        ) : null;

    return <div className={mergeClasses(classes.root, className)}>{attachmentList}</div>;
};
