DEFAULT_DISTANCES = [100, 200, 400, 800, 1000, 1500,
                     1609, 2000, 3000, 5000, 10000]
DEFAULT_TIMES = [14.3, 27.4, 61.7, 144.2, 165, 257.5,
                 278.7, 356.3, 550.8, 946.7, 1971.9, ]
# Create your views here.
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def analyze(request):
    """
    Returns auto_edit splits.
    """

    #SETUP and parse dataList
    user = request.user
    idx = request.POST.get('id')
    ts = TimingSession.objects.get(id = idx)
    run = ts.individual_results()
    dataList = []
    for r in run:
        times = r[3]
        for index, item in enumerate(times):
            times[index] = float(item)
        name = r[0]
        dataList.append({'name': name, 'times': times})

    r_dict = stats.investigate(dataList)

    return Response (r_dict, status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def VO2Max(request):
    user = request.user
    if is_coach(user):
        result = []
        cp = Coach.objects.get(user = user)
        for athlete in cp.athletes.all():
            sum_VO2 = 0
            count = 0
            for entry in athlete.performancerecord_set.all():
                sum_VO2 += entry.VO2
                count += 1
            try:
                avg_VO2 = sum_VO2 / count
                if entry.interval == 'i':
                    avg_VO2 = avg_VO2 / .9
                else:
                    avg_VO2 = avg_VO2 / .8
                avg_VO2 = int(avg_VO2)
                vVO2 = 2.8859 + .0686 * (avg_VO2 - 29)
                vVO2 = vVO2 / .9
            except:
                avg_VO2 = 'None'
                vVO2 = 1
            #print athlete
            #print 'VO2: ' + str(avg_VO2)
            #print 'vVO2: ' + str(vVO2)
            #print '100m: ' + str(100/vVO2)
            #print '200m: ' + str(200/vVO2)
            #print '400m: ' + str(400/vVO2)
            #print '800m: ' + str(800/vVO2)
            #print '1000m: ' + str(1000/vVO2)
            #print '1500m: ' + str(1500/vVO2)
            #print '1600m: ' + str(1609/vVO2)
            #print '3000m: ' + str(3000/vVO2)
            #print '5000m: ' + str(5000/vVO2)
            #print '10000m: ' + str(10000/vVO2)
    elif is_athlete(user):
        ap = Athlete.objects.get(user = user)

    return HttpResponse(status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def est_distance(request):
    """
    Updates user individual time tables using distance prediction.
    """

    #SETUP and parse dataList
    user = request.user
    idx = request.POST.get('id')
    ts = TimingSession.objects.get(id = idx)
    run = ts.individual_results()
    dataList = []
    for r in run:
        times = r[3]
        for index, item in enumerate(times):
            times[index] = float(item)
        name = r[0]
        dataList.append({'name': name, 'times': times})

    #Analysis split_times is distance prediction, r_times is individual runner times, and r_dicts is auto_edit dictionary
    split_times, r_times = stats.calculate_distance(dataList)

    #Interpolate split_times to data in coach's table.
    #Predict the distance run.
    cp = Coach.objects.get(user=user)
    r = cp.performancerecord_set.all()
    distanceList = []
    for interval in split_times.keys():
        int_time = split_times[interval]
        time_delta = 1000000
        for row in r:
            if abs(int_time-row.time) < time_delta:
                time_delta = abs(int_time-row.time)
                selected = row.distance

        #validate distance predictions with coach and update coach table as necessary.
        var = raw_input("Did you run a "+str(selected)+" in "+str(interval-1)+" splits?")
        if var == 'no':
            var2 = raw_input("What was the distance? ")
            if var2 == 'none':
                continue
            else:
                length = int(var2)
                s = cp.performancerecord_set.get(distance = length)
                s.time = (s.time + int_time)/2
                s.save()
                distanceList.append({'Splits': interval-1, 'Distance': length})
        else:
            distanceList.append({'Splits': interval-1, 'Distance': selected})

    #update each individual runner tables with their own data for distances predicted above.
    for runner in r_times:
        return_dict = []
        accumulate_VO2 = 0
        count_VO2 = 0
        accumulate_t_VO2 = 0
        count_t_VO2 = 0
        username = runner['name']
        a_user = User.objects.get(id = username)
        ap = Athlete.objects.get(user = a_user)
        cp.athletes.add(ap)
        for results in runner['results']:
            splits = results['splits']
            times = results['times']
            for distance in distanceList:
                if splits == distance['Splits'] and times != 0:
                    try:
                        r= ap.performancerecord_set.get(distance= distance['Distance'], interval= results['interval'])
                        r.time = (r.time + times)/2
                        velocity = r.distance / (r.time/60)
                        t_velocity = r.distance/ (times/60)
                        t_VO2 = (-4.60 + .182258 * t_velocity + 0.000104 * pow(t_velocity, 2)) / (.8 + .1894393 * pow(2.78, (-.012778 * times/60)) + .2989558 * pow(2.78, (-.1932605 * times/60)))
                        VO2 = (-4.60 + .182258 * velocity + 0.000104 * pow(velocity, 2)) / (.8 + .1894393 * pow(2.78, (-.012778 * r.time/60)) + .2989558 * pow(2.78, (-.1932605 * r.time/60)))
                        VO2 = int(VO2)
                        t_VO2 = int(t_VO2)
                        r.VO2 = VO2
                        r.save()
                    except:
                        velocity = distance['Distance']/ (times/60)
                        VO2 = (-4.60 + .182258 * velocity + 0.000104 * pow(velocity, 2)) / (.8 + .1894393 * pow(2.78, (-.012778 * times/60)) + .2989558 * pow(2.78, (-.1932605 * times/60)))
                        VO2 = int(VO2)
                        t_VO2 = VO2
                        r = PerformanceRecord.objects.create(distance=distance['Distance'], time=times, interval= results['interval'], VO2= VO2)
                    accumulate_t_VO2 += t_VO2
                    count_t_VO2 += 1
                    accumulate_VO2 += VO2
                    count_VO2 += 1
                    ap.performancerecord_set.add(r)
        temp_t_VO2 = accumulate_t_VO2 / count_t_VO2
        temp_VO2 = accumulate_VO2 / count_VO2
        return_dict.append({"runner":runner, "CurrentWorkout":temp_t_VO2, "Average":temp_VO2})
    print return_dict
    #return auto_edits 
    return HttpResponse(status.HTTP_200_OK)
