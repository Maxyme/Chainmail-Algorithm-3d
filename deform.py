﻿"""
Deform module where 1 pixel = 1mm distance.
This is the convention when comparing voxels, so not to get the comparisons mixed up:
    ytop is above ybottom so ytop has a bigger y value than y bottom.
    xright has a bigger x value than xleft. zdown has a smaller value than z.

"""
import numpy as np


def deform(disp_src, disp_area, disp_vector, original_cube, voxel_spacing, stiffness_coef):
    """
    Deform matrix from a sponsor list

    """
    disp_dst = disp_src + disp_vector

    # Get the original sponsors
    original_sponsors = find_original_sponsors(disp_dst, disp_src, original_cube, voxel_spacing, disp_area)

    # creates the history of all the sponsor positions so they cannot be deformed
    sponsor_history = original_sponsors[:, -1]

    # copies the original matrix in the new matrix that will be deformed
    new_matrix = np.copy(original_cube)

    # Updates the matrix with the new deformed position
    for el in original_sponsors:
        new_matrix[el[3]] = el[:3]

    # execute as long as there is an active sponsor
    while len(original_sponsors) > 0:
        use_sponsor = original_sponsors[0]
        original_sponsors = np.delete(original_sponsors, 0, axis=0)

        sponsor_index = use_sponsor[3]
        sponsor = original_cube[np.int(sponsor_index)]
        neighbors = find_neighbors(sponsor, original_cube, sponsor_history, voxel_spacing, False)

        while len(neighbors) > 0:
            use_neighbor = neighbors.pop(0)
            neighbor_position = find_index(use_neighbor[:3], original_cube)
            sponsor_history = np.append(sponsor_history, neighbor_position)

            use_neighbor = deform_neighbour(use_sponsor, use_neighbor, voxel_spacing, stiffness_coef)

            if use_neighbor:
                # adds the position value instead of the neighbor value
                use_neighbor[3] = neighbor_position
                use_neighbor = np.array(use_neighbor)
                original_sponsors = np.vstack((original_sponsors, use_neighbor))
                new_matrix[neighbor_position] = np.array(use_neighbor[:3])

    return new_matrix


def find_original_sponsors(displacement_dst, displacement_src, original_cube, step, displacement_area):
    """
    Find all original sponsors, depending on the displacement area

    """
    displacement_vector = displacement_dst - displacement_src

    # position of the original modified voxel
    sponsor_index = find_index(displacement_src, original_cube)
    # the list of sponsors to include in the deform function, includes the sponsor position also [3]
    original_sponsors = np.append(displacement_dst, sponsor_index)

    # the list of neighbors at the layer of the radius function.  Ex for radius 1, the layer neighbor is the sponsor
    outside_layer = [original_sponsors]

    # the sponsor_history list for a radius of 2, the new layer neighbors are the neighbors added for a radius of 1.
    # puts the sponsor position in a list so that it adds the sponsors when it looks for it
    sponsor_history = [sponsor_index]

    for i in range(displacement_area):
        storage_layer = []
        while len(outside_layer) > 0:
            index = outside_layer.pop(0)[3]
            sponsor = original_cube[index]
            neighbors = find_neighbors(sponsor, original_cube, sponsor_history, step)
            storage_layer = storage_layer + neighbors

            # Find and add the position of the new neighbors to the history list
            for el in storage_layer:
                el[3] = find_index(el[:3], original_cube)
                sponsor_history.append(el[3])

        original_sponsors = np.append(np.asarray(storage_layer), [original_sponsors], axis=0)
        outside_layer.extend(storage_layer)

    # Deforms the surface found (all the neighbors) according to the vector of deformation applied to the sponsor
    original_sponsors[:, :3] += displacement_vector

    return original_sponsors


def find_index(voxel, matrix):
    """
    function that finds a defined voxel position in a matrix

    """
    return np.where(np.all(matrix == voxel, axis=1))[0][0]


def deform_right(sponsor, candidate, step, stiffness_coef):
    """
    Deforms the Right (in x) neighbor of the sponsor

    """
    minimum = step - stiffness_coef
    maximum = step + stiffness_coef
    shear = stiffness_coef
    compare = candidate[:]
    if candidate[0] - sponsor[0] < minimum:
        candidate[0] = sponsor[0] + minimum
    elif candidate[0] - sponsor[0] > maximum:
        candidate[0] = sponsor[1] + maximum

    if candidate[1] - sponsor[1] < -shear:
        candidate[1] = sponsor[1] - shear
    elif candidate[1] - sponsor[1] > shear:
        candidate[1] = sponsor[1] + shear

    if candidate[2] - sponsor[2] < -shear:
        candidate[2] = sponsor[2] - shear
    elif candidate[2] - sponsor[2] > shear:
        candidate[2] = sponsor[2] + shear

    return 0 if np.array_equal(compare, candidate) else candidate


def deform_left(sponsor, candidate, step, stiffness_coef):
    """
    Deforms the Left (in x) neighbor of the sponsor

    """
    minimum = step - stiffness_coef
    maximum = step + stiffness_coef
    shear = stiffness_coef
    compare = candidate[:]
    if candidate[0] - sponsor[0] < -maximum:
        candidate[0] = sponsor[0] - maximum
    elif candidate[0] - sponsor[0] > -minimum:
        candidate[0] = sponsor[1] - minimum

    if candidate[1] - sponsor[1] < -shear:
        candidate[1] = sponsor[1] + shear
    elif candidate[1] - sponsor[1] > shear:
        candidate[1] = sponsor[1] + shear

    if candidate[2] - sponsor[2] < -shear:
        candidate[2] = sponsor[2] - shear
    elif candidate[2] - sponsor[2] > shear:
        candidate[2] = sponsor[2] + shear

    return 0 if np.array_equal(compare, candidate) else candidate


def deform_top(sponsor, candidate, step, shear):
    """
    Deforms the Top (in y) neighbor of the sponsor

    """
    minimum = step - shear
    maximum = step + shear

    original = candidate[:]
    if candidate[1] - sponsor[1] < minimum:
        candidate[1] = sponsor[1] + minimum
    elif candidate[1] - sponsor[1] > maximum:
        candidate[1] = sponsor[1] + maximum

    if candidate[0] - sponsor[0] < -shear:
        candidate[0] = sponsor[0] + shear
    elif candidate[0] - sponsor[0] > shear:
        candidate[0] = sponsor[1] + shear

    if candidate[2] - sponsor[2] < -shear:
        candidate[2] = sponsor[2] - shear
    elif candidate[2] - sponsor[2] > shear:
        candidate[2] = sponsor[2] + shear

    return 0 if np.array_equal(original, candidate) else candidate


def deform_lower(sponsor, candidate, step, shear):
    """
    Deforms the Bottom (in y) neighbor of the sponsor

    """
    minimum = step - shear
    maximum = step + shear

    original = candidate[:]
    if candidate[1] - sponsor[1] > -minimum:
        candidate[1] = sponsor[1] - minimum
    elif candidate[1] - sponsor[1] < -maximum:
        candidate[1] = sponsor[1] - maximum

    if candidate[0] - sponsor[0] < -shear:
        candidate[0] = sponsor[0] + shear
    elif candidate[0] - sponsor[0] > shear:
        candidate[0] = sponsor[1] + shear

    if candidate[2] - sponsor[2] < -shear:
        candidate[2] = sponsor[2] - shear
    elif candidate[2] - sponsor[2] > shear:
        candidate[2] = sponsor[2] + shear

    return 0 if np.array_equal(original, candidate) else candidate


def deform_down(sponsor, candidate, step, shear):
    """
    Deforms the DOWN (in z) neighbor of the sponsor

    """
    minimum = step - shear
    maximum = step + shear

    original = candidate[:]
    if candidate[2] - sponsor[2] > -minimum:
        candidate[2] = sponsor[2] - minimum
    elif candidate[2] - sponsor[2] < -maximum:
        candidate[2] = sponsor[2] - maximum

    if candidate[0] - sponsor[0] < -shear:
        candidate[0] = sponsor[0] + shear
    elif candidate[0] - sponsor[0] > shear:
        candidate[0] = sponsor[0] + shear

    if candidate[1] - sponsor[1] < -shear:
        candidate[1] = sponsor[1] - shear
    elif candidate[1] - sponsor[1] > shear:
        candidate[1] = sponsor[1] + shear

    return 0 if np.array_equal(original, candidate) else candidate


def deform_up(sponsor, candidate, step, shear):
    """
    Deforms the UP (in z) neighbor of the sponsor

    """
    minimum = step - shear
    maximum = step + shear

    original = candidate[:]
    if candidate[2] - sponsor[2] > minimum:
        candidate[2] = sponsor[2] + minimum
    elif candidate[2] - sponsor[2] > maximum:
        candidate[2] = sponsor[2] + maximum

    if candidate[0] - sponsor[0] < -shear:
        candidate[0] = sponsor[0] + shear
    elif candidate[0] - sponsor[0] > shear:
        candidate[0] = sponsor[0] + shear

    if candidate[1] - sponsor[1] < -shear:
        candidate[1] = sponsor[1] - shear
    elif candidate[1] - sponsor[1] > shear:
        candidate[1] = sponsor[1] + shear

    return 0 if np.array_equal(original, candidate) else candidate


def deform_neighbour(sponsor, neighbor, step, shear):
    """
    Selects the neighbour against the sponsor and sends them
    to the correct function it returns the modified value of the neighbor
    """
    if neighbor[3] == 0:
        return deform_right(sponsor, neighbor, step, shear)
    elif neighbor[3] == 1:
        return deform_left(sponsor, neighbor, step, shear)
    elif neighbor[3] == 2:
        return deform_top(sponsor, neighbor, step, shear)
    elif neighbor[3] == 3:
        return deform_lower(sponsor, neighbor, step, shear)
    elif neighbor[3] == 4:
        return deform_down(sponsor, neighbor, step, shear)
    elif neighbor[3] == 5:
        return deform_up(sponsor, neighbor, step, shear)


def find_neighbors(sponsor, cube_matrix, sponsor_hist, step, surface_only=True):
    """
    Find all the neighbors of the sponsor. Will not add values outside the cube as neighbors.
    Right neighbor value=0 ; left =1; top =2; bottom = 3 down = 4, up = 5.
    Find z neighbors if not only surface neighbors
    """
    side_length = np.ceil(np.power(cube_matrix.shape[0], 1 / 3) * step)
    neighbors = []

    if sponsor[0] + step < side_length:
        rn = [sponsor[0] + step, sponsor[1], sponsor[2], 0]
        if not find_index(rn[:3], cube_matrix) in sponsor_hist:
            neighbors.append(rn)

    if sponsor[0] - step >= 0:
        ln = [sponsor[0] - step, sponsor[1], sponsor[2], 1]
        if not find_index(ln[:3], cube_matrix) in sponsor_hist:
            neighbors.append(ln)

    if sponsor[1] + step < side_length:
        tn = [sponsor[0], sponsor[1] + step, sponsor[2], 2]
        if not find_index(tn[:3], cube_matrix) in sponsor_hist:
            neighbors.append(tn)

    if sponsor[1] - step >= 0:
        bn = [sponsor[0], sponsor[1] - step, sponsor[2], 3]
        if not find_index(bn[:3], cube_matrix) in sponsor_hist:
            neighbors.append(bn)

    if not surface_only:
        if sponsor[2] - step >= 0:
            dn = [sponsor[0], sponsor[1], sponsor[2] - step, 4]
            if not find_index(dn[:3], cube_matrix) in sponsor_hist:
                neighbors.append(dn)

        if sponsor[2] + step < side_length:
            un = [sponsor[0], sponsor[1], sponsor[2] + step, 5]
            if not find_index(un[:3], cube_matrix) in sponsor_hist:
                neighbors.append(un)

    return neighbors
