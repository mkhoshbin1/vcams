.. _modeling-techniques:

Modeling Techniques
===================
This section covers the different techniques for manipulating
a base model to obtain a complex structure.
But first, we need to define the term *Boolean mask*.

.. _boolean-masks:

Boolean Masks
-------------
A Boolean mask is an array of Boolean values (True/False) with the same shape as another array
and is used for many operation is programming.
For example, it can be used to select or highlight part of an image.
In NumPy, a Boolean mask can be used for selecting some elements
which can then be used for manipulate the array.

VCAMS offers a special function for applying a Boolean mask to a VoxelPart instance.
The :func:`~vcams.mask.function.mask_from_function` function
takes a Boolean mask and a *value* parameter and,
sets the elements selected by the mask to the *value* parameter.

Use of Boolean masks allows for creating highly complex structure.
Refer to the :ref:`examples` section for a large number of different use cases.

Model Manipulation
------------------
Upon creation, one material code is assigned to all elements in the model.
*Model Manipulation* refers to the methods using which
the part's *data* array is changed to obtain the desired model.
There are three methods for manipulating a model:

+ Manual changing of the values in the *data* array.
  This can be as simple as changing the value of individual elements,
  or as complex as the user desires.
  The *data* array is a NumPy array and any valid change
  that does not change its *dtype* is permitted.
  Realistically, this method has limited use because the other methods
  allow for modification is a larger scale.
  Examples :doc:`A-3 </examples/example-a3>`, :doc:`A-4 </examples/example-a4>`,
  and :doc:`A-5 </examples/example-a5>` show this method in practice:

+ Use of a custom boolean mask for manipulating a model.
  This is a simple and effective method when the mask is created elsewhere
  and is demonstrated in Examples :doc:`A-6 </examples/example-a6>`
  and :doc:`A-7 </examples/example-a7>`.
  This is the basis for the next two methods.

+ Using a boolean mask created from a level-set function.
  The level-set function is passed
  to the :func:`~vcams.mask.function.mask_from_function` function
  and must comply with its specifications.
  This method offers extreme control over the final structure
  and Examples :doc:`C-1 </examples/example-c1>`
  and :doc:`C-2 </examples/example-c2>` show this method in practice.

+ Use of a pre-defined boolean mask created using the facilities provided by the library.
  This method is identical to the previous method, and
  the only difference is that the mask is obtained from a predefined function or class
  that creates a common complex structure.
  The function and classes and their examples are covered
  in the :ref:`predefined-structures` section.