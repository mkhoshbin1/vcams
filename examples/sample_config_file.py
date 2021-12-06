"""In this example, a part is created based on the options specified in a configuration file."""

import vcams

# Create a part.
part = vcams.voxelpart.from_config_file(file_path=r'D:\Repositories\vcams\examples\sample_config_file.vcams')
