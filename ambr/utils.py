import re


def format_number(text: str) -> str:
    """Format numbers into bolded texts."""
    return re.sub(r"(\(?\d+.?\d+%?\)?)", r" **\1** ", text)  # type: ignore


def parse_html(html_string: str):
    html_string = html_string.replace("\\n", "\n")
    # replace tags with style attributes
    html_string = html_string.replace("</p>", "\n")
    html_string = html_string.replace("<strong>", "**")
    html_string = html_string.replace("</strong>", "**")

    # remove all HTML tags
    CLEANR = re.compile(r"<[^>]*>|&([a-z0-9]+|#\d{1,6}|#x[0-9a-f]{1,6});")
    html_string = re.sub(CLEANR, "", html_string)

    # remove time tags from mihoyo
    html_string = html_string.replace('t class="t_gl"', "")
    html_string = html_string.replace('t class="t_lc"', "")
    html_string = html_string.replace("/t", "")

    return html_string
