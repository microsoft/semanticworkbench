from context.context import Context, ContextProtocol, LogEmitter


def test_context_creation():
    # Create a context object
    context = Context()

    # Check that the context object was created
    assert context.session_id is not None
    assert context.run_id is None
    assert context.emit is not None


def test_context_type():
    # Create a context object
    context = Context()

    # Check that the context object has the correct type
    assert isinstance(context, ContextProtocol)


def test_context_methods():
    # Create a context object
    context = Context()

    # Check that the context object has the correct methods
    assert hasattr(context, "to_dict")
    assert hasattr(context, "__repr__")
    assert hasattr(context, "__str__")


def test_context_attributes():
    # Create a context object
    context = Context()

    # Check that the context object has the correct attributes
    assert hasattr(context, "session_id")
    assert hasattr(context, "run_id")
    assert hasattr(context, "emit")


def test_context_callable_methods():
    # Create a context object
    context = Context()

    # Check that the context object has callable methods
    assert callable(context.to_dict)
    assert callable(context.__repr__)
    assert callable(context.__str__)


def test_context_attribute_types():
    # Create a context object
    context = Context()

    # Check that the context object has the correct attribute types
    assert isinstance(context.session_id, str)
    assert isinstance(context.run_id, str) or context.run_id is None
    assert callable(context.emit)


def test_context_to_dict():
    # Create a context object
    context = Context()

    # Check that the to_dict method returns the correct dictionary
    assert context.to_dict() == {
        "session_id": context.session_id,
        "run_id": context.run_id,
        "emit": context.emit.__class__.__name__,
    }


def test_context_repr_str():
    # Create a context object
    context = Context()

    # Check that the __repr__ and __str__ methods return the correct strings
    assert context.__repr__() == f"Context({context.session_id})"
    assert context.__str__() == f"Context({context.session_id})"


def test_log_emitter_creation():
    # Create a log emitter object
    log_emitter = LogEmitter()

    # Check that the log emitter object was created
    assert log_emitter is not None


def test_log_emitter_type():
    # Create a log emitter object
    log_emitter = LogEmitter()

    # Check that the log emitter object has the correct type
    assert isinstance(log_emitter, LogEmitter)


def test_log_emitter_methods():
    # Create a log emitter object
    log_emitter = LogEmitter()

    # Check that the log emitter object has the correct methods
    assert hasattr(log_emitter, "emit")
    assert callable(log_emitter.emit)


def test_context_with_log_emitter():
    # Create a log emitter object
    log_emitter = LogEmitter()

    # Create a context object with a log emitter
    context = Context(emit=log_emitter.emit)

    # Check that the context object was created
    assert context.session_id is not None
    assert context.run_id is None
    assert context.emit is not None
