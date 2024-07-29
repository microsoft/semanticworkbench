// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Constants } from '../Constants';
import { ServiceEnvironment } from '../models/ServiceEnvironment';
import { useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';

export const useEnvironment = () => {
    const { environmentId } = useAppSelector((state: RootState) => state.settings);
    const [environment, setEnvironment] = React.useState<ServiceEnvironment>(getEnvironment(environmentId));

    React.useEffect(() => {
        const environment = getEnvironment(environmentId);
        setEnvironment(environment);
    }, [environmentId]);

    return environment;
};

export const getEnvironment = (environmentId?: string): ServiceEnvironment => {
    if (environmentId) {
        const environment = Constants.service.environments.find((environment) => environment.id === environmentId);
        if (environment) {
            return environment;
        }
    }

    const defaultEnvironment = Constants.service.environments.find(
        (environment) => environment.id === Constants.service.defaultEnvironmentId,
    );
    if (defaultEnvironment) {
        return defaultEnvironment;
    }

    throw new Error('No default environment found. Check Constants.ts file.');
};
