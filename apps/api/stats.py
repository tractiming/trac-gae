import math
import random
import bisect
import csv
import itertools

def calculate_distance(data_dict):
    list_of_times = {}
    rests, data, unused = investigate(data_dict)
    for runner in data:
        if runner['index'][0] in rests:
            temp = runner['times'][0:runner['index'][0]]
            temp_sum = sum(temp)
            list_of_times[runner['index'][0]] = [temp_sum]
        for index in range(0, len(rests)):
            idx = rests[index]
            try:
                idy = rests[index+1]
            except:
                idy = rests[index]
            if idx in runner['index']:
                i = runner['index'].index(idx)
                try:
                    if runner['index'][i+1] == idy:
                        temp = runner['times'][idx+1:idy]
                        temp_sum = sum(temp)
                        if (idy-idx) in list_of_times.keys():
                            list_of_times[idy-idx].append(temp_sum)
                        else:
                            list_of_times[idy-idx] = [temp_sum]
                    else:
                        continue
                except:
                    continue
    for key in list_of_times.keys():
        average = sum(list_of_times[key])
        average = average / len(list_of_times[key])
        list_of_times[key] = average
    return list_of_times

def create_list_of_lists(data_dict):
    list_of_lists = []
    for runner in data_dict:
        list_of_lists.append(runner['times'])
    return cross_check_runners(list_of_lists)

def investigate(data_dict):
    useUniversalRestAvg = False
    list_of_lists = []
    count = 0
    return_dictionary = []
    rest_avg = []
    result_avg = []
    tot_result_avg = []
    for runner in data_dict:
        runner['index'] = []
        list_of_lists.append(runner['times'])
        result_temp, runner['average'], temp = calc_rest_interval(runner['times'])
        for element in temp:
            runner['index'].append(runner['times'].index(element))
            rest_avg.append(element)
        for element in result_temp:
            result_avg.append(element)
            tot_result_avg.append(element)
        for lists in list_of_lists:
            if len(lists) > count:
                count = len(lists)
        runner['average'] = median(result_avg)
        result_avg = []
    rest_indices = cross_check_runners(list_of_lists)
    correct_rests, incorrect_rests = median_deviation(rest_avg)
    if (.3 * len(correct_rests)) > len(incorrect_rests):
        useUniversalRestAvg = True
    for runner in data_dict:
        if abs(runner['average'] - median(rest_avg)) < abs(runner['average'] - median(tot_result_avg)):
            runner['average'] = median(tot_result_avg)
    for idx in range(0, count):
        for runner in data_dict:
            if idx == 0:
                return_dictionary.append({'id': runner['name'], 'results':[]})
            try:
                element = runner['index'][runner['index'].index(idx)]
                prev_rest = find_lt(runner['index'], element)
                next_rest = find_ne(runner['index'], element)
                if element - prev_rest == next_rest - element:
                    likelihood = 1      # was previously used with random
                else:
                    likelihood = .7     # was previously used with random
                if useUniversalRestAvg and runner['times'][element] in incorrect_rests:
                    if abs((runner['times'][element]/2) - runner['average']) < 5:
                        runner['times'][element] = runner['times'][element]/2
                        runner['times'].insert(element, runner['times'][element])
                        for entry in return_dictionary:
                            if entry['id'] == runner['name']:
                                entry['results'].append({'index':element, 'times':[runner['times'][element], runner['times'][element+1]]})
                        for jj in range(0, len(runner['index'])):
                            if runner['index'][jj] > element:
                                runner['index'][jj] += 1
                    elif runner['times'][element] - runner['average'] >= 30:
                        runner['times'][element] = runner['times'][element] - runner['average']
                        runner['times'].insert(element + 1, runner['average'])
                        for entry in return_dictionary:
                            if entry['id'] == runner['name']:
                                entry['results'].append({'index':element, 'times':[runner['times'][element], runner['times'][element+1]]})
                        for jj in range(0, len(runner['index'])):
                                if runner['index'][jj] > element:
                                    runner['index'][jj] += 1
                    else:
                        continue
                elif element in rest_indices:
                    if (element + 1) in rest_indices:
                        if runner['times'][element] - runner['average'] >= 30:
                            runner['times'][element] = runner['times'][element] - runner['average']
                            runner['times'].insert(element, runner['average'])
                            for entry in return_dictionary:
                                if entry['id'] == runner['name']:
                                    entry['results'].append({'index':element, 'times':[runner['times'][element], runner['times'][element+1]]})
                            for jj in range(0, len(runner['index'])):
                                if runner['index'][jj] > element:
                                    runner['index'][jj] += 1
                elif (element + 1) in rest_indices:
                    if runner['times'][element] - runner['average'] >= 30:
                        runner['times'][element] = runner['times'][element] - runner['average']
                        runner['times'].insert(element, runner['average'])
                        for entry in return_dictionary:
                            if entry['id'] == runner['name']:
                                entry['results'].append({'index':element, 'times':[runner['times'][element], runner['times'][element+1]]})
                        for jj in range(0, len(runner['index'])):
                            if runner['index'][jj] > element:
                                runner['index'][jj] += 1
                else:
                    if abs((runner['times'][element]/2) - runner['average']) < 5:
                        runner['times'][element] = runner['times'][element]/2
                        runner['times'].insert(element, runner['times'][element])
                        for entry in return_dictionary:
                            if entry['id'] == runner['name']:
                                entry['results'].append({'index':element, 'times':[runner['times'][element], runner['times'][element+1]]})
                        for jj in range(0, len(runner['index'])):
                            if runner['index'][jj] > element:
                                runner['index'][jj] += 1
                    
                rest_indices = create_list_of_lists(data_dict)
            except:
                continue
    return return_dictionary

def cross_check_runners(data):
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
    return math.sqrt(count)

def median_deviation(data):
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
    li = sorted(data)
    if li < 1:
        return None
    if len(li) % 2 == 1:
        return li[((len(li)+1)/2)-1]
    else:
        return float(sum(li[(len(li)/2)-1:(len(li)/2)+1]))/2.0


def entropy(data):
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
    'Find leftmost value greater than x'
    i = bisect.bisect_left(a, x)
    if i != len(a):
        return a[i]
    else:
        return a[len(a) -1]

def find_lt(a, x):
    'Find rightmost value less than x'
    i = bisect.bisect_left(a, x)
    if i:
        return a[i-1]
    return 0

def returnCSV(data):
    with open ('runners.csv', 'w') as fp:
        writer = csv.writer(fp, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
        writer.writerow([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28])
        for row in data:
            name = row['name']
            lst = row['times']
            writer.writerow(lst)
        return 'finished'