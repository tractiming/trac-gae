def get_filter_constant(interval_distance, track_size):
    """Given a track size and distance, determine the minimum allowable
    split duration.
    """
    # Determine constant of impossible time for 400m off of distance.
    if interval_distance <= 200:
        constant = 20
    elif interval_distance > 200 and interval_distance <= 300:
        constant = 30
    elif interval_distance > 300 and interval_distance <= 400:
        constant = 50
    elif interval_distance > 400 and interval_distance <= 800:
        constant = 52
    elif interval_distance > 800 and interval_distance <= 1200:
        constant = 55
    elif  interval_distance > 1200 and interval_distance <= 1600:
        constant = 58
    else:
        constant = 59

    # Modify constant if on different sized track like 300m or 200m.
    # (Don't modify if 200s on 200m track.)
    if interval_distance > 200:
        constant = constant * (track_size/400.0)

    return constant

def get_ms(num):
    s = str(num).split('.')
    if len(s) == 1:
        return 0
    else:
        return int(s[1]+'0'*(3-len(s[1])))

def get_sec(num):
    s = str(num).split('.')
    if s[0] == '':
        return 0
    else:
        return int(s[0])

def get_sec_ms(num):
    return get_sec(num), get_ms(num)
