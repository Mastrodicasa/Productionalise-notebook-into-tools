from read_file import ReadFile
from aggregate_data import AggregateData
from derive_insights import DeriveInsights


class ToClippd(object):

    def __init__(self):
        # self.read_file = ReadFile()
        self.aggregate_data = AggregateData()
        self.derive_insights = DeriveInsights()

    def process(self, source, rounds_file, terrain_file, course_file):
        read_file = ReadFile(source, rounds_file, terrain_file, course_file)
        read_file.load_data()

        data = self.aggregate_data.process(read_file.source,
                                           read_file.rounds_data,
                                           read_file.terrain_data,
                                           read_file.course_info)
        return self.derive_insights.process(data)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('PyCharm')
    cl = ToClippd()

    print(cl.process("arccos", "round.json", "terrain.json", "2020-12-03T12_20_14.080Z.json"))
    # print(cl.process("arccos", "round.json", "terrain.json", "2020-12-03T12_20_14.080Z.json"))
    # print(cl.process("arccos", "round.json", "terrain.json", "2020-12-03T12_20_14.080Z.json"))
    # print(cl.process("arccos", "round.json", "terrain.json", "2020-12-03T12_20_14.080Z.json"))
    # print(cl.process("arccos", "round.json", "terrain.json", "2020-12-03T12_20_14.080Z.json"))

    from pprint import pprint

    # pprint(vars(cl.read_file))
