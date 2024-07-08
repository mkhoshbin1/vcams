Example C-3: Randomly Distributed Second Phase (2D)
===================================================
This example, a 2D part is created in which a second phase is randomly distributed
in a background.
This is similar to :doc:`Example A-5 <example-a5>`, but is achieved more easily
using a Boolean Mask. Also, a 3D version is demonstrated in :doc:`Example C-4 <example-c4>`.

These kinds of models are very useful.
For example, `this paper <https://doi.org/10.1016/j.msea.2012.09.046>`__ [1]_
uses a variant of this model with two materials for and a specific ratio
of the two phases for simulating the microstructure of a dual-phase steel
in the RVE framework.

First, a 2D part with a shape of 100×100 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Then, the :func:`~vcams.mask.random.random_binary_mask()` function is used
to create a Boolean mask based on the ``part`` instance.
The *true_fraction* parameter is set to 0.42, meaning that 42% of the elements will
be randomly selected by the mask::

    random_mask = random_binary_mask(part=part, true_fraction=0.42)

Afterwards, the Boolean mask is applied to the part with a value of 2.
This means that the values of the elements selected by the mask are set to 2::

    part.apply_mask(mask=random_mask, value=2)

Finally, The part is then exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_c3_random_mask_2d.py

The final model looks like :numref:`ex_c3_random_mask_2d`.
Note that elements in different sets are shown in different colors.

.. figure:: /images/ex_c3_random_mask_2d.png
   :name: ex_c3_random_mask_2d
   :align: center
   :alt: Final model of Example C-3.
         Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.

   Final model of Example C-3.
   Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.

.. [1] Ramazani, A., Mukherjee, K., Quade, H., Prahl, U., & Bleck, W. (2013).
       Correlation between 2D and 3D flow curve modelling of DP steels using
       a microstructure-based RVE approach.
       Materials Science and Engineering: A, 560, 129–139.
       `<https://doi.org/10.1016/j.msea.2012.09.046>`__