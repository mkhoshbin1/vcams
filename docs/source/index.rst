VCAMS: Voxel-Based Computer-Aided Modeling of Complex Structures
================================================================

.. _introduction:

Introduction
------------
VCAMS (Voxel-Based Computer-Aided Modeling of Complex Structures)
is a free and open source software for creating complex FEA models using voxels.

This software allows for accurate, fast, and reproducible modelling
and can be used and extended by anyone in accordance with the GNU AGPLv3 license.

It's main features are:

+ **Powerful Library**: The VCAMS library is simple but powerful, allowing for easy scripting
  which makes the results highly reproducible. Also, the scripts can be archived and shared with others.
+ **Simple GUI**: The *VCAMS GUI* is a simple but elegant graphical user interface that
  allows for easy creation of some of the more widely used structures.
+ **Fast**: VCAMS is very fast. It can create a model consisting of one million elements in less than a second!
+ **Thorough Documentation**: There are in-depth articles about all aspects of VCAMS in the online documentation.
+ **Free and Open Source**: VCAMS and its source code are provided free of charge under the GNU AGPLv3 license.
  You can download the source code and the executables on the project's GitHub page.

How it Works
------------
The software revolves around a main class named *VoxelPart* which defines a structure consisting of
a number of rectangular or cuboid elements.
This *VoxelPart* object can then be manipulated using a variety of methods to achieve a complex structure.
Afterwards, the user can define custom element and node sets and  boundary conditions for the object.
And finally, the object is exported to an Abaqus™ input file.

The VCAMS Library
-----------------
The main part of the software is its powerful library which is :ref:`very easy to install <installation_library>`
and has a complete :ref:`reference guide <api-reference>`.
It also comes with a large number of :ref:`example problems <examples>`.

The Graphical User Interface
----------------------------
The graphical user interface (GUI) offers part of the library's functionality
in a simple and convenient manner.
It also allows the model parameters to be exported to a configuration file,
and imported later for modification or re-creation of the models.

You can find installation instructions :ref:`here <installation_gui>`.
The various parts of the GUI are documented in the :ref:`gui` section,
and some :ref:`example problems <examples>` are also provided.


.. toctree::
   :caption: Documentation Contents:
   :maxdepth: 1

   installation
   graphical-user-interface
   modeling-concepts/index.rst
   api-reference/index.rst
   examples/index.rst


.. toctree::
   :hidden:

   LICENSE