// Copyright (c) Microsoft. All rights reserved.

import { Button } from '@fluentui/react-components';
import { Add24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useUploadConversationFilesMutation } from '../../services/workbench';

interface FileUploadProps {
    conversationId: string;
}

export const FileUpload: React.FC<FileUploadProps> = (props) => {
    const { conversationId } = props;
    const [uploading, setUploading] = React.useState(false);
    const [uploadConversationFiles] = useUploadConversationFilesMutation();
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const onFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setUploading(true);
            const files: File[] = [];
            for (let i = 0; i < event.target.files.length; i++) {
                files.push(event.target.files[i]);
            }
            await uploadConversationFiles({ conversationId, files });
            setUploading(false);
        }

        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const onUpload = async () => {
        fileInputRef.current?.click();
    };

    return (
        <div>
            <input hidden ref={fileInputRef} type="file" onChange={onFileChange} multiple />
            <Button icon={<Add24Regular />} onClick={onUpload} disabled={uploading}>
                Upload File(s)
            </Button>
        </div>
    );
};
