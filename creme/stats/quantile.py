from . import base
from math import copysign


class Quantile(base.RunningStatistic):
    """Compute the running quantile.
    We used the P-square algorithm to calculate the percentile.
    We based the code on LiveStat implementation [2].

    Attributes:
        percentile (float): Percentile you want compute.

    Example:


        >>> from creme import stats
        >>> import numpy as np

        >>> np.random.seed(42*1337)
        >>> mu, sigma = 0, 1 
        >>> s = np.random.normal(mu, sigma, 1337*42)

        >>> median = stats.Quantile(0.5)
        >>> for x in s:
        ...    _ = median.update(x)

        >>> print(f'The estimated value of the 50th (median) percentile is {median.get():.4f}')
        The estimated value of the 50th (median) percentile is -0.0006
        >>> print(f'The real value of the 50th (median) percentile is {np.median(s):.4f}')
        The real value of the 50th (median) percentile is -0.0002
        
        >>> percentile_17 = stats.Quantile(0.17)
        >>> for x in s:
        ...    _ = percentile_17.update(x)

        >>> print(f'The estimated value of the 17th percentile is  {percentile_17.get():.4f}')
        The estimated value of the 17th percentile is  -0.9522
        >>> print(f'The real value of the 17th percentile is {np.percentile(s,17):.4f}')
        The real value of the 17th percentile is -0.9510


    References:

    - `The P2 Algorithm for Dynamic Statistical Computing Calculation of Quantiles and Editor Histograms Without Storing Observations  <https://www.cse.wustl.edu/~jain/papers/ftp/psqr.pdf>`_
    - `Python implementation <https://github.com/cxxr/LiveStats/blob/master/livestats/livestats.py>`_

    """
    def __init__(self, percentile=0.5):

        if 0 < percentile < 1:
            self.percentile = percentile
        else:
            raise ValueError('percentile must be between 0 and 1 excluded')


        self.desired_marker_position = [0, self.percentile/2,
                   self.percentile, (1 + self.percentile)/2, 1]
        self.marker_position = [1, 1 + 2*self.percentile, 1 + 4 *
                     self.percentile, 3 + 2*self.percentile, 5]
        self.position = list(range(1, 6))
        self.heights = []
        self.heights_sorted = False


    @property
    def name(self):
        return 'quantile'

    def _find_k(self,x):
        if x < self.heights[0]:
            self.heights[0] = x
            k = 1
        else:
            for i in range(1, 5):
                if self.heights[i - 1] <= x and x < self.heights[i]:
                    k = i
                    break
            else:
                k = 4
                if self.heights[-1] < x:
                    self.heights[-1] = x
        return k 

    @classmethod
    def _compute_P2(cls,qp1, q, qm1, d, np1, n, nm1):

        d = float(d)
        n = float(n)
        np1 = float(np1)
        nm1 = float(nm1)

        outer = d / (np1 - nm1)
        inner_left = (n - nm1 + d) * (qp1 - q ) / (np1 - n)
        inner_right = (np1 - n - d) * (q - qm1 ) / (n - nm1)

        return q + outer * (inner_left + inner_right)
    
    def _adjust(self):

        for i in range(1, 4):
            n = self.position[i]
            q = self.heights[i]

            d = self.marker_position[i] - n

            if (d >= 1 and self.position[i + 1] - n > 1) or (d <= -1 and self.position[i - 1] - n < -1):
                d = int(copysign(1,d))

                qp1 = self.heights[i + 1]
                qm1 = self.heights[i - 1]
                np1 = self.position[i + 1]
                nm1 = self.position[i - 1]

                qn = self._compute_P2(qp1, q, qm1, d, np1, n, nm1)

                if qm1 < qn and qn < qp1:
                    self.heights[i] = qn
                else:
                    self.heights[i] = q + d * (self.heights[i + d] - q) / (self.position[i + d] - n)

                self.position[i] = n + d

        return self

    def update(self, x):
        # Initialisation
        if len(self.heights) != 5:
            self.heights.append(x)

        else : 
            if self.heights_sorted == False:
                self.heights.sort()
                self.heights_sorted = True
            
            #Find cell k such that qk < Xj <= qk+i and adjust extreme values (q1 and q) if necessary
            k = self._find_k(x)

            # increment all positions greater than k
            self.position = [j if i < k else j + 1 for i,j in enumerate(self.position)]
            self.marker_position = [x + y for x,y in zip(self.marker_position, self.desired_marker_position)]
            # Adjust heights of markers 2-4 if necessary
            self._adjust()
        return self


    def get(self):
        if self.heights_sorted:
            return self.heights[2]
        else:
            self.heights.sort()
            l = len(self.heights)
            return self.heights[int(min(max(l - 1, 0), l * self.percentile))]
