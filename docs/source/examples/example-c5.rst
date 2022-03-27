Example C-5: Gyroid TPMS
========================
In this example, a part is created based on the Gyroid
`TPMS <https://en.wikipedia.org/wiki/Triply_periodic_minimal_surface>`__,
and is then exported.

Normally, this operation would be complicated, but the :mod:`~vcams.mask.tpms` module
has a number of classes that define some of the more popular TPMS functions.
For an explanation of the TPMS predefined structures, refer to :ref:`predefined-tpms`.

First, a 3D part with a shape of 50×50×50 voxels is created
with a base material of 0 (empty space) and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Then a Boolean mask is created based on the voxel part
using the :class:`~vcams.mask.tpms.TpmsSchwarzG` class.
Unit cell length (*l*) is set to half of the parts real size
and the constant (*c*) is set to zero::

    t = part.real_size[0] / 2
    tpms_mask = mask_from_function(part=part, func=TpmsSchwarzG, l=t, c=0)

Afterwards, the Boolean mask is applied to the part with a value of 1.
This means that the values of the elements selected by the mask are set to 1,
making them the only non-empty elements in the model::

    part.apply_mask(mask=tpms_mask, value=1)

Finally, the part is then exported to an Abaqus™ input file in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_c5_tpms_gyroid.py

The final model looks like :numref:`ex_c5_tpms_gyroid`.
Note that the stepping visible in the part is due to the low resolution of the model.
A bigger model will result in a better shape.

.. figure:: /images/ex_c5_tpms_gyroid.png
   :name: ex_c5_tpms_gyroid
   :align: center
   :alt: A part created based on the Gyroid TPMS.

   A part created based on the Gyroid TPMS.