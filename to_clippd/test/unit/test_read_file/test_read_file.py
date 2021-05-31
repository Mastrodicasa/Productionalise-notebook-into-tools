import unittest
from io import StringIO
from unittest.mock import patch

from read_file.read_file import ReadFile

PATH_TEST_ROUNDS = "test/unit/test_read_file/test_rounds.json"
PATH_TEST_TERRAIN = "test/unit/test_read_file/test_terrain.json"
PATH_TEST_COURSE = "test/unit/test_read_file/test_course.json"
NOT_EXIST_ROUNDS = "test/unit/test_read_file/DOES_NOT_EXIST.json"
WRONG_TEST_ROUNDS = "test/unit/test_read_file/to_test_when_wrong_input.txt"


class MyTestCase(unittest.TestCase):

    def test_load_data_when_missing_file(self):
        # When missing file, 'Not all the files exist.' should be printed
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            rf = ReadFile("arccos", NOT_EXIST_ROUNDS, PATH_TEST_TERRAIN, PATH_TEST_COURSE)
            rf.load_data()
            self.assertEqual(fakeOutput.getvalue().strip(), 'Not all the files exist.')

    def test_load_data_when_not_json(self):
        # When wrong input, 'Can\'t read file, bad format.' should be printed
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            rf = ReadFile("arccos", WRONG_TEST_ROUNDS, PATH_TEST_TERRAIN, PATH_TEST_COURSE)
            rf.load_data()
            self.assertEqual(fakeOutput.getvalue().strip(), 'Can\'t read file, bad format.')

    def test_private_var_after_load_data(self):
        rf = ReadFile("arccos", PATH_TEST_ROUNDS, PATH_TEST_TERRAIN, PATH_TEST_COURSE)
        rf.load_data()
        self.assertEqual(rf.rounds_data, [{'name': 'rounds'}])
        self.assertEqual(rf.terrain_data, [{'name': 'terrain'}])
        self.assertEqual(rf.course_info, {'name': 'course'})


if __name__ == '__main__':
    unittest.main()
