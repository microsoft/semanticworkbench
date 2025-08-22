from types import SimpleNamespace

from .act import act
from .coordinator_next_action import get_coordinator_next_action_suggestion
from .create_invitation import create_invitation
from .detect_audience_and_takeaways import detect_audience_and_takeaways
from .detect_coordinator_actions import detect_coordinator_actions
from .detect_information_request_needs import detect_information_request_needs
from .detect_knowledge_package_gaps import detect_knowledge_package_gaps
from .focus import focus
from .team_welcome import generate_team_welcome_message
from .update_digest import update_digest

agentic = SimpleNamespace(
    act=act,
    create_invitation=create_invitation,
    detect_audience_and_takeaways=detect_audience_and_takeaways,
    detect_coordinator_actions=detect_coordinator_actions,
    detect_information_request_needs=detect_information_request_needs,
    detect_knowledge_package_gaps=detect_knowledge_package_gaps,
    focus=focus,
    generate_team_welcome_message=generate_team_welcome_message,
    get_coordinator_next_action_suggestion=get_coordinator_next_action_suggestion,
    update_digest=update_digest,
)
