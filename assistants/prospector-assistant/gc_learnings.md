# GC Learnings

## Overview

This doc is intended to capture our team learnings with using Guided Conversation. Learnings include best use cases, concerns, hacks, favorites aspects, and different re-design ideas to improve our use of GC and any future version of it.

## Notes - To Be Updated

1. Artifact accessibility - When using GC as a component conversation of a larger conversation, it would be helpful to have a way to set an artifact before starting up GC. Currently, GC takes in a schema and produces the original artifact. A current hack to to add information via context, rules, or conversation. Another approach is to start the GC in order to create the artifact, and then call call it again after manipulating the artifact.

2. Startup status - Within a larger conversation scope, a single gc (w/ config) may be called multiple times. But without the correct context, that gc may think its starting a new conversation, when its not. Currently I a "Hello!" is emited from GC every time it starts, even though it's in the middle of a large conversation context. A startup-status templated field for the artifiact could help address this.

3. Completion status - More information is needed when GC decides a conversation is over. Right now its a bool in the result at the end. Using the artifact may be a better approach in general -- this can allows customization. Some completion fields of interest are the status (a 'why' the conversation ended: user-completed, user-exit, etc.), a next-function call (to support branching in the code based on user decision), and final user message. (Currently a final message from GC appears to be hardcoded.) These could also be templated fields in the artifact, which could help the dev avoid re-creating prompts that can introduce bugs. (Currently the rules, context, and conversation flow are free form. It may benefit to tighten up certain aspects of these fields to be more structured.)
   > NOTE: It is possible the prompt instructions for setting a conversation status to "complete" does not coincide with gc thinking the "coversation_is_over". It is likely best to depend on one or the other, and not depend on both to be true at the same time.
