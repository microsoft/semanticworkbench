from .state import Step


def draft_outline_workflow() -> Step:
    next_step_name = StepName.UNDEFINED
    user_decision = GC_UserDecision.UNDEFINED

    current_step_name = self._state.mode.get_step().get_name()
    match current_step_name:
        case StepName.UNDEFINED:
            next_step_name = StepName.DO_DRAFT_OUTLINE
        case StepName.DO_DRAFT_OUTLINE:
            next_step_name = StepName.DO_GC_GET_OUTLINE_FEEDBACK
        case StepName.DO_GC_GET_OUTLINE_FEEDBACK:
            user_decision = self._state.mode.get_step().get_gc_user_decision()
            if user_decision is not GC_UserDecision.UNDEFINED:
                match user_decision:
                    case GC_UserDecision.UPDATE_OUTLINE:
                        next_step_name = StepName.DO_DRAFT_OUTLINE
                    case GC_UserDecision.DRAFT_PAPER:
                        next_step_name = StepName.DO_FINISH
                    case GC_UserDecision.EXIT_EARLY:
                        next_step_name = StepName.DO_FINISH
        case StepName.DO_FINISH:
            next_step_name = StepName.UNDEFINED

    return next_step_name

    return Step()
