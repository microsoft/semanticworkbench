import React from 'react';
import { Assistant } from '../models/Assistant';
import { AssistantCapability } from '../models/AssistantCapability';
import { useWorkbenchService } from './useWorkbenchService';

export function useGetAssistantCapabilities(assistants: Assistant[], skipToken: { skip: boolean } = { skip: false }) {
    const [isFetching, setIsFetching] = React.useState<boolean>(true);

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

    const [assistantCapabilities, setAssistantCapabilities] = React.useState<Set<AssistantCapability>>(allCapabilities);
    const workbenchService = useWorkbenchService();

    // Load the capabilities for all assistants and update the state with the result
    React.useEffect(() => {
        if (skipToken.skip) {
            return;
        }

        let active = true;

        if (assistants.length === 0) {
            if (assistantCapabilities.symmetricDifference(allCapabilities).size > 0) {
                setAssistantCapabilities(allCapabilities);
            }
            setIsFetching(false);
            return;
        }

        (async () => {
            if (active) {
                setIsFetching(true);
            }

            // Get the service info for each assistant
            const infosResponse = await workbenchService.getAssistantServiceInfosAsync(
                assistants.map((assistant) => assistant.assistantServiceId),
            );
            const serviceInfos = infosResponse.filter((info) => info !== undefined);

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

            if (active) {
                if (assistantCapabilities.symmetricDifference(capabilities).size > 0) {
                    setAssistantCapabilities(capabilities);
                }
                setIsFetching(false);
            }
        })();

        return () => {
            active = false;
        };
    }, [allCapabilities, assistants, assistantCapabilities, skipToken.skip, workbenchService]);

    return {
        data: assistantCapabilities,
        isFetching,
    };
}
