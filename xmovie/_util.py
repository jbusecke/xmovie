import importlib
from functools import wraps


def requires(*modules):
    """Function decorator to check for required modules before running.

    Parameters
    ----------
    *modules : iterable of str
        Required modules to check for.
    """
    def inner(fn):

        @wraps(fn)
        def wrapped(*args, **kwargs):
            failed = []
            for module in modules:
                try:
                    importlib.import_module(module)
                except ImportError:
                    failed.append(module)
            
            if failed:
                raise RuntimeError(
                    f"Required modules failed to import: {', '.join(f'{m!r}' for m in modules)}. "
                    "Please install the relevant packages if you wish to proceed."
                )

            fn(*args, **kwargs)

        return wrapped
    
    return inner
