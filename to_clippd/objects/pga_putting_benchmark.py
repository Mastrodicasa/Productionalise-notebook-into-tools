class PGAPuttingBenchmark(object):
    def __init__(self, distance, one_putt, two_putt, three_putt, expected_putts):
        self.distance = distance  # feet
        self.one_putt = one_putt
        self.two_putt = two_putt
        self.three_putt = three_putt
        self.expected_putts = expected_putts
