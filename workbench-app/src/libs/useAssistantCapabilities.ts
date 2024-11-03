import React from 'react';
import { Assistant } from '../models/Assistant';
import { AssistantCapability } from '../models/AssistantCapability';
import { useWorkbenchService } from './useWorkbenchService';

export function useGetAssistantCapabilities(assistants?: Assistant[]) {
    const [isFetching, setIsFetching] = React.useState<boolean>(false);
    const [assistantCapabilities, setAssistantCapabilities] = React.useState(new Set<AssistantCapability>());
    const workbenchService = useWorkbenchService();

    // Build a memoized set of all capabilities to be used as a default for assistants that do not
    // specify capabilities
    const allCapabilities = React.useMemo(
        () =>
            Object.entries(AssistantCapability).reduce((acc, [_, capability]) => {
                acc.add(capability);
                return acc;
            }, new Set<AssistantCapability>()),
        [],
    );

    // Load the capabilities for all assistants and update the state with the result
    React.useEffect(() => {
        let ignore = false;

        if (!assistants || assistants?.length === 0) {
            if (ignore) {
                return;
            }
            // only update the state if the capabilities have changed
            if (!assistantCapabilities || allCapabilities.symmetricDifference(assistantCapabilities).size > 0) {
                setAssistantCapabilities(allCapabilities);
            }
            return;
        }

        (async () => {
            setIsFetching(true);

            // Get the service info for each assistant
            const serviceInfos = (
                await Promise.all(
                    assistants.map(async (assistant) => {
                        return await workbenchService.getAssistantServiceInfoAsync(assistant.assistantServiceId);
                    }),
                )
            ).filter((info) => info !== undefined);

            // Combine all capabilities from all assistants into a single set
            const capabilities = serviceInfos.reduce<Set<AssistantCapability>>((acc, info) => {
                const metadataCapabilities = info.metadata?.capabilities;

                // If there are no capabilities specified at all, default to all capabilities
                if (metadataCapabilities === undefined) {
                    acc.union(allCapabilities);
                    return acc;
                }

                const capabilitiesSet = new Set(
                    Object.keys(metadataCapabilities)
                        .filter((key) => metadataCapabilities[key])
                        .map((key) => key as AssistantCapability),
                );
                acc = acc.union(capabilitiesSet);
                return acc;
            }, new Set<AssistantCapability>());

            if (!ignore) {
                // only update the state if the capabilities have changed
                if (!assistantCapabilities || capabilities.symmetricDifference(assistantCapabilities).size > 0) {
                    setAssistantCapabilities(capabilities);
                }
            }

            setIsFetching(false);
        })();

        return () => {
            ignore = true;
        };
    }, [allCapabilities, assistantCapabilities, assistants, workbenchService]);

    return {
        data: assistantCapabilities,
        isFetching,
    };
}
