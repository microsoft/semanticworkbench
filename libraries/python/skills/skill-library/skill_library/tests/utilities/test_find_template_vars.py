from skill_library.utilities import find_template_vars


def test_find_template_vars():
    template = "This is a {{test}} template with {{multiple}} variables. See: {{test}}"
    variables = find_template_vars(template)

    # Should be deduplicated, but kept in order of first appearance.
    assert variables == ["test", "multiple"]
