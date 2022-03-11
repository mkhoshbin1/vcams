Example B-1: Node Sets Only
===========================
This example demonstrates how to create the
:ref:`predefined node sets <boundary-conditions-nodeset_only>`
for a part. These node sets can then be used for a variety of constraints.

See the :ref:`boundary-conditions` section for a thorough explanation of this subject.

The model created in this example is similar to :doc:`Example A-2 <example-a2>`.
A 3D part with a shape of 50×75×100 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the node sets are requested using the following statement::

    part.add_bc(bc_type='Nodeset Only',
                vertices_nodeset=True, edges_nodeset=True, faces_nodeset=True,
                explicit_nodeset=True, simple_nodeset=True)

The part is then exported to an Abaqus™ input file in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_b1_nodesets_only.py

After importing the resulting file in Abaqus™, the node sets are available in the assembly.