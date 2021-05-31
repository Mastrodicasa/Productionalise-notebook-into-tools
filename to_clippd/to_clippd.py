from aggregate_data import AggregateData
from derive_insights import DeriveInsights
from map_to_clippd import MapToClippd
from read_file import ReadFile


class ToClippd(object):
    """
    Takes 3 files and their source and turn them into one Clippd Dataframe.

    Attributes:
        aggregate_data: An instance of AggregateData
        derive_insights: An instance of DeriveInsights
        map_to_clippd: An instance of MapToCLippd
    """
    def __init__(self):
        self.aggregate_data = AggregateData()
        self.derive_insights = DeriveInsights()
        self.map_to_clippd = MapToClippd()

    def process(self, source, rounds_file, terrain_file, course_file):
        """
        Takes 3 files and their source and turn them into one Clippd Dataframe.

        Args:
            source: Name of the external source
            rounds_file: Name of the file containing information about the rounds
            terrain_file: Name of the file containing information about the terrain
            course_file: Name of the file containing information about the course
        Returns:
            None if there is any problem with any of the files
            None if the source is not arccos
            (dataframe) Clippd Dataframe with all the data loaded
        """
        # A new ReadFile object is created at each call to process. Why?
        # Because if not and 2 consecutive calls are made, and the second can't load correctly certain files,
        # it will use the files from the first call. To avoid that, a new object is created each time.
        read_file = ReadFile(source, rounds_file, terrain_file, course_file)
        read_file.load_data()

        data = self.aggregate_data.process(read_file.rounds_data,
                                           read_file.terrain_data,
                                           read_file.course_info)
        data = self.derive_insights.process(data)
        return self.map_to_clippd.process(source, data)


if __name__ == '__main__':
    cl = ToClippd()
    print(cl.process("arccos", "round.json", "terrain.json", "2020-12-03T12_20_14.080Z.json"))
