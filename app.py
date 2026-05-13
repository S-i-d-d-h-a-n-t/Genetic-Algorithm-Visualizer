# app.py
import json
import time
import copy
import random
import math
import itertools
from flask import Flask, render_template, Response, stream_with_context

# --- DATA PARSING & PREPARATION ---
def parse(path):
    file = open(path, 'r')
    firstLine = file.readline()
    firstLineValues = list(map(int, firstLine.split()[0:2]))
    jobsNb = firstLineValues[0]
    machinesNb = firstLineValues[1]
    jobs = []
    for i in range(jobsNb):
        currentLine = file.readline()
        currentLineValues = list(map(int, currentLine.split()))
        operations = []
        j = 1
        while j < len(currentLineValues):
            k = currentLineValues[j]
            j = j+1
            operation = []
            for ik in range(k):
                machine = currentLineValues[j]
                j = j+1
                processingTime = currentLineValues[j]
                j = j+1
                operation.append({'machine': machine, 'processingTime': processingTime})
            operations.append(operation)
        jobs.append(operations)
    file.close()
    return {'machinesNb': machinesNb, 'jobs': jobs}

def noOfOptions(operation):
    return len(operation)

def noOfOperations(job):
    return len(job)

def noOfJobs(jobs):
    return len(jobs)

def totalNoOfOperations(jobs):
    operations = 0
    for job in jobs:
        operations = operations + noOfOperations(job)
    return operations

def totalNoOfOptions(jobs):
    options=1
    for job in jobs:
        for operation in job:
            options = options * noOfOptions(operation)
    return options

def rewriteJobs(jobs):
    for i,job in enumerate(jobs):
        for j,operation in enumerate(job):
            for k,option in enumerate(operation):
                option['job'] = i
                option['operation'] = j
                option['option'] = k
    return jobs

def totalNoOfSequences(jobs):
    return math.factorial(totalNoOfOperations(jobs)) * totalNoOfOptions(jobs)

def getOperations(jobs):
    operations =[]
    for job in jobs:
        for operation in job:
            operations.append(operation)
    return operations

def getPrimitiveSequences(jobs):
    operations = getOperations(jobs)
    sequences = [[] for _ in range(len(operations))]
    for i, operation in enumerate(operations):
        for j, option in enumerate(operation):
            sequences[i].append(option)
    return sequences
    
def getSequencesShape(sequences):
    num_operations = len(sequences)
    max_options = max(len(operation) for operation in sequences)
    return (num_operations, max_options)  

def printSequences(sequences):
    for i, seq in enumerate(sequences):
        print(f"Sequence {i}: {seq}")

def check_sequence_constraint(operations):
    job_dict = {}
    for op in operations:
        job = op['job']
        if job not in job_dict:
            job_dict[job] = []
        job_dict[job].append(op)
    for job_ops in job_dict.values():
        for i in range(1, len(job_ops)):
            prev_op = job_ops[i-1]
            curr_op = job_ops[i]
            if prev_op['operation'] > curr_op['operation']:
                return False
    return True

def permute_operations(jobs):
    job_groups = {}
    for operation in jobs:
        job = operation['job']
        if job not in job_groups:
            job_groups[job] = []
        job_groups[job].append(operation)
    permuted_groups = []
    for job, group in job_groups.items():
        permuted_groups.append(list(itertools.permutations(group)))
    combinations = list(itertools.product(*permuted_groups))
    return [operation for job in combinations for operation in job]

def getValidSequencePermutations(sequencePermutations):
    result = []
    for perm in sequencePermutations:
        if(check_sequence_constraint(perm)):
            result.append(perm)
    return result

def getValidSequences(sequences):
    sequence_combinations = list((list(item) for item in itertools.product(*sequences) ))
    result = []
    for combination in sequence_combinations:
        sequence_permutations = list(list(item) for item in itertools.permutations(combination, r=None) )
        valid_sequence_permutations = getValidSequencePermutations(sequence_permutations)
        result.extend(valid_sequence_permutations)    
    return result

def process_operations(sequence, noOfJobs, noOfMachines):
    machineState = {i: 0 for i in range(1, noOfMachines+1)}
    jobState = {i: 0 for i in range(noOfJobs)}
    jobOpState = {i: 0 for i in range(noOfJobs)}
    opState = {i: False for i in range(len(sequence))}
    opSequence = []
    startTimes = []
    stopTimes = []
    time=0
    possibleTimes = []
    makespan = 0
    while not all(opState.values()):
        executed = False
        for i,op in enumerate(sequence):
            if not(opState[i]) and op['operation'] == jobOpState[op['job']] and jobState[op['job']] <= time and machineState[op['machine']] <= time:
                opState[i] = True
                startTime = time
                stopTime = time + op['processingTime']
                opSequence.append(i)
                startTimes.append(startTime)
                stopTimes.append(stopTime)
                jobOpState[op['job']] += 1
                jobState[op['job']] = stopTime
                machineState[op['machine']] = stopTime
                possibleTimes.append(stopTime)
                executed = True
                if stopTime>= makespan:
                    makespan = stopTime
        if not executed:
            time += 1
        else:
            time = min(possibleTimes)
    operationSequence = [None] * len(opSequence)
    for i, op_index in enumerate(opSequence):
        operationSequence[i] = sequence[op_index]
    return makespan, operationSequence, startTimes, stopTimes 

def getAllData(sequences, noOfJobs, noOfMachines):
    makespans = []
    operationSequences = []
    allStartTimes = []
    allStopTimes = []
    for seq in sequences:
        makespan, operationSequence, startTimes, stopTimes = process_operations(seq, noOfJobs, noOfMachines)
        makespans.append(makespan)
        operationSequences.append(operationSequence)
        allStartTimes.append(startTimes)
        allStopTimes.append(stopTimes)
    return makespans, operationSequences, allStartTimes, allStopTimes
    
def printJobOperationInFormat(jobOperations):
    print("[", end='')
    for job in jobOperations:
        print("[", end='')
        for operation in job:
            print("[", end='')
            for option in operation:
                print("(", option['job'], ",",option['operation'], ",", option['option'], ")", end='')
            print("]", end='')
        print("]", end='')
    print("]")

def generateRandomSequence(jobOperations):
    sequence = []
    noOfOperations = totalNoOfOperations(jobOperations)
    for i in range(0,noOfOperations):
        randomJobNo = random.randrange(len(jobOperations))
        randomJob = jobOperations[randomJobNo]
        operation = randomJob.pop(0)
        randomOptionNo = random.randrange(len(operation))
        randomOption =  operation[randomOptionNo]
        sequence.append(randomOption)
        if len(randomJob) ==0:
            del jobOperations[randomJobNo]
    return sequence

def getInitialPopulation(populationSize, jobOperations):
    population = []
    for i in range(0, populationSize):
        randomSequence = generateRandomSequence(copy.deepcopy(jobOperations))
        population.append(randomSequence)
    return population

def random_selection(population,tournament_size):
    indices = list(range(len(population)))
    random.shuffle(indices)
    parent1_index = None
    parent2_index = None
    for i in range(0, len(indices), tournament_size):
        tournament_indices = indices[i:i+tournament_size]
        parents = random.sample(tournament_indices,2)
        parent1_index = parents[0]
        parent2_index = parents[1]
    return (parent1_index, parent2_index)

def tournament_selection(population, makespans, tournament_size):
    indices = list(range(len(population)))
    random.shuffle(indices)
    parent1_index = None
    parent2_index = None
    for i in range(0, len(indices), tournament_size):
        tournament_indices = indices[i:i+tournament_size]
        best_fitness = None
        best_index = None
        for index in tournament_indices:
            fitness = makespans[index]
            if best_fitness is None or fitness < best_fitness:
                best_fitness = fitness
                best_index = index
        if parent1_index is None:
            parent1_index = best_index
        elif parent2_index is None:
            parent2_index = best_index
        else:
            break
    return (parent1_index, parent2_index)

def delete_operation(chromosome, job_no, operation_no):
    for i in range(len(chromosome)):
        if chromosome[i]['job'] == job_no and chromosome[i]['operation'] == operation_no:
            del chromosome[i]
            break

def crossover(parent1, parent2):
    num_operations = len(parent1)
    num_selected = random.randint(1, num_operations)
    selected_indices = random.sample(range(num_operations), num_selected)
    child = []
    for i in range(num_operations):
        if i in selected_indices:
            operation = parent1[i]
            child.append(operation)
    for operation in child:
        if operation is not None:
            job, operation_no = operation['job'], operation['operation']
            delete_operation(parent2, job, operation_no)
    child.extend(parent2)
    return child

def mutation(chromosome):
    pos1 = random.randint(0, len(chromosome) - 1)
    pos2 = random.randint(0, len(chromosome) - 1)
    while pos1 == pos2:
        pos2 = random.randint(0, len(chromosome) - 1)
    chromosome[pos1], chromosome[pos2] = chromosome[pos2], chromosome[pos1]
    return chromosome

def repair(child):
    repairedChild = []
    jobPositions = []
    for operation in child:
        jobPositions.append(operation['job'])
    jobs = {}
    for operation in child:
        job = operation['job']
        if job not in jobs:
            jobs[job] = []
        jobs[job].append(operation)
    for job in jobs.values():
        job.sort(key=lambda x: x['operation'])
    for i,jobNo in enumerate(jobPositions):
        repairedChild.append(jobs[jobNo].pop(0))
    return repairedChild

def replace_worst_with_child(population, makespans, child, child_makespan):
    worst_index = makespans.index(max(makespans))
    if child_makespan <= makespans[worst_index]:
        population[worst_index] = child
        makespans[worst_index] = child_makespan

def addrewriteJobs(jobs,noofjobs):
    newnoofjobs = noofjobs-1
    for i,job in enumerate(jobs):
        newnoofjobs = newnoofjobs+1
        for j,operation in enumerate(job):
            for k,option in enumerate(operation):
                option['job'] = newnoofjobs
                option['operation'] = j
                option['option'] = k
    return jobs

def completion_time(sequence, noOfJobs, noOfMachines):
    machineState = {i: 0 for i in range(1, noOfMachines+1)}
    jobState = {i: 0 for i in range(noOfJobs)}
    jobOpState = {i: 0 for i in range(noOfJobs)}
    opState = {i: False for i in range(len(sequence))}
    opSequence = []
    startTimes = []
    stopTimes = []
    time=0
    possibleTimes = []
    makespan = 0
    while not all(opState.values()):
        executed = False
        for i,op in enumerate(sequence):
            if not(opState[i]) and op['operation'] == jobOpState[op['job']] and jobState[op['job']] <= time and machineState[op['machine']] <= time:
                opState[i] = True
                startTime = time
                stopTime = time + op['processingTime']
                opSequence.append(i)
                startTimes.append(startTime)
                stopTimes.append(stopTime)
                jobOpState[op['job']] += 1
                jobState[op['job']] = stopTime
                machineState[op['machine']] = stopTime
                possibleTimes.append(stopTime)
                executed = True
                if stopTime>= makespan:
                    makespan = stopTime
        if not executed:
            time += 1
        else:
            time = min(possibleTimes)
    operationSequence = [None] * len(opSequence)
    for i, op_index in enumerate(opSequence):
        operationSequence[i] = sequence[op_index]
    return machineState, jobState, jobOpState, opState, opSequence, startTimes, stopTimes, possibleTimes, operationSequence

# --- MODIFY ga_operation TO BECOME A GENERATOR FUNCTION ---
# In app.py - REPLACE the existing ga_operation_stream function with this one

def ga_operation_stream(jobs, noOfJobs, noOfMachines, populationSize, tournamentSize, iterationSize):
    """
    A generator function that yields the state of the GA at each iteration.
    Now includes color information for the Gantt chart.
    """
    # Define a list of visually distinct colors for the jobs
    color_palette = [
        '#4285F4', '#DB4437', '#F4B400', '#0F9D58', 
        '#AB47BC', '#00ACC1', '#FF7043', '#9CCC65',
        '#42A5F5', '#EF5350', '#FFCA28', '#66BB6A' 
    ]
    job_colors = {i: color_palette[i % len(color_palette)] for i in range(noOfJobs)}

    population = getInitialPopulation(populationSize, jobs)
    makespans, _, _, _ = getAllData(population, noOfJobs, noOfMachines)

    for i in range(0, iterationSize):
        parent1_idx, parent2_idx = random_selection(population, tournamentSize)
        
        child = crossover(copy.deepcopy(population[parent1_idx]), copy.deepcopy(population[parent2_idx]))
        child = mutation(child)
        child = repair(child)
        
        makespan, _, _, _ = process_operations(child, noOfJobs, noOfMachines)
        
        replace_worst_with_child(population, makespans, child, makespan)
        
        minMakespan = min(makespans)
        
        data_to_send = {
            "generation": i + 1,
            "minMakespan": minMakespan,
            "ganttData": None 
        }
        
        if (i + 1) % 20 == 0 or (i + 1) == iterationSize:
             best_index = makespans.index(minMakespan)
             _, best_op_seq, best_starts, best_stops = process_operations(population[best_index], noOfJobs, noOfMachines)
             
             # Format data for Google Gantt Chart, now including color
             gantt_data = []
             for j, op in enumerate(best_op_seq):
                 job_num = op['job']
                 task_label = f"({op['job']+1},{op['operation']+1},{op['option']+1})"
                 color = job_colors[job_num]
                 
                 gantt_data.append([
                     f"Machine {op['machine']}",
                     task_label, # The text on the bar
                     task_label, # The tooltip text on hover
                     best_starts[j] * 1000, 
                     best_stops[j] * 1000,
                     None, # Duration (not needed, calculated automatically)
                     100,  # Percent complete (not needed)
                     None, # Dependencies (not needed)
                     f'fill-color: {color}' # The style information!
                 ])
             data_to_send["ganttData"] = gantt_data

        yield f"data: {json.dumps(data_to_send)}\n\n"
        time.sleep(0.1)

# --- FLASK APPLICATION SETUP ---
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-ga')
def run_ga():
    # These parameters would ideally come from the frontend request
    data = parse("sf2batch1.txt") # Assuming the file is in the same directory
    noOfMachines = data['machinesNb']
    jobs = data['jobs']
    noOfJobs = len(jobs)
    jobs = rewriteJobs(jobs)

    # GA Parameters
    populationSize = 100
    tournamentSize = 50
    iterationSize = 500
    
    # Use stream_with_context to handle the generator
    return Response(stream_with_context(ga_operation_stream(jobs, noOfJobs, noOfMachines, populationSize, tournamentSize, iterationSize)),
                    mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)