Example 2: Simple Filled 3D Part
================================

In this example, a complete 3D part with a shape of 50×75×100 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

The part is then output to abaqus in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements (which happens to be the whole model),
are requested to be written to the output.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex2_simple_part_3d.py