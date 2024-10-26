// Copyright (c) Microsoft. All rights reserved.

import { ArrowUpload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { CommandButton } from '../App/CommandButton';

interface AssistantImportProps {
    disabled?: boolean;
    iconOnly?: boolean;
    label?: string;
    asToolbarButton?: boolean;
    onImport?: (result: { assistantIds: string[]; conversationIds: string[] }) => void;
    onError?: (error: Error) => void;
}

export const AssistantImport: React.FC<AssistantImportProps> = (props) => {
    const { disabled, iconOnly, label, asToolbarButton, onImport, onError } = props;
    const [uploading, setUploading] = React.useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);
    const workbenchService = useWorkbenchService();

    const onFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setUploading(true);
            try {
                const file = event.target.files[0];
                const result = await workbenchService.importConversationsAsync(file);
                onImport?.(result);
            } catch (error) {
                onError?.(error as Error);
            }
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
            <input hidden ref={fileInputRef} type="file" onChange={onFileChange} />
            <CommandButton
                disabled={uploading || disabled}
                description="Import assistant"
                icon={<ArrowUpload24Regular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label={label ?? 'Import'}
                onClick={onUpload}
            />
        </div>
    );
};
