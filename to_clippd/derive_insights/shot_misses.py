import numpy as np


def get_bearing(lat1, lon1, lat2, lon2):
    """Function to get bearing between two points."""
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dLon = lon2 - lon1
    y = np.sin(dLon) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dLon)
    brng = np.rad2deg(np.arctan2(y, x))
    return np.where(brng < 0, brng + 360, brng)


def calculate_start_end_pin_angle(shot_distance, shot_start_distance_yards, shot_end_distance_yards):
    """Function to calculate short/long distances."""
    phi = np.where((shot_end_distance_yards > 0) & (shot_distance > 0),
                   np.arccos((shot_distance ** 2 + shot_end_distance_yards ** 2 - shot_start_distance_yards ** 2) / (2 * shot_distance * shot_end_distance_yards)),
                   0)
    return np.rad2deg(phi)


def calculate_miss_distance(miss_bearing_left_right, start_end_pin_angle, shot_end_distance_yards):
    """Function to calculate left/right distances."""
    alpha = np.where(
        miss_bearing_left_right > 180,
        180 - (360 - miss_bearing_left_right) - start_end_pin_angle,
        180 - miss_bearing_left_right - start_end_pin_angle
    )

    distance_left_right = np.where(start_end_pin_angle > 90,
                                   np.where(
                                       miss_bearing_left_right > 180,
                                       -shot_end_distance_yards * np.sin(np.radians(alpha)),
                                       shot_end_distance_yards * np.sin(np.radians(alpha))),
                                   np.where(
                                       miss_bearing_left_right > 180,
                                       -shot_end_distance_yards * np.sin(np.radians(180 - alpha)),
                                       shot_end_distance_yards * np.cos(np.radians(180 - alpha))
                                   ))

    distance_short_long = np.where(
        start_end_pin_angle > 90,
        -shot_end_distance_yards * np.cos(np.radians(alpha)),
        shot_end_distance_yards * np.cos(np.radians(180 - alpha))
    )

    return distance_left_right, distance_short_long
