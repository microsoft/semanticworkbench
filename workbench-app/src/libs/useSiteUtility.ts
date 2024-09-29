// Copyright (c) Microsoft. All rights reserved.

import { Constants } from '../Constants';

export const useSiteUtility = () => {
    const setDocumentTitle = (title: string) => {
        document.title = `${title} - ${Constants.app.name}`;
    };

    const forceNavigateTo = (url: string | URL) => {
        window.history.pushState(null, '', url);
        window.location.reload();
    };

    return {
        setDocumentTitle,
        forceNavigateTo,
    };
};
