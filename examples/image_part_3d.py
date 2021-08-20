"""In this example, an empty part with a shape of 50*50*50 voxels is created.
Then, a random mask is applied and used to determine where material values must be equal to one.
Finally, the part is output to abaqus with a uniform scale of 0.02 in all directions."""

import vcams

results_path = r'C:\Users\MKhos\Desktop\Hylobates\New folder (2)'

load_pattern = r'C:\Users\MKhos\Desktop\morphosource-2021-08-08-091517\New folder\Fused_AMNH_82096_Papio_*.tif'
image_mask = mask_from_image_sequence(load_pattern=load_pattern, scale=0.5, denoise=False)
image_mask = image_mask.astype(bool)

# Create a part.
part = vcams.voxelpart.VoxelPart(size=image_mask.shape, fill_value=0,
                                 name='Image 3D Part',
                                 description='A cubic 50*50*50 part created using a random mask.',
                                 logger_path=results_path)

# Create a random mask with the same shape as part.data.


# Apply the mask to the part.
part.apply_mask(mask=image_mask, value=1)

# Output the part.
part.output_abaqus_inp(file_name='mask_part_3d', folder_path=results_path,
                       elem_type='C3D8R', dim='3D',
                       scale=(0.02, 0.02, 0.02),
                       material_elem_sets=(1,), custom_elem_sets=True)
