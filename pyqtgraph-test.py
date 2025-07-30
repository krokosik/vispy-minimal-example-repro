import pyqtgraph as pg
from pyqtgraph.examples.utils import FrameCounter
from pyqtgraph.Qt import QtCore

from data_source import ds


class StatePlot(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ds = ds

        self.setWindowTitle("Wavefunction Plotter")

        self.view = self.addPlot(
            *(0, 0, 1, 1),
            title="Wavefunction Squared",
            enableMenu=False,
        )

        self.pcmi = pg.ImageItem(
            self.ds.z,
            colorMap=pg.colormap.get("inferno"),
            autoDownsample=True,
            enableAutoLevels=False,
        )
        self.view.setAspectLocked(True)
        self.view.addItem(self.pcmi)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(0)

        self.textitem = pg.TextItem(anchor=(1, 0))
        self.view.addItem(self.textitem)
        self.framecnt = FrameCounter()
        self.framecnt.sigFpsUpdate.connect(
            lambda fps: self.textitem.setText(f"FPS: {fps:.1f}")
        )

    def update(self):
        self.framecnt.update()

        if self.ds is not None:
            self.pcmi.updateImage(self.ds.get_data())

app = pg.mkQApp("Waveplot Demo")
main_window = StatePlot()
main_window.show()
app.exec()