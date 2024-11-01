from typing import Annotated

from pydantic import BaseModel, Field

from . import gce
from .steps import acquire_form, extract_form_fields, fill_form


class FormFillAgentConfig(BaseModel):
    acquire_form_config: Annotated[
        gce.GuidedConversationDefinition,
        Field(title="Form Acquisition", description="Guided conversation for acquiring a form from the user."),
    ] = acquire_form.definition.model_copy()

    extract_form_fields_config: Annotated[
        extract_form_fields.ExtractFormFieldsConfig,
        Field(title="Extract Form Fields", description="Configuration for extracting form fields from the form."),
    ] = extract_form_fields.ExtractFormFieldsConfig()

    fill_form_config: Annotated[
        gce.GuidedConversationDefinition,
        Field(title="Fill Form", description="Guided conversation for filling out the form."),
    ] = fill_form.definition.model_copy()
