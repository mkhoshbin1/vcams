"""Various helper functions."""


def is_name_valid(name):
    """ Check whether a string represents a valid name.
    Abaqus (TM) has many rules for names (labels) in the input files.
    Here, The most strict combination is implemented here to ensure that
    a name is suitable for all purposes.

    This means that a name:
      + Must be 1-38 characters. This is because some object names
        in the abaqus scripting interface have a 38-character limit
        for their names.
      + May contain whitespace (If enclosed by whitespace).
      + Must start with a letter.
      + Must no begin or end with an underscore.
      + Must no include the following characters: $&*~!()[]{}|;'`",.?/\
      + Must not contains periods. This also means that any file names
        cannot contain any extensions. They will be added automatically.
      + Must be ASCII-compatible. This is checked by attempting str.decode('ascii')
        and checking for :py:obj:`UnicodeDecodeError`.

    For more information, refer to:
      + "Labels" under "Input Syntax Rules" of the Abaqus Analysis User's Manual.
      + The documentation for the InvalidNameError object under
        "Standard Abaqus Scripting Interface exceptions" of
        Abaqus Scripting User's Manual.

    Args:
        name (str): The string to be checked.

    Returns:
        bool: :py:obj:`True` for a valid name.
    """

    special_chars = "$&*~!()[]{}|;\'`\",.?/\\"
    if not isinstance(name, str):
        return False
    elif len(name) < 1:
        return False
    elif len(name) > 38:
        return False
    elif not name[0].isalpha():
        return False
    elif name.endswith('_'):  # The beginning is checked above.
        return False
    elif any((n in special_chars) for n in name):
        return False
    elif not(name.isascii() and name.isprintable()):
        # Source: https://stackoverflow.com/a/51141941/7180705.
        return False
    else:
        return True
