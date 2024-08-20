import os
import sys

import pyinstaller_versionfile

sys.path.append(os.path.split(os.getcwd())[0])
from vcams import (__version__ as version,
                   __author__ as author,
                   __copyright__ as legal_copyright,
                   __description__ as description,
                   gui_name, gui_file_name)

pyinstaller_versionfile.create_versionfile(
    output_file='versionfile.txt',
    version=version,
    company_name=author,
    file_description=description,
    internal_name=gui_file_name,
    legal_copyright=legal_copyright,
    original_filename=(gui_file_name + '.exe'),
    product_name=gui_name
)

print(gui_file_name)
