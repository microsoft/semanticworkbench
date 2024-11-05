export interface LocalUserState {
    id?: string;
    name?: string;
    email?: string;
    avatar: {
        name?: string;
        image?: {
            src: string;
        };
    };
}
