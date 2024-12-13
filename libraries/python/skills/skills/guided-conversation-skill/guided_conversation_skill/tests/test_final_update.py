import pytest
from guided_conversation_skill.chat_completions.final_artifact_update import final_artifact_update
from guided_conversation_skill.definitions import acrostic_poem
from guided_conversation_skill.message import Conversation, Message
from skill_library.types import LanguageModel


@pytest.mark.skip("For manual testing.")
async def test_final_artifact_update(client: LanguageModel) -> None:
    conversation = Conversation().add_user_message("Hi!")

    conversation = Conversation(
        messages=[
            Message(
                param={
                    "role": "assistant",
                    "content": "Hello! Today, we're going to learn how to write an acrostic poem. Have you ever heard of or tried writing one before?",
                },
                turn=1,
            ),
            Message(param={"content": "What's that?", "role": "user"}),
            Message(
                param={
                    "role": "assistant",
                    "content": "An acrostic poem is a fun and creative type of poem where the first letter of each line spells out a word or phrase vertically. Here's how you can make one:\n\n1. **Choose a word or phrase:** This will be the subject of your acrostic poem.\n2. **Write the letters vertically:** Write each letter from your chosen word or phrase down the page.\n3. **Think of words or phrases:** For each letter, think of a word or phrase that starts with it.\n4. **Write your words or phrases:** Write these next to their corresponding letters to create your poem.\n\nHere’s a quick example using the word “HAPPY”:\n\n- Having fun with friends all day,\n- Awesome games that we all play.\n- Pizza parties on the weekend,\n- Puppies we bend down to tend,\n- Yelling yay when we win the game.\n\nWould you like to try writing your own acrostic poem? You can start by choosing a word or phrase. Let me know what you pick!",
                },
                turn=2,
            ),
            Message(param={"content": "Yes. I'd like to write one!", "role": "user"}, turn=2),
            Message(
                param={
                    "role": "assistant",
                    "content": "That's great to hear! Let's start by choosing a word or phrase that you'd like to use for your acrostic poem. It can be anything that you find interesting or fun. Once you've picked it, we can move on to the next step. What word or phrase would you like to use?",
                },
                turn=3,
            ),
            Message(param={"content": "PIG", "role": "user"}, turn=3),
            Message(
                param={
                    "role": "assistant",
                    "content": 'Great choice! Let\'s start creating your acrostic poem with the word "PIG". \n\nRemember to think of a word or phrase for each letter in "PIG". For example, it might look something like this:\n\n- **P**: \n- **I**: \n- **G**: \n\nYou can be as creative as you like! What words or phrases would you like to use for each letter?',
                },
                turn=4,
            ),
            Message(param={"content": "Pretty. Illicit. Guilty.", "role": "user"}, turn=4),
            Message(
                param={
                    "role": "assistant",
                    "content": 'It\'s wonderful that you\'ve given it a try! Let\'s take a closer look at your poem. While the word choice is important in poetry, we should be mindful of the appropriateness and the message the poem conveys. The word "illicit" might not be suitable for what we\'re trying to achieve here.\n\nLet\'s think about other words for "I" and "G" that might fit more creatively and appropriately. Perhaps think about things pigs like to do, where they live, or how they look. Would you like to try coming up with alternative words or phrases for "I" and "G"?',
                },
                turn=5,
            ),
            Message(
                param={"content": "Pretty pork. I like spending time with them. Grimey.", "role": "user"},
                turn=5,
            ),
        ],
        turn=5,
    )

    artifact = {
        "student_poem": "Pretty pork. I like spending time with them. Guilty pleasure.",
        "initial_feedback": "The initial poem had great creativity with phrases like 'Pretty pork' and 'Guilty.' However, the choice of 'illicit' was inappropriate for the context.",
        "final_feedback": "The final version improved significantly by choosing more suitable phrases. 'I like spending time with them' makes the poem more personal and apt. Overall, nice adjustments to keep the tone light and fun, matching the subject!",
        "inappropriate_behavior": [],
    }
    definition = acrostic_poem.definition
    final_artifact = await final_artifact_update(
        client,
        definition,
        conversation,
        artifact,
    )
    assert final_artifact is not None
