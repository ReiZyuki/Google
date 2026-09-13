import inspect
import keyword


def set_result(target, value):
    if not isinstance(target, str):
        raise TypeError("Result variable name must be a string.")
    return value


def validate_target(target):
    if not isinstance(target, str):
        raise TypeError("Right-side value must be a variable name string.")
    if not target.isidentifier() or keyword.iskeyword(target):
        raise ValueError(f"Invalid Python variable name: {target}")


def inject_result(target, value, library_dir):
    frame = inspect.currentframe()
    try:
        frame = frame.f_back
        while frame:
            filename = frame.f_code.co_filename
            if not filename.startswith(library_dir):
                frame.f_globals[target] = value
                try:
                    frame.f_locals[target] = value
                except Exception:
                    pass
                break
            frame = frame.f_back
    finally:
        del frame
