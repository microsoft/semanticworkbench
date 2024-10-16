import { Menu, MenuItem, MenuList, MenuPopover, MenuTrigger, SplitButton } from '@fluentui/react-components';
import YAML from 'js-yaml';
import React from 'react';

interface AssistantConfigExportButtonProps {
    config: object;
    assistantId: string;
}

export const AssistantConfigExportButton: React.FC<AssistantConfigExportButtonProps> = ({ config, assistantId }) => {
    const exportConfig = (format: 'json' | 'yaml') => {
        let content = '';
        let filename = `config_${assistantId}`;

        try {
            if (format === 'yaml') {
                content = YAML.dump(config);
                filename += '.yaml';
            } else {
                content = JSON.stringify(config, null, 2);
                filename += '.json';
            }

            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();

            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error while generating config file:', error);
        }
    };

    const primaryActionButtonProps = {
        onClick: () => exportConfig('json'),
    };

    return (
        <Menu positioning="below-end">
            <MenuTrigger disableButtonEnhancement>
                {(triggerProps) => (
                    <SplitButton menuButton={triggerProps} primaryActionButton={primaryActionButtonProps}>
                        Export Config
                    </SplitButton>
                )}
            </MenuTrigger>

            <MenuPopover>
                <MenuList>
                    <MenuItem onClick={() => exportConfig('json')}>JSON Format</MenuItem>
                    <MenuItem onClick={() => exportConfig('yaml')}>YAML Format</MenuItem>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
