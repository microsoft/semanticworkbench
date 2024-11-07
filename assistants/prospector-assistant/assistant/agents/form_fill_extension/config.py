from typing import Annotated

from pydantic import BaseModel, Field

from .steps import acquire_form_step, extract_form_fields_step, fill_form_step


class FormFillConfig(BaseModel):
    acquire_form_config: Annotated[
        acquire_form_step.AcquireFormConfig,
        Field(title="Form Acquisition", description="Guided conversation for acquiring a form from the user."),
    ] = acquire_form_step.AcquireFormConfig()

    extract_form_fields_config: Annotated[
        extract_form_fields_step.ExtractFormFieldsConfig,
        Field(title="Extract Form Fields", description="Configuration for extracting form fields from the form."),
    ] = extract_form_fields_step.ExtractFormFieldsConfig()

    fill_form_config: Annotated[
        fill_form_step.FillFormConfig,
        Field(title="Fill Form", description="Guided conversation for filling out the form."),
    ] = fill_form_step.FillFormConfig()
