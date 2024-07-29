// Copyright (c) Microsoft. All rights reserved.

import { ArrowUpload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { CommandButton } from '../../App/CommandButton';

interface WorkflowImportProps {
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    onImport?: (workflowDefinition: Partial<WorkflowDefinition>) => void;
    onError?: (error: Error) => void;
}

export const WorkflowImport: React.FC<WorkflowImportProps> = (props) => {
    const { iconOnly, asToolbarButton, onImport, onError } = props;
    const [uploading, setUploading] = React.useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const onFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setUploading(true);
            try {
                const file = event.target.files[0];
                const workflowData = await file.text();
                onImport?.(JSON.parse(workflowData));
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
                description="Import workflow"
                icon={<ArrowUpload24Regular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label="Import"
                onClick={onUpload}
                disabled={uploading}
            />
        </div>
    );
};
