.. _modeling-techniques:

Modeling Techniques
===================
This section covers the different techniques for manipulating a base model to obtain a complex structure.

Model Manipulation
------------------
Upon creation, one material code is assigned to all elements in the model.
*Model Manipulation* refers to the methods using which the part's *data* array is changed to obtain the desired model.
There are three methods for manipulating a model:

+ Manual changing of the values in the *data* array.
  This can be as simple as changing the value of individual elements, or as complex as the user desires.
  The *data* array is a NumPy array and any valid change that does not change its *dtype* is permitted.
  The following examples show this method in practice:

  - :doc:`/examples/example-a3`
  - :doc:`/examples/example-a4`
  - :doc:`/examples/example-a5`

+ Use of a custom boolean mask for manipulating a model.
  This is a simple and effective method which is covered in TODO.

  - :doc:`/examples/example-a6`
  - :doc:`/examples/example-a7`

+ Use of a pre-defined boolean mask created using the facilities provided by the library.
  This method is identical to the previous, more general, method.
  The only difference is that the mask is obtained from a predefined function or class
  that creates a common complex structure.
  The function and classes and their examples are covered in TODO.

.. _boolean-masks:

Boolean Masks
-------------
A Boolean mask is an array of Boolean values (True/False) with the same shape as another array
and is used for many operation is programming.
For example, it can be used to select or highlight part of an image.
In NumPy, a Boolean mask can be used for selecting some elements
which can then be used for manipulate the array.

VCAMS offers a special function for applying a Boolean mask to a VoxelPart instance.
The TODO function takes a Boolean mask and a *value* parameter and,
sets the elements selected by the mask to the *value* parameter.

Use of Boolean masks allows for creating highly complex structure.
Some examples are shown in TODO.

Pre-Defined Boolean Masks
-------------------------
Although a general Boolean mask allows for a highly customized structure,
some processes or algorithms are so common and useful that they have been implemented
in VCAMS as part of the masks (TODO) module.

Use of these pre-defined masks allows for easy creation of fairly complex structures
based on tested common patterns. These are described in TODO.