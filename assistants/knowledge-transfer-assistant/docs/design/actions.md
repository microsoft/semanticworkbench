# Actions

It is important that when actions can be taken they are. Sometimes a single response should result in numerous actions.

I'm not sure... maybe more rigorous instructions about taking multiple actions, maybe maintain action lists and make sure they all get taken, maybe evaluate if there were any actions we could have taken but didn't, and then do them.

I don't recall off the top of my head, but the idea is to use gpt-4-mini to ask "was there a promise to call a tool in the last assistant response, if so what tool call should we make" when we got the last message that didn't include a tool, then if so go run the tool and inject the results into the conversation history as if the original llm had made the call... I had to do this for the early reasoning models that really just never wanted to call tools.  Maybe look and see if I did it in Explorer or Codespace Assistant?

4.1