"""Functions used for creating boundary conditions.
The BC and it's information is stored in
the :class:`~vcams.voxelpart.VoxelPart` object and written to the output with it.

See the :ref:`boundary-conditions` section for a complete explanation
of the basic concepts.
"""

import logging
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Union, Iterable

from numpy import ravel_multi_index, array, arange, meshgrid, concatenate, isin, count_nonzero
from numpy.typing import NDArray

from vcams.helper import validate_materials_to_be_output

logger = logging.getLogger(__name__)


class BcNotApplicableError(Exception):
    pass


@dataclass
class TieConstraint:
    """Class for tying a master set (single node) and a slave set (multiple nodes).
    The tie is defined using the ``*EQUATION`` keyword with the coefficients set to +1 and -1."""
    dof: int
    """Degree of freedom used in the constraint."""
    rp_set_name: str
    """Name of the set containing only a single master node (AKA dummy node/reference point)."""
    slave_set_name: str
    """Name of the set containing the slave nodes."""

    def __repr__(self):
        return (f'*Equation\n2\n'
                f'"{self.slave_set_name}", {self.dof}, -1.\n'
                f'"{self.rp_set_name}", {self.dof}, +1.\n')


@dataclass
class BasePbcConstraint(ABC):
    """Abstract base class for defining a constraint for a Periodic Boundary Condition (PBC).

    Subclasses are created for 2D and 3D spaces and for faces, edges, and vertices.
    This dataclass simply defines the required parameters and establishes a common interface.
    tying a master set (single node) and a slave set (multiple nodes).
    The tie is defined using the ``*EQUATION`` keyword with the coefficients set to +1 and -1.

    Subclasses must redefine the ``__repr__()`` method to output
    a complete statement based on the ``*EQUATION`` keyword
    of *Abaqus Keywords Reference Guide*.
    """
    part_instance_name: str
    """Name of the part instance that the nodes belong to."""
    dummy_names: tuple[str]
    """Name of the set containing the dummy node, or a tuple of the names."""
    dummy_coeffs: tuple[float]
    """Value of the coefficient for the dummy node, or a tuple of the coefficients."""
    node1_id: int
    """ID of the first node used for the equation."""
    node2_id: int
    """ID of the second node used for the equation."""

    @abstractmethod
    def __repr__(self):
        pass


@dataclass
class Pbc3DFaceConstraint(BasePbcConstraint):
    """Class for defining the following 3D PBC constraint
    between a dummy nodes and two corresponding nodes on the faces of a cuboid:

    .. math::
       u_i^{F_{j2}} - u_i^{F_{j1}} + C_j u_i^{D_j} = 0

    where :math:`F_{j1}` and :math:`F_{j2}` are the two faces in the :math:`j` direction,
    :math:`D_j` and :math:`C_j` are the dummy node and the coefficient used for that direction,
    and the equation is written for all DOFs, i.e. :math:`i=1,2,3`
    Note that :math:`C_j` is typically supplied as a negative value.

    The parameters for creating an object are similar to :class:`BasePbcConstraint`,
    except for the meaning of *dummy_names* and *dummy_coeffs* which are:
    """
    dummy_names: str
    """Name of the set containing the dummy node :math:`D_j`."""
    dummy_coeffs: float
    """Value of the coefficient :math:`C_j`."""

    def __repr__(self):
        return ''.join((f'*Equation\n3\n'
                        f'"{self.part_instance_name}".{self.node2_id + 1}, {dof}, 1.\n'
                        f'"{self.part_instance_name}".{self.node1_id + 1}, {dof}, -1.\n'
                        f'"{self.dummy_names}", {dof}, {self.dummy_coeffs}\n')
                       for dof in (1, 2, 3))


@dataclass
class Pbc3DEdgeConstraint(BasePbcConstraint):
    """Class for defining the following 3D PBC constraint
    between a dummy nodes and two corresponding nodes on the edges of a cuboid:

    .. math::
       u_i^{E2} - u_i^{E1} + C_1 u_i^{D_1} + C_2 u_i^{D_2} = 0

    where :math:`E1` and :math:`E2` are two compatible edges,
    :math:`D_1` and :math:`D_2` are the dummy nodes used for the edges,
    :math:`C_1` and :math:`C_2` are the coefficients used those dummy nodes,
    and the equation is written for all DOFs, i.e. :math:`i=1,2,3`.

    The above equation is a generalization of the edge equations
    in Eq. :eq:`bc-eq-pbc`. Compatible edges, dummy nodes,
    and the value of coefficients must be taken from Eq. :eq:`bc-eq-pbc`.

    The parameters for creating an object are similar to :class:`BasePbcConstraint`.
    """

    def __repr__(self):
        return ''.join((f'*Equation\n4\n'
                        f'"{self.part_instance_name}".{self.node2_id + 1}, {dof}, 1.\n'
                        f'"{self.part_instance_name}".{self.node1_id + 1}, {dof}, -1.\n'
                        f'"{self.dummy_names[0]}", {dof}, {self.dummy_coeffs[0]}\n'
                        f'"{self.dummy_names[1]}", {dof}, {self.dummy_coeffs[1]}\n')
                       for dof in (1, 2, 3))


class Pbc3DVertexConstraint(BasePbcConstraint):
    """Class for defining the following 3D PBC constraint
    between a dummy nodes and two nodes on vertices of a cuboid:

    .. math::
       u_i^{V2} - u_i^{V1} + C_1 u_i^{D_1} + C_2 u_i^{D_2} + C_3 u_i^{D_3} = 0

    where :math:`V1` and :math:`V2` are two compatible vertices,
    :math:`D_j` and :math:`C_j` are the dummy nodes and coefficients
    (all are used), and the equation is written for all DOFs, i.e. :math:`i=1,2,3`.

    The above equation is a generalization of the vertex equations
    in Eq. :eq:`bc-eq-pbc`. Compatible vertices and the value of coefficients
    must be taken from Eq. :eq:`bc-eq-pbc`.

    The parameters for creating an object are similar to :class:`BasePbcConstraint`.
    """

    def __repr__(self):
        return ''.join((f'*Equation\n5\n'
                        f'"{self.part_instance_name}".{self.node2_id + 1}, {dof}, 1.\n'
                        f'"{self.part_instance_name}".{self.node1_id + 1}, {dof}, -1.\n'
                        f'"{self.dummy_names[0]}", {dof}, {self.dummy_coeffs[0]}\n'
                        f'"{self.dummy_names[1]}", {dof}, {self.dummy_coeffs[1]}\n'
                        f'"{self.dummy_names[2]}", {dof}, {self.dummy_coeffs[2]}\n')
                       for dof in (1, 2, 3))


@dataclass
class Pbc2DEdgeConstraint:
    """Class for defining the following *two* 2D PBC constraints
    between a dummy nodes and two nodes on vertices of a square:

    .. math::
       u_{dof}^{V2} - u_{dof}^{V1} + C u_{dof}^{D} = 0 \\\\
       u_{aux\\_dof}^{V2} - u_{aux\\_dof}^{V1} = 0

    where :math:`V1` and :math:`V2` are two compatible vertices,
    :math:`D` and :math:`C` are the dummy node and coefficient
    used for the equation.

    Note that this class behaves differently from the children of :class:`BasePbcConstraint`.
    While they define equations for all DOFs, this class receives a *dof* which can
    either be 1 or 2, and sets *aux_dof* to be the other one.

    The above equation is a generalization of the vertex equations
    in Eq. :eq:`bc-eq-pbc2d`. Compatible vertices and the value of coefficients
    must be taken from Eq. :eq:`bc-eq-pbc2d`.

    The parameters for creating an object are:
    """
    part_instance_name: str
    """Name of the part instance that the nodes belong to."""
    dof: int
    """The DOF for which the first equation is defined.
    It must be 1 or 2 and the other value is assigned to *aux_dof*
    for which the second equation is defined."""
    dummy_names: str
    """Name of the set containing the dummy node."""
    dummy_coeffs: float
    """Value of the coefficient for the dummy node."""
    node1_id: int
    """ID of the first node used for the equation."""
    node2_id: int
    """ID of the second node used for the equation."""

    def __post_init__(self):
        if self.dof == 1:
            self.aux_dof: int = 2
        elif self.dof == 2:
            self.aux_dof: int = 1
        else:
            raise ValueError('Invalid value for dof. Only 1 and 2 are allowed.')

    def __repr__(self):
        return (f'*Equation\n3\n'
                f'"{self.part_instance_name}".{self.node2_id + 1}, {self.dof}, 1.\n'
                f'"{self.part_instance_name}".{self.node1_id + 1}, {self.dof}, -1.\n'
                f'"{self.dummy_names}", {self.dof}, {self.dummy_coeffs}\n'
                f'*Equation\n2\n'
                f'"{self.part_instance_name}".{self.node2_id + 1}, {self.aux_dof}, 1.\n'
                f'"{self.part_instance_name}".{self.node1_id + 1}, {self.aux_dof}, -1.\n')


class Pbc2DVertexConstraint(BasePbcConstraint):
    """Class for defining the following 2D PBC constraint
    between a dummy nodes and two nodes on vertices of a square:

    .. math::
       u_i^{V2} - u_i^{V1} + C_1 u_i^{D_1} + C_2 u_i^{D_2} = 0

    where :math:`V1` and :math:`V2` are two compatible vertices,
    :math:`D_j` and :math:`C_j` are the dummy nodes and coefficients
    (all are used), and the equation is written for all DOFs, i.e. :math:`i=1,2`.

    The above equation is a generalization of the vertex equations
    in Eq. :eq:`bc-eq-pbc2d`. Compatible vertices and the value of coefficients
    must be taken from Eq. :eq:`bc-eq-pbc2d`.

    The parameters for creating an object are similar to :class:`BasePbcConstraint`.
    """

    def __repr__(self):
        return ''.join((f'*Equation\n4\n'
                        f'"{self.part_instance_name}".{self.node2_id + 1}, {dof}, 1.\n'
                        f'"{self.part_instance_name}".{self.node1_id + 1}, {dof}, -1.\n'
                        f'"{self.dummy_names[0]}", {dof}, {self.dummy_coeffs[0]}\n'
                        f'"{self.dummy_names[1]}", {dof}, {self.dummy_coeffs[1]}\n')
                       for dof in (1, 2))


# noinspection PyProtectedMember
def create_bc(part, dim: str, mat_codes_to_accept: str | int | Iterable | NDArray,
              max_empty_border_elems: float = 0.5) -> list:
    """Create a boundary condition (BC) for a VoxelPart object.

    This function uses the VoxelPart object's *_bc_type* property and
    (1) creates the relevant node sets using :func:`create_node_sets`
    and, (2) returns a tuple of constraint objects to be written to output.

    Args:
        part (VoxelPart): The :class:`~.voxelpart.VoxelPart` object on which the operation is performed.
        dim: Dimensionality of the intended output. Valid values are '2D' and '3D'.
        max_empty_border_elems: Maximum ratio of empty elements in each border or edge.
                                Defaults to 0.5 which means 50%.
        mat_codes_to_accept: See the *material_list* parameter of
                             :func:`helper.validate_materials_to_be_output`.

    Returns:
        A list of constraint objects. The number and class of list contents
        depends on the VoxelPart object's *_bc_type* property.
    """
    if dim.upper() not in ['2D', '3D']:
        raise ValueError("dim can only be one of '2D' or '3D'.")

    bc_type = part._bc_type
    if bc_type is None:
        part._bc_add_dummy_nodes = False
        logger.info('No BCs have been created.')
        return []

    bc_applicability_status = check_border_elements(part, dim,
                                                    mat_codes_to_accept, max_empty_border_elems)
    if bc_applicability_status == 'OK':
        pass
    elif bc_applicability_status == 'WINDOW':
        raise BcNotApplicableError("The part's boundaries contain some empty elements which invalidate BCs. "
                                   "This can be mitigated using The Window Method,"
                                   "which has not been implemented yet.")
    elif bc_applicability_status == 'UNABLE':
        raise BcNotApplicableError("The part's boundaries contain too many empty elements which invalidate BCs.")

    if bc_type.upper() == 'NODESET ONLY':
        create_node_sets(part, dim, explicit_sets=part._bc_nodeset_explicit,
                         simple_sets=part._bc_nodeset_simple)
        logger.info('No BCs have been created but node sets were added to the part.')
        return []

    elif bc_type.upper() == 'LINEAR DISPLACEMENT':
        part._add_dummy_nodes(fixed=True, single_node=True)
        create_node_sets(part, dim, explicit_sets=part._bc_nodeset_explicit, simple_sets=True)
        if dim.upper() == '2D':
            constraint_list = [TieConstraint(dof=1, rp_set_name='RP0-NodeSet', slave_set_name='Simple-Edge11-NodeSet'),
                               TieConstraint(dof=2, rp_set_name='RP0-NodeSet', slave_set_name='Simple-Edge21-NodeSet'),
                               TieConstraint(dof=1, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Edge12-NodeSet'),
                               TieConstraint(dof=2, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Edge22-NodeSet')]
        else:  # dim.upper() == '3D'
            constraint_list = [TieConstraint(dof=1, rp_set_name='RP0-NodeSet', slave_set_name='Simple-Face11-NodeSet'),
                               TieConstraint(dof=2, rp_set_name='RP0-NodeSet', slave_set_name='Simple-Face21-NodeSet'),
                               TieConstraint(dof=3, rp_set_name='RP0-NodeSet', slave_set_name='Simple-Face31-NodeSet'),
                               TieConstraint(dof=1, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Face12-NodeSet'),
                               TieConstraint(dof=2, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Face22-NodeSet'),
                               TieConstraint(dof=3, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Face32-NodeSet')]

        logger.info('Linear Displacement BCs have were created.')
        return constraint_list

    elif bc_type.upper() == 'PERIODIC':
        part._add_dummy_nodes(fixed=False, three_nodes=True)
        create_node_sets(part, dim, explicit_sets=True, simple_sets=part._bc_nodeset_simple)
        constraint_list = []
        pl = part.real_size  # Length of the part.

        if dim.upper() == '2D':
            # Add constraints for the edges.
            constraint_list += add_2d_pbc_constraints(part, 'edge', dof=2,
                                                      dummy_names='RP2-NodeSet', dummy_coeffs=-pl[1],
                                                      set_names=('Edge12-NodeSet', 'Edge34-NodeSet'))
            constraint_list += add_2d_pbc_constraints(part, 'edge', dof=1,
                                                      dummy_names='RP1-NodeSet', dummy_coeffs=-pl[0],
                                                      set_names=('Edge14-NodeSet', 'Edge23-NodeSet'))
            # Add constraints for the vertices.
            constraint_list += add_2d_pbc_constraints(part, 'vertex', dof=None,
                                                      dummy_names=('RP1-NodeSet', 'RP2-NodeSet'),
                                                      dummy_coeffs=(-pl[0], -pl[1]),
                                                      set_names=('Vertex1-NodeSet', 'Vertex3-NodeSet'))
            constraint_list += add_2d_pbc_constraints(part, 'vertex', dof=None,
                                                      dummy_names=('RP1-NodeSet', 'RP2-NodeSet'),
                                                      dummy_coeffs=(+pl[0], -pl[1]),
                                                      set_names=('Vertex2-NodeSet', 'Vertex4-NodeSet'))
        else:  # dim.upper() == '3D'
            # Add constraints for the faces.
            constraint_list += add_3d_pbc_constraints(part, 'face', 'RP1-NodeSet', -pl[0],
                                                      ('Face11-NodeSet', 'Face12-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'face', 'RP2-NodeSet', -pl[1],
                                                      ('Face21-NodeSet', 'Face22-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'face', 'RP3-NodeSet', -pl[2],
                                                      ('Face31-NodeSet', 'Face32-NodeSet'))
            # Add constraints for the edges.
            constraint_list += add_3d_pbc_constraints(part, 'edge', ('RP2-NodeSet', 'RP3-NodeSet'), (-pl[1], -pl[2]),
                                                      ('Edge12-NodeSet', 'Edge78-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'edge', ('RP2-NodeSet', 'RP3-NodeSet'), (+pl[1], -pl[2]),
                                                      ('Edge34-NodeSet', 'Edge56-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'edge', ('RP1-NodeSet', 'RP2-NodeSet'), (-pl[0], -pl[1]),
                                                      ('Edge15-NodeSet', 'Edge37-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'edge', ('RP1-NodeSet', 'RP2-NodeSet'), (-pl[0], +pl[1]),
                                                      ('Edge48-NodeSet', 'Edge26-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'edge', ('RP1-NodeSet', 'RP3-NodeSet'), (-pl[0], -pl[2]),
                                                      ('Edge14-NodeSet', 'Edge67-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'edge', ('RP1-NodeSet', 'RP3-NodeSet'), (-pl[0], +pl[2]),
                                                      ('Edge58-NodeSet', 'Edge23-NodeSet'))
            # Add constraints for the vertices.
            dummy_names = ('RP1-NodeSet', 'RP2-NodeSet', 'RP3-NodeSet')
            constraint_list += add_3d_pbc_constraints(part, 'vertex', dummy_names, (-pl[0], -pl[1], -pl[2]),
                                                      ('Vertex1-NodeSet', 'Vertex7-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'vertex', dummy_names, (+pl[0], -pl[1], -pl[2]),
                                                      ('Vertex2-NodeSet', 'Vertex8-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'vertex', dummy_names, (+pl[0], +pl[1], -pl[2]),
                                                      ('Vertex3-NodeSet', 'Vertex5-NodeSet'))
            constraint_list += add_3d_pbc_constraints(part, 'vertex', dummy_names, (-pl[0], +pl[1], -pl[2]),
                                                      ('Vertex4-NodeSet', 'Vertex6-NodeSet'))
        logger.info('Periodic BCs have were created.')
        return constraint_list

    else:
        raise ValueError('Invalid value for bc_type.')


def check_border_elements(part, dim: str,
                          mat_codes_to_accept: str | int | Iterable | NDArray,
                          max_empty_border_elems: float = 0.5) -> str:
    """Check the border elements for empty space and return the status.

    Args:
        part (VoxelPart): The *VoxelPart* instance where operations take place.
        dim: Dimensionality of the intended output. Valid values are '2D' and '3D'.
        max_empty_border_elems: Maximum ratio of empty elements in each border or edge.
                                Defaults to 0.5 which means 50%.
        mat_codes_to_accept: See the *material_list* parameter of
                             :func:`helper.validate_materials_to_be_output`.

    Returns:
        One of the following strings

        - *'OK'* if all border elements are non-empty and the BC can be applied as is.
        - *'WINDOW'* if there are empty elements in some border areas,
          but the ratio of empty to non-empty is acceptable for each border area.
          This means that BCs can be applied using the Window Method.
        - *'FAIL'* if the part has too many non-empty elements in the borders and
          BCs cannot be applied.

    """
    # Validate parameters.
    mat_codes_to_accept = validate_materials_to_be_output(part, mat_codes_to_accept)
    if dim.upper() not in ['2D', '3D']:
        raise ValueError("dim can only be one of '2D' or '3D'.")
    if max_empty_border_elems <= 0.05:
        raise ValueError('max_empty_border_elems should be greater or equal to 0.05.')

    arr = part.data
    # Create a list of arrays for each border area.
    # Note that there is an overlap between border areas which is OK.
    if dim.upper() == '2D':
        border_arrays_list = (arr[0, :], arr[-1, :],
                              arr[:, 0], arr[:, -1])
    elif dim.upper() == '3D':
        border_arrays_list = (arr[0, :, :], arr[-1, :, :],
                              arr[:, 0, :], arr[:, -1, :],
                              arr[:, :, 0], arr[:, :, -1])
    else:
        raise RuntimeError('Invalid Value for dim. This should have been caught earlier.')

    # Count the number of rejected elements in each border array.
    num_rejected_elems_list = []
    num_border_elems_list = []
    for bal in border_arrays_list:
        num_rejected_elems_list.append(
            count_nonzero(
                isin(element=bal, test_elements=mat_codes_to_accept, invert=True, kind='table')))
        num_border_elems_list.append(bal.size)

    # Determine status based on the number of rejected elements.
    # Start with OK.
    status = 'OK'
    # If there are any rejected border elements the window method must be used.
    if any(array(num_rejected_elems_list) != 0):
        status = 'WINDOW'
    # If there are too many rejected border elements, even the window method won't work.
    if any((array(num_rejected_elems_list) / array(num_border_elems_list)) > max_empty_border_elems):
        status = 'UNABLE'

    return status


def add_2d_pbc_constraints(part, typ: str, dof: int | None,
                           dummy_names: Union[str, tuple],
                           dummy_coeffs: Union[float, tuple],
                           set_names: tuple) -> list:
    """Add an equation for a 2D PBC.
    With the correct arguments, all the equations
    in Eq. :eq:`bc-eq-pbc2d` can be implemented using this function.

    Args:
        part (VoxelPart): The *VoxelPart* object on which the operation is performed.
        typ: Type of the node sets to be constrained. Valid values are 'edge' and 'vertex'.
        dof: If *typ=edge*, must be either be 1 or 2, otherwise is not used. Defaults to *None*.
        dummy_names: If *typ=edge*, a tuple containing the names of the
                     two sets containing the dummy nodes for the equation.
                     If *typ=vertex*, a single string denoting the name of the vertex set.
                     Otherwise, an error is raised.
        dummy_coeffs: If *typ=edge*, a single float or
                      if *typ=vertex*, a tuple containing the coefficients for the dummy nodes.
                      Otherwise, an error is raised.
        set_names: Tuple of the names of the sets of the edges or vertices to be constrained.
                   The sets must contain the same number of nodes,
                   and they must be in the same order.

    Returns:
        A list of constraint objects for the given parameters.
    """
    set1_ids = part.node_sets[set_names[0]]
    set2_ids = part.node_sets[set_names[1]]
    instance_name = part.instance_name
    if len(set1_ids) != len(set2_ids):
        raise ValueError("Sets '%s' and '%s' are of different lengths."
                         "This should have been caught before calling this function.")
    if typ.lower() == 'edge':
        if dof not in (1, 2):
            raise ValueError(f"For type='edge', dof must be 1 or 2 but is {dof}.")
        return [Pbc2DEdgeConstraint(instance_name, dof, dummy_names, dummy_coeffs, set1_ids[i], set2_ids[i])
                for i in range(len(set1_ids))]
    elif typ.lower() == 'vertex':
        return [Pbc2DVertexConstraint(instance_name, dummy_names, dummy_coeffs, set1_ids[i], set2_ids[i])
                for i in range(len(set1_ids))]
    else:
        raise ValueError("typ must be either 'edge' or 'vertex'.")


def add_3d_pbc_constraints(part, typ: str,
                           dummy_names: Union[str, tuple],
                           dummy_coeffs: Union[float, tuple],
                           set_names: tuple) -> list:
    """Add an equation for a 3D PBC.
    With the correct arguments, all the equations
    in Eq. :eq:`bc-eq-pbc` can be implemented using this function.

    Args:
        part (VoxelPart): The :class:`~.voxelpart.VoxelPart` object on which the operation is performed.
        typ: Type of the node sets to be constrained. Valid values are 'face', 'edge', and 'vertex'.
        dummy_names: Tuple of the names of the sets containing the dummy nodes for the equation
                     or in the case of ``typ==vertex``, a single string.
        dummy_coeffs: Tuple of the values of the coefficients for the dummy nodes.
                      or in the case of ``typ==vertex``, a single float.
        set_names: Tuple of the names of the sets of the edges or vertices to be constrained.
                   The sets must contain the same number of nodes,
                   and they must be in the same order.

    Returns:
        A list of constraint objects for the given parameters.
    """
    set1_ids = part.node_sets[set_names[0]]
    set2_ids = part.node_sets[set_names[1]]
    instance_name = part.instance_name
    if len(set1_ids) != len(set2_ids):
        raise ValueError("Sets '%s' and '%s' are of different lengths."
                         "This should have been caught before calling this function.")
    if typ.lower() == 'face':
        constraint_class = Pbc3DFaceConstraint
    elif typ.lower() == 'edge':
        constraint_class = Pbc3DEdgeConstraint
    elif typ.lower() == 'vertex':
        constraint_class = Pbc3DVertexConstraint
    else:
        raise ValueError("typ must be one of 'face', 'edge', or 'vertex'.")
    return [constraint_class(instance_name, dummy_names, dummy_coeffs, set1_ids[i], set2_ids[i])
            for i in range(len(set1_ids))]


def create_node_sets(part, dim: str, explicit_sets: bool = False, simple_sets: bool = True):
    """Define node sets in a VoxelPart. They are created according to :numref:`bc-nodesets`:

    Args:
        part (VoxelPart): The :class:`~.voxelpart.VoxelPart` object on which the operation is performed.
        dim: Dimensionality of the output part. Valid values are '2D' and '3D'.
        explicit_sets: If True, explicit node sets are created for vertices, edges, and faces.
                       as described in the section titled :ref:`boundary-conditions-pbc`.
                       Defaults to *False*.
        simple_sets: If True, simplified node sets are created
                     which are the full faces for the 3D models or the edges for the 2D models,
                     as described in the section titled :ref:`boundary-conditions-lin-disp`.
                     Defaults to *True*.
    """
    if dim.upper() not in ['2D', '3D']:
        raise ValueError("dim can only be one of '2D' or '3D'.")

    if not any([explicit_sets, simple_sets]):
        raise ValueError('At least one of explicit_sets and simple_sets must be set to True.')

    # Define a ravel function based on numpy.ravel_multi_index.
    def custom_ravel(inds):
        return ravel_multi_index(multi_index=inds, dims=node_array_shape,
                                 mode='raise', order='C').flatten()

    # Define a numpy.array containing a single number 0.
    zro = array([0])
    # Define elem_array_shape.
    elem_array_shape = part.size
    # In each direction, node array is larger by one.
    node_array_shape = tuple(i + 1 for i in elem_array_shape)
    if dim.upper() == '2D':
        max_x, max_y = elem_array_shape
    else:
        max_x, max_y, max_z = elem_array_shape
        inds_dir3 = arange(1, max_z)
    # Find indices of nodes in all directions. Indices for vertices are not included.
    inds_dir1 = arange(1, max_x)
    inds_dir2 = arange(1, max_y)

    # Define dictionaries for the sets.
    vertex_dict = dict()
    edge_dict = dict()
    face_dict = dict()
    simple_sets_dict = dict()

    # Define vertices.
    # Find IDs for vertices.
    if dim.upper() == '2D':
        vertex_coords = (array([0, max_x, max_x, 0]),
                         array([0, 0, max_y, max_y]))
    else:
        vertex_coords = (array([0, max_x, max_x, 0, 0, max_x, max_x, 0]),
                         array([0, 0, max_y, max_y, 0, 0, max_y, max_y]),
                         array([0, 0, 0, 0, max_z, max_z, max_z, max_z]))  # noqa F823
    # Find IDs and define node sets for the vertices.
    vertex_ids = custom_ravel(vertex_coords)
    for i in range(len(vertex_ids)):
        vertex_dict['Vertex%i-NodeSet' % (i + 1)] = vertex_ids[i]

    # Define edges.
    # Find IDs for edges. edge_ij refers to the edge formed by vertices i and j.
    if dim.upper() == '2D':
        edge_dict['Edge12-NodeSet'] = custom_ravel((inds_dir1, zro))
        edge_dict['Edge23-NodeSet'] = custom_ravel((max_x, inds_dir2))
        edge_dict['Edge34-NodeSet'] = custom_ravel((inds_dir1, max_y))
        edge_dict['Edge14-NodeSet'] = custom_ravel((zro, inds_dir2))
    else:
        edge_dict['Edge12-NodeSet'] = custom_ravel((inds_dir1, zro, zro))
        edge_dict['Edge23-NodeSet'] = custom_ravel((max_x, inds_dir2, zro))
        edge_dict['Edge34-NodeSet'] = custom_ravel((inds_dir1, max_y, zro))
        edge_dict['Edge14-NodeSet'] = custom_ravel((zro, inds_dir2, zro))
        edge_dict['Edge56-NodeSet'] = custom_ravel((inds_dir1, zro, max_z))
        edge_dict['Edge67-NodeSet'] = custom_ravel((max_x, inds_dir2, max_z))
        edge_dict['Edge78-NodeSet'] = custom_ravel((inds_dir1, max_y, max_z))
        edge_dict['Edge58-NodeSet'] = custom_ravel((zro, inds_dir2, max_z))
        edge_dict['Edge15-NodeSet'] = custom_ravel((zro, zro, inds_dir3))  # noqa F823
        edge_dict['Edge26-NodeSet'] = custom_ravel((max_x, zro, inds_dir3))
        edge_dict['Edge37-NodeSet'] = custom_ravel((max_x, max_y, inds_dir3))
        edge_dict['Edge48-NodeSet'] = custom_ravel((zro, max_y, inds_dir3))

    if dim.upper() == '3D':
        # Define faces.
        # Find IDs for faces. For face_ij, i refers the direction of normal vector
        # and j refers to whether this is the first or second edge in the direction.
        face_dict['Face11-NodeSet'] = custom_ravel(
            meshgrid(zro, inds_dir2, inds_dir3, sparse=True))
        face_dict['Face12-NodeSet'] = custom_ravel(
            meshgrid(max_x, inds_dir2, inds_dir3, sparse=True))
        face_dict['Face21-NodeSet'] = custom_ravel(
            meshgrid(inds_dir1, zro, inds_dir3, sparse=True))
        face_dict['Face22-NodeSet'] = custom_ravel(
            meshgrid(inds_dir1, max_y, inds_dir3, sparse=True))
        face_dict['Face31-NodeSet'] = custom_ravel(
            meshgrid(inds_dir1, inds_dir2, zro, sparse=True))
        face_dict['Face32-NodeSet'] = custom_ravel(
            meshgrid(inds_dir1, inds_dir2, max_z, sparse=True))

    if simple_sets:
        if dim == '2D':
            simple_sets_dict['Simple-Edge11-NodeSet'] = concatenate((edge_dict['Edge14-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex4-NodeSet']))),
                                                                    axis=0)
            simple_sets_dict['Simple-Edge12-NodeSet'] = concatenate((edge_dict['Edge23-NodeSet'],
                                                                     array((vertex_dict['Vertex2-NodeSet'],
                                                                            vertex_dict['Vertex3-NodeSet']))),
                                                                    axis=0)
            simple_sets_dict['Simple-Edge21-NodeSet'] = concatenate((edge_dict['Edge12-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex2-NodeSet']))),
                                                                    axis=0)
            simple_sets_dict['Simple-Edge22-NodeSet'] = concatenate((edge_dict['Edge34-NodeSet'],
                                                                     array((vertex_dict['Vertex3-NodeSet'],
                                                                            vertex_dict['Vertex4-NodeSet']))),
                                                                    axis=0)
        else:  # dim == '3D'
            simple_sets_dict['Simple-Face11-NodeSet'] = concatenate((face_dict['Face11-NodeSet'],
                                                                     edge_dict['Edge14-NodeSet'],
                                                                     edge_dict['Edge48-NodeSet'],
                                                                     edge_dict['Edge58-NodeSet'],
                                                                     edge_dict['Edge15-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex4-NodeSet'],
                                                                            vertex_dict['Vertex8-NodeSet'],
                                                                            vertex_dict['Vertex5-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face12-NodeSet'] = concatenate((face_dict['Face12-NodeSet'],
                                                                     edge_dict['Edge23-NodeSet'],
                                                                     edge_dict['Edge37-NodeSet'],
                                                                     edge_dict['Edge67-NodeSet'],
                                                                     edge_dict['Edge26-NodeSet'],
                                                                     array((vertex_dict['Vertex2-NodeSet'],
                                                                            vertex_dict['Vertex3-NodeSet'],
                                                                            vertex_dict['Vertex7-NodeSet'],
                                                                            vertex_dict['Vertex6-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face21-NodeSet'] = concatenate((face_dict['Face21-NodeSet'],
                                                                     edge_dict['Edge12-NodeSet'],
                                                                     edge_dict['Edge26-NodeSet'],
                                                                     edge_dict['Edge56-NodeSet'],
                                                                     edge_dict['Edge15-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex2-NodeSet'],
                                                                            vertex_dict['Vertex6-NodeSet'],
                                                                            vertex_dict['Vertex5-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face22-NodeSet'] = concatenate((face_dict['Face22-NodeSet'],
                                                                     edge_dict['Edge34-NodeSet'],
                                                                     edge_dict['Edge37-NodeSet'],
                                                                     edge_dict['Edge78-NodeSet'],
                                                                     edge_dict['Edge48-NodeSet'],
                                                                     array((vertex_dict['Vertex4-NodeSet'],
                                                                            vertex_dict['Vertex3-NodeSet'],
                                                                            vertex_dict['Vertex7-NodeSet'],
                                                                            vertex_dict['Vertex8-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face31-NodeSet'] = concatenate((face_dict['Face31-NodeSet'],
                                                                     edge_dict['Edge12-NodeSet'],
                                                                     edge_dict['Edge23-NodeSet'],
                                                                     edge_dict['Edge34-NodeSet'],
                                                                     edge_dict['Edge14-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex2-NodeSet'],
                                                                            vertex_dict['Vertex3-NodeSet'],
                                                                            vertex_dict['Vertex4-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face32-NodeSet'] = concatenate((face_dict['Face32-NodeSet'],
                                                                     edge_dict['Edge56-NodeSet'],
                                                                     edge_dict['Edge67-NodeSet'],
                                                                     edge_dict['Edge78-NodeSet'],
                                                                     edge_dict['Edge58-NodeSet'],
                                                                     array((vertex_dict['Vertex5-NodeSet'],
                                                                            vertex_dict['Vertex6-NodeSet'],
                                                                            vertex_dict['Vertex7-NodeSet'],
                                                                            vertex_dict['Vertex8-NodeSet']))),
                                                                    axis=None)
        # Define the simple node sets.
        for name, ids in simple_sets_dict.items():
            part.add_node_set(name=name, ids=ids)

    # Define the individual node sets for vertices, edges and faces.
    if explicit_sets:
        # Define node sets for the vertices.
        for name, ids in vertex_dict.items():
            part.add_node_set(name=name, ids=ids)
        # Define node sets for the edges.
        for name, ids in edge_dict.items():
            part.add_node_set(name=name, ids=ids)
        if dim.upper() == '3D':
            # Define node sets for the faces.
            for name, ids in face_dict.items():
                part.add_node_set(name=name, ids=ids)
