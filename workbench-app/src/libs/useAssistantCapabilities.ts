import React from 'react';
import { Assistant } from '../models/Assistant';
import { AssistantCapability } from '../models/AssistantCapability';
import { useWorkbenchService } from './useWorkbenchService';

export function useGetAssistantCapabilitiesSet(assistants: Assistant[]) {
    const [assistantCapabilities, setAssistantCapabilities] = React.useState<Set<AssistantCapability> | undefined>();
    const workbenchService = useWorkbenchService();

    // Build a memo-ized set of all capabilities to be used as a default for assistants that do not
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

        loadCapabilities();

        return () => {
            ignore = true;
        };

        async function loadCapabilities() {
            if (assistants.length === 0) {
                if (ignore) {
                    return;
                }
                // only update the state if the capabilities have changed
                if (!assistantCapabilities || allCapabilities.symmetricDifference(assistantCapabilities).size > 0) {
                    setAssistantCapabilities(allCapabilities);
                }
                return;
            }
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
                if (metadataCapabilities === undefined || Object.keys(metadataCapabilities).length === 0) {
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

            if (ignore) {
                return;
            }

            // only update the state if the capabilities have changed
            if (!assistantCapabilities || capabilities.symmetricDifference(assistantCapabilities).size > 0) {
                setAssistantCapabilities(capabilities);
            }
        }
    }, [allCapabilities, assistantCapabilities, assistants, workbenchService]);

    return assistantCapabilities;
}
