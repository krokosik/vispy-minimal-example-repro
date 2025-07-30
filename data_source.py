from arc import CG, Wavefunction, AlkaliAtom, Ylm
import numpy as np
from arc import Rubidium87 as ATOM

type StateTuple = tuple[int, int, float, float]  # (n, l, j, mj)


class AtomDataSource(object):
    def __init__(self, atom: AlkaliAtom, n_points: int = 300, dt: float = 1e-12):
        self.atom = atom
        self.n_points = n_points
        self.dt = dt
        self.t = 0.0
        self.wf = None
        self.energies = None

    def set_states(self, states: list[StateTuple]):
        """
        Set the superposition of quantum states for the wavefunction.
        Precalculate the grid to save calculation time during plotting.

        :param states: List of tuples (n, l, j, mj) representing quantum states.
        """
        self.wf = Wavefunction(
            self.atom, states, np.repeat(np.sqrt(1 / len(states)), len(states))
        )
        self.t = 0.0

        nMax = 1
        for state in self.wf.basisStates:
            nMax = max(nMax, state[0])
        axisLength = 2.0 * 2.0 * nMax * (nMax + 15.0)

        self.x, self.y = np.meshgrid(
            np.linspace(-axisLength / 2.0, axisLength / 2.0, self.n_points),
            np.linspace(-axisLength / 2.0, axisLength / 2.0, self.n_points),
        )

        self.z = np.zeros((self.n_points, self.n_points), dtype=np.float64)
        self.theta = np.arctan2((self.x**2 + self.y**2) ** 0.5, 0)
        self.phi = np.arctan2(self.y, self.x)
        self.r = np.sqrt(self.x**2 + self.y**2)
        self.basisFrequencies = np.array(self.wf.basisFrequencies)
        self.precalcBasisWavefunctions = np.empty(
            (len(self.wf.basisStates), 2, *self.z.shape),
            dtype=np.complex128,
        )

        for i in range(len(self.wf.basisStates)):
            wfP, wfM = self._getSingleRtimesPsiSpherical(i)
            self.precalcBasisWavefunctions[i][0] = wfP
            self.precalcBasisWavefunctions[i][1] = wfM
            self.z += np.abs(wfP) ** 2 + np.abs(wfM) ** 2

    def get_data(self) -> np.ndarray:
        """
        Get the wavefunction data at the current time step.

        :return: Tuple (x, y, data) where x and y are the coordinates and data is the wavefunction squared.
        """
        if self.wf is None:
            raise ValueError("Wavefunction not set. Call set_states() first.")

        self.z = np.sum(
            np.abs(
                np.sum(
                    self.precalcBasisWavefunctions
                    * np.exp(-1j * self.basisFrequencies * self.t)[
                        :,
                        np.newaxis,
                        np.newaxis,
                        np.newaxis,
                    ],
                    axis=0,
                )
            )
            ** 2,
            axis=(0),
        )
        self.t += self.dt
        return self.z.copy().astype(np.float32)

    def _getSingleRtimesPsiSpherical(self, i: int):
        if self.wf is None:
            raise ValueError("Wavefunction not set. Call set_states() first.")

        wfElectronP = 0 + 0j  # electron spin +1/2
        wfElectronM = 0 + 0j  # electron spin -1/2

        state = self.wf.basisStates[i]
        l = state[1]  # noqa: E741
        j = state[2]
        mj = state[3]
        if abs(mj - 0.5) - 0.1 < l:
            wfElectronP += (
                CG(l, mj - 0.5, 0.5, +0.5, j, mj)
                * Ylm(l, mj - 0.5, self.theta, self.phi)
                * self.wf.basisWavefunctions[i](self.r)
                * self.wf.coef[i]
            )
        if abs(mj + 0.5) - 0.1 < l:
            wfElectronM += (
                CG(l, mj + 0.5, 0.5, -0.5, j, mj)
                * Ylm(l, mj + 0.5, self.theta, self.phi)
                * self.wf.basisWavefunctions[i](self.r)
                * self.wf.coef[i]
            )

        return wfElectronP, wfElectronM

atom = ATOM()

ds = AtomDataSource(atom, n_points=300, dt=1e-12)
ds.set_states(
    [
        (54, 3, 7 / 2, 7 / 2),
        (54, 2, 5 / 2, 5 / 2),
    ]
)