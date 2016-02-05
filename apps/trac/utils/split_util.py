def format_total_seconds(raw_time):
    """Take a total time in seconds and convert to 'hh:mm:ss.f'
    format.
    """
    minutes, seconds = divmod(raw_time, 60)
    hours, minutes = divmod(minutes, 60)
    hours = str(int(hours)) + ':' if hours > 0 else ''
    return '{}{:02d}:{:06.3f}'.format(hours, int(minutes), seconds)
