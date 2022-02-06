.. _boundary-conditions:

Boundary Conditions
===================
This section covers the different boundary conditions (BCs) implemented in VCAMS.

Although the goal of the software is creation of structures,
the usefulness of creating BCs along with the model
and the complexity of various BCs calls for implementation of various BCs in VCAMS.
Definition of BCs for a part is not mandatory, and their accuracy/correctness is not guaranteed,
so users are advised to check the theory, created BCs, and analysis results for possible errors.

Currently, three possible options are available regarding BCs:

  + No boundary conditions
  + Node Sets Only
  + Linear Displacement Boundary Conditions
  + Periodic Boundary Conditions



No Boundary Conditions
----------------------
For this option, The user doesn't need to do anything.
The default state of a VoxelPart instance contains an empty BC definition.

In the GUI, the TODO option must be selected as shown in FigXXX TODO.
This option is selected by default.

Node Sets Only
--------------
This option creates node sets from the faces, edges, and vertices as shown in :numref:`bc-nodesets`.
These sets are exclusive, meaning for example that a face does not include the edges or vertices connected to it.
Optionally, the user can create a set of *simplified* sets which only covers faces.
Each of the *explicit* or *simplified* node set configurations
are useful for a different kind of boundary conditions.

.. figure:: /images/bc-nodesets.png
   :name: bc-nodesets
   :align: center
   :alt: Illustration of the Naming convention for faces, edges, and vertices in a cubic model.

   Naming convention for faces, edges, and vertices in a cubic model.

Each square or cube has a number of vertices, which are named as shown in :numref:`bc-nodesets`.
Edges are numbered based on the vertices, e.g., E34 connects V3 and V4
with the numbers written in increasing order.
In a cube, there are six faces. For face F\ *ij*, the number *i* refers to the direction,
and *j* is the number of the face.

The program also uses a number of *Dummy Nodes*, which are known in Abaqus™ as *Reference Points* and
are used for applying the actual BCs. These and are placed along the diagonal and offset from the end points.
D\ :subscript:`0` is always present and must be fixed in space to prevent rigid body motion
and one or more D\ :subscript:`i` are used in equations that implement the desired BC.


Uniform Displacement Boundary Condition
---------------------------------------
In this boundary condition, the faces or edges of the part undergo a uniform displacement
such that the face or edge retains its shape as a line or a plane.
Currently, the formulation is implemented only for normal loads.
Based on the notation in :numref:`bc-nodesets` and for 2D models,

As shown in FigTODO, Two dummy nodes are

shape + numbers + movements
formula




