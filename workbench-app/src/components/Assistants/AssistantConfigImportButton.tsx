import { Button } from '@fluentui/react-components';
import YAML from 'js-yaml';
import React, { useRef } from 'react';
import { useAppDispatch } from '../../redux/app/hooks'; // Import the relevant hooks
import { addError } from '../../redux/features/app/appSlice'; // Import the error action

interface AssistantConfigImportButtonProps {
    onImport: (config: object) => void;
}

export const AssistantConfigImportButton: React.FC<AssistantConfigImportButtonProps> = ({ onImport }) => {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const dispatch = useAppDispatch(); // Use the dispatch hook

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target?.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const content = e.target?.result as string;
                    let importedConfig;

                    if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
                        importedConfig = YAML.load(content);
                    } else {
                        importedConfig = JSON.parse(content);
                    }

                    if (typeof importedConfig === 'object' && importedConfig !== null) {
                        onImport(importedConfig as object);
                    } else {
                        throw new Error('Invalid configuration format');
                    }
                } catch (error) {
                    console.error('Error reading configuration file:', error);
                    dispatch(
                        addError({
                            title: 'Import Error',
                            message:
                                'There was an error importing the configuration file. Please check the file format and contents.',
                        }),
                    );
                }
            };
            reader.readAsText(file);
        }
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div>
            <input type="file" hidden ref={fileInputRef} accept=".json,.yaml,.yml" onChange={handleFileChange} />
            <Button onClick={() => fileInputRef.current?.click()}>Import Config</Button>
        </div>
    );
};
