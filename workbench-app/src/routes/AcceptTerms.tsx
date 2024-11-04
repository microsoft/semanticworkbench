// Copyright (c) Microsoft. All rights reserved.

import { Button, Title2, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { setCompletedFirstRun } from '../redux/features/app/appSlice';

const log = debug(Constants.debug.root).extend('accept-terms');

const useClasses = makeStyles({
    root: {
        height: '100%',
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        display: 'grid',
        gridTemplateRows: 'auto 1fr auto',
        gridTemplateColumns: '1fr',
        gridTemplateAreas: "'header' 'content' 'footer'",
        boxSizing: 'border-box',
        gap: tokens.spacingVerticalL,
        borderRadius: `${tokens.borderRadiusLarge} ${tokens.borderRadiusLarge} 0 0`,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM, tokens.spacingVerticalXXXL),
    },
    header: {
        ...shorthands.gridArea('header'),
    },
    content: {
        backgroundColor: tokens.colorNeutralBackgroundAlpha2,
        overflow: 'auto',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        ...shorthands.gridArea('content'),
    },
    terms: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
    footer: {
        ...shorthands.gridArea('footer'),
        textAlign: 'right',
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
});

export const AcceptTerms: React.FC = () => {
    const classes = useClasses();
    const completedFirstRun = useAppSelector((state) => state.app.completedFirstRun);
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const location = useLocation();

    React.useEffect(() => {
        if (completedFirstRun?.app) {
            const redirectTo = location.state?.redirectTo ?? '/';
            navigate(redirectTo);
        }
    }, [completedFirstRun, location.state?.redirectTo, navigate]);

    const handleAccept = () => {
        log('User accepted terms');
        dispatch(setCompletedFirstRun({ app: true }));
    };

    return (
        <AppView title="Terms" actions={{ items: [], replaceExisting: true, hideProfileSettings: true }}>
            <div className={classes.root}>
                <div className={classes.header}>
                    <Title2>MICROSOFT SEMANTIC WORKBENCH</Title2>
                </div>
                <div className={classes.content}>{terms}</div>
                <div className={classes.footer}>
                    <div>
                        <em>
                            You must accept the use terms before you can install or use the software. If you do not
                            accept the use terms, do not install or use the software.
                        </em>
                    </div>
                    <div>
                        <Button appearance="primary" onClick={handleAccept}>
                            I accept the terms
                        </Button>
                    </div>
                </div>
            </div>
        </AppView>
    );
};

const terms = (
    <div>
        <div>
            MIT License
            <br />
            <br />
        </div>
        <div>
            Copyright (c) Microsoft Corporation.
            <br />
            <br />
        </div>
        <div>
            Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
            documentation files (the &quot;Software&quot;), to deal in the Software without restriction, including
            without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
            following conditions:
            <br />
            <br />
        </div>
        <div>
            The above copyright notice and this permission notice shall be included in all copies or substantial
            portions of the Software.
            <br />
            <br />
        </div>
        <div>
            THE SOFTWARE IS PROVIDED &quot;AS IS&quot;, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
            NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
            NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
            IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
            USE OR OTHER DEALINGS IN THE SOFTWARE
            <br />
            <br />
        </div>
    </div>
);
