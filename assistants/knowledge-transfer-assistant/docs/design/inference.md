# Inference

Sub-agents should be watching for information they are responsible for gathering. When they see some, they should confirm with the user that they should take action with it.

Instead of just writing out the next suggested action, we should see if there is already info in the context for it, and suggest as more of a proposal than just "let's talk about X next". In other words, don't ask open-ended questions.

Things the assistant should infer at appropriate times:

- On production side:
    - What are the takeaways?
    - Who is the audience?
    - What is the user's preferred communication style?
    - What should be in the brief (what all is included in this knowledge share?)
    - Are there any learning objectives or learning outcomes that make sense to be tracked for the consumers?
    - Are there any gaps in the shared knowledge that need to be filled in?
    - What are the overall topics of this knowledge share that we need to make sure are transferred clearly?
    - How might the user want to communicate this share to others (taking into account the audience, takeaways, communication style, etc.)?
- On the consumer side:
  - How well is this consumer doing in progressing through the information?
  - Have they met the learning objectives and outcomes?
  - Have they grokked the takeaways?
  - Has the info they asked about actually been shared? Should I create a request?
  - Is the consumer exhibiting any confusion?
  - Is the consumer progressing through bloom on all important topics?
  - What is the user's preferred communication style?

## BK's original message

I have a pattern that I'd like to explore for improving our experience developing assistants.  There are times where assistants need to gather info from a user but likely has enough context from the current conversation history, attachments, etc., to make a pretty "educated guess" and infer the right answer.  For example, we may want to capture information about the desired audience for a document or knowledge transfer session so that we can use that to inform other processes in our assistant guidance and/or workflow.  Instead of explicitly asking the user for this, maybe we do something that will let us do more of the work for the user.

Let's take the example of what you just asked me here.  You gave me a whole bunch of things up front.  You let me know what all you can help with, you asked me to share my content or ideas, but then you also ask me about my audience.  You talk about the knowledge brief (which btw, I don't see yet, is that a bug?  You said, 'In the side panel, you can see your "knowledge brief"'.) and let me know I can ask you to update it at any time (is that burden on me now, or is it optional for me because really you are managing it?  I hope it's the latter, I'm hoping you can do more for me and reduce my burden).  Then you close with once again asking me about the audience.

Ok, so that's a LOT to take in on the first interaction of the conversation.  That's also a lot of text to read, and honestly this is the first time I've read it ALL and I have heard from others that they would just skim this much content and move right to chatting, so we should think about how to support that WHEN (not IF) it happens...

But regardless, what if we took a different approach, what if we instead asked purely about the content or ideas - or even better yet, since the whole point of this experience is that we're trying to transfer knowledge to someone else (or many others), maybe we should start with asking what the desired takeaways are for those we're going to share it with; then you can be more helpful in making sure you have what you need from me to do so (tip: for THIS conversation, my takeaway that I want for my recipients is that they understand the proposed feature I want to have implemented and that you have enough info to answer their questions on the "why" behind it, etc.)

Ok, so if asked for that kind of context _first_, then it seems when we actually want/need the audience info (don't think it's critical on the first interaction), there MAY be a lot of contextual hints to at least point us in the right direction.  Look at what I've said so far... I have indicated a takeaway that includes implementing a feature within our assistant code, so that says a LOT about who are audience IS and also who it ISN'T for this particular conversation.  I bet you could probably even assert something like "Let's talk about your audience, it appears we want to target developers would implement these features in code <... etc.>, is this correct?  Is there anything else you want to tell me?" from that info.

If you do that, then here is the impact on the user felt experience.  If it's wrong, it's not really much more work for the user to share what the actual audience is than the current approach of asking the very open-ended question "Who are you going to be sharing your knowledge with?"  I suspect, however, that every conversation will have at least some hints and even with the least contextual hints, what you infer and assert may be better than the blank-slate question and allow for users to provide feedback and tweak it - or, in the ideal case, you nail it and the user can just say "yep" and continue on.  Win!  We call this "designing for failure with AI" and it's the idea that we want to use AI in smart ways when we can, but we should assume we're going to be wrong and put it into place in ways were we're not creating extra burden for the user for how they would already do a thing (in this case, answering a fully open-ended question from the assistant about the target audience), but in the cases where we are right can be delighters for the user, or in cases like this with NL, "degrees" of being right or partially so can be somewhere on the spectrum between and at least reduce user burden and potentially help make it easier for them to answer.

There are many other places where this could apply just in the knowledge transfer scenario.  For example, we also care about the communication style that users on both side (the knowledge transfer coordinator and the recipients) would benefit from you using with them.  Sure, again we could ask them directly, OR after a few interactions we could take cues from how they are interacting with you and then follow the same infer/assert but confirm pattern.  We might apply the same approach if asked to create a blurb to paste into other conversations/docs/emails with the share link to get a better feel for what level of detail, tone, etc. to put into that.

So here is my proposal.  Since this is a pattern I expect exists more frequently than we realize, let's start looking for it more often and let's consider how we make any code we write for this as something more reusable in that way.  I generally think it should go something like this:

* Identify the scenario in which we want to try this out within the flow of a conversation/workflow
* Have some level of conversation to build up some context
* Hook into whatever assistant response flow we have designed that would allow us to determine "when" we are ready to invoke this behavior and then do so
* Pass that conversation history (and relevant attachments, etc.) into an LLM call that asks for a response that could be returned as the next assistant message that infers the answer to the question we have, asserts it to the user in an observational way while also confirming with them if it is correct or feedback that is needed
* Insert that message into the conversation history as the assistant and let the conversation/workflow proceed as before

By doing this as a sub-step, with a separate context + instructions than the general conversation/workflow or assistant response flow, we can both build and receive a more focused request as we use the LLM.  Also, this makes for a nice way to abstract this out for re-use.  It can become a function that is called, pass in the right context + instruction and insert the message back into the conversation, making it easy to do more often and also to later invest more in the "under the hood" of that function if/as needed.

Ok, that's a lot, let's start there and see where we're at.  What do you think?  Do you have enough to answer any reasonable questions you would expect from our recipients of this knowledge transfer, and do you have enough to propose a plan for how they would build it, in collaboration with them providing more context on their code, etc.?