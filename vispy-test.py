import numpy as np
from PyQt6 import QtWidgets, QtCore
from pyqtgraph.examples.utils import FrameCounter

from vispy.scene import SceneCanvas
from vispy.scene.visuals import Image
from vispy.app import use_app


from data_source import ds


class Controls(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout()

        self.fps_label = QtWidgets.QLabel("FPS: 0.0")
        layout.addWidget(self.fps_label)
        self.framecnt = FrameCounter()
        self.framecnt.sigFpsUpdate.connect(
            lambda fps: self.fps_label.setText(f"FPS: {fps:.1f}")
        )

        layout.addStretch(1)
        self.setLayout(layout)


class CanvasWrapper(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.canvas = SceneCanvas(size=(800, 600))
        self.grid = self.canvas.central_widget.add_grid()

        self.view_top = self.grid.add_view(0, 0, bgcolor="k")
        image_data = ds.get_data()
        self.image = Image(
            image_data,
            texture_format="auto",
            cmap="inferno",
            parent=self.view_top.scene,
        )

    def update_data(self, data):
        self.image.set_data(data)
        self.image.update()
        self.updated.emit()


class MyMainWindow(QtWidgets.QMainWindow):
    closing = QtCore.pyqtSignal()

    def __init__(self, canvas_wrapper: CanvasWrapper, *args, **kwargs):
        super().__init__(*args, **kwargs)

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout()

        self._controls = Controls()
        main_layout.addWidget(self._controls)
        self._canvas_wrapper = canvas_wrapper
        main_layout.addWidget(self._canvas_wrapper.canvas.native)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self._connect_controls()

    def _connect_controls(self):
        self._canvas_wrapper.updated.connect(self._controls.framecnt.update)

    def closeEvent(self, event):
        print("Closing main window!")
        self.closing.emit()
        return super().closeEvent(event)


class QDataSource(QtCore.QObject):
    """Object representing a complex data producer."""

    new_data = QtCore.pyqtSignal(np.ndarray)
    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ds = ds
        self._should_end = False
        self._image_data = ds.get_data()

    def run_data_creation(self):
        if self._should_end:
            print("Data source finishing")
            self.finished.emit()
            return

        image_data = self.ds.get_data()

        self.new_data.emit(image_data)
        QtCore.QTimer.singleShot(0, self.run_data_creation)

    def stop_data(self):
        print("Data source is quitting...")
        self._should_end = True


if __name__ == "__main__":
    app = use_app("pyqt6")
    app.create()

    canvas_wrapper = CanvasWrapper()
    win = MyMainWindow(canvas_wrapper)
    data_thread = QtCore.QThread(parent=win)
    data_source = QDataSource()
    data_source.moveToThread(data_thread)

    data_source.new_data.connect(canvas_wrapper.update_data)
    data_thread.started.connect(data_source.run_data_creation)
    data_source.finished.connect(data_thread.quit)
    win.closing.connect(data_source.stop_data)
    data_thread.finished.connect(data_source.deleteLater)

    win.show()
    data_thread.start()
    app.run()

    print("Waiting for data source to close gracefully...")
    data_thread.quit()
    data_thread.wait(5000)
