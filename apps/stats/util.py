from trac.models import Athlete
from models import PerformanceRecord
import stats_calcs as stats

def estimate_intervals(session):
    """
    Estimates intervals run with distance and number of splits in each interval
    """
    run = session.individual_results()
    dataList = []
    for r in run:
        times = r[3]
        for index, item in enumerate(times):
            times[index] = float(item)
        id = r[0]
        dataList.append({'id': id, 'times': times})

    #Analysis split_times is distance prediction, r_times is individual runner times, and r_dicts is auto_edit dictionary
    split_times, r_times = stats.calculate_distance(dataList)

    #Interpolate split_times to data in coach's table.
    #Predict the distance run.
    c = session.coach
    distances = c.performancerecord_set.values_list('distance',flat=True).distinct()
    intervals = []
    for s in split_times:
        int_time = s['time']
        time_delta = 1000000
        for d in distances:
            pr_set = c.performancerecord_set.filter(distance=d)
            avg_time = sum(pr_set.values_list('time',flat=True)) / pr_set.count()
            if abs(int_time-avg_time) < time_delta:
                time_delta = abs(int_time-avg_time)
                distance = d
        intervals.append({'num_splits': s['num_splits'], 'distance': distance, 'type': s['type']})

    return intervals

def record_performance(session, intervals):
    """ 
    Deletes and recreates PerformanceRecord objects associated with this session 
    based on intervals supplied.
    """
    # get the coach
    c = session.coach

    # remove old records
    session.performancerecord_set.all().delete()

    # get session results
    results = session.individual_results()

    # define start and end split indices
    start = 0
    end = 0
    for interval in intervals:
        distance = int(interval['distance'])
        interval_type = interval['type']
        end = start+int(interval['num_splits'])
        min_time = 1000000
        for r in results:
            # skip incomplete sets
            if end > len(r[3]):
                continue

            time = round(sum(r[3][start:end]), 3)
            velocity = distance / (time/60)
            VO2 = (-4.60 + .182258 * velocity + 0.000104 * pow(velocity, 2)) \
                    / (.8 + .1894393 * pow(2.78, (-.012778 * time/60)) + .2989558 * pow(2.78, (-.1932605 * time/60)))

            pr = PerformanceRecord.objects.create(timingsession=session, distance=distance, time=time, interval=interval_type, VO2=VO2)
            a = Athlete.objects.get(id=r[0])
            a.performancerecord_set.add(pr)

            # update min_time for this interval
            min_time = time if time < min_time else min_time

        # save min_time performance record for future reference
        pr = PerformanceRecord.objects.create(timingsession=session, distance=distance, time=min_time)
        c.performancerecord_set.add(pr)

        # update start split index
        start = end+1

    return 0
