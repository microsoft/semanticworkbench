// Copyright (c) Microsoft. All rights reserved.

import { ArrowUploadRegular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from '../App/CommandButton';

interface ContentImportProps<T> {
    contentTypeLabel: string;
    importFunction: (file: File) => Promise<T>;
    onImport?: (value: T) => void;
    onError?: (error: Error) => void;
    disabled?: boolean;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    appearance?: 'primary' | 'secondary' | 'outline' | 'subtle' | 'transparent';
    size?: 'small' | 'medium' | 'large';
}

export const ContentImport = <T extends unknown>(props: ContentImportProps<T>) => {
    const {
        contentTypeLabel,
        importFunction,
        onImport,
        onError,
        disabled,
        iconOnly,
        asToolbarButton,
        appearance,
        size,
    } = props;
    const [uploading, setUploading] = React.useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const onFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setUploading(true);
            try {
                const file = event.target.files[0];
                const content = await importFunction(file);
                onImport?.(content);
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
                description={`Import ${contentTypeLabel}`}
                icon={<ArrowUploadRegular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                appearance={appearance}
                size={size}
                label="Import"
                onClick={onUpload}
            />
        </div>
    );
};
