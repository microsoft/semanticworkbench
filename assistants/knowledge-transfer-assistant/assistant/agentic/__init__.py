from types import SimpleNamespace

from .coordinator_next_action import get_coordinator_next_action_suggestion
from .detect_audience_and_takeaways import detect_audience_and_takeaways
from .team_welcome import generate_team_welcome_message
from .update_digest import update_digest

agentic = SimpleNamespace(
    get_coordinator_next_action_suggestion=get_coordinator_next_action_suggestion,
    detect_audience_and_takeaways=detect_audience_and_takeaways,
    generate_team_welcome_message=generate_team_welcome_message,
    update_digest=update_digest,
)
