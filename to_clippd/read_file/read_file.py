import json
from os.path import exists


class ReadFile(object):
    """
    Reads the json files coming from external sources and store the data as private variables.

    At the moment the class can only ready files from the source "arccos". If the files can't be read,
    the class will be returned with private variables equal to None.

    Attributes:
        source: Name of the external source
        rounds_file: Name of the file containing information about the rounds
        terrain_file: Name of the file containing information about the terrain
        course_file: Name of the file containing information about the course
        rounds_data: Array with the rounds data
        terrain_data: Array with the terrain data
        course_info: Dict with course data
    """

    def __init__(self, source, rounds_file, terrain_file, course_file):
        """Inits ReadFile"""
        self.source = source
        self.rounds_file = rounds_file
        self.terrain_file = terrain_file
        self.course_file = course_file
        self.rounds_data = None
        self.terrain_data = None
        self.course_info = None

    def load_data(self):
        """Reads the 3 files and store the data as private variables"""
        # In case loading changes with different platforms
        # Check if all the files exist
        files_exists = all([exists(self.rounds_file), exists(self.terrain_file), exists(self.course_file)])
        if not files_exists:
            print("Not all the files exist.")
        else:
            # In case the loading changes with different sources
            if self.source == "arccos":
                try:
                    with open(self.rounds_file) as f:
                        self.rounds_data = [json.load(f)]
                    with open(self.terrain_file) as f:
                        self.terrain_data = [json.load(f)]
                    with open(self.course_file) as f:
                        self.course_info = json.load(f)
                # if the files are not json
                except json.JSONDecodeError as j_e:
                    print('Can\'t read file, bad format.')
                except Exception as e:
                    print("Can't read file", e)
