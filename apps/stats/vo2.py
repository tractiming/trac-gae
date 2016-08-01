import math


def calc_vo2(distance, time):
    """Calculate VO2 max based on a race result.

    Taken from Daniels and Gilbert. See, for example:
    * http://www.simpsonassociatesinc.com/runningmath1.htm
    * "The Conditioning for Distance Running -- the Scientific Aspects"

    Parameters
    ----------
    distance : float
        Race distance in meters.
    time : float
        Race result in seconds.

    Returns
    -------
    vo2_max : float
        Estimated VO2 max.
    """

    minutes = time/60.0
    velocity = distance/minutes
    percent_max = (0.8 + 0.1894393*math.exp(-0.012778*minutes) +
                   0.2989558*math.exp(-0.1932605*minutes))
    vo2 = (-4.60 + 0.182258*velocity + 0.000104*pow(velocity, 2))
    return vo2/percent_max


def predict_from_vo2(vo2_max, distance, tolerance=1e-5, max_iter=250):
    """Predict the result of a race based on a VO2 max.

    This is a root-finding problem: vo2_max = f(distance, time), solved for
    time given vo2_max and distance. Note that we are writing a pure python
    implementation because scipy is not supported on GAE.

    Parameters
    ----------
    vo2_max : int
        Measured VO2 max.
    distance : float
        Distance in meters to predict a result for.
    tolerance : float
        Numerical tolerance on solution. Stop when normalized step size is
        less than this amount.
    max_iter : int
        Maximum number of iterations. Raises a RuntimeError if this value
        is exceeded.

    Returns
    -------
    float
        Predicted race result in seconds.
    """
    h = 0.001
    vo2_f = lambda x: calc_vo2(distance, x) - vo2_max
    dvo2_f = lambda x: (vo2_f(x+h) - vo2_f(x))/h
    t0 = (distance/1000.0)*3*60  # Initial guess is calculated at 3 min/km.

    for _ in xrange(max_iter):
        t1 = t0 - vo2_f(t0)/dvo2_f(t0)
        if abs(t1 - t0)/abs(t1) < tolerance:
            return t1
        t0 = t1
    raise RuntimeError('Failed to converge')
