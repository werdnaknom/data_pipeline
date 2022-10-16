import typing as t
from pathlib import Path

import matplotlib.pyplot as plt
from app.shared.Requests.requests import ValidRequestObject

class PlotRequestObject(ValidRequestObject):
    num_plots:int = 0
    share_x = False
    axes: None
    entity_list: list = None

    def __init__(self, axes, entities):
        self.entity_list=entities
        self.axes = axes



class Plotter(object):
    base_directory: Path


    def plot(self, request_object: PlotRequestObject) -> None:
        raise NotImplementedError