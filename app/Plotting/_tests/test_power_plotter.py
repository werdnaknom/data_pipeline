from basicTestCase.basic_test_case import BasicTestCase

from app.Plotting.power_plotting import PowerPlotter, PlotRequestObject

import matplotlib.pyplot as plt

plt.style.use('ggplot')


class PowerPlotterTestCase(BasicTestCase):

    def test_plot(self):
        wfs = self._helper_load_waveforms()
        voltage = wfs[0]
        current = wfs[1]

        # req = PlotRequestObject(axes=, entities=[voltage])

        fig, axes = plt.subplots(nrows=3, ncols=1, sharex='all')
        print(axes)

        for wf, ax in zip(wfs, axes):
            if wf.spec_max == None:
                wf.spec_max = 0


            xmin = wf.x_axis()[wf.steady_state_index()]
            xmax = wf.x_axis()[-1]
            ax.plot(wf.x_axis(), wf.y_axis())
            ax.hlines(y=wf.spec_max, xmin=xmin, xmax=xmax, colors='b',
                       linestyles='dashdot')

        plt.show()
