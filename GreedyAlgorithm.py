import heapq
import numpy as np
from itertools import product
import pandas as pd
import math
import fpdf
import pickle
import to_pdf

def algorithm(data_files, semester, file_name=''):

    output_data = data_files[0].copy()
    indeces = np.where(data_files[0]['IW Type'] == 'Seminar')
    indeces = indeces[0]
    relevant_data = data_files[0][data_files[0]['IW Type'] == 'Seminar']
    students = np.array(relevant_data['NetID'])
    student_to_idx = {key: (indeces[i]) for i, key in enumerate(students)}
 
    np.random.shuffle(students)

    sem_info = data_files[1]
    seminars = np.array(sem_info['Seminar'])
    caps = np.array(sem_info['Capacity'])

    num_of_stds = len(students)
    num_of_sems = len(seminars)

    #Student Info
    st_progs = np.array(relevant_data['Program'])
    st_class = np.array(relevant_data['Sr/Jr/Soph'])

    def pref_to_reward(rank):
        if rank == 1:
            return 100
        elif rank == 2:
            return 30
        elif rank == 3:
            return 20
        elif rank > 3:
            return 0
        else:
            return -1
    
    
    #st_to_info[student] = [isAB, isBSE]

    st_to_info = {}
    for i, student in enumerate(students):

        student_info = []
        if st_progs[i] == 'A.B.':
            student_info.append(1)
        else:
            student_info.append(0)

        if st_class[i] == 'Sr':
            student_info.append(1)
        else:
            student_info.append(0)
        
        st_to_info[student] = student_info

    def priority_weight(std):
        #if spring semester, add one more
        if st_to_info[std][0] == 1:
            return num_of_stds*100
        
        if st_to_info[std][1] == 1 and semester == 'Spring':
            return num_of_stds*100
        
        else:
            return 1

    # Preference Matrix: cartesian product of students and seminars   
    pref_matrix = list(product(students, seminars))
   

    # Preference map: maps (student, seminar) pair to ranking

    pref_map = {key: (num_of_sems + 1) for key in pref_matrix}

    start_indx = relevant_data.columns.get_loc("Seminar Choice #1")
    row = 0

    for i, netid in enumerate(students):

        col = 1
        for choice in relevant_data.columns[start_indx:start_indx + num_of_sems]:

            #extract the ranking from the dataframe if a ranking was given to that seminar
            if(relevant_data.at[relevant_data.index[row], choice] != None):
                pref_map[str(netid), str(relevant_data.at[relevant_data.index[row], choice])] = col
            col += 1
     
        row += 1
 

    sorted_stds = []
    
    # Sort students based on priority
    for student in students:
        weight = priority_weight(student)
        heapq.heappush(sorted_stds, (weight, student))

    spots_remaining = np.array(caps)
    assignments_dict = {}
    seminars_remaining = np.array(seminars)

    # Assign every student in order the highest ranking seminar given remaining open seminars
    for i in range(len(sorted_stds)):
       
       student = heapq.heappop(sorted_stds)[1]
       rankings = [pref_map[student, j] for j in seminars_remaining]
       best_sem_position = np.argmin(rankings)
       assignment_rank = rankings[best_sem_position]
       assignments_dict[student] = (seminars_remaining[best_sem_position], assignment_rank)

       # update seminar spots left
       spots_remaining[best_sem_position] -= 1
       if spots_remaining[best_sem_position] == 0:
          seminars_remaining = np.delete(seminars_remaining, best_sem_position)
          spots_remaining = np.delete(spots_remaining, best_sem_position)
    

    assignments = [None] * (output_data.shape[0])
   
    output_file_name = '[Greedy Assignments]' + str(file_name)
    
    # populate assignments list
    stats = {}
    for key in assignments_dict.keys():
        val = assignments_dict.get(key)

        idx = student_to_idx[key]
        assignments[idx] = val[0]
        if val[1] in stats:
            stats[val[1]] += 1
        else:
            stats[val[1]] = 1

        
    # Put assignments into csv file
    output_data['Assignments'] = assignments
    output_data.to_csv(output_file_name)

    # calculate statistics
    num_of_ABs = len([k for k,v in st_to_info.items() if v[0] == 1])
    num_of_Srs = len([k for k,v in st_to_info.items() if v[1] == 1])
    AB_top = len([k for k,v in assignments_dict.items() if (v[1] == 1 and st_to_info[k][0] == 1)])
    Sr_top = len([k for k,v in assignments_dict.items() if (v[1] == 1 and st_to_info[k][1] == 1)])

    # calculate objective function value
    obj_val = 0
    for std in assignments_dict.keys():
        obj_val += priority_weight(std)*pref_to_reward(assignments_dict.get(std)[1])
    
    # Create statistics report
    report_file_name = 'Statistics Report.pdf'
    to_pdf.to_pdf(Sr_top, AB_top, num_of_ABs, num_of_Srs, stats, num_of_stds, semester, obj_val, report_file_name)
   
    return stats, math.log(obj_val), output_file_name, report_file_name
    
def main():
    # testing

    print('********************Fall 2016*********************')
    std_info = pd.read_csv('IW Test Data/Fall 2016/Fall 2016 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Fall 2016/Fall 2016 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Fall')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Fall 2017*********************')
    std_info = pd.read_csv('IW Test Data/Fall 2017/Fall 2017 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Fall 2017/Fall 2017 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Fall')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Fall 2018*********************')
    std_info = pd.read_csv('IW Test Data/Fall 2018/Fall 2018 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Fall 2018/Fall 2018 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Fall')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Fall 2019*********************')
    std_info = pd.read_csv('IW Test Data/Fall 2019/Fall 2019 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Fall 2019/Fall 2019 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Fall')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Fall 2020*********************')
    std_info = pd.read_csv('IW Test Data/Fall 2020/Fall 2020 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Fall 2020/Fall 2020 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Fall')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Fall 2021*********************')
    std_info = pd.read_csv('IW Test Data/Fall 2021/Fall 2021 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Fall 2021/Fall 2021 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Fall')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Spring 2016*********************')
    std_info = pd.read_csv('IW Test Data/Spring 2016/Spring 2016 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Spring 2016/Spring 2016 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Spring')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Spring 2017*********************')
    std_info = pd.read_csv('IW Test Data/Spring 2017/Spring 2017 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Spring 2017/Spring 2017 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Spring')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Spring 2018*********************')
    std_info = pd.read_csv('IW Test Data/Spring 2018/Spring 2018 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Spring 2018/Spring 2018 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Spring')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Spring 2019*********************')
    std_info = pd.read_csv('IW Test Data/Spring 2019/Spring 2019 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Spring 2019/Spring 2019 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Spring')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Spring 2020*********************')
    std_info = pd.read_csv('IW Test Data/Spring 2020/Spring 2020 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Spring 2020/Spring 2020 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Spring')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Spring 2021*********************')
    std_info = pd.read_csv('IW Test Data/Spring 2021/Spring 2021 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Spring 2021/Spring 2021 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Spring')
    print('stats: ', stats)
    print('Objective value: ', objval)

    print('********************Spring 2022*********************')
    std_info = pd.read_csv('IW Test Data/Spring 2022/Spring 2022 - Sign Up Information.csv')
    sem_info = pd.read_csv('IW Test Data/Spring 2022/Spring 2022 - Seminars.csv')
    stats, objval,_,_ = algorithm([std_info, sem_info], 'Spring')
    print('stats: ', stats)
    print('Objective value: ', objval)
    
if __name__ == "__main__":
    main()


    