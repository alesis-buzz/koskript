class Errors:
    class SyntaxError(Exception):
        def __init__(self, *args):
            super().__init__(*args)

    class NameError(Exception):
        def __init__(self, *args):
            super().__init__(*args)

    class MismatchType(Exception):
        def __init__(self, *args):
            super().__init__(*args)
    
    class ProtectedObject(Exception):
        def __init__(self, *args):
            super().__init__(*args)

    class RuntimeError(Exception):
        def __init__(self, *args):
            super().__init__(*args)

    class KoskriptError(Exception):
        """A `throw` that reached the top level without a matching `catch`.

        The message is the error name plus its `message` field, and
        `instance` holds the underlying `ErrorInstance`.
        """

        def __init__(self, message, instance=None):
            super().__init__(message)
            self.instance = instance
