import { useAccount, useIsAuthenticated, useMsal } from '@azure/msal-react';
import {
    Caption1,
    Label,
    Menu,
    MenuDivider,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Persona,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import {
    ArrowEnterRegular,
    ArrowExitRegular,
    NavigationRegular,
    OpenRegular,
    SettingsRegular,
    ShareRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthHelper } from '../../../libs/AuthHelper';
import { useMicrosoftGraph } from '../../../libs/useMicrosoftGraph';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { setLocalUser } from '../../../redux/features/localUser/localUserSlice';

const useClasses = makeStyles({
    accountInfo: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.padding(tokens.spacingHorizontalS),
    },
});

export const SiteMenuButton: React.FC = () => {
    const classes = useClasses();
    const navigate = useNavigate();
    const { instance } = useMsal();
    const isAuthenticated = useIsAuthenticated();
    const account = useAccount();
    const microsoftGraph = useMicrosoftGraph();
    const localUserState = useAppSelector((state) => state.localUser);
    const dispatch = useAppDispatch();

    React.useEffect(() => {
        (async () => {
            if (!isAuthenticated || !account?.name || localUserState.id) {
                return;
            }

            const photo = await microsoftGraph.getMyPhotoAsync();

            dispatch(
                setLocalUser({
                    id: (account.homeAccountId || '').split('.').reverse().join('.'),
                    name: account.name,
                    email: account.username,
                    avatar: {
                        name: account.name,
                        image: photo ? { src: photo } : undefined,
                    },
                }),
            );
        })();
    }, [account, dispatch, isAuthenticated, localUserState.id, microsoftGraph]);

    const handleSignOut = () => {
        void AuthHelper.logoutAsync(instance);
    };

    const handleSignIn = () => {
        void AuthHelper.loginAsync(instance);
    };

    return (
        <Menu>
            <MenuTrigger disableButtonEnhancement>
                <Persona className="user-avatar" avatar={localUserState.avatar} presence={{ status: 'available' }} />
            </MenuTrigger>
            <MenuPopover>
                <MenuList>
                    {isAuthenticated && (
                        <>
                            <div className={classes.accountInfo}>
                                <Label>{localUserState.name}</Label>
                                <Label size="small">{localUserState.email ?? ''}</Label>
                            </div>
                            <MenuDivider />
                        </>
                    )}
                    <MenuItem
                        icon={<NavigationRegular />}
                        onClick={() => {
                            navigate('/');
                        }}
                    >
                        Dashboard
                    </MenuItem>
                    <MenuItem
                        icon={<ShareRegular />}
                        onClick={() => {
                            navigate('/shares');
                        }}
                    >
                        Shares
                    </MenuItem>
                    <MenuItem
                        icon={<SettingsRegular />}
                        onClick={() => {
                            navigate('/settings');
                        }}
                    >
                        Settings
                    </MenuItem>
                    <MenuDivider />
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() => window.open('https://go.microsoft.com/fwlink/?LinkId=521839')}
                    >
                        {' '}
                        Privacy &amp; Cookies
                    </MenuItem>
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() => window.open('https://go.microsoft.com/fwlink/?linkid=2259814')}
                    >
                        {' '}
                        Consumer Health Privacy
                    </MenuItem>
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() => window.open('https://go.microsoft.com/fwlink/?LinkID=246338')}
                    >
                        {' '}
                        Terms of Use
                    </MenuItem>
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() =>
                            window.open(
                                'https://www.microsoft.com/en-us/legal/intellectualproperty/Trademarks/EN-US.aspx',
                            )
                        }
                    >
                        {' '}
                        Trademarks
                    </MenuItem>
                    <MenuItem
                        icon={<OpenRegular />}
                        onClick={() => window.open('http://github.com/microsoft/semanticworkbench')}
                    >
                        {' '}
                        @GitHub
                    </MenuItem>
                    <MenuDivider />
                    {isAuthenticated ? (
                        <MenuItem icon={<ArrowExitRegular />} onClick={handleSignOut}>
                            Sign Out
                        </MenuItem>
                    ) : (
                        <MenuItem icon={<ArrowEnterRegular />} onClick={handleSignIn}>
                            Sign In
                        </MenuItem>
                    )}
                    <MenuDivider />
                    <div className={classes.accountInfo}>
                        <Caption1>© Microsoft {new Date().getFullYear()}</Caption1>
                    </div>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
