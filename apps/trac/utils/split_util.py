def format_total_seconds(raw_time):
    """Take a total time in seconds and convert to 'hh:mm:ss.f'
    format.
    """
    minutes, seconds = divmod(raw_time, 60)
    hours, minutes = divmod(minutes, 60)
    hours = str(int(hours)) + ':' if hours > 0 else ''
    return '{}{:02d}:{:06.3f}'.format(hours, int(minutes), seconds)


def convert_units(distance, input_units, output_units):
    """Convert units of distance (miles, meters, and kilometers)."""
    conversion_factors = {
        'miles': {
            'meters': 1609.34,
            'kilometers': 1.60934,
        },
        'kilometers': {
            'meters': 1000.0,
            'miles': 0.621371,
        },
        'meters': {
            'miles': 0.000621371,
            'kilometers': 0.001
        }
    }
    allowed_units = conversion_factors.keys()
    if not all(x in allowed_units for x in (input_units, output_units)):
        raise ValueError('Invalid units provided. Should use "miles", '
                         '"kilometers", or "meters".')

    return distance*conversion_factors[input_units][output_units]
