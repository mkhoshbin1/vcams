.. _predefined-structures:

Pre-Defined Structures
======================
This section covers the different techniques for manipulating a base model to obtain a complex structure.
Users are advised to read the :ref:`modeling-techniques` section first.

Although a general Boolean mask allows for a highly customized structure,
some processes or algorithms are so common and useful that they have been implemented
in VCAMS as part of the *mask* module.

These pre-defined structures are boolean masks that are widely used
and have been added to the library so they can be created using very little input.
This allows for a degree of standardization,
eases creation of fairly complex structures based on common patterns,
and reduces the risk of bugs.
As discussed in the :ref:`modeling-techniques` section,
the masks can then be combined in various ways and applied to a *VoxelPart* object.

Currently, the following groups of pre-defined structures can be used:

  .. toctree::
     :maxdepth: 1

     shape
     tpms
     image

.. _level-set-functions:

Level-Set Functions
-------------------

A number of these structures are modeled using level-set functions.
The main idea behind this method is that an implicit function :math:`\Phi` describes a closed curve.
:math:`\Phi(x,y,z)` can then be evaluated for each point :math:`P` in space, and:

.. math::

   \Phi(x,y,z)=
   \begin{cases}
    < 0, & \text{$P$ is inside the surface}\\
    = 0, & \text{$P$ is on the surface boundary}\\
    > 0, & \text{$P$ is outside the surface}
  \end{cases}

Many different functions can be derived for modeling simple or complex shapes, as listed above.
For more information, see the famous book by Osher and Fedkiw [1]_.

.. [1] Osher, Stanley, and Ronald Fedkiw.
       “Level set methods and dynamic implicit surfaces.”
       Applied mathematical sciences, 2003, doi:10.1007/b98879.