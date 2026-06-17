"""Compatibility shim for ``python -m quickbib.verify``.

The reference-verification engine moved to :mod:`doi2bib3.verify` -- this
module delegates to its CLI (``doi2bib3 verify``) while adding the one
piece doi2bib3 deliberately stays out of: cloning an Overleaf project via
its Git bridge.

For new code, prefer ``doi2bib3 verify <path>`` (CLI) or
``from doi2bib3 import verify_bibtex`` (library).
"""

import argparse
import os
import sys
import tempfile

from doi2bib3.cli import main as _d2b_main

from .overleaf import OverleafError, clone_or_pull


def main(argv: list[str] | None = None) -> int:
    """Pre-handle ``--overleaf`` and ``--token``, then defer to ``doi2bib3 verify``."""
    argv = list(sys.argv[1:] if argv is None else argv)

    overleaf, token, rest = _extract_overleaf_args(argv)
    if overleaf is not None:
        token = token or os.environ.get("OVERLEAF_GIT_TOKEN", "")
        try:
            repo = clone_or_pull(overleaf, token, workdir=tempfile.gettempdir())
        except OverleafError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        rest = [str(repo), *rest]

    return _d2b_main(["verify", *rest])


def _extract_overleaf_args(argv: list[str]) -> tuple[str | None, str, list[str]]:
    """Pull ``--overleaf`` / ``--token`` out of ``argv``, returning the rest unchanged.

    A tiny argparse is used so we accept both ``--overleaf ID`` and
    ``--overleaf=ID`` forms without disturbing the other flags that
    ``doi2bib3 verify`` will see.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--overleaf", metavar="PROJECT_ID")
    parser.add_argument("--token")
    args, rest = parser.parse_known_args(argv)
    return args.overleaf, args.token or "", rest


if __name__ == "__main__":
    sys.exit(main())
