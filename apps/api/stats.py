import math
import random
import bisect
import csv
import itertools

def calculate_distance(data_dict):
    """
    If the universal rest times and runners personal rest times line up, sum up all of the splits in between restpoints to find how
    far a runner runs given total time and number of splits. If only 2 splits, then it was likely a continuous workout so find total
    time. Take the minimum of each time per interval to interpolate from an average times per distance graph.
    """

    #SET global variables
    list_of_times = {}
    runner_specific_times=[]
    list_of_lists = []

    for runner in data_dict:
        runner['indices'] = []
        list_of_lists.append(runner['times'])

        result_temp, runner['average'], temp = calc_rest_interval(runner['times'])
        for element in temp:
            runner['indices'].append(runner['times'].index(element))

    rests = cross_check_runners(list_of_lists)
    print rests
    data = data_dict

    #for each runner, if there are <= 2 universal rest points, it is continuous, else it is interval.
    for runner in data:
        runner_specific_times.append({'name': runner['name'], 'results':[]})

        #for continuous, just sum up total times. In order to estimate distance use the min of all the runners times of this interval.
        #add all individual times to respective tables.
        if len(rests) <= 2 and rests[0] == 0 and rests[1] == (len(runner['times']) - 1):
            temp_sum = sum(runner['times'])
            if (rests[1]+1) in list_of_times.keys():
                list_of_times[rests[1]+1].append(temp_sum)
                for entry in runner_specific_times:
                    if entry['name'] == runner['name']:
                        entry['results'].append({'splits': rests[1], 'times': temp_sum, 'interval': 'c'})
            else:
                list_of_times[rests[1]+1] = [temp_sum]
                for entry in runner_specific_times:
                    if entry['name'] == runner['name']:
                        entry['results'].append({'splits': rests[1], 'times': temp_sum, 'interval': 'c'})
        else: 

            #filter through each interval between rest points. If athlete personal rest intervals line up, sum up the times in
            #between rest points. Take the minimum for distance prediction and all individual times are added to their own tables.
            for index in range(0, len(rests)):
                idx = rests[index]
                try:
                    idy = rests[index+1]
                except:
                    idy = rests[index]
                if idx in runner['indices']:
                    i = runner['indices'].index(idx)
                    try:
                        if runner['indices'][i+1] == idy:
                            temp = runner['times'][idx+1:idy]
                            temp_sum = sum(temp)
                            if (idy-idx) in list_of_times.keys():
                                list_of_times[idy-idx].append(temp_sum)
                                for entry in runner_specific_times:
                                    if entry['name'] == runner['name']:
                                        entry['results'].append({'splits': idy-idx-1, 'times': temp_sum, 'interval': 'i'})
                            else:
                                list_of_times[idy-idx] = [temp_sum]
                                for entry in runner_specific_times:
                                    if entry['name'] == runner['name']:
                                        entry['results'].append({'splits': idy-idx-1, 'times': temp_sum, 'interval': 'i'})
                        else:
                            continue
                    except:
                        continue

    #distance prediction
    for key in list_of_times.keys():
        average = min(i for i in list_of_times[key] if i>0)
        #average = average / len(list_of_times[key])
        list_of_times[key] = average
    print list_of_times
    return list_of_times, runner_specific_times

def create_list_of_lists(data_dict):
    """
    SubTool for Investigate: reset all rest_indices after new splits added to keep them all lined up.
    """
    list_of_lists = []
    for runner in data_dict:
        list_of_lists.append(runner['times'])
    return list_of_lists, cross_check_runners(list_of_lists)

def investigate(data_dict):
    """
    Auto-FIX: first loop through all times for runners to find individual rest indices using 
    median_deviation and then calc_rest_interval (both below). Using those append individual rest
    indices into data_dict and create universal_rest_indices list. After that begins point by point analysis.
    If there are enough rest times that are close to each other, then flag all absurdly large or small rests.
    If a point is in line with a universal rest, then probably a rest. If it is one in front of it, then it is
    probably a split and a rest. If the rest is nowhere near a universal rest, it is probably two splits or an
    unusual rest. The big analysis loop is ordered to go through every runners' first point, then every runners'
    other points in that order. It is to dynamically ensure that all the splits and rests eventually line up.
    """
    # FUNCTION VARIABLE DECLARATIONS
    useUniversalRestAvg = False
    list_of_lists = []
    count = 0
    return_dictionary = []
    rest_avg = []
    result_avg = []
    tot_result_avg = []


    for runner in data_dict:
        runner['indices'] = []
        list_of_lists.append(runner['times'])

        #This is to find universal rest medians
        result_temp, runner['average'], temp = calc_rest_interval(runner['times'])
        for element in temp:
            runner['indices'].append(runner['times'].index(element))
            rest_avg.append(element)
        for element in result_temp:
            result_avg.append(element)
            tot_result_avg.append(element)

        #Make length of longest list    
        for lists in list_of_lists:
            if len(lists) > count:
                count = len(lists)

        #Set median of running points as runner Average
        runner['average'] = round(median(result_avg), 3)
        result_avg = []

    #Create Universal Rest Indices
    rest_indices = cross_check_runners(list_of_lists)

    #Set rest points either normal or absurdly large or small
    rest_avg = sorted(rest_avg)
    avg = median(rest_avg)
    incorrect_rests = []
    correct_rests = []
    for element in rest_avg:
        if abs(element - avg) > 10:
            incorrect_rests.append(element)
        else:
            correct_rests.append(element)

    #If there are enough consistent rests, use Universal Rest Median as standard
    if len(correct_rests) > len(incorrect_rests):
        useUniversalRestAvg = True

    #If runner's average is absurd, make it the median of the total average.
    for runner in data_dict:
        if abs(runner['average'] - median(rest_avg)) < abs(runner['average'] - median(tot_result_avg)):
            runner['average'] = round(median(tot_result_avg), 3)


    #point by point analysis begins here.
    for idx in range(0, count):
        for runner in data_dict:
            #Set up the return dictionary
            if idx == 0:
                return_dictionary.append({'id': runner['name'], 'results':[]})
            try:

                #if idx is an index in the specific runner's rest points set, then investigate
                element = runner['indices'][runner['indices'].index(idx)]

                #This is if the workout is using Universal Rest Medians. If not skip this.
                if useUniversalRestAvg and runner['times'][element] in incorrect_rests:
                    #Check to see if runner's personal rest is too wacky.

                    #If 2 median splits fit, split it.
                    if abs((runner['times'][element]/2) - runner['average']) < 5:
                        half = round(runner['times'][element]/2, 3)
                        other_half = round(runner['times'][element] - half, 3)
                        runner['times'][element] = half
                        runner['times'].insert(element, other_half)
                        for entry in return_dictionary:
                            if entry['id'] == runner['name']:
                                entry['results'].append({'index': element, 'times': [runner['times'][element], runner['times'][element+1]]})
                        for jj in range(0, len(runner['indices'])):
                            if runner['indices'][jj] > element:
                                runner['indices'][jj] += 1

                    #OR its a split and a rest
                    elif runner['times'][element] - runner['average'] >= 30:
                        runner['times'][element] = round(runner['times'][element] - runner['average'], 3)
                        runner['times'].insert(element + 1, runner['average'])
                        for entry in return_dictionary:
                            if entry['id'] == runner['name']:
                                entry['results'].append({'index': element, 'times': [runner['times'][element], runner['times'][element+1]]})
                        for jj in range(0, len(runner['indices'])):
                                if runner['indices'][jj] > element:
                                    runner['indices'][jj] += 1
                    #OR its neither
                    else:
                        continue


                #If the rest is a universal rest do nothing
                elif element in rest_indices:
                    continue

                #If this personal rest is 1 away from a universal rest, It is a split and a rest
                elif (element + 1) in rest_indices:
                    if (runner['times'][element] - runner['average'])>=30:
                        runner['times'][element] = round(runner['times'][element] - runner['average'], 3)
                        runner['times'].insert(element, runner['average'])
                        for entry in return_dictionary:
                            if entry['id'] == runner['name']:
                                entry['results'].append({'index': element, 'times': [runner['times'][element], runner['times'][element+1]]})
                        for jj in range(0, len(runner['indices'])):
                            if runner['indices'][jj] > element:
                               runner['indices'][jj] += 1

                #If not either of those, it is a rest that does not belong, check to split if it is an even split if not it is a rest.
                else:
                    if abs((runner['times'][element]/2) - runner['average']) < 5:
                        half = round(runner['times'][element]/2, 3)
                        other_half = round(runner['times'][element] - half, 3)
                        runner['times'][element] = half
                        runner['times'].insert(element, other_half)
                        for entry in return_dictionary:
                            if entry['id'] == runner['name']:
                                entry['results'].append({'index': element, 'times': [runner['times'][element], runner['times'][element+1]]})
                        for jj in range(0, len(runner['indices'])):
                            if runner['indices'][jj] > element:
                                runner['indices'][jj] += 1

                #reset universal rest indices with updated values
                listy, rest_indices = create_list_of_lists(data_dict)
                for lists in listy:
                    if len(lists) > count:
                        count = len(lists)
            except:
                continue
    #returnCSV(data_dict)
    for runners in data_dict:
        for rests in rest_indices:
            if rests not in runners['indices']:
                runners['indices'].append(rests)
        runners['indices'] = sorted(runners['indices'])

    # correct offset indices
    for entry in return_dictionary:
        for i, correction in enumerate(entry['results']):
            correction['index'] -= i

    return return_dictionary

def cross_check_runners(data):
    """
    SubTool for Investigate: This lines up all runner rest indices and if the frequency of a certain index is high enough,
    add the index to a universal index list.
    """
    frequencies = {}
    count = 0
    for lst in data:
        rest = calc_rest_interval(lst)[2]
        indices = []
        for element in rest:
            if lst.index(element) in frequencies:
                frequencies[lst.index(element)] += 1
            else:
                frequencies[lst.index(element)] = 1
        for keys in frequencies.keys():
            count = 0
            for instance in data:
                if len(instance) > keys:
                    count += 1
            if frequencies[keys] >= (count/2):
                if keys-1 in indices:
                    ii = indices.index(keys-1)
                    if frequencies[keys] < frequencies[keys-1]:
                        keys = keys-1
                    indices[ii] = keys
                else:
                    indices.append(keys)
    indices = sorted(indices)
    return indices

def quantify(iterable, pred=bool):
    "Count how many times the predicate is true"
    return sum(itertools.imap(pred, iterable))

def calc_rest_interval(data):
    """
    SubTool for Investigate: after median_deviation filters through all the points run entropy on the remaining non_rest points.
    This will filter the close but could still be rest points.
    """
    lst, rest = median_deviation(data)
    average = median(data)
    st_entropy = entropy(lst)
    maximum = 0.0
    array = lst
    result = []
    for instance in lst:
        temp_array = list(array)
        temp_array.remove(instance)
        temp_array.insert(0, average)
        ne_entropy = entropy(temp_array)
        if ne_entropy < (st_entropy - st_entropy/5):
            rest.append(instance)
        else:
            result.append(instance)
    return result, average, rest

def standard_deviation(data):
    """
    This is standard deviation function.
    """
    try:
        middle = median(data)
        count = 0
        for instance in data:
            temp = instance - middle
            temp = math.pow(temp, 2)
            count += temp
        count = count / (len(data) - 1)
    except:
        count = 1
    result = math.sqrt(count)
    return result

def median_deviation(data):
    """
    This takes all the points and filters rests by determining as rests all points one standard deviation away from the median.
    """
    average = median(data)
    lst = data
    result = []
    rest = []
    sd = standard_deviation(data)
    for instance in lst:
        if instance < (average + sd) and instance > (average - sd):
            result.append(instance)
        else:
            rest.append(instance)
    return result, rest

def median(data):
    """
    This function is for median
    """
    li = sorted(data)
    if li < 1:
        return None
    if len(li) % 2 == 1:
        return li[((len(li)+1)/2)-1]
    else:
        return float(sum(li[(len(li)/2)-1:(len(li)/2)+1]))/2.0


def entropy(data):
    """
    Calculate informational entropy.
    """
    entropy = 0.0
    frequency = {}
    for instance in data:
        p_instance = int(round(instance/5) * 5)
        if p_instance in frequency:
            frequency[p_instance] += 1
        else:
            frequency[p_instance] = 1
        for freq in frequency.values():
            entropy += (-freq/len(data)) * math.log(float(freq)/len(data), 2)
    return entropy

def find_ne(a, x):
    """
    Find leftmost value greater than x
    """
    i = bisect.bisect_left(a, x)
    if i != len(a):
        return a[i]
    else:
        return a[len(a) -1]

def find_lt(a, x):
    """
    Find rightmost value less than x
    """
    i = bisect.bisect_left(a, x)
    if i:
        return a[i-1]
    return 0

#def returnCSV(data):
#    """
#    unused. For when I was testing the algorithm.
#    """
#    with open ('runners.csv', 'w') as fp:
#        writer = csv.writer(fp, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
#        writer.writerow([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28])
#        for row in data:
#            name = row['name']
#            lst = row['times']
#            writer.writerow(lst)
#        return 'finished'