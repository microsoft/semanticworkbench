import { useIsAuthenticated, useMsal } from '@azure/msal-react';
import {
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
    InfoRegular,
    NavigationRegular,
    SettingsRegular,
    ShareRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthHelper } from '../../../libs/AuthHelper';
import { useMicrosoftGraph } from '../../../libs/useMicrosoftGraph';

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
    const [profileImage, setProfileImage] = React.useState<string>();

    React.useEffect(() => {
        if (isAuthenticated && !profileImage) {
            void (async () => {
                const photo = await microsoftGraph.getMyPhotoAsync();
                setProfileImage(photo);
            })();
        }
    }, [isAuthenticated, profileImage, microsoftGraph]);

    const account = instance.getActiveAccount();
    const avatar = profileImage ? { image: { src: profileImage } } : undefined;

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
                    <MenuItem icon={<InfoRegular />}>About</MenuItem>
                    {account ? (
                        <MenuItem icon={<ArrowExitRegular />} onClick={handleSignOut}>
                            Sign Out
                        </MenuItem>
                    ) : (
                        <MenuItem icon={<ArrowEnterRegular />} onClick={handleSignIn}>
                            Sign In
                        </MenuItem>
                    )}
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
