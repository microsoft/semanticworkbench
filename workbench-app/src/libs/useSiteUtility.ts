// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Constants } from '../Constants';

export const useSiteUtility = () => {
    const setDocumentTitle = React.useCallback((title: string) => {
        document.title = `${title} - ${Constants.app.name}`;
    }, []);

    const forceNavigateTo = React.useCallback((url: string | URL) => {
        window.history.pushState(null, '', url);
        window.location.reload();
    }, []);

    return {
        setDocumentTitle,
        forceNavigateTo,
    };
};
