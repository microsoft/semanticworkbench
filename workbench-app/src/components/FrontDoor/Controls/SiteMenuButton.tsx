import { useIsAuthenticated, useMsal } from '@azure/msal-react';
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
import { useLocalUserAccount } from '../../../libs/useLocalUserAccount';
import { useMicrosoftGraph } from '../../../libs/useMicrosoftGraph';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { setUser } from '../../../redux/features/app/appSlice';

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
    const microsoftGraph = useMicrosoftGraph();
    const isAuthenticated = useIsAuthenticated();
    const { getUserId, getUserName } = useLocalUserAccount();
    const { user } = useAppSelector((state) => state.app);
    const dispatch = useAppDispatch();

    const account = instance.getActiveAccount();
    const userId = getUserId();
    const userName = getUserName();

    React.useEffect(() => {
        if (isAuthenticated && userId && userName && !user?.image) {
            (async () => {
                const photo = await microsoftGraph.getMyPhotoAsync();
                dispatch(
                    setUser({
                        id: userId,
                        name: userName,
                        image: photo,
                    }),
                );
            })();
        }
    }, [isAuthenticated, microsoftGraph, userId, userName, user?.image, dispatch]);

    const avatar = user?.image
        ? {
              name: userName,
              image: { src: user.image },
          }
        : { name: userName };

    const handleSignOut = () => {
        void AuthHelper.logoutAsync(instance);
    };

    const handleSignIn = () => {
        void AuthHelper.loginAsync(instance);
    };

    return (
        <Menu>
            <MenuTrigger disableButtonEnhancement>
                <Persona className="user-avatar" avatar={avatar} presence={{ status: 'available' }} />
            </MenuTrigger>
            <MenuPopover>
                <MenuList>
                    {account && (
                        <>
                            <div className={classes.accountInfo}>
                                <Label>{account.name}</Label>
                                <Label size="small">{account.username}</Label>
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
                    {account ? (
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
