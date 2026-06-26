__all__ = ["read_tex"]


def __getattr__(name):
    if name == "read_tex":
        from tex2imgs.utils import read_tex

        return read_tex
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
