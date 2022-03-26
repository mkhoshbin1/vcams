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