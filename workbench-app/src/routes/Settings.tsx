// Copyright (c) Microsoft. All rights reserved.

import {
    Card,
    Divider,
    Dropdown,
    Field,
    Input,
    Label,
    Option,
    Text,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { MyAssistantServiceRegistrations } from '../components/App/MyAssistantServiceRegistrations';
import { useEnvironment } from '../libs/useEnvironment';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { setEnvironmentId, setSpeechKey, setSpeechRegion } from '../redux/features/settings/settingsSlice';
import { useGetAssistantServiceRegistrationsQuery } from '../services/workbench';

const useClasses = makeStyles({
    card: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    input: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'stretch',
        width: '100%',
        maxWidth: '300px',
    },
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
    },
});

export const Settings: React.FC = () => {
    const classes = useClasses();
    const environment = useEnvironment();
    // const { devMode } = useAppSelector((state) => state.app);
    const { speechKey, speechRegion } = useAppSelector((state) => state.settings);
    const { data: assistantServiceRegistrations, error: assistantServiceRegistrationsError } =
        useGetAssistantServiceRegistrationsQuery({ userIds: ['me'] });

    const dispatch = useAppDispatch();
    const siteUtility = useSiteUtility();

    siteUtility.setDocumentTitle('Settings');

    // Don't throw on assistant service registration error,
    // instead show the error message in the UI and allow the
    // rest of the settings page to render.

    const handleSettingChange = React.useCallback(
        (setting: string, value: string) => {
            switch (setting) {
                case 'environmentId':
                    dispatch(setEnvironmentId(value));
                    break;
                case 'speechKey':
                    dispatch(setSpeechKey(value));
                    break;
                case 'speechRegion':
                    dispatch(setSpeechRegion(value));
                    break;
                default:
                    throw new Error(`Unknown setting: ${setting}`);
            }
        },
        [dispatch],
    );

    // const handleDevModeChange = () => {
    //     dispatch(toggleDevMode());
    // };

    return (
        <AppView title="Settings">
            <Card className={classes.card}>
                <Field label="Service Environment">
                    <Dropdown
                        className={classes.input}
                        value={environment.name}
                        selectedOptions={[environment.id]}
                        onOptionSelect={(_event, data) =>
                            handleSettingChange('environmentId', data.optionValue as string)
                        }
                    >
                        {Constants.service.environments.map((environmentOption) => (
                            <Option
                                key={environmentOption.id}
                                text={environmentOption.name}
                                value={environmentOption.id}
                            >
                                <Label>{environmentOption.name}</Label>
                            </Option>
                        ))}
                    </Dropdown>
                </Field>
                <Divider>Speech Settings [Optional]</Divider>
                <Text>
                    Providing a valid Azure Speech Key and Region will enable the option to use of your system default
                    microphone for chat input within conversations. The use of this feature is optional.
                </Text>
                <Field label="Speech Key">
                    <Input
                        className={classes.input}
                        type="password"
                        value={speechKey}
                        placeholder="[optional]"
                        onChange={(_event, data) => handleSettingChange('speechKey', data.value)}
                    />
                </Field>
                <Field label="Speech Region">
                    <Input
                        className={classes.input}
                        value={speechRegion}
                        placeholder="[optional] e.g. westus3"
                        onChange={(_event, data) => handleSettingChange('speechRegion', data.value)}
                    />
                </Field>
                {/* <Field label="Enable Developer Mode">
                    <div className={classes.row}>
                        <Switch checked={devMode} onChange={handleDevModeChange} />
                        <Tooltip
                            content={
                                'These settings are for early, in-development features that are enabled throughout the app.' +
                                ' These are features that are not yet ready for general availability and may not be fully' +
                                ' functional. Use at your own risk.'
                            }
                            relationship="description"
                        >
                            <QuestionCircle16Regular />
                        </Tooltip>
                    </div>
                </Field> */}
            </Card>
            {!assistantServiceRegistrationsError && (
                <Card className={classes.card}>
                    <Field label="Assistant Service Registrations">
                        <MyAssistantServiceRegistrations
                            assistantServiceRegistrations={assistantServiceRegistrations}
                        />
                    </Field>
                </Card>
            )}
        </AppView>
    );
};
