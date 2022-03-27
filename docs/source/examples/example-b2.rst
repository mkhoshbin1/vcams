Example B-2: Linear Displacement BC
===================================
This example demonstrates how to apply the constraints for
a :ref:`linear displacement BC <boundary-conditions-lin-disp>`
to a part.

These constraints can then be used for applying the boundary conditions to the part.
A sample script fot Abaqus’ Python Scripting Interface is provided for clarity.

See the :ref:`boundary-conditions` section for a thorough explanation of this subject.

The model created in this example is similar to :doc:`Example A-1 <example-a1>`.
A 2D part with a shape of 50×100 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the linear displacement BC is requested using the following statement::

    part.add_bc(bc_type='Linear Displacement')

The part is then exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_b2_lindisp.py

After importing the resulting file in Abaqus™, we can define a step
and apply loading on the dummy nodes using the following Python commands::

    # Define some parameters for ease of use.
    model = mdb.models['ex_b2_lindisp']  # Make sure the name is correct.
    assembly = model.rootAssembly

    # Fix RP-0 in place.
    model.EncastreBC(name='Fixed-BC', createStepName='Initial', region=assembly.sets['RP0-NodeSet'])

    # Apply the displacement vector (1.1, 2.2) to RP-1.
    # Note that the BC is in the step named 'Step-1' and only u1 and u2 are valid displacements.
    model.DisplacementBC(name='Disp-BC', createStepName='Step-1',
        region=assembly.sets['RP1-NodeSet'],
        u1=1.1, u2=2.2)

