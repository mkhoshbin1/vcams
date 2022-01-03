"""TODO"""

from vcams.voxelpart import VoxelPart
from vcams.mask.shape import ShapeArray, Circle

# Create a part.
part = VoxelPart(size=(100, 100), base_material=1,
                 voxel_size=(0.01, 0.01),
                 name='Periodic BC 2D Part',
                 description='A square 100*100 part filled with elements with periodic BC.',
                 log_debug=True)

# Create a mask with the same shape and voxel_size as the part.
t = part.real_size / 2
shape_array = ShapeArray(dim='2D', part_shape=part.data.shape,
                         voxel_size=part.voxel_size, is_mask_calculation_lazy=True)
shape_array.add_shape(Circle, a=0.5, b=0.8, r=0.1)
shape_array.add_shape(Circle, a=0.4, b=0.2, r=0.15)
shape_array.add_shape(Circle, a=0.7, b=0.5, r=0.15)

# Apply the mask to the part.
part.apply_mask(mask=shape_array.mask, value=2)

# Apply a periodic boundary condition.
part.add_bc(bc_type='PERIODIC')

# Output the part.
part.output_abaqus_inp(file_name='periodic_bc_2d',
                       elem_type='CPE4R', dim='2D',
                       material_elem_sets='All', custom_elem_sets=True, )
