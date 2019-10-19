import math
import numpy as np

#Function to find index of list
def index_of(a,list):
    for i in range(0,len(list)):
        if list[i] == a:
            return i
    return -1

#Function to sort by values
def sort_by_values(list1, values):
    sorted_list = []
    while(len(sorted_list)!=len(list1)):
        if index_of(min(values),values) in list1:
            sorted_list.append(index_of(min(values),values))
        values[index_of(min(values),values)] = math.inf
    return sorted_list

def dominates(p, q, values, maximize=True):
    """ returns 1 if p dominates q and -1 if q dominates p.
        0 if neither dominates the other.
    """
    n_objectives = len(values[0])
    dominate_p = False
    dominate_q = False
    for i in range(n_objectives):
        v_p = values[p, i]
        v_q = values[q, i]
        if not maximize:
            v_p *= -1
            v_q *= -1

        if v_p > v_q:
            dominate_p = True

        elif v_p < v_q:
            dominate_q = True

    if dominate_p == dominate_q:
        # Both have the same values.
        return 0
    elif dominate_p:
        return 1
    else:
        return -1

def fast_non_dominated_sort(values, maximize=True):
    # values = np.array(list(zip(values1, values2)))
    """ Function to carry out NSGA-II's fast non dominated sort """
    n_individual, n_objectives = values.shape
    dominated_by = [[] for _ in range(n_individual)]
    front = [[]]
    domination_count = np.zeros(n_individual, dtype='i')
    rank = np.zeros(n_individual, dtype='i')

    for p in range(n_individual):
        for q in range(n_individual):
            domination = dominates(p, q, values, maximize)
            if domination == 1:
                dominated_by[p].append(q)
            elif (domination == -1):
                domination_count[p] += 1
        if domination_count[p] == 0:
            rank[p] = 0
            front[0].append(p)

    i = 0
    while front[i]:
        Q = []
        for p in front[i]:
            for q in dominated_by[p]:
                domination_count[q] -= 1
                if domination_count[q] == 0:
                    rank[q] = i + 1
                    if q not in Q:
                        Q.append(q)
        i += 1
        front.append(Q)

    return front[:-1]

def crowding_distance(values1, values2, front):
    distance = [0 for i in range(0,len(front))]
    sorted1 = sort_by_values(front, values1[:])
    sorted2 = sort_by_values(front, values2[:])
    distance[0] = 4444444444444444
    distance[len(front) - 1] = 4444444444444444
    for k in range(1,len(front)-1):
        distance[k] += (values1[sorted1[k+1]] - values1[sorted1[k-1]])/(max(values1)-min(values1))
    for k in range(1,len(front)-1):
        distance[k] += (values2[sorted2[k+1]] - values2[sorted2[k-1]])/(max(values2)-min(values2))
    return distance

def crowding_distance(values, front):
    n_individual, n_objectives = values.shape
    distance = np.zeros(len(front))
    distance[0] = 99999999999999
    distance[len(front) - 1] = 99999999999999
    for i in range(n_objectives):
        V = values[:, i].tolist()
        sorted1 = sort_by_values(front, V[:])
        for k in range(1, len(front)-1):
            distance[k] += (V[sorted1[k+1]] - V[sorted1[k-1]])/(max(V)-min(V))
    return distance
