import typing as t
from pathlib import Path
from zipfile import ZipFile

import numpy as np

XY_WAVEFORM = t.List[np.ndarray] #X, Y waveform


def read_waveform_binary(location: Path, compressed: bool) -> np.ndarray:
    if not compressed:
        f = ZipFile(location, 'r')
        f_name = f.namelist()
        w = f.read(f_name[0])
        f.close()
    else:
        # TODO:: Implement reading waveform_names that are compressed
        raise NotImplementedError("Waveform must be compressed")

    dt = np.dtype(float)
    wf = np.frombuffer(w, dtype=dt)

    return wf


def create_waveform_x_coords(x_increment: float, length: int) -> np.array:
    wf_x = np.linspace(start=0, stop=length * x_increment, num=length)
    return wf_x


def min_max_downsample_2d(wf_x: np.ndarray, wf_y: np.ndarray, size: int) -> \
        XY_WAVEFORM:
    pts_per_bin = wf_x.size // size

    x_view = wf_x[:pts_per_bin * size].reshape(size, pts_per_bin)
    y_view = wf_y[:pts_per_bin * size].reshape(size, pts_per_bin)
    i_min = np.argmin(y_view, axis=1)
    i_max = np.argmax(y_view, axis=1)

    r_index = np.repeat(np.arange(size), 2)
    c_index = np.sort(np.stack((i_min, i_max), axis=1)).ravel()

    return [x_view[r_index, c_index], y_view[r_index, c_index]]


def min_max_downsample_1d(wf: np.ndarray, size: int) -> np.ndarray:
    pts_per_bin = wf.size // size

    view = wf[:pts_per_bin * size].reshape(size, pts_per_bin)
    i_min = np.argmin(view, axis=1)
    i_max = np.argmax(view, axis=1)

    r_index = np.repeat(np.arange(size), 2)
    c_index = np.sort(np.stack((i_min, i_max), axis=1)).ravel()

    return view[r_index, c_index]


def find_cutoff_target_by_percentile(wf: np.ndarray,
                                     percentile: int = 92) -> float:
    target = np.percentile(wf, percentile)
    return target


def find_steady_state_wf(wf: np.ndarray, value: float) -> np.ndarray:
    cutoff_location = np.argmax(wf >= value)
    return wf[cutoff_location:]


def find_steady_state_waveform_by_percentile(wf: np.ndarray,
                                             percentile: int = 92,
                                             accuracy: float = 0.99) -> \
        np.ndarray:
    '''
    Takes in a wf and finds the value that meets the {percentile} computation.
    Assumes the percentile value is the target value of the rail and calculates
    the -{accuracy} from that value.  Returns the WF that is first above that accuracy target.

    '''
    assert 0 < accuracy < 1, f"accuracy ({accuracy}) must be between 0 and 1"
    percentile_value = find_cutoff_target_by_percentile(wf=wf,
                                                        percentile=percentile)
    accuracy_value = percentile_value * accuracy

    ss_wf = find_steady_state_wf(wf=wf, value=accuracy_value)

    return ss_wf
