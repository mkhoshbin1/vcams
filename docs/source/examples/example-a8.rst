Example A-8: Custom Element and Node Sets
=========================================
This example demonstrates how to create custom element and node sets.
These can then be used for a variety of purposes
and the fact that they are named means that they can be easily used
in Abaqus’ Python Scripting Interface.
See the :ref:`element-node-sets` section for a thorough explanation of this subject.

The model created in this example is similar to :doc:`Example A-1 <example-a1>`.
A 2D part with a shape of 50×100 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, a node set is added to the *part* object using
the :meth:`~.voxelpart.VoxelPart.add_node_set` method.
It should be noted that the *ids* argument need not be sorted.
The statement is::

    part.add_node_set(name='custom node set', ids=(0, 10, 450, 112, 250))

Also, a custom element set is added using
the :meth:`~.voxelpart.VoxelPart.add_custom_elem_set` method.
The parameters are similar to the previous statement
and here, it is demonstrated that the *ids* argument can be
an iterable such as ``range(10, 151)`` which is the same as the array ``(10, 11,..., 150)``.
The statement is::

    part.add_custom_elem_set(name='custom node set', ids=range(10, 151))

Finally, the part is exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.
Also, that *custom_elem_sets* argument is set to True so the custom element sets are exported.
However, this is not necessary because it defaults to True.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_a8_custom_sets.py