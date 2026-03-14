import hashlib

from .models import Segment


INLINE_TEXT_COMMANDS = {
    "textbf",
    "textit",
    "texttt",
    "textsf",
    "textrm",
    "textsc",
    "textmd",
    "textup",
    "emph",
    "underline",
    "uline",
    "uuline",
    "sout",
    "st",
    "textsuperscript",
    "textsubscript",
    "mbox",
    "parbox",
    "makebox",
    "textcolor",
    "colorbox",
    "fcolorbox",
    "hl",
    "url",
    "nolinkurl",
    "footnote",
    "caption",
    "foreignlanguage",
    "enquote",
}


def hash_text(value: str) -> str:
    """Return a stable hash for a text segment used in incremental sync."""

    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def get_document_window(content: str) -> tuple[int, int]:
    """Return the content boundaries to parse inside the LaTeX document body."""

    start_marker = r"\begin{document}"
    end_marker = r"\end{document}"

    start = content.find(start_marker)
    end = content.rfind(end_marker)

    if start == -1 or end == -1 or start >= end:
        return (0, len(content))

    return (start + len(start_marker), end)


def _consume_balanced(content: str, i: int, end: int, opener: str, closer: str) -> int:
    """Advance cursor past a balanced bracketed expression."""

    if i >= end or content[i] != opener:
        return i

    depth = 0
    while i < end:
        char = content[i]
        if char == "\\":
            i += 2
            continue

        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return i + 1

        i += 1

    return i


def _advance_inline_command(content: str, i: int, end: int) -> int | None:
    """Advance over inline text commands that should stay attached to content."""

    if i >= end or content[i] != "\\":
        return None

    j = i + 1
    if j >= end or not content[j].isalpha():
        return None

    while j < end and content[j].isalpha():
        j += 1

    command_name = content[i + 1 : j]
    if j < end and content[j] == "*":
        j += 1

    if command_name not in INLINE_TEXT_COMMANDS:
        return None

    # Keep optional/required arguments attached to the inline command.
    while j < end:
        if content[j].isspace():
            j += 1
            continue

        if content[j] == "[":
            j = _consume_balanced(content, j, end, "[", "]")
            continue

        if content[j] == "{":
            j = _consume_balanced(content, j, end, "{", "}")
            continue

        break

    return j


def _advance_latex_command(content: str, i: int, end: int) -> int:
    """Advance cursor over a generic LaTeX command and selected arguments."""

    j = i + 1
    if j < end and content[j].isalpha():
        while j < end and content[j].isalpha():
            j += 1

        command_name = content[i + 1 : j]
        if j < end and content[j] == "*":
            j += 1

        if command_name in {"begin", "end", "href", "vspace", "hspace"}:
            # Skip all immediate [] / {} arguments after selected commands.
            # - \begin / \end: layout declarations should never be translated.
            # - \href: both URL and label arguments are left untouched.
            # - \vspace / \hspace: spacing arguments should never be translated.
            while j < end:
                if content[j].isspace():
                    j += 1
                    continue

                if content[j] == "[":
                    j = _consume_balanced(content, j, end, "[", "]")
                    continue

                if content[j] == "{":
                    j = _consume_balanced(content, j, end, "{", "}")
                    continue

                break

        return j

    if j < end:
        return j + 1

    return j


def _consume_text_chunk(content: str, i: int, end: int) -> int:
    """Consume a contiguous chunk considered translatable text."""

    while i < end:
        current = content[i]

        if current == "%" or current in "{}[]$&":
            break

        if current == "\\":
            if i + 1 < end and content[i + 1] == "&":
                i += 2
                continue

            inline_advance = _advance_inline_command(content, i, end)
            if inline_advance is not None:
                i = inline_advance
                continue

            break

        i += 1

    return i


def extract_translatable_segments(content: str) -> list[Segment]:
    """Extract line-oriented translatable segments from LaTeX source content."""

    segments: list[Segment] = []
    start, end = get_document_window(content)
    i = start

    while i < end:
        char = content[i]

        if char == "%":
            newline = content.find("\n", i)
            i = end if newline == -1 else newline + 1
            continue

        if char == "\\":
            inline_advance = _advance_inline_command(content, i, end)
            if inline_advance is not None or (i + 1 < end and content[i + 1] == "&"):
                chunk_start = i
                i = _consume_text_chunk(content, i, end)

                chunk = content[chunk_start:i]
                line_start = chunk_start
                for line in chunk.splitlines(keepends=True):
                    line_end = line_start + len(line)
                    if any(c.isalpha() for c in line):
                        segments.append(Segment(start=line_start, end=line_end, text=line))
                    line_start = line_end
                continue

            i = _advance_latex_command(content, i, end)
            continue

        if char in "{}[]$":
            i += 1
            continue

        if char == "&":
            i += 1
            continue

        chunk_start = i
        i = _consume_text_chunk(content, i, end)

        chunk = content[chunk_start:i]
        line_start = chunk_start
        for line in chunk.splitlines(keepends=True):
            line_end = line_start + len(line)
            if any(c.isalpha() for c in line):
                segments.append(Segment(start=line_start, end=line_end, text=line))
            line_start = line_end

    return segments


def stitch_content(base_content: str, segments: list[Segment], replacements: list[str]) -> str:
    """Rebuild full content by replacing extracted segments with new text."""

    if len(segments) != len(replacements):
        raise ValueError("Segments and replacements length mismatch.")

    built: list[str] = []
    cursor = 0
    for segment, replacement in zip(segments, replacements):
        built.append(base_content[cursor:segment.start])
        built.append(replacement)
        cursor = segment.end
    built.append(base_content[cursor:])
    return "".join(built)
