"""Various helper functions."""

from pathlib import Path


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
    elif not (name.isascii() and name.isprintable()):
        # Source: https://stackoverflow.com/a/51141941/7180705.
        return False
    else:
        return True


def return_default_results_path(part_name=None):
    """Return a suitable path in the user's Desktop
       for storing the intermediate and final results of the program.

    Args:
        part_name (str): Name of the part which is to be output
                         which must be valid according to #TODO.
                         If set to :py:obj:`None`, the folder will simply be named 'results'.
                         Defaults to :py:obj:`None`.

    Returns:
        A path object containing the full path of a suitable folder in the users Desktop.
    """

    parts = ['Desktop', 'VCAMS Working Directory']
    # Validate part_name.
    if part_name is None:
        pass  # No subfolder.
    elif is_name_valid(part_name):
        parts.append(part_name)
    else:
        raise ValueError('part_name is not valid.')

    return Path.home().joinpath(*parts)
