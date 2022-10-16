import matplotlib.pyplot as plt

from .plotter import Plotter, PlotRequestObject


class PowerPlotter(Plotter):

    def plot(self, request_object:PlotRequestObject) -> None:
        """

        @param request_object:
        @return:
        """
        power_entity = request_object.power_entity
        spec_max = request_object.spec_max
        ax = request_object.axes

        #fig = plt.figure()
        x = power_entity.x_axis()
        xmin = x[power_entity.steady_state_index()]
        xmax = x[-1]

        ax.plot(power_entity.x_axis(), power_entity.y_axis())
        ax.hlines(y=spec_max, xmin=xmin, xmax=xmax, colors='r',
                   linestyles='dashdot',
                   label=f"Spec Max Limit Line ({spec_max}{power_entity.units})")
        ax.ylim(power_entity.min - 1, max(power_entity.max, spec_max) + 1)
        ax.legend()
        #plt.savefig(file_path, format="png")
        #plt.close(fig)

