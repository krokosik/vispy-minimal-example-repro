import pyqtgraph as pg
from pyqtgraph.examples.utils import FrameCounter
from pyqtgraph.Qt import QtCore, QtWidgets

from data_source import data_source

initial_data = data_source.ds.get_data()

class MyMainWindow(QtWidgets.QMainWindow):
    closing = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ds = data_source.ds

        self.setWindowTitle("Wavefunction Plotter")

        cw = pg.GraphicsLayoutWidget()
        self.setCentralWidget(cw)

        self.view = cw.addPlot(
            *(0, 0, 1, 1),
            title="Wavefunction Squared",
            enableMenu=False,
        )

        self.pcmi = pg.ImageItem(
            initial_data,
            colorMap=pg.colormap.get("inferno"),
            autoDownsample=True,
            enableAutoLevels=False,
        )
        self.view.setAspectLocked(True)
        self.view.addItem(self.pcmi)

        self.textitem = pg.TextItem(anchor=(1, 0))
        self.view.addItem(self.textitem)
        self.framecnt = FrameCounter()
        self.framecnt.sigFpsUpdate.connect(
            lambda fps: self.textitem.setText(f"FPS: {fps:.1f}")
        )

    def update(self, data):
        self.framecnt.update()
        self.pcmi.updateImage(data)
    
    def closeEvent(self, event):
        print("Closing main window!")
        self.closing.emit()
        return super().closeEvent(event)

app = pg.mkQApp("Waveplot Demo")
win = MyMainWindow()
win.show()

data_thread = QtCore.QThread(parent=win)
data_source.moveToThread(data_thread)

data_source.new_data.connect(win.update)
data_thread.started.connect(data_source.run_data_creation)
data_source.finished.connect(data_thread.quit)
win.closing.connect(data_source.stop_data)
data_thread.finished.connect(data_source.deleteLater)

win.show()
data_thread.start()
app.exec()

data_thread.quit()
data_thread.wait(5000)