import numpy as np
import pandas as pd
import sys
import os
import csv
from itertools import product
import fpdf
import math
import to_pdf

# Extract from inputs, store, and return student information, 
# seminar information, and reward weights 
def read_and_process(data_files, weights):
  
  output_data = data_files[0].copy()

  # The index of the row for each student in the original file
  student_idxs = np.where(data_files[0]['IW Type'] == 'Seminar')
  student_idxs = student_idxs[0]

  relevant_data = data_files[0][data_files[0]['IW Type'] == 'Seminar']
  students = np.array(relevant_data['NetID'])

  sem_info = data_files[1]
  seminars = np.array(sem_info['Seminar'])
  caps = np.array(sem_info['Capacity'])

  def pref_to_reward(rank):
    if rank == 1:
      return int(weights[0])
    elif rank == 2:
      return int(weights[1])
    elif rank == 3:
      return int(weights[2])
    elif rank > 3:
      return int(weights[3])
    else:
      return -1

  #Student Info
  st_progs = np.array(relevant_data['Program'])
  st_class = np.array(relevant_data['Sr/Jr/Soph'])
  
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
  
  return relevant_data, output_data, students, student_idxs, st_to_info, seminars, pref_to_reward, caps


#Gurobi Model for ILP problem
from gurobipy import *
def optimization(data, output_data, students, student_idxs, st_to_info, seminars, pref_to_reward_fn, caps, max_pref_weight, topk, semester, input_file_name = '', priorities = []):
  m = Model("Sem_Assignment")

  # Preference Matrix: cartesian product of students and seminars
  num_of_sems = len(seminars)
  num_of_stds = len(students)
  pref_matrix = list(product(students, seminars))

  # Preference map: maps (student, seminar) pair to ranking

  pref_map = {key: (num_of_sems + 1) for key in pref_matrix}

  start_indx = data.columns.get_loc("Seminar Choice #1")
  row = 0
  for netid in students:
    col = 1
    for choice in data.columns[start_indx:start_indx + num_of_sems]:

      #extract the ranking from the dataframe if a ranking was given to that seminar
      if(data.at[data.index[row], choice] != None):
        pref_map[str(netid), str(data.at[data.index[row], choice])] = col
      col += 1

    row += 1

  # Decision variables   
  x = m.addVars(students, seminars, vtype = GRB.BINARY, lb = 0, name = 'x')

  #Constraints
  for std in students:
    m.addConstr(quicksum(x[std, j] for j in seminars) == 1, '1_to_1')

  for i, sem in enumerate(seminars):
    m.addConstr(quicksum(x[i, sem] for i in students) <= caps[i], 'capacity')

  #Extra constraint for update, if previous assignments existed

  if 'Assignments' in data.columns:

    for i, std in enumerate(students):
      if data.at[student_idxs[i], 'Assignments'] != 'None':
        prev_assignment_pref = pref_map[std, data.at[student_idxs[i], 'Assignments']]

        m.addConstr(quicksum(pref_map[std, j] * x[std, j] for j in seminars) <= prev_assignment_pref, 'not_worse')

    else:
      for std in students:
        m.addConstr(quicksum(pref_map[std, j] * x[std, j] for j in seminars) <= int(topk), 'top_k_pref')
  

  def default_priority_weight(std):

    # AB students
    if st_to_info[std][0] == 1:
      return num_of_stds* int(max_pref_weight)
    
    # Senior BSE students in the spring semester
    if st_to_info[std][1] == 1 and semester == 'Spring':
      return num_of_stds* int(max_pref_weight)
    
    # All other students
    else:
      return 1
    
  def relaxed_priority_weight(std):
     # AB students
    if st_to_info[std][0] == 1:
      return int(priorities[0])
    
    # Senior BSE students in the spring semester
    if st_to_info[std][1] == 1 and semester == 'Spring':
      return int(priorities[1])
    
    # All other students
    else:
      return int(priorities[2])
  
  # Objective function
  if len(priorities) == 0:
    m.setObjective(quicksum(default_priority_weight(i) * pref_to_reward_fn(pref_map[i, j]) * x[i, j] for i in students for j in seminars), GRB.MAXIMIZE)
  else:
    m.setObjective(quicksum(relaxed_priority_weight(i) * pref_to_reward_fn(pref_map[i, j]) * x[i, j] for i in students for j in seminars), GRB.MAXIMIZE)
  
  m.optimize()

  #Check feasibility of solution
  if m.Status != GRB.OPTIMAL:
    return 0, '', '', 0, 0

  assignments = [None] * (output_data.shape[0])

  # calculating statistics

  AB_top = 0
  Sr_top = 0
  num_of_ABs = len([k for k,v in st_to_info.items() if v[0] == 1])
  num_of_Srs = len([k for k,v in st_to_info.items() if v[1] == 1])

  # number of students who got a seminar ranked ith on their list, where i is the index of 
  # the array
  stats = {}

  for i, std in enumerate(students):
    for j in seminars:
      if st_to_info[std][0] == 1 and x[std, j].x == 1 and pref_map[std, j] == 1:
        AB_top += 1
      
      if st_to_info[std][1] == 1 and x[std, j].x == 1 and pref_map[std, j] == 1:
        Sr_top += 1

      if x[std, j].x == 1:
          #get original index of student before removing non-seminar students
          idx = student_idxs[i]
          assignments[idx] = j

      for rank in range(num_of_sems):
        if pref_map[std, j] == rank+1 and x[std, j].x == 1:
          if (rank+1) in stats:
            stats[rank+1] += 1
          else:
            stats[rank+1] = 1
  
  # Put assignments into csv file
  output_data['Assignments'] = assignments

  output_file_name = '[ILP Assignments]' + str(input_file_name)
  output_data.to_csv(output_file_name)

  # Create statistics report
  report_file_name = 'Statistics Report.pdf'
  to_pdf.to_pdf(Sr_top, AB_top, num_of_ABs, num_of_Srs, stats, num_of_stds, semester, m.objval, report_file_name)

  return 1, output_file_name, report_file_name, math.log(m.objval), stats

def main(prefs, sems, w_1, w_2, w_3, w_4, topk, semester, file_name = '', priorities = []):
    data, output_data, students, student_idxs, st_to_info, seminars, pref_to_reward, cap = read_and_process([prefs, sems], [w_1, w_2, w_3, w_4])
    feasible, output_file_name,  report_file_name, obj_val, students_per_rank = optimization(data, output_data, students, student_idxs, st_to_info, seminars, pref_to_reward, cap, w_1, topk, semester, file_name, priorities)

    return feasible, output_file_name, report_file_name, obj_val, students_per_rank
if __name__ == "__main__":
    main()