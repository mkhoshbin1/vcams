Example A-4: Manual Manipulation of the Structure (Whole Array)
===============================================================
This example illustrated manual modification of the *data* array of a VoxelPart instance.
Unlike :doc:`Example A-3 <example-a3>`, here we change the entire *data* array.

First, a complete 2D part with a shape of 5×5 voxels is created
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

   random_array = rng.integers(low=1, high=3, size=part.size,
                            dtype=part.data.dtype, endpoint=True)
   part.data = random_array

Finally, The part is exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_a4_manual_manipulation_whole.py

The final model looks like :numref:`ex_a4_manual_manipulation_whole`.
Note that elements in different sets are shown in different colors.
Also, because of the random nature of this example, each model will be different.

.. figure:: /images/ex_a4_manual_manipulation_whole.png
   :name: ex_a4_manual_manipulation_whole
   :align: center
   :alt: Final model of Example A-4.
         Element sets corresponding to MAT-1, MAT-2 and MAT-3 are shown in green, beige, and red, respectively.

   Final model of Example A-4.
   Element sets corresponding to MAT-1, MAT-2 and MAT-3 are shown in green, beige, and red, respectively.