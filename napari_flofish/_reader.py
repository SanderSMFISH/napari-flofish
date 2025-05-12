"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the Reader specification, but your plugin may choose to
implement multiple readers or even other plugin contributions. see:
https://napari.org/stable/plugins/guides.html?#readers
"""
import numpy as np
import pandas as pd
import json
from skimage import io
from pathlib import Path
from skimage import io
from textwrap import dedent
from napari.utils.notifications import show_info

def napari_get_reader(path):
    """A basic implementation of a Reader contribution.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    if isinstance(path, list):
        # reader plugins may be handed single path, or a list of paths.
        # if it is a list, it is assumed to be an image stack...
        # so we are only going to look at the first file.
        path = path[0]

    # if we know we cannot read the file, we immediately return None.
    if not path.endswith(".json"):
        return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def reader_function(path):
    """Take a path or list of paths and return a list of LayerData tuples.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.

    Parameters
    ----------
    path : str
        Path to img.json file

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of
        layer. Both "meta", and "layer_type" are optional. napari will
        default to layer_type=="image" if not provided
    """
    # handle both a string and a list of strings
    # paths = [path] if isinstance(path, str) else path
    # # load all files into array
    # arrays = [np.load(_path) for _path in paths]
    # # stack arrays into single array
    # data = np.squeeze(np.stack(arrays))
    #
    # # optional kwargs for the corresponding viewer.add_* method
    # add_kwargs = {}
    #
    # layer_type = "image"  # optional, default is "image"
    #
    # return [(data, add_kwargs, layer_type)]

    layer_tuples = read_smfish_json(path)
    pass
    return layer_tuples

def read_smfish_json(path):
    import json
    import numpy as np
    import pandas as pd
    from pathlib import Path
    from skimage import io

    layer_list = [
        # Static layers
        { 'file': 'DIC.tif', 'layer_type': "image",
          'add_kwargs': { 'name': "DIC", 'colormap': 'grey', 'visible': True, 'blending': 'additive' } },
        { 'file': 'DIC_masks_pp.tif', 'layer_type': 'labels',
          'add_kwargs': { 'name': "DIC masks", 'visible': False, 'blending': 'additive', 'opacity': 0.2 } },
        { 'file': 'DIC_masks_pp_expanded.tif', 'layer_type': 'labels',
          'add_kwargs': { 'name': "DIC masks expanded", 'visible': False, 'blending': 'additive', 'opacity': 0.2 } },
        { 'file': 'DAPI.tif', 'layer_type': "image",
          'add_kwargs': { 'name': "DAPI", 'colormap': 'blue', 'visible': True, 'blending': 'additive' } },
        { 'file': 'DAPI_masks.tif', 'layer_type': 'labels',
          'add_kwargs': { 'name': "DAPI masks", 'visible': False, 'blending': 'additive', 'opacity': 0.2 } },
    ]

    layer_tuples = []
    missing_files = []

    with open(path, "r") as f:
        img = json.load(f)
        colors = { k: v.get('colormap', 'gray') for k, v in img['results'].items() }

        for ch in img['results'].keys():
            metadata = { 'channel': ch, **img['parameters'] }
            threshold = img['results'][ch].get('threshold', 0)
            metadata.update({'threshold': threshold})

            layer_list.extend([
                { 'file': f'{ch}.tif', 'layer_type': "image",
                  'add_kwargs': { 'name': f'{ch}', 'metadata': metadata,
                                  'colormap': colors.get(ch, 'gray'), 'visible': False } },
                { 'file': f'{ch}_filtered.npy', 'layer_type': "image",
                  'add_kwargs': { 'name': f'{ch} background filtered', 'metadata': metadata,
                                  'colormap': colors.get(ch, 'gray'), 'visible': True } },
                { 'file': f'{ch}_spots.npy', 'layer_type': "points",
                  'add_kwargs': { 'name': f'{ch} spots detected thr={threshold}', 'metadata': metadata,
                                  'symbol': 'disc', 'size': 10, 'opacity': 0.5, 'face_color': 'transparent',
                                  'border_color': 'label' } },
                { 'file': f'{ch}_decomposed_spots.npy', 'layer_type': "points",
                  'add_kwargs': { 'name': f'{ch} decomposed spots', 'metadata': metadata,
                                  'symbol': 'disc', 'size': 10, 'opacity': 0.5, 'face_color': 'transparent',
                                  'border_color': colors.get(ch, 'gray') } }
            ])

    for l in layer_list:
        file = Path(path).parent / l['file']
        if not file.exists():
            missing_files.append(l['file'])
            continue

        if file.suffix == '.tif':
            data = io.imread(file)
        elif file.suffix == '.npy':
            data = np.load(file)
            if l['layer_type'] == "points" and "spots" in l['file']:
                features = pd.DataFrame(data, columns=['z', 'y', 'x', 'intensity', 'filtered_intensity', 'label'])
                data = data[:, :3]
                l['add_kwargs']['features'] = features
        else:
            continue

        layer_tuples.append((data, l['add_kwargs'], l['layer_type']))

    if missing_files:
        print(f"Missing files ({len(missing_files)}):")
        for f in missing_files:
            print(f" - {f}")

    return layer_tuples
