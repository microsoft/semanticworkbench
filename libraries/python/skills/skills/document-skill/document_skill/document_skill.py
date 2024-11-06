from chat_driver import ChatDriverConfig
from context import Context
from pydantic import BaseModel  # temp to have something to experiment with
from skill_library import RoutineTypes, Skill
from skill_library.routine import InstructionRoutine, ProgramRoutine

NAME = "document_skill"
DESCRIPTION = "Anything related to documents - creation, edit, translation"


class Attachment(BaseModel):
    filename: str
    content: str


class Outline(BaseModel):
    version: int = 0
    content: str


class Content(BaseModel):
    content: str  # Content/fragment/page that is created will likely have
    # data associated with it... not sure what more at this point.


class Paper(BaseModel):
    version: int = 0
    contents: list[Content] = []


class DocumentSkillContext(Context):
    def __init__(self) -> None:
        self.chat_history: str = ""
        self.attachments_list: list[Attachment] = []
        self.outline_versions: list[Outline] = []
        self.paper_versions: list[Paper] = []

        super().__init__()  # currently all params of Context can be None.


class DocumentSkill(Skill):
    def __init__(
        self,
        context: Context,
        chat_driver_config: ChatDriverConfig,
    ) -> None:
        self.document_skill_context: DocumentSkillContext = DocumentSkillContext()

        actions = [
            self.test_action,
        ]

        # however, with current skill chat driver config (no chat connection setup),
        # i see an issue when running the instruction routine as a command.  It correctly detects the
        # test_action step to run... but the I get the response: "Error running function: 'NoneType' object has no attribute 'chat'"
        # it looks like information events after actions run in posix command are passed through a chat driver with model
        # connectivity... as it explains the result in a natural language response wrapper (not the simple result of directly calling each command).
        # i'm wondering if this is where the skill chat driver gets used as a chat connection?
        # YES.  look at instruction_routine_runner.  This is how it is designed currently.
        # i.r.r. will use the configured chat driver of the routine's skill to call "respond" with message being the "step" (the function in the routine)...
        # but this means it is passed to the language model with the tool choices (assuming the action/function has also been registered as a function not just
        # as a command... so that it can be included in the tool selection for the skill's chat driver to pass to the language model). Our code will execute (code in the
        # chat driver... i think... i need to look into chat driver code more...) but the wrapped response out of the respond function is returned and messaged
        # out as an information event.
        # so big Q here... should a program routine or instruction routine be run by a language model?  I'm not sure I want this... can we have an option?
        routines: list[RoutineTypes] = [
            self.test_instruction_routine(),
        ]

        # Configure the skill's chat driver.
        #####
        # EVEN IF, the skill will not use the chat driver for any llm call, right now
        # the skill's chat driver is used to forward available skill commands and functions to
        # any higher level assistant that has those skills registered.
        #####
        chat_driver_config.commands = actions
        chat_driver_config.functions = actions

        super().__init__(
            name=NAME,
            description=DESCRIPTION,
            context=context,
            chat_driver_config=chat_driver_config,
            skill_actions=actions,
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def test_instruction_routine(self) -> InstructionRoutine:
        """
        Update this routine description.
        """
        return InstructionRoutine(
            name="test_instruction_routine",
            description="Description of what the routine does.",
            routine=("test_action"),
        )

    def template_example_routine(self) -> ProgramRoutine:
        """
        Update this routine description.
        """
        return ProgramRoutine(
            name="template_example_routine",
            description="Description of what the routine does.",
            program=("TBD"),
        )

    ##################################
    # Actions
    ##################################
    def test_action(
        self,
        context: Context,
    ) -> str:
        return "hello world"  #

    # This may not be needed as an action... not sure yet how context will be set.


#    def set_context(
#        self,
#        context: Context,
#        chat_history: str,
#        attachments_list: list[Attachment]
#    ) -> None:
#        self.context.chat_history = chat_history
#        self.context.attachments_list = attachments_list
#
#    async def draft_outline(
#        self,
#        context: Context,
#        openai_client: AsyncOpenAI,
#        model: str,
#        user_feedback: str | None = None
#        ) -> None:
#
#        # construct completion request - draft outline from existing info
#        messages: list[ChatCompletionMessageParam] = []
#        _add_main_system_message(messages, draft_outline_main_system_message)
#        _add_chat_history_system_message(messages, self.context.chat_history)
#        _add_attachments_system_message(messages, self.context.attachments_list)
#
#        if len(self.context.outline_versions) != 0:
#            _add_existing_outline_system_message(messages, self.context.outline_versions[-1].content)
#
#        if user_feedback is not None:
#            _add_user_feedback_system_message(messages, user_feedback)
#
#        completion_args = {
#            "messages": messages,
#            "model": model,
#            "response_format": {
#                "type": "text"
#              }
#        }
#        completion = await openai_client.chat.completions.create(**completion_args)
#        outline = completion.choices[0].message.content
#
#        debug_log = json.dumps(completion_args, indent=2) + "\n\n"
#        debug_log += f"Response:\n{completion.model_dump_json(indent=2)}\n\n"
#        #print(debug_log)
#
#        # message event should be sent from within this action. For now using stdout.
#        chat_output = f"\nAssistant: Outline drafted\n\n{outline}\n"
#        sys.stdout.write(chat_output)
#        sys.stdout.flush()
#
#        # store generated outline
#        version_no = len(self.context.outline_versions) + 1
#        self.context.outline_versions.append(Outline(version=version_no, content=outline))
#
#        # update chat_history.
#        self.context.chat_history = self.context.chat_history + chat_output
#        return
#
#    async def draft_content(
#        self,
#        context: Context,
#        openai_client: AsyncOpenAI,
#        model: str,
#        user_feedback: str | None = None,
#        decision: str | None = None
#    ) -> None:
#         # construct completion request - draft content/page/fragment from existing info
#        messages: list[ChatCompletionMessageParam] = []
#
#        if decision == "[ITERATE]":
#            _add_main_system_message(messages, draft_page_iterate_main_system_message)
#        else:
#            _add_main_system_message(messages, draft_page_continue_main_system_message)
#
#        _add_chat_history_system_message(messages, self.context.chat_history)
#        _add_attachments_system_message(messages, self.context.attachments_list)
#        _add_approved_outline_system_message(messages, self.context.outline_versions[-1].content)
#
#        if len(self.context.paper_versions) != 0:
#            if decision == "[ITERATE]" and user_feedback is not None:
#                _add_existing_content_system_message(messages, self.context.paper_versions[-1].contents[-1].content)
#                _add_user_feedback_system_message(messages, user_feedback)
#            else:
#                full_content = ""
#                for content in self.context.paper_versions[-1].contents:
#                    full_content += content.content
#                _add_existing_content_system_message(messages, full_content)
#
#        completion_args = {
#            "messages": messages,
#            "model": model,
#            "response_format": {
#                "type": "text"
#              }
#        }
#        completion = await openai_client.chat.completions.create(**completion_args)
#        draft = completion.choices[0].message.content
#
#        debug_log = json.dumps(completion_args, indent=2) + "\n\n"
#        debug_log += f"Response:\n{completion.model_dump_json(indent=2)}\n\n"
#        #print(debug_log)
#
#        # message event should be sent from within this action. For now using stdout.
#        if decision == "[ITERATE]":
#            chat_output = f"\nAssistant: Updated page based on your feedback:\n\n{draft}\n"
#        else:
#            chat_output = f"\nAssistant: Page drafted:\n\n{draft}\n"
#        sys.stdout.write(chat_output)
#        sys.stdout.flush()
#
#        # store generated content/page/fragment
#        version_no = len(self.context.paper_versions) + 1
#        if len(self.context.paper_versions) == 0:
#            self.context.paper_versions.append(Paper(version=version_no, contents=[Content(content=draft)]))
#        else:
#            existing_contents = self.context.paper_versions[-1].contents
#            if decision == "[ITERATE]":
#                existing_contents[-1].content = draft
#            else:
#                existing_contents.append(Content(content=draft))
#            self.context.paper_versions.append(Paper(version=version_no, contents=existing_contents))
#
#        # update chat_history.
#        self.context.chat_history = self.context.chat_history + chat_output
#        return
#
#    async def get_user_feedback(
#        self,
#        context: Context,
#        openai_client: AsyncOpenAI,
#        model: str,
#        outline: bool
#    ) -> tuple[str, str]:
#
#        # message event should be sent from within this action. For now using stdout.
#        event_message = ("Please review the above draft and provide me any feedback. You can also "
#                        "let me know if you are ready to continue drafting the paper or would like"
#                        " to iterate on the current content.")
#        # msg_event = MessageEvent(message=event_message)
#        chat_output = f"\nAssistant: {event_message}\n"
#        sys.stdout.write(chat_output)
#        sys.stdout.flush()
#        self.context.chat_history = self.context.chat_history + chat_output
#
#        #user response input should be awaited for here from interface. For now using stdout.
#        sys.stdout.write("\nUser: ")
#        user_feedback = input()
#        sys.stdout.write(user_feedback)
#        sys.stdout.flush()
#        chat_output = f"\nUser: {user_feedback}"
#        self.context.chat_history = self.context.chat_history + chat_output
#
#        # construct completion request - determine user intent from feedback
#        messages: list[ChatCompletionMessageParam] = []
#        if outline is True:
#            _add_main_system_message(messages, outline_feedback_main_system_message)
#        else:
#            _add_main_system_message(messages, draft_page_feedback_main_system_message)
#
#        _add_chat_history_system_message(messages, self.context.chat_history)
#
#        if len(self.context.outline_versions) != 0:
#            if outline is True:
#                _add_existing_outline_system_message(messages, self.context.outline_versions[-1].content)
#            else:
#                _add_approved_outline_system_message(messages, self.context.outline_versions[-1].content)
#
#        if outline is False:
#            if len(self.context.paper_versions) != 0:
#                full_content = ""
#                for content in self.context.paper_versions[-1].contents:
#                    full_content += content.content
#                _add_existing_content_system_message(messages, full_content)
#
#        _add_user_feedback_system_message(messages, user_feedback)
#
#        completion_args = {
#            "messages": messages,
#            "model": model,
#            "response_format": {
#                "type": "text"
#              }
#        }
#        completion = await openai_client.chat.completions.create(**completion_args)
#        decision = completion.choices[0].message.content # this should NOT be done as a string.
#
#        debug_log = json.dumps(completion_args, indent=2) + "\n\n"
#        debug_log += f"Response:\n{completion.model_dump_json(indent=2)}\n\n"
#        #print(debug_log)
#
#        return decision, user_feedback
#
#    # A little helper
#    def print_final_doc(self, context: Context) -> None:
#        print("Assistant: Looks like we have a completed doc. Here it is!\n")
#        # compose full content for existing paper (the latest version)
#        full_content = ""
#        for content in self.context.paper_versions[-1].contents:
#            full_content += content.content
#        print(full_content)
#
#
## Current approach uses system messages for everything.
# draft_outline_main_system_message = ("Generate an outline for the document, including title. The outline should include the key points that will"
#    " be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the"
#    " conversation that has taken place. The outline should be a hierarchical structure with multiple levels of"
#    " detail, and it should be clear and easy to understand. The outline should be generated in a way that is"
#    " consistent with the document that will be generated from it.")
#    #("You are an AI assistant that helps draft outlines for a future flushed-out document."
#    # " You use information from a chat history between a user and an assistant, a prior version of a draft"
#    # " outline if it exists, as well as any other attachments provided by the user to inform a newly revised "
#    # "outline draft. Provide ONLY any outline. Provide no further instructions to the user.")
#
# outline_feedback_main_system_message = ("Use the user's most recent feedback to determine if the user wants to iterate further on the"
#    " provided outline [ITERATE], or if the user is ready to move on to drafting a paper from the"
#    " provided outline [CONTINUE]. Based on the user's feedback on the provided outline, determine if"
#    " the user wants to [ITERATE], [CONTINUE], or [QUIT]. Reply with ONLY [ITERATE], [CONTINUE], or [QUIT].")
#
# draft_page_continue_main_system_message = ("Following the structure of the outline, create the content for the next (or first) page of the"
#    " document - don't try to create the entire document in one pass nor wrap it up too quickly, it will be a"
#    " multi-page document so just create the next page. It's more important to maintain"
#    " an appropriately useful level of detail. After this page is generated, the system will follow up"
#    " and ask for the next page. If you have already generated all the pages for the"
#    " document as defined in the outline, return empty content.")
#    #("You are an AI assistant that helps draft new content of a document based on an outline."
#    # " You use information from a chat history between a user and an assistant, the approved outline from the user,"
#    # "and an existing version of drafted content if it exists, as well as any other attachments provided by the user to inform newly revised "
#    # "content. Newly drafted content does not need to cover the entire outline.  Instead it should be limited to a reasonable 100 lines of natural language"
#    # " or subsection of the outline (which ever is shorter). The newly drafted content should be written as to append to any existing drafted content."
#    # " This way the user can review newly drafted content as a subset of the future full document and not be overwhelmed."
#    # "Only provide the newly drafted content. Provide no further instructions to the user.")
#
# draft_page_iterate_main_system_message = ("Following the structure of the outline, iterate on the currently drafted page of the"
#    " document. It's more important to maintain"
#    " an appropriately useful level of detail. After this page is iterated upon, the system will follow up"
#    " and ask for the next page.")
#
# draft_page_feedback_main_system_message = ("You are an AI assistant that helps draft outlines for a future flushed-out document."
#    " You use the user's most recent feedback to determine if the user wants to iterate further on the"
#    " provided draft content [ITERATE], or if the user is ready to move on to drafting new additional content"
#    " [CONTINUE]. Based on the user's feedback on the provided drafted content, determine if"
#    " the user wants to [ITERATE], [CONTINUE], or [QUIT]. Reply with ONLY [ITERATE], [CONTINUE], or [QUIT].")
#
# def _add_main_system_message(messages: list[ChatCompletionMessageParam], prompt: str) -> None:
#    message: ChatCompletionSystemMessageParam = {
#        "role": "system",
#        "content": prompt
#    }
#    messages.append(message)
#
# def _add_chat_history_system_message(messages: list[ChatCompletionMessageParam], chat_history: str) -> None:
#    message: ChatCompletionSystemMessageParam = {
#        "role": "system",
#        "content": f"<CHAT_HISTORY>{chat_history}</CHAT_HISTORY>"
#    }
#    messages.append(message)
#
# def _add_attachments_system_message(messages: list[ChatCompletionMessageParam], attachments: list[Attachment]) -> None:
#    for item in attachments:
#        message: ChatCompletionSystemMessageParam = {
#            "role": "system",
#            "content": (f"<ATTACHMENT><FILENAME>{item.filename}</FILENAME><CONTENT>{item.content}</CONTENT></ATTACHMENT>")
#        }
#        messages.append(message)
#
# def _add_existing_outline_system_message(messages: list[ChatCompletionMessageParam], outline: str) -> None:
#    message: ChatCompletionSystemMessageParam = {
#        "role": "system",
#        "content": (f"<EXISTING_OUTLINE>{outline}</EXISTING_OUTLINE>")
#    }
#    messages.append(message)
#
# def _add_approved_outline_system_message(messages: list[ChatCompletionMessageParam], outline: str) -> None:
#    message: ChatCompletionSystemMessageParam = {
#        "role": "system",
#        "content": (f"<APPROVED_OUTLINE>{outline}</APPROVED_OUTLINE>")
#    }
#    messages.append(message)
#
# def _add_existing_content_system_message(messages: list[ChatCompletionMessageParam], content: str) -> None:
#    message: ChatCompletionSystemMessageParam = {
#        "role": "system",
#        "content": (f"<EXISTING_CONTENT>{content}</EXISTING_CONTENT>")
#    }
#    messages.append(message)
#
# def _add_user_feedback_system_message(messages: list[ChatCompletionMessageParam], user_feedback: str) -> None:
#    message: ChatCompletionSystemMessageParam = {
#        "role": "system",
#        "content": (f"<USER_FEEDBACK>{user_feedback}</USER_FEEDBACK>")
#    }
#    messages.append(message)
#
