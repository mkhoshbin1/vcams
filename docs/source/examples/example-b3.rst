Example B-3: Periodic BC
========================
This example demonstrates how to apply the constraints for
a :ref:`linear displacement BC <boundary-conditions-pbc>`
to a part.

These constraints can then be used for applying the boundary conditions to the part.
A sample script fot Abaqus’ Python Scripting Interface is provided for clarity.

See the :ref:`boundary-conditions` section for a thorough explanation of this subject.

The model created in this example is similar to :doc:`Example A-1 <example-a1>`.
A 2D part with a shape of 50×100 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the periodic BC is requested using the following statement::

    part.add_bc(bc_type='Periodic')

The part is then exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_b3_pbc.py

After importing the resulting file in Abaqus™, we must do the following:

#. Define a step. Here we assume it is named ``'Step-1'``.
#. Fix vertex :math:`V_1`, which is the node set named ``'Vertex1-NodeSet'``.
#. Apply the displacement tensor :math:`\mathbf{U}` to the part.

   .. math::
      \mathbf{U} =
      \begin{bmatrix}
        U_{11} & U_{12} \\
        U_{21} & U_{22}
      \end{bmatrix}
      =
      \begin{bmatrix}
        1.1 & 0.6 \\
        0.6 & 2.2
      \end{bmatrix}

   To do this, and according to Eq. :eq:`bc-eq-pbc-loading3`,
   we must apply the following displacement vectors to each dummy node:

   .. math::
      \begin{cases}
        \begin{alignat}{3}
          \vec{u}^{D_1} = (&U_{11} - 1&,&\ U_{12}    &)& = (0.1, 0.6)\\
          \vec{u}^{D_2} = (&U_{12}    &,&\ U_{22} - 1&)& = (0.6, 1.2)
        \end{alignat}
      \end{cases}

Steps 2 and 3 can be done using the following Python commands::

    # Define some parameters for ease of use.
    model = mdb.models['ex_b3_pbc']  # Make sure the name is correct.
    assembly = model.rootAssembly

    # Fix RP-0 in place.
    model.EncastreBC(name='Fixed-BC', createStepName='Initial', region=assembly.sets['Vertex1-NodeSet'])

    # Apply the displacements.
    # Note that they are added in the step named 'Step-1',
    # and only u1 and u2 are valid displacements.

    # Apply the displacement vector (0.1, 0.6) to RP-1.
    model.DisplacementBC(name='Disp-BC-1', createStepName='Step-1',
        region=assembly.sets['RP1-NodeSet'],
        u1=0.1, u2=0.6)

    # Apply the displacement vector (0.6, 1.2) to RP-2.
    model.DisplacementBC(name='Disp-BC-2', createStepName='Step-1',
        region=assembly.sets['RP2-NodeSet'],
        u1=0.6, u2=1.2)

