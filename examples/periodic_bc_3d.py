"""TODO"""

from vcams.voxelpart import VoxelPart
from vcams.mask.shape import ShapeArray, Sphere

# Create a part.
part = VoxelPart(size=(50, 50, 50), base_material=1,
                 voxel_size=(0.02, 0.02, 0.02),
                 name='Periodic BC 3D Part',
                 description='A cubic 50*50*50 part filled with elements with periodic BC.',
                 log_debug=True)

# Create a mask with the same shape and voxel_size as the part.
t = part.real_size / 2
shape_array = ShapeArray(dim='3D', part_shape=part.data.shape,
                         voxel_size=part.voxel_size, is_mask_calculation_lazy=True)
shape_array.add_shape(Sphere, a=0.5, b=0.8, c=0.4, r=0.1)
shape_array.add_shape(Sphere, a=0.4, b=0.2, c=0.7, r=0.15)
shape_array.add_shape(Sphere, a=0.7, b=0.5, c=0.2, r=0.15)

# Apply the mask to the part.
part.apply_mask(mask=shape_array.mask, value=2)

# Apply a periodic boundary condition.
part.add_bc(bc_type='PERIODIC')

# Output the part.
part.output_abaqus_inp(file_name='periodic_bc_3d',
                       elem_type='C3D8R', dim='3D',
                       material_elem_sets='All', custom_elem_sets=True)
