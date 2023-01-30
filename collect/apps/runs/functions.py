from math import acos, cos, radians, sin


def distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance between two points.

    Parameters:
        lat1, lon1, lat2, lon2: float
            Position in degrees

    Returns: int
        Distance in meters
    """
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    return round(
        6_371_000. * acos(
            sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2)
        )
    )


def time_to_next_display(next_, this):
    """Calculate time difference between the two dates to be displayed in the measurements table.

    Parameters:
        next_, this: datetime

    Returns: str
    """
    diff = round((next_ - this).total_seconds())  # s

    sec = diff % 60
    diff //= 60  # min
    min_ = diff % 60
    diff //= 60  # hour
    hour = diff % 24
    diff //= 24
    day = diff

    ret = f'{day}d ' if day else ''
    ret += f'{hour:02d}h ' if hour or day else ''
    ret += f'{min_:02d}m {sec:02d}s'
    return ret
