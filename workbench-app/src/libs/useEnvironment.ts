// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Constants } from '../Constants';
import { ServiceEnvironment } from '../models/ServiceEnvironment';
import { useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { Utility } from './Utility';

import debug from 'debug';

const log = debug(Constants.debug.root).extend('useEnvironment');

export const useEnvironment = () => {
    const { environmentId } = useAppSelector((state: RootState) => state.settings);
    const [environment, setEnvironment] = React.useState<ServiceEnvironment>(getEnvironment(environmentId));

    React.useEffect(() => {
        const updatedEnvironment = getEnvironment(environmentId);
        if (!Utility.deepEqual(environment, updatedEnvironment)) {
            log('Environment changed', environment, updatedEnvironment);
            setEnvironment(updatedEnvironment);
        }
    }, [environment, environmentId]);

    return environment;
};

export const getEnvironment = (environmentId?: string): ServiceEnvironment => {
    if (environmentId) {
        const environment = Constants.service.environments.find((environment) => environment.id === environmentId);
        if (environment) {
            return transformEnvironment(environment);
        }
    }

    const defaultEnvironment = Constants.service.environments.find(
        (environment) => environment.id === Constants.service.defaultEnvironmentId,
    );
    if (defaultEnvironment) {
        return transformEnvironment(defaultEnvironment);
    }

    throw new Error('No default environment found. Check Constants.ts file.');
};

const transformEnvironment = (environment: ServiceEnvironment) => {
    if (window.location.hostname.includes('-4000.app.github.dev') && environment.id === 'local') {
        return {
            ...environment,
            url: window.location.origin.replace('-4000.app.github.dev', '-3000.app.github.dev'),
        };
    }

    return environment;
};
