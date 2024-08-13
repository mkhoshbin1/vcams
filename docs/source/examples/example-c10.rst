Example C-10: Dispersion of a Specified Number of Shapes
========================================================
This example demonstrates the use of the :class:`~vcams.mask.shape_dispersion.ShapeDispersionArray` class
for creating a Boolean mask which is then used to manipulate the part.
This example deals with the case when we want to disperse a specific number of shapes.
:doc:`Example C-11 <example-c11>` deals with creating and dispersing shapes based on volume fraction.

A :class:`~vcams.mask.shape_dispersion.ShapeDispersionArray` instance contains
a number of shape requests which are used to create and disperse shapes in it.
Using this class can be quite complicated and computationally expensive
An example is demonstrated in the 2D space.

First, a 2D part with a shape of 200×200 voxels is created
with a base material of 1 and a voxel size of 0.005 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes::

    part = VoxelPart(size=(200, 200), base_material=1,
                     voxel_size=(0.005, 0.005),
                     name='Ex C-10 Dispersion of a Specified Number of Shapes',
                     description='A 2D square 200*200 part created with '
                                 'a specified number of shapes randomly dispersed in it.',
                     log_debug=True)

At this point, we will define a few parameters that will be used in the future.
The first, is the number of boundary pixels and subsequently, boundary length::

    num_bound_pixels = 2
    bound_length = num_bound_pixels * part.voxel_size[0]

And the second one is the minimum acceptable value for radius *r* that we can accept::

    min_valid_r = 4 * part.voxel_size[0]

Now we can define a 2D *ShapeDispersionArray* in the 2D space based on the *VoxelPart* instance::

    shape_disp_array_obj = ShapeDispersionArray(dim='2D', part=part,
                                                num_bound_pixels=num_bound_pixels,
                                                short_msg=True)

Then, two shape requests are added. The first is a request
for 10 instances of type :class:`~vcams.mask.shape.Circle`.
This is a 2D circle which requires the following:

  - 10 values for the radius.
    Although they are random, we would like a normal distribution for them
    and since radius must be positive, we will use a
    `truncated normal distribution <https://en.wikipedia.org/wiki/Truncated_normal_distribution>`_.
    To do so, we create an instance
    of :class:`~vcams.mask.shape_dispersion.TruncatedNormalDistributionDispersion`.
    Number of values is set to 10, and mean and standard deviation are set to 0.06 and 0.03, respectively.
    *bound_a* is set to *min_valid_r* which ensures that values are greater than *min_valid_r*.
  - A random value for the x coordinate.
    An instance of :class:`~vcams.mask.shape_dispersion.RandomDispersion`
    is created and used. The minimum value is 0,
    and the maximum value is the part's size in the x direction.
    A boundary is defined which is equal to the sum of the maximum radius
    for all requested circles and the *bound_length* parameter.
    This ensures that no circle is placed outside the *ShapeDispersionArray* instance.
  - A random value for the y coordinate. See above.

We can now add a shape request for the circles::

    num_circle = 10
    circle_r = TruncatedNormalDistributionDispersion(num_values=num_circle,
                                                     target_mean=0.06, target_std=0.03, bound_a=min_valid_r)
    circle_xc = RandomDispersion(0, part.real_size[0], max(circle_r) + bound_length)
    circle_yc = RandomDispersion(0, part.real_size[1], max(circle_r) + bound_length)
    shape_disp_array_obj.add_shape_request(num_shapes=num_circle, cls=Circle,
                                           xc=circle_xc, yc=circle_yc, r=circle_r, br=bound_length)

The second shape request is for 10 instances of type :class:`~vcams.mask.shape.Ellipse`.
This is done similar to the previous request::

    num_ellipse = 10
    ellipse_a = TruncatedNormalDistributionDispersion(num_values=num_ellipse,
                                                      target_mean=0.06, target_std=0.03, bound_a=min_valid_r)
    ellipse_aspect_ratio = TruncatedNormalDistributionDispersion(num_values=num_ellipse,
                                                                 target_mean=0.75, target_std=0.75, bound_a=0.1)
    ellipse_xc = RandomDispersion(0, part.real_size[0])
    ellipse_yc = RandomDispersion(0, part.real_size[1])
    ellipse_alpha = RandomDispersion(low=0, high=360)
    shape_disp_array_obj.add_shape_request(num_shapes=num_ellipse, cls=EllipseFromAspectRatio,
                                           xc=ellipse_xc, yc=ellipse_yc, alpha=ellipse_alpha,
                                           a=ellipse_a, aspect_ratio=ellipse_aspect_ratio,
                                           ba=bound_length, bb=bound_length)

Now we can disperse the shapes in the *ShapeDispersionArray* instance.
Dispersion may or may not be successful based on the requests
and the specified number of trials and attempts.
See :meth:`~vcams.mask.shape_dispersion.ShapeDispersionArray.disperse_shapes`
for a list of parameters. The simplest form of the dispersion command is::

    shape_disp_array_obj.disperse_shapes()

If dispersion is successful, we can use resulting mask to manipulate the part.
When using the *ShapeDispersionArray* class we don't need to calculate a mask,
we just ask it to give us its mask using the *ShapeDispersionArray*'s
*mask* property which will always be up-to-date.
This Boolean mask is applied to the part with a value of 2.
This means that the values of the elements selected by the mask are set to 2::

    part.apply_mask(mask=shape_array_obj.mask, value=2)

Finally, The part is exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_c10_shape_dispersion_number.py

The final model looks like :numref:`ex_c10_shape_dispersion_number`.
Note that elements in different sets are shown in different colors.

.. figure:: /images/ex_c10_shape_dispersion_number.png
   :name: ex_c10_shape_dispersion_number
   :align: center
   :alt: Final model of Example C-10.
         Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.

   Final model of Example C-10.
   Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.