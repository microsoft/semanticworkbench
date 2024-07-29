from . import auth

workflow = auth.ServiceUserPrincipal(user_id="workflow", name="Workflow Service")

semantic_workbench = auth.ServiceUserPrincipal(user_id="semantic-workbench", name="Semantic Workbench Service")
