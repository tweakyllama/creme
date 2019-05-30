import collections

from .. import base
from .. import stats


class PCA(base.Transformer):
    """

    """
    def __init__(self, n_components):
        self.n_components = n_components
        self.means = collections.defaultdict(stats.Mean)
        self.variances = collections.defaultdict(stats.Var)

    def fit_one(self, x, y=None):

        for i, xi in x.items():
            self.means[i].update(xi)
            self.variances[i].update(xi)

        return self

    def transform_one(self, x):
        pass
