import numpy as np

from typing import List


def pairwise_hamming_distance(indexes: List[str]):
    n_indexes: int = len(indexes)
    index_length = len(indexes[0])

    # Create a 2D array from the list of strings
    index_array = np.array([list(index) for index in indexes])

    # Reshape the array to a 3D array for broadcasting
    index_array = index_array.reshape(n_indexes, 1, index_length)

    # Calculate the Hamming distance
    distances = (index_array != index_array.transpose(1, 0, 2)).sum(axis=2)

    return distances.tolist()
