import math

import numpy as np

from . import Baseproblem
from .Baseproblem import QUBO


class PortfolioOptimization(QUBO):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.__checkParams()
        self.risk = self.params.get("risk")
        self.budget = self.params.get("budget")
        self.params["k"] = self.budget
        self.cov_matrix = self.params.get("cov_matrix")
        self.exp_return = self.params.get("exp_return")
        self.penalty = self.params.get("penalty", 0.0)
        self.N_qubits = len(self.exp_return)

        self.params['N_qubits'] = self.N_qubits

        # Reformulated as a QUBO
        # min x^T Q x + c^T x + b
        # Writing Q as lower triangular matrix since it otherwise is symmetric
        Q = self.risk * np.tril(
            self.cov_matrix + np.tril(self.cov_matrix, k=-1)
        ) + self.penalty * (
            np.eye(self.N_qubits)
            + 2 * np.tril(np.ones((self.N_qubits, self.N_qubits)), k=-1)
        )
        c = -self.exp_return - (
            2 * self.penalty * self.budget * np.ones_like(self.exp_return)
        )
        b = self.penalty * self.budget * self.budget

        self._init_QUBO(Q=Q, c=c, b=b)

    def cost_nonQUBO(self, string, penalize=True):
        risk = self.params.get("risk")
        budget = self.params.get("budget")
        cov_matrix = self.params.get("cov_matrix")
        exp_return = self.params.get("exp_return")
        penalty = self.params.get("penalty", 0.0)

        x = np.array(list(map(int, string)))
        cost = risk * (x.T @ cov_matrix @ x) - exp_return.T @ x
        if penalize:
            cost += penalty * (x.sum() - budget) ** 2

        return -cost

    def isFeasible(self, string):
        x = self.__str2np(string)
        constraint = np.sum(x) - self.params.get("budget")
        return math.isclose(constraint, 0, abs_tol=1e-7)


    def __checkParams(self):
        # we require the following params:
        for key in ["risk", "budget", "cov_matrix", "exp_return"]:
            assert key in self.params, "missing required parameter " + key

    def __str2np(self, s):
        x = np.array(list(map(int, s)))
        assert len(x) == len(self.params.get("exp_return")), (
            "bitstring  "
            + s
            + " of wrong size. Expected "
            + str(len(self.params.get("exp_return")))
            + " but got "
            + str(len(x))
        )
        return x