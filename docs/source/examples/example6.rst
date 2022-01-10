Example 6: Random 3D Model
==========================

This example, a 3D part is created with random dispersion of three elements.
This can be achieved by combining :doc:`Example 2 <example2>` and :doc:`Example 5 <example5>`.
In fact, the code for creating a random part was based on the part's properties
and we don't need to change it for this model.

These kinds of models are very useful.
For example, `this paper <https://doi.org/10.1016/j.msea.2012.09.046>`__ [1]_
uses a variant of this model with two materials for and a specific ratio
of the two phases for simulating the microstructure of a dual-phase steel
in the RVE framework.

First, a complete 3D part with a shape of 50×75×100 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the an array of random integers between 1 and 3 is created.
To do this, the random module of NumPy must be imported::

   from numpy import random

The random number generator can then be constructed::

   rng = random.default_rng()

With the random number generator prepared, we can create an array of random numbers.
We must specify the size, highest and lowest numbers, and the *dtype* of the random array.
These can be extracted from the part's *data* array.
We will then assign the created array to part.data, thus replacing its previous contents::

   random_array = rng.integers(low=1, high=3, size=part.data.shape,
                            dtype=part.data.dtype, endpoint=True)
   part.data = random_array

Finally, The part is output to abaqus in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements are requested to be written to the output.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex6_random_3d_part.py

The final model looks like :numref:`ex6_random_3d_part`.
Note that elements in different sets are shown in different colors.
Also, because of the random nature of this example, each model will be different.

.. figure:: /images/ex6_random_3d_part.png
   :name: ex6_random_3d_part
   :align: center
   :alt: Final model of Example 6.
         Element sets corresponding to MAT-1, MAT-2 and MAT-3 are shown in green, beige, and red, respectively.

   Final model of Example 6.
   Element sets corresponding to MAT-1, MAT-2 and MAT-3 are shown in green, beige, and red, respectively.

.. [1] Ramazani, A., Mukherjee, K., Quade, H., Prahl, U., & Bleck, W. (2013).
       Correlation between 2D and 3D flow curve modelling of DP steels using
       a microstructure-based RVE approach.
       Materials Science and Engineering: A, 560, 129–139.
       `<https://doi.org/10.1016/j.msea.2012.09.046>`__