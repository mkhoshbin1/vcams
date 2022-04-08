.. _gui:

The Graphical User Interface
============================
VCAMS is a python library for creating complex models,
but it also comes with *VCAMS GUI* which a graphical user interface (GUI)
offering part of the libraries functionality in a simple and convenient manner.
It also allows the parameters to be exported to a configuration file,
and imported later for modification or re-creation of the models.

The GUI has is shipped as a single portable executable (*.exe* file)
which contains the library and all of the dependencies.
It is currently compiled only for Microsoft Windows,
but can be easily built from the source code on most platforms.

It should be noted that the GUI only offers *some* of the library's functionality.
Extremely complex models still need the scripting interface.

The following sections describe the different parts of the GUI.

Structure of the GUI
--------------------
The GUI consists of three main sections which are illustrated in :numref:`gui_0`.
They are:

- **The Menu Bar** contains a number of menus which allow the user fast access
  to the import/export and model creation functionalities and also software help.
- **The Page Selection Area** contains *tabs* similar to those found in a binder notebook.
  Each page has a purpose and asks for the parameters needed for that purpose.
  The pages are in a logical order and must be filled in that order.
  They will be described in the following sections.
- **Page Contents**: After a page is opened, its contents are shown.
  Some of the parameters have default values and some fields will
  depend on other parameters.

.. figure:: /images/gui_0.png
   :name: gui_0
   :align: center
   :alt: Different sections of the VCAMS graphical user interface (GUI).

   Different sections of the VCAMS graphical user interface (GUI).

The *Welcome* Page
------------------
The welcome page simply shows a welcome screen and some information about the VCAMS software.
It does not contain any model-related parameters or information.

.. figure:: /images/gui_1.png
   :name: gui_1
   :align: center
   :alt: The Welcome Page of the VCAMS graphical user interface (GUI).

   The Welcome Page of the VCAMS graphical user interface (GUI).


The *Basic Model Information* Page
----------------------------------
This page (:numref:`gui_2`) asks for the information used for creating the base part.
These parameters are used to create a :class:`VoxelPart <vcams.voxelpart.VoxelPart.__init__>` object
which is then manipulated and exported in the next sections.

.. figure:: /images/gui_2.png
   :name: gui_2
   :align: center
   :alt: The Basic Model Information Page of the VCAMS graphical user interface (GUI).

   The Basic Model Information Page of the VCAMS graphical user interface (GUI).

The items numbered in :numref:`gui_2` are as follows:

1. **Part Name** is used in a variety of places, including when exporting the part.
   It must be valid according to the documentation for the :func:`vcams.helper.is_name_valid` function.
   The default value is *"unnamed"*.
2. **Modeling Space** is the dimensionality of the output part which can be 2D or 3D.
   Some of the other features, such as modeling techniques, depend on this parameter.
3. **Number of Voxels** is an integer which determines the number of voxel elements.
   The third field will be disabled in the 2D mode.
4. **Voxel Size** is the actual size of a single voxel in each direction.
   The third field will be disabled in the 2D mode.
5. **Part Size** is the actual size of the resulting part if it was filled with elements.
   It is be automatically calculated by multiplying *Number of Voxels* and *Voxel Size*.
6. **Max Number of Materials** is an important parameter determining the number of
   *material codes* available for modeling. It is described in detail in the :ref:`materials` section.
   The default value is usually enough for models created using the GUI.
7. **Model Size** shows the number of elements in the model and the amount of memory that is needed.
   It is be automatically based on *Number of Voxels* and *Max Number of Materials*.
8. **Base Material** is the *material code* assigned to all elements before any manipulation takes place.
   Users must make sure it is within the range specified by the *Max Number of Materials* parameter.
9. **Part Description** is a short description of the part which is used in a variety of places,
   including when exporting the part.
10. **Working Directory** is the path to a folder where the final results, temporary file,
    and log files will be stored.
    By default, it is set to a folder in the current user's Desktop and the folder's name
    is based on *Part Name*. It can also be changed using the *Select* button.
11. **Debug Log** determines if debug information should be written to the program logs.

The *Model Manipulations* Page
------------------------------

The *Boundary Conditions* Page
------------------------------

.. _gui-output:

The *Output* Page
-----------------
asdf



The *Run* Page
--------------


The Menu Bar
------------

