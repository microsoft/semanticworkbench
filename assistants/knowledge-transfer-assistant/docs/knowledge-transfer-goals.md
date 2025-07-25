# Goals for the Knowledge Transfer Assistant

## Core idea

Assist users in synthesizing knowledge from data and ideas and transfer that knowledge to others.

## Shortcomings of existing solutions

- Even though assistants can help do this well, it normally requires the user to have the idea to use an assistant this way and to guide the assistant through the process.
- While we had previously used shared (single) assistant conversations to do this, it was confusing for users to all work in the same conversation.
- Users could opt to instead create a copy of the original conversation, but that suffered due to the fact that it was now disconnected from any ongoing development in each of the conversations.

## Our solution

### Give both knowledge producers and knowledge learners individual conversations

This solution addresses all of these items with a creative take on the scenario through separate conversations with an assistant that has built-in guidance and ability to work across all of the conversations.

Splitting the producer/consumer (or coordinator/team) conversations unlocked many more interesting benefits:

- Multiple producers can collaborate within a single conversation to set up the knowledge share.
- The knowledge share can be transferred to multiple recipients.
- Since each conversation has its own assistant, we have the assistants manage communication between producers and consumers through "information requests".
- Each conversation assistant can adopt a communication style preferred by it's users.

### Learning progress

In order to guide consumers through the knowledge transfer experience, we introduced the idea of "learning objectives" and "learning outcomes". The producer and their assistant can define what objectives and outcomes they desire their learning audience to achieve. The learners are assisted by their assistant in achieving those outcomes. The assistants guide them through their material at a pace and way that they prefer. When learners achieve outcomes, the producers are notified. This provides clear feedback to all parties of the progression through the knowledge transfer.

## Read more about the problem space

See [Knowledge Transfer Jobs-to-be-done](./JTBD.md)
