import { Image } from '@fluentui/react-components';
import { FileTypeIconSize, getFileTypeIconAsUrl } from '@fluentui/react-file-type-icons';
import { FileIconTypeInput } from '@fluentui/react-file-type-icons/lib/FileIconType';
import React from 'react';
import { ConversationFile } from '../../models/ConversationFile';

interface ConversationFileIconProps {
    file: File | ConversationFile | string;
    className?: string;
    /**
     * The type of file type icon you need. Use this property for
     * file type icons that are not associated with a file extension,
     * such as folder.
     */
    type?: FileIconTypeInput;
    size?: FileTypeIconSize;
}

export const ConversationFileIcon: React.FC<ConversationFileIconProps> = (props) => {
    const { file, className, type, size } = props;

    // if it is of type File and is an image, display the image instead of the file type icon
    if (file instanceof File && file.type.startsWith('image/')) {
        return <Image className={className} src={URL.createObjectURL(file)} alt={file.name} />;
    }

    // for all other cases, display the file type icon
    const filename = typeof file === 'string' ? file : file.name;
    return (
        <Image
            className={className}
            src={getFileTypeIconAsUrl({ extension: filename.split('.').pop() ?? '', type, size })}
            alt={filename}
        />
    );
};
