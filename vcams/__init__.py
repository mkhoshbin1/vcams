__author__ = 'Mohammadreza Khoshbin'
__copyright__ = 'Copyright © 2025, Mohammadreza Khoshbin.'
__credits__ = ['Mohammadreza Khoshbin']
__license__ = 'AGPLv3'
__version__ = '3.1.1'
__maintainer__ = 'Mohammadreza Khoshbin'
__email__ = 'm.khoshbin@live.com'
__status__ = 'Production'
__website__ = 'https://github.com/mkhoshbin1/vcams'
__repo__ = 'https://github.com/mkhoshbin1/vcams'
__docs__ = 'https://vcams.readthedocs.io/'
__description__ = 'A Program and Python Library for Voxel-Based Computer-Aided Modeling of Complex Structures '
__author_website__ = 'www.mkhoshbin.com'
__contact__ = __email__
__deprecated__ = False

# The following are used in the GUI:
gui_footer_notice = (f'{__copyright__}\nVCAMS is a free and open source software published '
                     f'under the GNU AGPLv3 license.\n')
# gui_footer_notice = ('VCAMS is a free and open source software published '
#                      'under the GNU AGPLv3 license.\n')
about_vcams = ('<h1>VCAMS v%s</h1>'
               '<font size="+1"><p align="justify">VCAMS (Voxel-Based Computer-Aided '
               'Modeling of Complex Structures) is a free and open source '
               'software for creating complex FEA models using voxels. It can be used '
               'and extended by anyone in accordance with the GNU AGPLv3 license.</p>'
               '<p align="justify">You are currently using the software\'s GUI, '
               'but the main library is even more powerful! You will find links to the '
               'software\'s code and documentation (including examples) '
               'in the Help menu.</p></font>'
               '<p align="center">%s</p>' % (__version__, __copyright__))
gui_name = 'VCAMS GUI'
gui_file_name = gui_name + ' v' + __version__
gui_window_title = gui_name + ' v' + __version__
# Import the modules. Although general guidelines are against polluting the namespace,
# it's done to improve usability for less experienced users.
from . import bc  # noqa: E402
from . import mask  # noqa: E402
from . import voxelpart  # noqa: E402
