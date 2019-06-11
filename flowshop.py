#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import permutations
import numpy as np
from functools import lru_cache
from geneticFunctions import *


class Flowshop(object):
    """
    A class for initiaizing & solving a Permutation Flowshop Scheduling Problem
    """

    def __init__(self, data=None, nb_machines=2, nb_jobs=6):
        """[summary]

        Keyword Arguments:
            data {list} -- A 2D array of processing time on machines (default: {None})
            nb_machines {int} -- Number of machines for the given problem must be the number of rows of first param (default: {2})
            nb_jobs {[type]} -- Number of jobs for the given problem, must be equal to the number of columns of the data param. (default: {6})
        """

        self.nb_machines = nb_machines
        self.nb_jobs = nb_jobs
        if data is not None:
            self.data = data
        else:
            self.data = RandomFlowshop(
                self.nb_machines, self.nb_jobs).get_data()

    def solve_johnson(self):
        """Solves a permutation flowshop problem using johnson's rule for a permutation problem of 2 machines and N jobs 

        Raises:
            Exception: Raises exception when given a problem with more than 2 machines

        Returns:
            tuple -- returns a tuple containing the optimal sequence of scheduled jobs and a list of scheduled jobs on the 2 machines
        """
        if self.nb_machines != 2:
            raise Exception(
                "Johnson's algorithm only possible for a 2 machine problem"
            )
        # Build optimal sequence array
        machine_1_sequence = [j for j in range(
            self.nb_jobs) if self.data[0][j] <= self.data[1][j]]
        machine_1_sequence.sort(key=lambda x: self.data[0][x])
        machine_2_sequence = [j for j in range(
            self.nb_jobs) if self.data[0][j] > self.data[1][j]]
        machine_2_sequence.sort(key=lambda x: self.data[1][x], reverse=True)

        seq = machine_1_sequence + machine_2_sequence
        jobs_m1, jobs_m2 = [], []
        job_name_rad = "job_"
        job = {"name": job_name_rad +
               str(
                   seq[0]+1,
               ),
               "start_time": 0,
               "end_time": self.data[0][seq[0]]}
        jobs_m1.append(job)
        job = {"name": job_name_rad+str(seq[0]+1), "start_time": self.data[0]
               [seq[0]],
               "end_time": self.data[0][seq[0]] + self.data[1][seq[0]]}
        jobs_m2.append(job)

        for job_id in seq[1::]:
            # job on machine 1
            job_name = job_name_rad + str(job_id + 1)
            job_start_m1 = jobs_m1[-1]["end_time"]
            job_end_m1 = job_start_m1 + self.data[0][job_id]
            job = {"name": job_name, "start_time": job_start_m1,
                   "end_time": job_end_m1}
            jobs_m1.append(job)

            # job on machine 2
            job_start_m2 = max(job_end_m1, jobs_m2[-1]["end_time"])
            job_end_m2 = job_start_m2 + self.data[1][job_id]

            job = {"name": job_name, "start_time": job_start_m2,
                   "end_time": job_end_m2}
            jobs_m2.append(job)
        optim_makespan = int(jobs_m2[-1]["end_time"])
        return seq, [jobs_m1, jobs_m2], optim_makespan

    @staticmethod
    def johnson_seq(data):
        # data matrix must have only two machines
        nb_machines = len(data)
        nb_jobs = len(data[0])
        machine_1_sequence = [j for j in range(
            nb_jobs) if data[0][j] <= data[1][j]]
        machine_1_sequence.sort(key=lambda x: data[0][x])
        machine_2_sequence = [j for j in range(
            nb_jobs) if data[0][j] > data[1][j]]
        machine_2_sequence.sort(key=lambda x: data[1][x], reverse=True)
        seq = machine_1_sequence + machine_2_sequence
        return seq

    def cds(self):
        raise NotImplementedError

    def palmer_heuristic(self):
        """solves an N machines M jobs pfsp problem using Palmer's Heuristic
        Returns:
            tuple -- a tuple containing the job sequence, scheduled jobs and optimal makespan.
        """

        def palmer_f(x): return -(self.nb_machines - (2*x - 1))
        weights = list(map(palmer_f, range(1, self.nb_machines+1)))
        ws = []
        print(weights)
        print(self.data)
        for job_id in range(self.nb_jobs):
            p_ij = sum([self.data[j][job_id]*weights[j]
                        for j in range(self.nb_machines)])
            ws.append((job_id, p_ij))
        ws.sort(key=lambda x: x[1], reverse=True)
        h_seq = [x[0] for x in ws]
        print(h_seq)
        schedules = np.zeros((self.nb_machines, self.nb_jobs), dtype=dict)
        # schedule first job alone first
        task = {"name": "job_{}".format(
            h_seq[0]+1), "start_time": 0, "end_time": self.data[0][h_seq[0]]}
        schedules[0][0] = task
        for m_id in range(1, self.nb_machines):
            start_t = schedules[m_id-1][0]["end_time"]
            end_t = start_t + self.data[m_id][0]
            task = {"name": "job_{}".format(
                h_seq[0]+1), "start_time": start_t, "end_time": end_t}
            schedules[m_id][0] = task

        for index, job_id in enumerate(h_seq[1::]):
            start_t = schedules[0][index]["end_time"]
            end_t = start_t + self.data[0][job_id]
            task = {"name": "job_{}".format(
                job_id+1), "start_time": start_t, "end_time": end_t}
            schedules[0][index+1] = task
            for m_id in range(1, self.nb_machines):
                start_t = max(schedules[m_id][index]["end_time"],
                              schedules[m_id-1][index+1]["end_time"])
                end_t = start_t + self.data[m_id][job_id]
                task = {"name": "job_{}".format(
                    job_id+1), "start_time": start_t, "end_time": end_t}
                schedules[m_id][index+1] = task
        opt_makespan = int(schedules[self.nb_machines-1][-1]["end_time"])
        return h_seq, schedules, opt_makespan

    def _get_makespan(self, seq, data):
        c = np.zeros((self.nb_machines, len(seq)), dtype=object)
        c[0][0] = (0, data[0][seq[0]])
        for m_id in range(1, self.nb_machines):
            s_t = c[m_id-1][0][1]
            e_t = s_t + data[m_id][0]
            c[m_id][0] = (s_t, e_t)
        if len(seq) > 1:
            for i, job_id in enumerate(seq[1::]):
                s_t = c[0][i][1]
                e_t = s_t + data[0][job_id]
                c[0][i+1] = (s_t, e_t)
                for m_id in range(1, self.nb_machines):
                    s_t = max(c[m_id][i][1], c[m_id-1][i+1][1])
                    e_t = s_t + data[m_id][job_id]
                    c[m_id][i+1] = (s_t, e_t)
        return c[self.nb_machines-1][-1][1]

    def neh_heuristic(self):
        sums = []
        for job_id in range(self.nb_jobs):
            p_ij = sum([self.data[j][job_id]
                        for j in range(self.nb_machines)])
            sums.append((job_id, p_ij))
        sums.sort(key=lambda x: x[1], reverse=True)
        seq = []
        for job in sums:
            cands = []
            for i in range(0, len(seq) + 1):
                cand = seq[:i] + [job[0]] + seq[i:]
                cands.append((cand, self._get_makespan(cand, self.data)))
            seq = min(cands, key=lambda x: x[1])[0]

        schedules = np.zeros((self.nb_machines, self.nb_jobs), dtype=dict)
        # schedule first job alone first
        task = {"name": "job_{}".format(
            seq[0]+1), "start_time": 0, "end_time": self.data[0][seq[0]]}
        schedules[0][0] = task
        for m_id in range(1, self.nb_machines):
            start_t = schedules[m_id-1][0]["end_time"]
            end_t = start_t + self.data[m_id][0]
            task = {"name": "job_{}".format(
                seq[0]+1), "start_time": start_t, "end_time": end_t}
            schedules[m_id][0] = task

        for index, job_id in enumerate(seq[1::]):
            start_t = schedules[0][index]["end_time"]
            end_t = start_t + self.data[0][job_id]
            task = {"name": "job_{}".format(
                job_id+1), "start_time": start_t, "end_time": end_t}
            schedules[0][index+1] = task
            for m_id in range(1, self.nb_machines):
                start_t = max(schedules[m_id][index]["end_time"],
                              schedules[m_id-1][index+1]["end_time"])
                end_t = start_t + self.data[m_id][job_id]
                task = {"name": "job_{}".format(
                    job_id+1), "start_time": start_t, "end_time": end_t}
                schedules[m_id][index+1] = task
        max_mkspn = int(schedules[self.nb_machines-1][-1]["end_time"])
        return seq, schedules, max_mkspn

    @lru_cache(maxsize=128)
    def brute_force_exact(self):
        jobs_perm = permutations(range(self.nb_jobs))
        seq = min(jobs_perm, key=lambda x: self._get_makespan(x, self.data))
        schedules = np.zeros((self.nb_machines, self.nb_jobs), dtype=dict)
        # schedule first job alone first
        task = {"name": "job_{}".format(
            seq[0]+1), "start_time": 0, "end_time": self.data[0][seq[0]]}
        schedules[0][0] = task
        for m_id in range(1, self.nb_machines):
            start_t = schedules[m_id-1][0]["end_time"]
            end_t = start_t + self.data[m_id][0]
            task = {"name": "job_{}".format(
                seq[0]+1), "start_time": start_t, "end_time": end_t}
            schedules[m_id][0] = task

        for index, job_id in enumerate(seq[1::]):
            start_t = schedules[0][index]["end_time"]
            end_t = start_t + self.data[0][job_id]
            task = {"name": "job_{}".format(
                job_id+1), "start_time": start_t, "end_time": end_t}
            schedules[0][index+1] = task
            for m_id in range(1, self.nb_machines):
                start_t = max(schedules[m_id][index]["end_time"],
                              schedules[m_id-1][index+1]["end_time"])
                end_t = start_t + self.data[m_id][job_id]
                task = {"name": "job_{}".format(
                    job_id+1), "start_time": start_t, "end_time": end_t}
                schedules[m_id][index+1] = task
        makespan = int(schedules[self.nb_machines-1][-1]["end_time"])
        return seq, schedules, makespan

    def genetic_algorithm(self):
        optimal = [4534, 920, 1302]
        opt = 0
        no_of_jobs, no_of_machines = self.nb_jobs, self.nb_machines
        processing_time = []
        for i in range(no_of_jobs):
            temp = []
            for j in range(no_of_machines):
                temp.append(self.data[j][i])
            processing_time.append(temp)
        # generate an initial population proportional to no_of_jobs
        number_of_population = no_of_jobs**2
        no_of_iterations = 5000
        p_crossover = 1.0
        p_mutation = 1.0

        # Initialize population
        population = initialize_population(
            number_of_population, no_of_jobs)

        for evaluation in range(no_of_iterations):
            # Select parents
            parent_list = select_parent(
                population, processing_time, no_of_jobs, no_of_machines)
            childs = []

            # Apply crossover to generate children
            for parents in parent_list:
                r = np.random.rand()
                if r < p_crossover:
                    childs.append(crossover(parents))
                else:
                    if r < 0.5:
                        childs.append(parents[0])
                    else:
                        childs.append(parents[1])

            # Apply mutation operation to change the order of the n-jobs
            mutated_childs = []
            for child in childs:
                r = np.random.rand()
                if r < p_mutation:
                    mutated_child = mutation(child)
                    mutated_childs.append(mutated_child)

            childs.extend(mutated_childs)
            if len(childs) > 0:
                update_population(
                    population, childs, processing_time, no_of_jobs, no_of_machines)

        costed_population = []
        for individual in population:
            ind_makespan = (calc_makespan(
                individual, processing_time, no_of_jobs, no_of_machines), individual)
            costed_population.append(ind_makespan)
        costed_population.sort(key=lambda x: x[0])

        seq = list(map(int, costed_population[0][1]))
        makespan = self._get_makespan(seq, self.data)

        schedules = np.zeros((self.nb_machines, self.nb_jobs), dtype=dict)
        # schedule first job alone first
        task = {"name": "job_{}".format(
                seq[0]+1), "start_time": 0, "end_time": self.data[0][seq[0]]}
        schedules[0][0] = task
        for m_id in range(1, self.nb_machines):
            start_t = schedules[m_id-1][0]["end_time"]
            end_t = start_t + self.data[m_id][0]
            task = {"name": "job_{}".format(
                    seq[0]+1), "start_time": start_t, "end_time": end_t}
            schedules[m_id][0] = task

        for index, job_id in enumerate(seq[1::]):
            start_t = schedules[0][index]["end_time"]
            end_t = start_t + self.data[0][job_id]
            task = {"name": "job_{}".format(
                    job_id+1), "start_time": start_t, "end_time": end_t}
            schedules[0][index+1] = task
            for m_id in range(1, self.nb_machines):
                start_t = max(schedules[m_id][index]["end_time"],
                              schedules[m_id-1][index+1]["end_time"])
                end_t = start_t + self.data[m_id][job_id]
                task = {"name": "job_{}".format(
                        job_id+1), "start_time": start_t, "end_time": end_t}
                schedules[m_id][index+1] = task

        #print(seq, makespan)
        # print(schedules)
        return seq, schedules, makespan


class RandomFlowshop:
    """This module makes an instance of random flowshop problem,
     given number of machines and number of jobs,
     and generates random data of jobs processing times

    Returns:
        RandomFlowshop object -- A RandomFlowshop object instance
    """

    def __init__(self, nb_machines, nb_jobs):
        self.nb_machines = nb_machines
        self.nb_jobs = nb_jobs
        self.data = self.get_random_p_times(10)

    def get_random_p_times(self, p_times_ub):
        """
        Generates matrix of random processing times of jobs in machines

        Attributes:
            p_times_ub (int): upper bound of processing times of each job

        Returns:
            ndarray of random processing times of size (nb_machines x nb_jobs)
        """
        return np.random.randint(
            1,
            p_times_ub,
            size=(
                self.nb_machines,
                self.nb_jobs
            )
        )

    def get_data(self):
        """
        Getter for data attribute

        Returns:
            ndarray: the return value of random processing times matrix
        """
        return self.data

    def get_number_machines(self):
        """
        number of machines getter

        Returns:
            int: Returns number of machines specified in instance problem
        """
        return self.nb_machines

    def get_number_jobs(self):
        """
        Number of jobs getter

        Returns:
            int: returns the number of jobs in instance problem
        """
        return self.nb_jobs

    def get_problem_instance(self):
        """
        Returns a Flowshop instance from randomly generated problem
        Returns:
            Flowshop object: A Flowshop object with the randomly generated data
        """
        return Flowshop(self.data, self.nb_machines, self.nb_jobs)


if __name__ == "__main__":
    random_problem = RandomFlowshop(4, 5)
    random_problem_instance = random_problem.get_problem_instance()
    seq, _, g_mkspan = random_problem_instance.genetic_algorithm()
    b_seq, b_scheds, b_opt_makespan = random_problem_instance.brute_force_exact()
    print(type(seq))
    print(type(seq[0]))
    print(b_opt_makespan, g_mkspan)
    # print(seq)
    #print("Brute Force: {}, Palmer heuristic: {}".format(b_seq, seq))
    #seq, jobs, opt_makespan = random_problem_instance.solve_johnson()
    # print("Sequence: {} \nJobs on Machine 1: \n {} \n Jobs on machine 2:\n {} \n".format(
    #    seq, jobs[0], jobs[1]))
