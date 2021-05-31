import numpy as np


def expected_shots(x, lie, expected_shots_tee=None, expected_shots_fairway=None, expected_shots_rough=None, expected_shots_sand=None, expected_shots_green=None, **kwargs):
    if lie == "Tee":
        average_number_of_shots = expected_shots_tee(x)
    elif lie == "Fairway":
        average_number_of_shots = expected_shots_fairway(x)
    elif lie == "Rough":
        average_number_of_shots = expected_shots_rough(x)
    elif lie == "Sand":
        average_number_of_shots = expected_shots_sand(x)
    elif lie == "Green":
        average_number_of_shots = expected_shots_green(x)
    elif lie == "In The Hole":
        average_number_of_shots = 0
    else:
        average_number_of_shots = np.nan
    return average_number_of_shots


def strokes_gained_calculation(start_lie, start_distance, end_lie, end_distance, shot_number, next_shot_number, expected_shots, expected_shots_functions):
    start_average_number_of_shots = expected_shots(start_distance, start_lie, **expected_shots_functions)
    end_average_number_of_shots = expected_shots(end_distance, end_lie, **expected_shots_functions)
    if next_shot_number:
        strokes_gained = start_average_number_of_shots - end_average_number_of_shots - 1
    else:
        strokes_gained = (start_average_number_of_shots - end_average_number_of_shots
                          - (next_shot_number - shot_number))
    return strokes_gained
