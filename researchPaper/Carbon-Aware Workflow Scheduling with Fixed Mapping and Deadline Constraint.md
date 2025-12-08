Carbon-Aware Workflow Scheduling with Fixed Mapping and Deadline Constraint
Dominik Schweisgut
Humboldt-Universität zu Berlin, Germany, dominik.schweisgut@kit.edu, now at Karlsruhe Institue of Technology (KIT)
Anne Benoit
ENS Lyon and IUF, France & IDEaS, Atlanta, USA Anne.Benoit@ens-lyon.fr
Yves Robert
ENS Lyon, France, Yves.Robert@ens-lyon.fr
Henning Meyerhenke
Karlsruhe Institute of Technology (KIT), Germany, meyerhenke@kit.edu
Abstract
Large data and computing centers consume a significant share of the world’s energy consumption. A prominent subset of the workloads in such centers are workflows with interdependent tasks, usually represented as directed acyclic graphs (DAGs). To reduce the carbon emissions resulting from executing such workflows in centers with a mixed (renewable and non-renewable) energy supply, it is advisable to move task executions to time intervals with sufficient green energy when possible. To this end, we formalize the above problem as a scheduling problem with a given mapping and ordering of the tasks. We show that this problem can be solved in polynomial time in the uniprocessor case. For at least two processors, however, the problem becomes NP-hard. Hence, we propose a heuristic framework called CaWoSched that combines several greedy approaches with local search. To assess the 16 heuristics resulting from different combinations, we also devise a simple baseline algorithm and an exact ILP-based solution. Our experimental results show that our heuristics provide significant savings in carbon emissions compared to the baseline.

1Introduction
The number of large and geo-distributed data and computing centers grows rapidly and so is the amount of data processed by them. Their services have become indispensable in industry and academia alike. Yet, these services result in a globally significant energy consumption as well as carbon emissions due to computations and data transfer, see for example [3] for concrete numbers. Since the combined carbon footprint of all data/computing centers on the globe is even higher than that of air traffic [24], reducing this footprint is of immense importance, both from an ecological, political, and economical perspective. On the technical side, data/computing centers have started to use a mix of different power sources, giving priority to lower carbon-emitting technologies (solar, wind, nuclear) over higher ones (coal, natural gas). This raises new challenges and opportunities for HPC (High Performance Computing) scientists;  for example, designing efficient scheduling algorithms was already a complicated task when computer platforms had only a single power source – and thus the same level of carbon emissions at each point in time. This task becomes even more difficult when a mix of power sources leads to different carbon emissions over time: in addition to optimizing only standard performance-related objectives, one important new objective is to optimize the total amount of carbon emissions induced by the execution of all applications in a particular data/computing center.

Many workloads in a data/computing center, not only but in particular in a scientific context, can be seen as workflows consisting of individual tasks with input/output relations. The algorithmic task we focus on in this paper is to schedule such workflows (abstracted as directed acyclic task graphs) on a parallel platform within some deadline. To focus on carbon footprint minimization, we assume that the mapping and ordering of all tasks and communications are already given, for instance as the result of executing the de-facto standard HEFT algorithm [34]. A somewhat similar approach of assuming a fixed mapping can be found in the literature, e. g., for energy- and reliability-aware task scheduling and frequency scaling in embedded systems [28].

In our simplified setting with a given mapping, minimizing the total execution time, or makespan, can easily be achieved in linear time with the ASAP greedy algorithm: simply execute each task as soon as all preceding tasks and corresponding communications have completed. The computing platform that we target instead has a time-varying amount of green energy available, for example due to solar and/or wind power produced for its data/computing center. Moreover, the carbon emissions can vary from processor to processor due to the latter’s different power demands, making the platform completely carbon-heterogeneous.

The problem becomes combinatorial: while we cannot change the mapping nor the ordering of the tasks on each processor, we can shift the tasks (and the corresponding communication operations) to benefit from lower-carbon intervals, while enforcing the deadline. Previous studies have shown that exploiting lower-carbon intervals can be very beneficial, see e. g., [38]. Yet, this previous line of research has either not focused on scheduling individual workflows or focused on reducing energy consumption [35, 7] rather than carbon emission. As we outline in more detail in Section 2, carbon-aware scheduling algorithms are still in their infancy.

Contributions.
The main contributions of this paper are both theoretical and practical. On the theory side, we lay the foundations for the problem complexity, with (i) a sophisticated fully-polynomial time dynamic programming algorithm for the single processor case, (ii) a proof of strong NP-completeness for a simplified instance with 2 or more processors, independent tasks, and carbon-homogeneous processors, and (iii) the formulation of the general problem as an integer linear program (ILP). On the practical side, we design efficient algorithms that greatly decrease the total carbon cost compared to a standard carbon-unaware competitor; for small instances, our experimental results indicate that our algorithms achieve a quality that is close to the optimal one derived from the ILP.

Outline.
The rest of the paper is organized as follows. Section 2 surveys related work. In Section 3, we detail the framework. Section 4 is devoted to complexity results. We introduce new carbon-aware algorithms in Section 5 and assess their performance through an extensive set of simulations in Section 6. Finally, we give concluding remarks and hints for future work in Section 7.

2Related Work
Carbon-aware computing has received increasing attention in the past few years, acknowledging the clearly non-negligible share data/computing centers have on mankind’s carbon footprint – as well as the need for action to reduce the emissions given the rapid increase in data to be processed [10]. Most works in this more general line of research retain a high-level workload perspective and thus do not consider the concrete task of workflow scheduling. For example, a carbon-aware load balancing algorithm to reduce the carbon footprint of geo-distributed data centers considers abstract workloads, not interdependent tasks [26]. It uses the alternating direction method of multipliers to move workloads to locations with lower carbon intensity. On a similar granularity, global cloud providers use scheduler-agnostic workload shifting to less carbon-intensive data centers, depending on the projected availability of green energy in suitable locations and time intervals [29]. A high-level workload perspective and a similar objective is used by Hall et al. [18]. They devise a two-phase approach of (i) day-ahead planning based on historical data and (ii) real-time job placement and scheduling. As they consider abstract workloads and not workflows with interdependencies, their approach is not directly comparable, either. Finally, while Breukelmann et al. [9] model interconnected data centers as a weighted graph, they still consider unrelated batch compute jobs as the workload. They formalize the optimal allocation problem in this setting as a single-leader multiple-follower Stackelberg game and suggest an ad-hoc algorithm (which is not applicable in our setting) to solve it.

Regarding workflow scheduling in general, we refer the interested reader to surveys [2, 25] and a monograph [33] for a broader overview. One possible way to categorize workflow scheduling algorithms is to distinguish online algorithms (which do not know the complete workflow when taking decisions for tasks) and plan-based algorithms. Since this paper proposes a plan-based algorithm, we focus on the latter. Even rather simplistic versions of plan-based scheduling are NP-hard [15], which motivates the use of heuristics for real-world applications. Two common approaches are list- and partitioning-based heuristics. HEFT (heterogeneous earliest finish time) [34] is a very influential and still popular list-scheduling algorithm that has seen numerous extensions and variations over the years [5, 32, 31, 8, 30]. It has two main phases that (i) assign priorities to tasks and (ii) then assign tasks to processors based on the priorities from the previous phase.

Partitioning-based scheduling heuristics, in turn, group tasks into blocks and assign these blocks to processors, see e. g. [27, 23, 36]. This aggregation step helps in reducing the complexity of dealing with individual task assignments in large-scale workflows.

Two prominent algorithms for energy-efficient workflow scheduling are GreenHEFT [13] and MOHEFT [14]. Both heuristics optimize where tasks are scheduled in order to save energy. Similar to one type of our heuristics, TaskFlow [35] exploits slack in workflows, i. e., it takes advantage of tolerable delays by executing the corresponding tasks on more energy-efficient hardware. Yet, they all do not optimize for carbon emissions and thus do not consider when tasks should run in order to exploit green energy availability.

The importance of reducing carbon emissions has led to a number of papers working on this goal. Wen et al. [37], for example, propose a genetic algorithm for adaptive workflow mapping whose main rationale is to move tasks between geographically distributed data centers – depending on their energy mix. The approach only provides a mapping of tasks to data centers, but no task starting times. Moreover, the largest workflows in their experiments have up to 1,000 tasks, an indication that the genetic algorithm is quite time-consuming. A similar rationale of moving tasks to locations with sufficient green energy is used by Hanafy et al. [19], who scale the resources assigned to elastic cloud applications in a carbon-aware manner. Considering a single data center location, in turn, Wiesner et al. [38] investigate how beneficial shifting of execution times to intervals with lower carbon emissions can be. By evaluating the impact of time constraints, scheduling strategies, and forecast accuracy, they find significant potential (under certain conditions) and provide guidance regarding corresponding data center policies.

Altogether, this work is in line with the general trend of minimizing energy consumption and/or carbon emissions. However, to the best of our knowledge, it is the first to focus on optimizing the scheduling of a given workflow mapping and ordering to benefit from time-varying green energy.

3Framework
We use a suitable time unit (e.g. seconds, minutes, …) and express all parameters as integer multiples of this unit.

Platform and application.
The target platform 
𝒞
 is a cluster of 
P
 heterogeneous processors 
{
p
1
,
…
,
p
P
}
. The target application consists of a workflow modeled as a Directed Acyclic Graph (DAG) 
G
=
(
V
,
E
,
ω
,
c
)
, where the vertex set 
V
 represents the set of 
n
 tasks 
v
1
,
…
,
v
n
. An edge 
(
v
i
,
v
j
)
∈
E
 represents a precedence constraint between tasks 
v
i
 and 
v
j
, meaning that task 
v
j
 cannot start before task 
v
i
 is completed and its output was communicated to the processor handling task 
v
i
.

We assume that the mapping is given, as well as the ordering of the tasks and the communication operations (i.e., data transfer) on each processor. Therefore, if two tasks are mapped on the same processor with task 
v
i
 planned before task 
v
j
, we add a precedence constraint 
(
v
i
,
v
j
)
 to 
E
, to ensure that the order is respected.

Given the mapping, the set of communications is represented by 
E
′
⊆
E
, which contains all edges 
(
v
i
,
v
j
)
∈
E
 such that the two tasks are mapped on different processors, in which case data must be communicated between both processors before 
v
j
 can start its execution. However, when the two tasks are on the same processor (
(
v
i
,
v
j
)
∈
E
∖
E
′
), task 
v
j
 can start as soon as task 
v
i
 is finished.

Each task 
v
i
∈
V
 has a running time 
ω
​
(
v
i
)
, and each edge 
(
v
i
,
v
j
)
∈
E
′
 has a communication time 
c
​
(
v
i
,
v
j
)
, which accounts for the amount of data that has to be communicated from the processor of task 
v
i
 to the processor of task 
v
j
. Computation and communication times can be arbitrary and are given, which allows us to account for any heterogeneity in computing speeds and/or link bandwidths across the processors.

Communication-enhanced DAG 
G
c
.
For simplicity, we assume that the cluster employs a fully connected, full-duplex communication topology, where each processor can directly communicate with every other processor simultaneously in both directions. We introduce 
P
​
(
P
−
1
)
 fictional processors 
{
p
P
+
1
,
…
,
p
P
2
}
, one per communication link, whose role is to execute all (potential) communications on that link. This will clarify how to compute the cost of a schedule. With these additional processors, each communication 
(
v
i
,
v
j
)
∈
E
′
 becomes a (fictional) task 
v
i
,
j
 of length 
ω
​
(
v
i
,
j
)
=
c
​
(
v
i
,
v
j
)
. Furthermore, we add dependencies 
(
v
i
,
v
i
,
j
)
 and 
(
v
i
,
j
,
v
j
)
, each with zero communication cost. Since the order of communications is also assumed to be given with the mapping, we add precedence constraints to express this order if two tasks 
v
i
,
j
 and 
v
k
,
ℓ
 are on the same communication link (represented by a fictional processor). This is similar to the precedence constraints added to express the order of computing tasks and we refer to this set of constraints as 
E
′′
.

We obtain a communication-enhanced DAG 
G
c
=
(
V
c
,
E
c
,
ω
)
, where 
V
c
 contains both 
V
 and all 
|
E
′
|
 communication tasks 
v
i
,
j
:

V
c
=
V
∪
{
v
i
,
j
|
(
v
i
,
v
j
)
∈
E
′
}
,
and 
E
c
 contains both the precedence relations expressing the order on each processor (
E
∖
E
′
) and the new dependencies related to communication tasks:

E
c
=
(
E
∖
E
′
)
∪
{
(
v
i
,
v
i
,
j
)
,
(
v
i
,
j
,
v
j
)
|
(
v
i
,
v
j
)
∈
E
′
}
∪
E
′′
.
This DAG does not have any communication costs, since they have all been replaced by tasks. The number of tasks is 
N
=
|
V
c
|
=
n
+
|
E
′
|
, the mapping of tasks on processors is given as well as the order of tasks on processors (both original tasks from 
V
 and communication tasks from 
E
′
). The construction of the extended platform with 
P
2
 processors and the corresponding DAG 
G
c
 is straightforward.

Power profile.
In every time unit, processor 
p
i
, 
1
≤
i
≤
P
2
, consumes idle power of 
𝒫
idle
i
 units, to which a working power of 
𝒫
work
i
 units is added whenever 
P
i
 is active, for a total power 
𝒫
i
​
(
t
)
 at time 
t
. A processor executing a task or a communication is active from that operation’s start to its end. Note that communication processors are likely to consume much less than regular (computing) processors. In particular, we could set the static power of a link that is never used to 
0
.

The horizon is an interval 
[
0
,
T
[
, where 
T
 is the deadline. We assume that the horizon is divided into 
J
 intervals 
{
I
1
,
…
,
I
J
}
, where interval 
I
j
 has length 
ℓ
j
 and 
∑
j
=
1
J
ℓ
j
=
T
. We let 
I
j
=
[
b
j
,
e
j
[
 so that 
ℓ
j
=
e
j
−
b
j
 for every 
1
≤
j
≤
J
. The set of starting and ending times of the 
J
 intervals is

ℰ
=
{
b
1
=
0
,
e
1
=
b
2
,
e
2
=
b
3
,
…
,
e
J
−
1
=
b
J
,
e
J
=
T
}
.
Within each interval 
I
j
, there is a (constant) green power budget 
𝒢
j
 for each time unit 
t
∈
I
j
. If the power consumed by all processors at time 
t
 exceeds this budget, the platform must resort to brown carbonated power, which will incur some carbon cost at time 
t
. This is the key hypothesis of this work: the carbon cost of a schedule will depend in the end on which intervals are heavily used, or not, by the processors. The scheduler must maximize the benefit from greener intervals while enforcing all dependencies and meeting the global deadline 
T
.

Carbon cost.
Given a schedule, i. e., a start time for each task of 
V
c
 (i. e., including communication tasks), it is easy to compute its total carbon cost by looping over the 
T
 time units: for each time unit 
t
, sum up the power consumed by each processor, either computing or communicating, 
𝒫
t
=
∑
i
=
1
P
2
𝒫
i
​
(
t
)
 (which may include 
𝒫
work
i
 or not). The carbon cost for 
t
∈
I
j
 is assumed to be proportional to the non-green power, and hence we simply write 
𝒞
​
𝒞
t
=
max
⁡
(
𝒫
t
−
𝒢
j
,
0
)
. The total carbon cost of the schedule is then 
𝒞
​
𝒞
=
∑
t
=
0
T
−
1
𝒞
​
𝒞
t
. However, this approach has exponential (in fact, pseudo-polynomial) complexity, since the problem instance has size 
O
​
(
P
2
+
N
+
J
+
log
⁡
(
T
)
+
max
1
≤
i
≤
P
2
⁡
log
⁡
(
𝒫
idle
i
)
+
max
1
≤
i
≤
P
2
⁡
log
⁡
(
𝒫
work
i
)
+
max
1
≤
j
≤
J
⁡
log
⁡
(
𝒢
j
)
)
. To compute the cost of a schedule in polynomial time, we need to proceed interval by interval and create sub-intervals each time a task starts or ends, so that the number of active tasks is constant within each subinterval. The carbon cost per subinterval then depends on the power cost of the subinterval (
𝒞
​
𝒞
t
 is constant within a subinterval) and the interval length. Details can be found in Appendix A.1.

Optimization problem.
The objective is to find an optimal schedule, defined as a schedule whose total carbon cost 
𝒞
​
𝒞
 is minimum. To achieve this goal, the scheduler can shift around tasks (including communication tasks) to benefit from greener intervals, while enforcing all dependencies and meeting the deadline 
T
.

4Complexity Results
In this section, we present an involved dynamic programming (DP) algorithm, establishing that the problem with a single processor has polynomial time complexity. On the contrary, and as expected, the problem with several processors is strongly NP-complete, even with homogeneous processors and no communications, but we can formulate the general problem as an integer linear program (ILP).

4.1Polynomial DP algorithm for one processor
Theorem 4.1.
The problem instance with a single processor has polynomial time complexity.

Proof.
Consider the problem instance with a single processor executing tasks 
v
1
,
…
,
v
n
 in this order (with 
n
=
|
V
|
, no communication tasks in this case). We start with a pseudo-polynomial algorithm: for 
1
≤
i
≤
n
 and 
1
≤
t
≤
T
, we let 
Opt
​
(
i
,
t
)
 be the cost of an optimal schedule for the first 
i
 tasks and where task 
v
i
 completes its execution exactly at time 
t
, storing the value 
∞
 if no such schedule exists. We have the induction formula

Opt
​
(
i
,
t
)
=
min
s
≤
t
−
ω
​
(
v
i
)
⁡
{
Opt
​
(
i
−
1
,
s
)
+
cc
​
(
v
i
,
t
)
}
,
(1)
where 
cc
​
(
v
i
,
t
)
 is the cost to execute task 
v
i
 during the interval 
[
t
−
ω
(
v
i
)
,
t
[
. Since there is a single processor, this can be computed in linear time by computing the length of its intersection with the intervals 
I
j
. In Eq. (1), we loop over possible termination dates for the previous task 
v
i
−
1
. For the initialization, we simply compute the value of 
Opt
​
(
1
,
t
)
 for all 
t
≥
ω
​
(
v
1
)
, and let 
Opt
​
(
1
,
t
)
=
∞
 for 
t
<
ω
​
(
v
1
)
.

This dynamic programming algorithm is pseudo-polynomial because it tries all possible values 
t
∈
[
1
,
T
]
 for the end times of the tasks. To derive a polynomial-time algorithm, we show that we can derive an optimal algorithm while restricting to a polynomial number of end dates.

Given any single processor schedule 
𝒮
, we define a block as a set of consecutive tasks in the schedule, i. e., there is no idle time between tasks within a block. Note that if a task has idle time before and after it, it forms a block by itself. Furthermore, schedules where each block either starts or ends at a time in 
ℰ
 are called 
ℰ
-schedules (recall that 
ℰ
=
{
b
1
=
0
,
e
1
=
b
2
,
e
2
=
b
3
,
…
,
e
J
−
1
=
b
J
,
e
J
=
T
}
 is the set of starting/ending times of intervals). We can then prove the following Lemma (see proof in Appendix A.2).

Lemma 4.2.
With a single processor, there always exists an optimal 
ℰ
-schedule.

According to this lemma, we can therefore restrict the pseudo-polynomial dynamic programming algorithm to only using task end times that belong to a refined set of end times 
ℰ
′
, which is of size 
O
​
(
n
3
​
J
)
 (see Appendix A.2) thereby leading to a fully polynomial running time. ∎

4.2NP-completeness of the multiprocessor case
Theorem 4.3.
The problem instance with several processors is strongly NP-complete, even with uniform processors and independent tasks (hence no communications).

Proof.
We consider the class UCAS of decision problem instances with 
P
 processors with uniform power consumption, i.e., 
𝒫
idle
i
=
0
, 
𝒫
work
i
=
1
 for 
1
≤
i
≤
P
, and an input DAG 
G
=
(
V
,
E
,
ω
,
c
≡
0
)
. Given a bound 
C
, we ask whether there exists a valid schedule whose total carbon cost does not exceed 
C
. We prove in Appendix A.3 that UCAS is strongly NP-complete by reducing the well-known 
3
-Partition problem to it. ∎

4.3Integer linear program
We formulate the problem as an integer linear program. Due to space constraints, we only sketch the derivation and refer to Appendix A.4 for details. The ILP is written in terms of time units, hence it has a pseudo-polynomial number of variables. As stated in Section 3, the objective function is then to minimize

𝒞
​
𝒞
=
∑
t
=
0
T
−
1
max
⁡
(
∑
i
=
1
P
2
(
𝒫
idle
i
+
δ
​
(
t
,
i
)
​
𝒫
work
i
)
−
𝒢
t
,
0
)
,
(2)
where 
δ
​
(
t
,
i
)
 is a boolean variable that specifies whether processor 
p
i
 is active at time 
t
. Note that we still use the communication-enhanced graph, and the ILP enforces all dependence constraints and guarantees that all tasks are completed by the deadline 
T
.

5Algorithms
In this section, we present CaWoSched, a carbon-aware workflow scheduler for the scheduling problem of minimizing the carbon cost, given a mapping and a deadline. Recall that we work on the communication-enhanced DAG 
G
c
=
(
V
c
,
E
c
,
ω
)
. In Section 5.1, we first present the baseline algorithm, ASAP (As Soon As Possible), which schedules each task at its earliest possible start time, without taking the intervals into account. Section 5.2 presents several variants of a greedy procedure that allocates start times to tasks, building on a score that is computed for each task. Finally, we explain in Section 5.3 how to further improve the schedule obtained by the greedy algorithm, by using local search.

5.1Baseline algorithm
The ASAP baseline algorithm starts each task at their earliest possible start time (
E
​
S
​
T
). To compute these times, we proceed similarly to the computation of a topological ordering.

For all tasks 
u
∈
V
c
 with in-degree 
0
 (guaranteed to exist since 
G
c
 is acyclic), we set 
E
​
S
​
T
​
(
u
)
=
0
 and decrease by one the in-degree of successor tasks (tasks 
v
 such that 
(
u
,
v
)
∈
E
c
). A task 
v
 obtains an in-degree of 
0
 once all of its predecessors have been handled, and we can then compute its earliest start time as:

E
​
S
​
T
​
(
v
)
=
max
(
u
,
v
)
∈
E
c
⁡
{
E
​
S
​
T
​
(
u
)
+
ω
​
(
u
)
}
,
which corresponds to the time when all predecessors have completed their execution, when they are started as soon as possible.

The computation of 
E
​
S
​
T
 is done with a queue to handle tasks. The proof for correctness and existence is similar to the proof of correctness for Kahn’s algorithm for topological sorting [21] and is hence omitted here.

5.2Greedy schedule
We now describe how to compute a greedy schedule for the workflow, while accounting for the carbon cost of each interval (ASAP does not consider intervals at all). The idea is to assign a score to each task, and sort the tasks accordingly. Afterwards, we process the tasks in this order and try to find a good starting time for them.

Scores for the tasks.
The goal of the scores is to express how beneficial it is to schedule a task before other tasks.

The first score is the slack 
s
​
(
v
)
 of task 
v
, which represents the difference between the latest possible starting time of a task 
v
, 
L
​
S
​
T
​
(
v
)
, and its earliest start time 
E
​
S
​
T
​
(
v
)
.

L
​
S
​
T
 can be computed similarly to 
E
​
S
​
T
, using a queue to handle tasks. We set 
L
​
S
​
T
​
(
v
)
=
T
−
ω
​
(
v
)
 if 
v
∈
V
c
 and decrease by one the out-degree of predecessor tasks (tasks 
u
 such that 
(
u
,
v
)
∈
E
c
). A task 
u
 obtains an out-degree of 
0
 once all of its successors have been handled, and we can then compute its latest start time as:

L
​
S
​
T
​
(
u
)
=
min
(
u
,
v
)
∈
E
c
⁡
{
L
​
S
​
T
​
(
v
)
−
ω
​
(
u
)
}
.
Hence, the slack 
s
​
(
v
)
=
L
​
S
​
T
​
(
v
)
−
E
​
S
​
T
​
(
v
)
 describes the number of time units by which a task 
v
 can be shifted, since its start time has to be between 
E
​
S
​
T
​
(
v
)
 and 
L
​
S
​
T
​
(
v
)
. If the slack of a task is large, then it usually means that we have some flexibility to schedule it. We therefore try first to schedule tasks with a small slack, since there will still be room to shift tasks with a higher slack later. Note, however, that the slack does not account for the running time of the task.

The second score is the pressure of a task 
v
, defined as:

ρ
​
(
v
)
=
ω
​
(
v
)
s
​
(
v
)
+
ω
​
(
v
)
.
While slack does not take the running time into account, pressure accounts for it since it might play an important role for the power usage of the cluster. For pressure values, we have 
0
≤
ρ
​
(
v
)
≤
1
, with a pressure of 
1
 when there is no flexibility (i.e., 
s
​
(
v
)
=
0
).

Hence, on the one hand, there is a high pressure to schedule a task 
v
 if its running time is large compared to the range in which it can run. On the other hand, if a task has low pressure, it means that there is a lot of flexibility for starting the task. In this case, it is beneficial to schedule tasks with high pressure first; hence, we sort the tasks by non-increasing order of pressure.

However, both scores do not account for the heterogeneity of the processors in terms of power consumption. Hence, we also introduce two weighted scores, where the functions for a task 
v
 mapped on processor 
p
i
 are multiplied by the factor:

w
​
f
​
(
i
)
=
𝒫
idle
i
+
𝒫
work
i
max
j
⁡
(
𝒫
idle
j
+
𝒫
work
j
)
for pressure and its reciprocal for slack. For slack, we use the reciprocal since tasks are sorted in non-decreasing order.

Subdivision of the intervals.
Recall that 
I
1
,
…
,
I
J
 are the initial intervals coming from the power profile. As discussed in Section 4.1, there is a more fine-grained subdivision of these intervals, such that every task starts at the beginning of such an interval when we look at the special case of one processor. Motivated by this result and the question of how to find a good starting time for a task without looking at every time unit, we do a similar subdivision for the multiprocessor case. On each processor, we create all possible blocks of at most 
k
=
3
 consecutive tasks (the parameter 
k
 is used to limit the number of intervals, and hence the time complexity of the heuristics). Each block is tentatively scheduled to start or end at one of the original intervals, and we memorize the possible start times for each task and each block. When this is done on all processors, we sort the possible start times and compute the induced subdivision of the intervals.

Further refinement could be used by considering larger block sizes 
k
>
3
, but we observed in our experiments that 
k
=
3
 already creates a lot of subintervals.

Algorithm variants without local search.
With four scores (slack, pressure, weighted-slack, weighted-pressure) and two interval subdivisions (normal or refined), we obtain eight algorithm variants: slack (unweighted, normal), slackW (weighted, normal), slackR (unweighted, refined), slackWR (weighted, refined) for slack and analogously with prefix press for pressure.

We now detail how these algorithms select a starting time for each task, which is always a time at the beginning of an interval.

Given a score and an interval subdivision, we pick the next task, say 
v
, according to the best score value. The interval set is denoted as 
{
I
1
,
…
,
I
J
′
}
, where 
J
′
=
J
 if intervals are not refined, and 
J
′
≥
J
 otherwise. We have 
I
j
=
[
b
j
,
e
j
[
. First, the algorithm computes the subset of the intervals such that 
E
​
S
​
T
​
(
v
)
≤
b
j
≤
L
​
S
​
T
​
(
v
)
, i.e., intervals at the beginning of which the task can be started.

If this set is empty (which is rarely the case in practice), we simply start the task at time 
E
​
S
​
T
​
(
v
)
. Otherwise, we sort the intervals according to their budget 
𝒢
j
 and schedule the task to start at the beginning of the interval with the highest budget. If there are multiple intervals that are possible, we use the interval with the earliest starting point.

Afterwards, we look at all intervals during which task 
v
 runs. For the first and last intervals, if 
v
 does not cover the whole interval, we split the interval in two sub-intervals (one where the task is running, the other where it is not). Then, on each interval where the task runs, we decrease the power budget by 
𝒫
idle
i
+
𝒫
work
i
, where 
p
i
 is the processor on which task 
v
 is mapped, to account for the fact that there is now a task running in this interval and consuming some power – hence the green budget is lower.

Also, once the task has been scheduled, this influences the 
E
​
S
​
T
 and 
L
​
S
​
T
 of other tasks as well. Hence, we update this for all tasks that have not been scheduled yet. In particular, these updates have to be made possibly for the whole graph, and we use a precomputed topological order for this. These updates take 
O
​
(
n
+
|
E
c
|
)
 time.

5.3Local search
Once a greedy schedule has been obtained, we propose to refine this schedule by doing a local search, exploiting the flexibility that tasks still provide within the greedy schedule. The corresponding algorithm variants receive a suffix of -LS, for example pressWR-LS.

For the local search, we introduce a parameter 
0
≤
μ
≤
T
−
1
. First, we sort the processors by non-increasing power consumption 
𝒫
work
i
, i.e., the more costly processor is considered first. For each processor in this order, we then iterate over the tasks of the processors from left to right and look 
τ
 time units to the left and right, and check whether moving the task would give us a gain and is valid. This means that we make sure for every possible move that the corresponding start time of a task 
v
 stays in the interval 
[
E
​
S
​
T
​
(
v
)
,
L
​
S
​
T
​
(
v
)
]
. To this end, we iterate over the time units from the earliest to the latest. If we find a legal move with a positive gain, we apply it and update the cost. (One could also check all legal moves and apply the best one. However, preliminary experiments showed that this would not significantly improve the outcome, so we opted for the faster variant.) Once this has been done for all tasks on the current processor, we process the tasks of the next processor in the ranking. At each round, we record whether we had a positive gain or not. If there was one round through the tasks without gain, we stop the local search.

6Experimental Evaluation
In this section, we evaluate the proposed carbon-aware scheduling framework CaWoSched with its numerous algorithm variants. We mainly focus on solution quality and running time in comparison to the baseline ASAP. For small instances, we also compare the quality against optimal solutions derived from the ILP formulation. The code and data used in the simulations are publicly available for reproducibility purposes at https://github.com/KIT-EAE/CaWoSched.

6.1Simulation setup
Target computing platform.
We consider two target computing platforms with a heterogeneous setup; their properties are inspired by real-world machines used for the experimental evaluation in [6]. There are six processor types, and we consider 
12
 (resp. 
24
) nodes of each type for the small (resp. large) cluster, hence a total of 
72
 (resp. 
144
) compute nodes.

In addition to the normalized speed values (see Table 1), we assign each processor a value for its idle power consumption 
𝒫
idle
 and its active power consumption 
𝒫
work
. The values for the power consumption are inspired by values coming from Intel [20] for modern processors. Note that we did not choose 
𝒫
work
 too large since the CPU utilization in data centers is often far from 
100
%
 [1]. While the correlation between power consumption and processor speeds may not be obvious, the general trend is that faster processors consume more power, hence a ranking of the processor types: nodes of type 
P
​
T
​
1
 are the slowest/least consuming nodes, up to 
P
​
T
​
6
, which are the fastest/most consuming ones. According to [1], the power consumption of the network is much smaller than that of computation, hence we draw the values for 
𝒫
idle
 and 
𝒫
work
 randomly between 
1
 and 
2
 for communication links, in order to introduce a small amount of heterogeneity.

Table 1:Processor specifications in the clusters.
Processor Name	Speed	
𝒫
idle
𝒫
work
small	large
P
​
T
​
1
4	40	10	
×
12
×
24
P
​
T
​
2
6	60	30	
×
12
×
24
P
​
T
​
3
8	80	40	
×
12
×
24
P
​
T
​
4
12	120	50	
×
12
×
24
P
​
T
​
5
16	150	70	
×
12
×
24
P
​
T
​
6
32	200	100	
×
12
×
24
Workflows and mappings.
We evaluate the presented algorithmic framework on 
34
 workflows. The corresponding DAGs can be divided into real-world workflows obtained from [6] (atacseq, bacass, eager and methylseq) and workflows obtained by simulating real-world instances using the WFGen generator [11]. We transformed the corresponding definition for the workflow management system Nextflow [12] to a .dot format with a Nextflow tool. Since the resulting DAGs contain many pseudo-tasks that are only internally relevant for Nextflow, we deleted them, following what was done in [22]. For the simulated workflows, we use one of the respective real-world instances as a model graph and scale it up in size. As number of vertices, we use 200, 1,000, 2,000, 4,000, 8,000, 10,000, 15,000, 18,000, 20,000, 25,000 and 30,000. Every graph has vertex and edge weights following a normal distribution, where we make sure that the vertex weights are in general larger than the edge weights. Note that these are normalized values, and the actual running time of the task is determined by its vertex weight and its assigned processor. We normalize the network communication bandwidth to 
1
 since its influence is not considered here.

Furthermore, we generate for every graph two mappings, one for cluster small and one for cluster large. The mappings are generated with our own basic HEFT implementation without special techniques for tie-breaking, because that would not change the fact that HEFT is not carbon-aware. Since there are more fast and power-intensive processors on the large cluster, HEFT schedules more tasks to these processors and hence there are fewer tasks per processor on the other processors, compared to the small cluster.

Power profiles.
For each workflow, we generate four differently shaped (renewable) energy profiles for different scenarios. We make sure that green power is always at least the sum of the idle power of the processors and at most the sum of idle power and 
80
%
 of the sum of the work power. The rationale is as follows: if we do not have enough green power or more green power than required overall, the decisions of the scheduler become irrelevant. Hence, we try to create scenarios where scheduling decisions have to be done in a smart way. The scenarios are the following:

S1: A 
−
x
2
 shape, where the interval budgets follow this function with random perturbations. This models a situation where there is little green power in the beginning, then the supply with green energy is rising and falls at some point again (solar power from morning to evening, for example).
S2: An 
x
2
 shape that models the same situation as in S1, but starting from midday, again with random perturbations.
S3: A 
sin
⁡
(
x
)
 shape, where we model 24 hours of this scenario, i.e., we have little green power in the beginning and then we follow a sinus shape as given on 
[
0
,
2
​
π
]
. We also add random perturbations.
S4: A constant green power budget with perturbations (which can model situations where one has storage for renewable energy or nuclear power – see setting of France in [38]).
For each scenario, we have four different deadlines. Let 
D
 be the time required by the ASAP schedule, which is the tightest deadline. We consider deadlines 
D
, 
1.5
​
D
, 
2
​
D
, and 
3
​
D
, providing more or less flexibility to shift tasks around in the schedule.

Hence, we have in total 
16
 power profiles. For the workflow types atacseq and methylseq, we have 12 graphs per type, for bacass we only use the real-world version due to problems with scaling, and for eager we have 9 graphs with up to 18,000 vertices. This results in 
2
×
34
×
16
=
1088
 simulations (2 platforms, 34 workflows, 16 power profiles) per algorithm. All algorithms are implemented in C++ and compiled with g++ (v.13.2.0) with compiler flag -O3. The experiments are managed by simexpal [4] and executed on workstations with 192 GB RAM and 2x 12-Core Intel Xeon 6126 @3.2 GHz and CentOS 8 as OS. Code, input data, and experiment scripts are available to allow reproducibility of the results at https://github.com/KIT-EAE/CaWoSched. The ILP is implemented using Gurobi’s Python API [16] and for license reasons executed on a machine with a 13th Gen Intel(R) Core(TM) i7-1355U processor with 16GB RAM running Ubuntu 24.04.1 LTS. Further, for the simulation results below, we set the tuning parameter for the subdivision to 
k
=
3
 and the tuning paramater for the local search to 
μ
=
10
.

6.2Simulation results
We compare the quality of the schedules returned by the CaWoSched variants. Recall that there are two base scores, slack and pressure, that can be weighted by a factor accounting for the heterogeneity in power consumption of the processors, and we can use either the original or refined intervals (see Section 5). The heuristics then apply a local search to further improve the solution. We first compare the solution quality when the local search is applied, but we also analyze the influence of the local search on different algorithm variants. Next, we study the impact of various parameters. We also compare the heuristics’ solution to the optimal solution returned by the ILP on small instances.

With local search.
As a first measure of performance, we rank the different algorithm variants for each instance. This means that we record the frequency with which each algorithm variant ranks first, second, third, etc., in terms of carbon cost. Note that this means that if two variants have the same cost, they will end up with the same rank and the next rank is then skipped. The results can be seen in Figure 1; the main observations are the following.

Refer to caption
Figure 1:The distribution shows for which percentage of the instances each algorithm variant was ranked first, second, third, etc. Note that multiple algorithm variants can have the same rank.
First, we can see that all our algorithm variants are ranked first significantly more often than this is the case for the baseline ASAP. Note that even if the baseline has rank 
1
, it does not necessarily mean that a variant of the algorithm performed worse, since they all could have found the optimal solution. In particular, we can see that the baseline performed worst in 
84.01
%
 of the cases. Another observation is that none of the algorithm variants does significantly outperform the others in terms of ranking. The pressWR-LS variant is ranked first most frequently (
34.47
%
), but with a small margin.

If we look at performance profiles, we obtain more detailed insights about the quality of each variant, see Figure 2.

Refer to caption
Figure 2:The ratio is the best cost found divided by the algorithm variants’ own cost. Then the percentage of instances for which this is larger than or equal to 
τ
 is plotted. A higher curve is better.
We report the proportion of instances with a cost ratio at most 
1
, where the cost ratio is the best carbon cost divided by the algorithm’s carbon cost. Note that if the algorithm’s carbon cost is 0, then the best cost is also 0 and the ratio is set to 
1
. Otherwise, a ratio of 
1
/
2
 means that the heuristic’s cost is twice higher than the best cost, and a ratio of 
0
 corresponds to a non-null carbon cost, while the best is 
0
. Even though we can see here again that for 
τ
=
1.0
, i.e., the proportion of instances for which the algorithm variant achieves the best cost, is the highest for pressWR-LS, we also observe that for lower 
τ
 values, i.e. more suboptimality tolerance, the curves for the algorithm variants using slack as base score surpass the pressure variant, which hints at a better overall performance on average. Interestingly, this observation seems to be influenced by the tolerance in the deadline. This is why we next illustrate how the deadline impacts the performance profile, as shown in Figure 3.

Refer to caption
Refer to caption
Refer to caption
Figure 3:The evolution of the performance profiles when adding more tolerance to the deadline from left to right (data for deadline factor 
2.0
 can be found in Appendix A.5).
While we can observe for a tight deadline that pressR and pressWR have a higher curve, these variants are clearly surpassed by slack variants when there is more tolerance in the deadline.

Another important aspect for the evaluation is the cost improvement over the baseline algorithm ASAP. For this, we first look at the median of the cost ratio between the baseline ASAP and the different algorithm variants over all instances. This is shown in Figure 4.

Refer to caption
Figure 4:The median of the cost ratios obtained by dividing heuristics carbon cost by the carbon cost of the deadline.
(Note that a geometric mean is not applicable here because the ratio can be 
0
 if our heuristic has carbon cost zero but the baseline has not. Further, since there are cases when the baseline performs better than our heuristics, we cannot use the arithmetic mean, either.) We can see that all algorithms are closely together with a cost ratio median of 
≈
0.6
, meaning that the algorithm needs only 
60
%
 of the carbon cost compared to the baseline (or, vice versa, they are 
≈
1.67
×
 better). We also see that regarding this cost ratio, the algorithm versions using pressure as base score perform better than the slack variants – pressWR-LS has the best cost ratio median with 
0.58
. Again, we observe the impact of exploiting more flexibility in terms of deadline in Figure 5, where it becomes clear that the cost ratio improves with more flexibility.

Refer to caption
Refer to caption
Refer to caption
Figure 5:The evolution of the median of the cost ratios when adding more tolerance to the deadline from left to right (data for deadline factor 
2.0
 can be found in Appendix A.5).
There, we can see that while the gains for a tight deadline are moderate, the algorithm slackW has a cost ratio of only 
0.15
 compared to the baseline (or, vice versa, 
≈
6.67
×
 better). This is a behavior that we expected from the algorithms, since we have more opportunities for scheduling the tasks with an increased deadline.

To further investigate the improvement over the baseline, we look at boxplots for the improvement. The results for all instances are shown in Figure 6.

Refer to caption
Figure 6:Boxplot of the cost ratios obtained by dividing the heuristics carbon cost by the carbon cost of the baseline. Outliers are shown in the separate plot on the right.
What we can see here is that the solutions for most instances lie in between 
≈
0.25
 and 
≈
0.9
, with most medians around 
0.6
 (compared to the baseline). We also see that, for some instances, the baseline performs better than the proposed algorithms. One reason for this is that some power profiles provide a lot of green power in the beginning of the horizon 
[
0
,
T
[
. Hence, for these profiles, scheduling the tasks as soon as possible might be the best strategy. However, overall one can observe that this is rarely the case and that the new algorithms significantly improve over ASAP in terms of carbon cost.

Influence of local search.
While we have studied so far the heuristics’ behavior when the local search was applied, we also run four of the heuristics without the local search to assess how much gain, in terms of carbon cost, can be achieved thanks to the local search. Note that we use a subset of the full test set for this approach, namely all variants of the atacseq workflow type and the bacass workflow. However, note that this still results in more than 
400
 experiments per algorithm variant. We report the minimum, maximum and average improvement in Table 2. Note that here we use the arithmetic mean since the geometric mean is not applicable because we can have a cost ratio of 
0
. (The results are still meaningful since we only have values between 
0
 and 
1
.)

Table 2:Minimum, maximum and average cost ratio for comparing the algorithm with and without local search.
Algorithm Variant	Min	Max	Avg
slackR	0	1.0	0.25
slackWR	0	1.0	0.25
pressR	0	1.0	0.25
pressWR	0	1.0	0.23
We can see that for every variant the cost ratio ranges from 
0
 to 
1.0
. A cost ratio of 
0
 comes from instances where the algorithm achieves zero carbon cost using local search, but the algorithm variant without local search has positive carbon cost. Note that a cost ratio larger than 
1.0
 is not possible since the local search approach is designed as a hill climber. In general, we can see that our local search approach significantly improves the solution of the initial schedule (on average up to 
≈
4.35
×
 better). In particular, we can observe in our experiments that there is a significant number of instances where the local search approach reaches an optimal solution of 
0
, but the initial schedule has still positive carbon cost. Further, we can see that the local search improves all algorithm variants by a similar margin.

Impact of parameters.
A complete study highlighting the impact of all parameters through detailed results is available in Appendix A.5. First, as expected, the ASAP baseline performs better when there is a lot of green power at the beginning of the time horizon or when there is no huge change as in Scenarios S4 or S2. We provide detailed results for each power profile, while we have presented so far aggregated results. Further, we can see that our algorithm achieves a significantly better cost ratio when there is not much green power in the beginning such as in Scenarios S1 and S3.

Also, we look separately at the cost ratios depending on the cluster size. We can see here that the cluster size has no significant influence on the performance of our heuristics. However, it influences the performance profile. While for the large cluster, the curves are closer together, we see a similar situation as in Figure 2 for the smaller cluster.

Finally, we also study the impact of the number of tasks on the solution. The general trend is that the cost ratio gets slightly worse when the number of tasks increases. However, the effect is not significant, and we can conclude that the improvement of our heuristic over the baseline is in all cases significant.

Comparison with optimal solutions.
We explore the quality of the novel heuristics when compared to an exact solution. For this, we use the ILP formulation presented in Section 4.3, and use the ILP solver Gurobi [16]. Further, our implementation in Python makes use of the NetworkX library [17]. We restrict to instances with up to 
200
 tasks, since the solver takes too long on larger instances (already up to one hour for 
200
 tasks vs only milliseconds for each heuristic). Note that the scope of this work is not to explore an efficient ILP formulation for this algorithm, we solely want to explore the quality of the novel algorithms. This is why we keep a simple but correct ILP with time units instead of moving to an interval formulation.

We show an analysis of the results in Figure 7.

Refer to caption
Figure 7:Cost ratio obtained by dividing the ILP result through the heuristic result. Red dots show the actual cost ratios.
What we can see here is that the median cost ratio is still reasonable when we compare our heuristics to exact solutions. Further, this seems to be an achievement of our heuristics since we can see that the baseline has a much worse cost ratio than our heuristics. Further, it is interesting to see that there are a significant number of instances where the cost ratio is 
1.0
, meaning that our heuristic is able to achieve the optimal solution.

6.3Running Time Evaluation
In this section, we present the time needed by the various algorithm variants for computing a carbon-aware schedule. Even though it is not the main goal of the scheduler to be as fast as possible, it is important that it is not overly time-consuming to be applicable in real-world scenarios.

Refer to caption
Figure 8:Time (in seconds) for each algorithm variant.
Aggregated running time values based on all workflows are shown in Figure 8. We can observe that all algorithm variants yield a reasonable slowdown compared to the baseline. For most of the instances, the scheduler is able to compute a schedule within seconds, while larger workflows with up to 
30
,
000
 tasks can take several minutes.

In Appendix A.5 we can see that the largest running times result from large workflows with 
20
,
000
 to 
30
,
000
 tasks. Overall, most of the instances are still solvable in less than a few minutes.

Another interesting aspect is that the running time seems to be mainly influenced by graph size, but not by the length of the time horizon 
T
. The running time increases only slightly with an increased deadline, which indicates that the algorithms successfully make decisions based on structural graph information – without having a too broad search tree for each task if the deadline increases. The data leading to this insight can be found in Appendix A.5

7Conclusions
This work aimed at minimizing carbon emissions when executing a scientific workflow on a parallel platform with a time-varying mixed (renewable and non-renewable) energy supply. We focused on improving a given mapping and ordering of the tasks (for instance generated by HEFT) by shifting task executions to greener time intervals whenever possible, while still enforcing all dependencies. We showed that this algorithmic problem can be solved in polynomial time in the uniprocessor case. For two processors, the problem becomes NP-hard, even for a simple instance with independent tasks and carbon-homogeneous processors. We proposed a heuristic framework combining several greedy approaches with local search. The experimental results showed that our heuristics provide significant savings in carbon emissions compared to the baseline. Furthermore, for smaller problem instances, we showed that several heuristics achieve a performance close to the optimal ILP solution. Altogether, all these results represent a major advance in the understanding of the problem.

Future work will be devoted to the next step, namely targeting the design of a carbon-aware extension of HEFT. Mapping and scheduling the workflow at the same time while minimizing carbon emissions may well lead to even better solutions. Given the difficulty of the problem, we envision a two-pass approach: a first pass devoted to mapping and ordering, but without a finalized schedule, and a second pass devoted to optimizing the schedule through the approach followed in this paper.

Acknowledgements.
This work is partially supported by Collaborative Research Center (CRC) 1404 FONDA – Foundations of Workflows for Large-Scale Scientific Data Analysis, which is funded by German Research Foundation (DFG).

References
[1]
D. Abts, M. R. Marty, P. M. Wells, P. Klausler, and H. Liu.Energy proportional datacenter networks.In Proc. of the 37th Annual International Symposium on Computer Architecture, page 338–347, 2010.
[2]
M. Adhikari, T. Amgoth, and S. N. Srirama.A survey on scheduling strategies for workflows in cloud environment and emerging trends.ACM Comput. Surv., 52(4), aug 2019.
[3]
K. M. U. Ahmed, M. H. J. Bollen, and M. Alvarez.A review of data centers energy consumption and reliability modeling.IEEE Access, 9:152536–152563, 2021.
[4]
E. Angriman, A. van der Grinten, M. von Looz, H. Meyerhenke, M. Nöllenburg, M. Predari, and C. Tzovas.Guidelines for experimental algorithmics: A case study in network analysis.Algorithms, 12(7):127, 2019.
[5]
H. Arabnejad and J. G. Barbosa.List scheduling algorithm for heterogeneous systems by an optimistic cost table.IEEE Transactions on Parallel and Distributed Systems, 25(3):682–694, 2013.
[6]
J. Bader, F. Lehmann, L. Thamsen, U. Leser, and O. Kao.Lotaru: Locally predicting workflow task runtimes for resource management on heterogeneous infrastructures.Future Generation Computer Systems, 150:171–185, 2024.
[7]
J. Bader, K. West, S. Becker, S. Kulagina, F. Lehmann, L. Thamsen, H. Meyerhenke, and O. Kao.Predicting the performance of scientific workflow tasks for cluster resource management: An overview of the state of the art, 2025.https://arxiv.org/abs/2504.20867.
[8]
J. G. Barbosa and B. Moreira.Dynamic scheduling of a batch of parallel task jobs on heterogeneous clusters.Parallel computing, 37(8), 2011.
[9]
E. Breukelman, S. Hall, G. Belgioioso, and F. Dörfler.Carbon-aware computing in a network of data centers: A hierarchical game-theoretic approach.In 2024 European Control Conference (ECC), pages 798–803. IEEE, 2024.
[10]
Z. Cao, X. Zhou, H. Hu, Z. Wang, and Y. Wen.Toward a systematic survey for carbon neutral data centers.IEEE Communications Surveys & Tutorials, 24(2):895–936, 2022.
[11]
T. Coleman, H. Casanova, L. Pottier, M. Kaushik, E. Deelman, and R. Ferreira da Silva.Wfcommons: A framework for enabling scientific workflow research and development.Future Generation Computer Systems, 128:16–27, 2022.
[12]
P. Di Tommaso, M. Chatzou, E. W. Floden, P. P. Barja, E. Palumbo, and C. Notredame.Nextflow enables reproducible computational workflows.Nature biotechnology, 35(4):316–319, 2017.
[13]
J. J. Durillo, V. Nae, and R. Prodan.Multi-objective energy-efficient workflow scheduling using list-based heuristics.Future Generation Computer Systems, 36:221–236, July 2014.
[14]
J. J. Durillo, R. Prodan, and J. G. Barbosa.Pareto tradeoff scheduling of workflows on federated commercial Clouds.Simulation Modelling Practice and Theory, 58:95–111, Nov. 2015.
[15]
M. R. Garey and D. S. Johnson.Computers and Intractability, a Guide to the Theory of NP-Completeness.W.H. Freeman and Company, 1979.
[16]
Gurobi Optimization, LLC.Gurobi Optimizer Reference Manual, 2024.
[17]
A. A. Hagberg, D. A. Schult, and P. J. Swart.Exploring network structure, dynamics, and function using networkx.In G. Varoquaux, T. Vaught, and J. Millman, editors, Proceedings of the 7th Python in Science Conference, pages 11 – 15, Pasadena, CA USA, 2008.
[18]
S. Hall, F. Micheli, G. Belgioioso, A. Radovanović, and F. Dörfler.Carbon-aware computing for data centers with probabilistic performance guarantees.arXiv preprint arXiv:2410.21510, 2024.
[19]
W. A. Hanafy, Q. Liang, N. Bashir, D. Irwin, and P. Shenoy.CarbonScaler: Leveraging Cloud Workload Elasticity for Optimizing Carbon-Efficiency.Proc. ACM Meas. Anal. Comput. Syst., 7(3):57:1–57:28, Dec. 2023.
[20]
Intel Corporation.Measuring Processor Power - TDP vs. ACP.White paper, Intel Corporation, 2011.
[21]
A. B. Kahn.Topological sorting of large networks.Communications of the ACM, 5(11):558–562, Nov. 1962.
[22]
S. Kulagina, A. Benoit, and H. Meyerhenke.Memory-aware adaptive scheduling of scientific workflows on heterogeneous architectures, 2025.https://arxiv.org/abs/2503.22365.
[23]
S. Kulagina, H. Meyerhenke, and A. Benoit.Mapping large memory-constrained workflows onto heterogeneous platforms.In 53rd Int. Conference on Parallel Processing (ICPP), 2024.
[24]
H. Lavi.Measuring greenhouse gas emissions in data centres: the environmental impact of cloud computing, 2023.https://www.climatiq.io/blog/measure-greenhouse-gas-emissions-carbon-data-centres-cloud-computing.
[25]
J. Liu, E. Pacitti, and P. Valduriez.A survey of scheduling frameworks in big data systems.International Journal of Cloud Computing, 7(2):103–128, 2018.
[26]
A. H. Mahmud and S. S. Iyengar.A distributed framework for carbon and cost aware geographical job scheduling in a hybrid data center infrastructure.In IEEE Int. Conference on Autonomic Computing (ICAC), pages 75–84, 2016.
[27]
M. Y. Özkaya, A. Benoit, B. Uçar, J. Herrmann, and Ü. V. Çatalyürek.A scalable clustering-based task scheduler for homogeneous processors using DAG partitioning.In 33rd IEEE Int. Parallel and Distributed Processing Symp., 2019.
[28]
P. Pop, K. H. Poulsen, V. Izosimov, and P. Eles.Scheduling and voltage scaling for energy/reliability trade-offs in fault-tolerant time-triggered embedded systems.In Proceedings of the 5th IEEE/ACM International Conference on Hardware/Software Codesign and System Synthesis, page 233–238, 2007.
[29]
A. Radovanović, R. Koningstein, I. Schneider, B. Chen, A. Duarte, B. Roy, D. Xiao, M. Haridasan, P. Hung, N. Care, et al.Carbon-aware computing for datacenters.IEEE Transactions on Power Systems, 38(2):1270–1280, 2022.
[30]
Y. Samadi, M. Zbakh, and C. Tadonki.E-heft: Enhancement heterogeneous earliest finish time algorithm for task scheduling based on load balancing in cloud computing.In 2018 International Conference on High Performance Computing & Simulation (HPCS), pages 601–609, 2018.
[31]
S. Sandokji and F. Eassa.Dynamic Variant Rank HEFT Task Scheduling Algorithm Toward Exascale Computing.Procedia Computer Science, 163:482–493, 2019.
[32]
Z. Shi and J. J. Dongarra.Scheduling workflow applications on processors with different capabilities.Future Generation Computer Systems, 22(6):665–675, 2006.
[33]
O. Sinnen.Task scheduling for parallel systems, volume 60.John Wiley & Sons, 2007.
[34]
H. Topcuoglu, S. Hariri, and M.-Y. Wu.Performance-effective and low-complexity task scheduling for heterogeneous computing.IEEE Transactions on Parallel and Distributed Systems, 13(3):260–274, 2002.
[35]
L. Versluis and A. Iosup.Taskflow: An energy-and makespan-aware task placement policy for workflow scheduling through delay management.In Proc. of the 2022 ACM/SPEC Int. Conference on Performance Engineering, pages 81–88, 2022.
[36]
J. Viil and S. N. Srirama.Framework for automated partitioning and execution of scientific workflows in the cloud.The Journal of Supercomputing, 74:2656–2683, 2018.
[37]
Z. Wen, S. Garg, G. S. Aujla, K. Alwasel, D. Puthal, S. Dustdar, A. Y. Zomaya, and R. Ranjan.Running Industrial Workflow Applications in a Software-Defined Multicloud Environment Using Green Energy Aware Scheduling Algorithm.IEEE Transactions on Industrial Informatics, 17(8):5645–5656, Aug. 2021.
[38]
P. Wiesner, I. Behnke, D. Scheinert, K. Gontarska, and L. Thamsen.Let’s wait awhile: How temporal workload shifting can reduce carbon emissions in the cloud.In Proc. of the 22nd Int. Middleware Conference, pages 260–272, 2021.
AAppendix
A.1Cost of a Schedule
In this section, we detail how to compute the cost of a schedule in polynomial time. The schedule 
σ
 gives the starting time of each task: task 
u
∈
V
c
 starts at time 
σ
​
(
u
)
, and hence completes at time 
σ
​
(
u
)
+
ω
​
(
u
)
.

We proceed interval by interval. Recall that we are given 
J
 intervals 
{
I
1
,
…
,
I
J
}
, where interval 
I
j
 has length 
ℓ
j
, and 
∑
j
=
1
J
ℓ
j
=
T
. We have 
I
j
=
[
b
j
,
e
j
[
 so that 
ℓ
j
=
e
j
−
b
j
 for every 
1
≤
j
≤
J
, and the set of starting and ending times of the 
J
 intervals is

ℰ
=
{
b
1
=
0
,
e
1
=
b
2
,
e
2
=
b
3
,
…
,
e
J
−
1
=
b
J
,
e
J
=
T
}
.
For each interval 
I
j
=
[
b
j
,
e
j
[
:

• We compute the intersection of the execution of each task with 
I
j
. Since the schedule 
σ
 is given, we can complete this step in linear time. We let 
𝒬
j
 be the subset of tasks intersecting with 
I
j
, i.e.,
u
∈
𝒬
j
⇔
[
σ
(
u
)
,
σ
(
u
)
+
ω
(
u
)
[
∩
I
j
≠
∅
.
• For each task 
u
∈
𝒬
j
, we let 
[
𝑠𝑡𝑎𝑟𝑡
u
j
,
𝑒𝑛𝑑
u
j
[
⊆
[
b
j
,
e
j
[
 denote its execution interval within 
I
j
.
• We sort the list 
{
𝑠𝑡𝑎𝑟𝑡
u
j
,
𝑒𝑛𝑑
u
j
}
 for 
u
∈
𝒬
j
, adding 
b
j
 and 
e
j
 if these values are not already in the list, and removing duplicates. Let 
q
j
 be the number of elements of the list. We derive the ordered list 
ℰ
j
:=
{
d
1
=
b
j
,
d
2
,
…
,
d
q
j
=
e
j
}
 and record the length 
λ
k
 of each subinterval 
[
d
k
,
d
k
+
1
[
 for 
1
≤
k
<
q
j
.
•
• Now, the consumed power is constant in each subinterval 
[
d
k
,
d
k
+
1
[
, equal to 
𝒫
i
​
(
d
k
)
 on processor 
i
, for a green budget of 
𝒢
j
 in this subinterval. Hence, the carbon cost for this subinterval is the total power above the green budget, which is 
max
⁡
(
∑
i
=
1
P
2
𝒫
i
​
(
d
k
)
−
𝒢
j
,
0
)
, multiplied by the interval length 
λ
k
. Finally, we can compute the total carbon cost of the interval 
I
j
 as
𝒞
​
𝒞
j
=
∑
k
=
1
q
j
−
1
λ
k
​
max
⁡
(
(
∑
i
=
1
P
2
𝒫
i
​
(
d
k
)
)
−
𝒢
j
,
0
)
.
The total carbon cost of the schedule is 
𝒞
​
𝒞
=
∑
j
=
1
J
𝒞
​
𝒞
j
, it is obtained in polynomial time using this approach.

A.2Proof of Lemma 4.2
In this section, we first prove Lemma 4.2 and show that with a single processor there always exists an optimal 
ℰ
-schedule. Then, we show that the dynamic programming algorithm can restrict to a polynomial number of task end times.

Proof of Lemma 4.2.
Recall that the set of starting and ending times of the 
J
 intervals is:

ℰ
=
{
b
1
=
0
,
e
1
=
b
2
,
e
2
=
b
3
,
…
,
e
J
−
1
=
b
J
,
e
J
=
T
}
.
Consider an optimal schedule 
𝒮
 with a single processor. If all blocks are aligned to the beginning or end of an interval, we already have an 
ℰ
-schedule. Otherwise, there is a block of tasks

v
r
→
v
r
+
1
→
…
→
v
s
(we can have 
r
=
s
) that is not aligned: 
v
r
 starts at time 
b
k
+
α
, i.e., 
α
 units of time after the beginning of interval 
I
k
, and 
v
s
 ends at time 
b
ℓ
+
β
, i.e., 
β
 units of time after the beginning of interval 
I
ℓ
, where 
k
≤
ℓ
. By hypothesis, 
α
 and 
β
 are both nonzero, since the block is not aligned.

By symmetry, assume w.l.o.g. that 
𝒢
k
≥
𝒢
ℓ
, meaning that we should try to shift the block to the left. If no other task is scheduled during the beginning of 
I
k
, let 
γ
=
0
. Otherwise, let 
b
k
+
γ
 denote the end time of the last task 
v
q
 that is scheduled before 
v
r
. Note that 
γ
<
α
 because this last task does not belong to the block. We can shift the block left by 
α
−
γ
 time units without exiting 
I
k
. Similarly, we can shift the block left by 
β
 up to reaching the beginning of 
I
ℓ
. Hence, we shift the block left by 
δ
=
min
⁡
(
α
−
γ
,
β
)
 time units. After this shift, the block will either be aligned with the beginning of 
I
k
, or merged with (the block of) task 
v
q
, or aligned to the beginning of 
I
ℓ
 (see Figure 9). Also, after this shift, the carbon cost cannot have increased, since we moved some load to an interval with a higher green power budget. Since the initial schedule is optimal, the carbon cost remains the same, the new schedule is optimal and it has either one more block aligned, or one less block (or both) than the original optimal schedule 
𝒮
. Proceeding by induction, this proves that there exists an optimal schedule where all blocks are aligned, namely an optimal 
ℰ
-schedule.

{tikztimingtable}
[ timing/slope=0, timing/rowdist=0.5, timing/coldist=2pt, xscale=3,yscale=2, thin, ] D
⋯
 [fill=blue!20] 1.5D
v
q
1.5D [fill=blue!20] 1D
v
r
[fill=blue!20] 0.7D
v
r
+
1
[fill=blue!20] 0.4D
⋯
[fill=blue!20] 0.9D
v
s
 D  D
⋯

\extracode

Figure 9:Illustration of the block shift to create an 
ℰ
-schedule.
Restriction to a polynomial number of task end times.
Given an optimal 
ℰ
-schedule with a single processor, each task 
v
u
 belongs to a block 
[
v
r
,
v
s
]
, where 
r
≤
u
≤
s
. There are 
O
​
(
n
2
)
 possible such blocks. Either 
v
r
 starts or 
v
s
 ends (or both) at some time in 
ℰ
. Hence, the end time of 
v
u
 can be deduced from the block that it belongs to and the set 
ℰ
 (simply add or subtract the length of previous or following tasks in the block). This leads to 
O
​
(
n
2
​
J
)
 possible end times for 
v
u
. Summing up over all 
n
 tasks, we get 
O
​
(
n
3
​
J
)
 possible end times for all the tasks. We define 
ℰ
′
 as the set of all these possible task end times.

Fully-polynomial dynamic programming algorithm on a single processor.
Given a schedule on a single processor, we transform it into an 
ℰ
-schedule as explained above, without increasing its carbon cost. We obtain the set 
ℰ
′
 of all possible task end times, which is of cardinality at most 
O
​
(
n
3
​
J
)
. We can safely restrict the values of 
t
 in the pseudo-polynomial dynamic programming algorithm described in Section 4.1 to these end times, and still derive an optimal schedule. This concludes the proof for the design of the fully-polynomial dynamic programming algorithm.

A.3Proof of Theorem 4.3
In this section, we prove Theorem 4.3, namely that UCAS is strongly NP-complete. Recall that UCAS denotes the class of decision problem instances with 
P
 processors with uniform power consumption, i.e., 
𝒫
idle
i
=
0
, 
𝒫
work
i
=
1
 for 
1
≤
i
≤
P
, and independent tasks (no dependence nor communication). Given a bound 
C
, we ask whether there exists a valid schedule whose total carbon cost does not exceed 
C
.

First, UCAS clearly belongs to NP, a certificate being the schedule itself with the start and end times of the tasks. For the strong completeness, we make a reduction from the 3-Partition problem, which is strongly NP-complete [15]. Consider an instance 
ℐ
3
​
P
 of 3-Partition as follows. Let 
S
=
{
x
1
,
…
,
x
3
​
n
}
 be the multiset of 
3
​
n
 positive integers, and let 
B
 be a bound such that

B
=
∑
i
=
1
3
​
n
x
i
n
and
B
4
<
x
i
<
B
2
​
 for 
​
1
≤
i
≤
3
​
n
.
Is there a partition of 
S
 into triplets 
S
=
S
1
∪
⋯
∪
S
n
 such that the sum over the elements of each triplet 
S
i
 is equal to 
B
? We construct the following instance 
ℐ
UCAS
 of UCAS:

• We have 
3
​
n
 power-homogeneous processors 
p
1
,
…
,
p
3
​
n
 with 
𝒫
idle
i
=
0
 and 
𝒫
work
i
=
1
 for 
1
≤
i
≤
3
​
n
.
• We have a workflow of 
3
​
n
 independent tasks 
v
1
,
…
,
v
3
​
n
 with 
ω
​
(
v
i
)
=
x
i
 for 
1
≤
i
≤
3
​
n
. Task 
v
i
 executes on processor 
p
i
 for 
1
≤
i
≤
3
​
n
.
• The horizon is a set of 
J
=
2
​
n
−
1
 intervals of total length 
T
=
n
​
B
+
n
−
1
. Odd-numbered intervals 
I
1
,
I
3
,
…
,
I
2
​
n
−
1
 each have length 
B
 and green power budget 
1
, while even-numbered intervals 
I
2
,
I
4
,
…
,
I
2
​
n
−
2
 have length 
1
 and green budget 
0
.
• The bound on total carbon cost is 
C
=
0
.
Clearly, the size of 
ℐ
UCAS
 is linear in the size of 
ℐ
3
​
P
. We show that 
ℐ
UCAS
 has a solution if and only if 
ℐ
3
​
P
 does.

First, if 
ℐ
3
​
P
 has a solution 
S
=
S
1
∪
⋯
∪
S
n
, we execute each triplet 
S
k
 in sequence during interval 
I
2
​
k
−
1
. The total duration is 
B
, and at any time unit, exactly one processor is active. The total cost is indeed 
0
, and 
ℐ
UCAS
 has a solution.

Now, if 
ℐ
UCAS
 has a solution, what is the corresponding schedule? Because the total cost is 
0
: (i) no task can be executed during even-numbered intervals; and (ii) at most one task can be executed during any time unit of odd-numbered intervals. Because the total length of these intervals is 
n
​
B
 (the sum of all task durations), exactly one task is executed at each time unit of odd-numbered intervals. Hence, we have a partition of the 
3
​
n
 tasks into 
n
 subsets of total duration 
B
 that are executed sequentially and entirely during these intervals. Because 
B
4
<
x
i
<
B
2
 for 
1
≤
i
≤
3
​
n
, the 
n
 subsets are in fact triplets, and we have a solution to 
ℐ
3
​
P
. This concludes the proof.

A.4Details on the Integer Linear Program
In this section, we give a detailed formulation for the integer linear program sketched in Section 4.3. First, we introduce all necessary variables for the model. We need variables for the amount of green (renewable) power and brown (carbon-emitting) power we use during every time step. Hence, we introduce integer variables

g
​
u
t
≥
0
and
b
​
u
t
≥
0
,
0
≤
t
<
T
,
(3)
for the green power usage and the brown power usage, respectively. Let 
G
c
=
(
V
c
,
E
c
,
ω
)
 be the communication-enhanced DAG as defined in Section 3. For every (task, processor) pair 
(
v
,
p
v
)
, where 
p
v
 is the processor where 
v
 is located, we define variables

s
​
(
v
,
p
v
)
t
∈
{
0
,
1
}
,
e
​
(
v
,
p
v
)
t
∈
{
0
,
1
}
,
r
​
(
v
,
p
v
)
t
∈
{
0
,
1
}
,
0
≤
t
<
T
,
(4)
where 
s
​
(
v
,
p
v
)
t
=
1
 if and only if task 
v
 is started on processor 
p
v
 at time unit 
t
, 
e
​
(
v
,
p
v
)
=
1
 if and only if task 
v
 ends on processor 
p
v
 at time unit 
t
, and 
r
​
(
v
,
p
v
)
t
=
1
 if and only if task 
v
 is running on processor 
p
v
 at time unit 
t
. For ease of notation, we may omit the processor since the mapping is given in advance. Further, we define for every time unit 
t
 an integer variable 
γ
t
≥
0
, which represents the overall power that the cluster uses at time unit 
t
. In order to compute the brown power usage, we also introduce auxiliary variables 
α
t
 for every time unit 
t
, where 
α
t
=
1
 if and only if we need brown power at time unit 
t
. With these variables, we can now formulate the integer linear program. First, we set the objective function, which writes:

min
​
∑
t
=
0
T
−
1
b
​
u
t
.
We now set the constraints for the ILP. First, we need to ensure that every task is executed exactly once, such that it finishes before the deadline. This can be modeled by

∑
t
=
0
T
−
ω
​
(
v
)
s
​
(
v
,
p
v
)
t
=
1
∀
v
∈
V
c
,
(5)
∑
t
=
T
−
ω
​
(
v
)
+
1
T
−
1
s
​
(
v
,
p
v
)
t
=
0
∀
v
∈
V
c
.
(6)
Further, we have to ensure the same for the end of the tasks. This is given by

∑
t
=
0
ω
​
(
v
)
−
2
e
​
(
v
,
p
v
)
t
=
0
∀
v
∈
V
c
,
(7)
∑
t
=
ω
​
(
v
)
−
1
T
−
1
e
​
(
v
,
p
v
)
t
=
1
∀
v
∈
V
c
.
(8)
Note that if 
ω
​
(
v
)
<
2
, sums in Eqs. (6) and (7) are just empty.

Next, we have to make sure that the beginning of a task and the end of a task are aligned according to the execution time of the task. Hence, we get for every task 
v
∈
V
c
 the constraints:

s
​
(
v
,
p
v
)
t
=
e
​
(
v
,
p
v
)
t
+
ω
​
(
v
)
−
1
,
0
≤
t
≤
T
−
ω
​
(
v
)
.
(9)
Lastly, we have to make sure that the variables 
r
​
(
v
,
p
v
)
t
 are aligned with the beginning and end of the task. Hence, we get for every task 
v
 the constraints:

∑
t
=
0
T
−
1
r
​
(
v
,
p
v
)
t
=
ω
​
(
v
)
,
(10)
r
​
(
v
,
p
v
)
k
≥
s
​
(
v
,
p
v
)
t
,
t
≤
k
≤
t
+
ω
​
(
v
)
−
1
,
0
≤
t
<
T
−
ω
​
(
v
)
.
(11)
Altogether, we have ensured that every task starts in time. Hence, we now have to make sure that all precedence and communication constraints are respected. Due to the structure of the communication-enhanced DAG 
G
c
, it is enough to respect every edge as a simple order constraint. Using this graph, we introduce for every edge 
(
u
,
v
)
∈
E
c
 the constraint

s
​
(
v
,
p
v
)
t
≤
∑
l
=
0
t
−
1
e
​
(
u
,
p
u
)
l
,
0
≤
t
<
T
.
(12)
Note that by construction of 
G
c
 these constraints ensure both the internal order of a processor and the inter-processor communication constraints.

Finally, we have to introduce constraints for the power usage. As seen in Section 3, we have to ensure

g
​
u
t
=
min
⁡
(
𝒢
t
,
γ
t
)
,
(13)
b
​
u
t
=
max
⁡
(
0
,
γ
t
−
𝒢
t
)
,
(14)
where 
γ
t
 is the overall power usage at time unit 
t
. To model Eqs. (13) and (14), we use the Big-M method. For this, we need auxiliary constants 
ϵ
,
M
∈
ℝ
>
0
, where 
ϵ
 is sufficiently small and 
M
 is sufficiently large. For 
ϵ
, we can choose any value 
0
<
ϵ
<
1
. Further, it suffices to estimate 
M
 by

M
≥
∑
i
=
1
P
2
(
𝒫
idle
i
+
𝒫
work
i
)
,
since we cannot use more brown power than that.

First, we ensure Eq. (14) by the following constraints:

b
​
u
t
≥
0
,
0
≤
t
<
T
(15)
b
​
u
t
≥
γ
t
−
𝒢
t
,
0
≤
t
<
T
(16)
b
​
u
t
≤
γ
t
−
𝒢
t
+
M
​
(
1
−
α
t
)
0
≤
t
<
T
(17)
b
​
u
t
≤
M
⋅
α
t
,
0
≤
t
<
T
(18)
γ
t
−
𝒢
t
≤
M
⋅
α
t
,
0
≤
t
<
T
(19)
γ
t
−
𝒢
t
≥
ϵ
−
M
​
(
1
−
α
t
)
0
≤
t
<
T
.
(20)
Here, 
α
t
 is a binary variable indicating whether we need brown power or not. To determine the green power usage, we then only need the constraints

g
​
u
t
≥
0
,
0
≤
t
<
T
(21)
g
​
u
t
+
b
​
u
t
=
γ
t
,
0
≤
t
<
T
.
(22)
Finally, we must determine the overall power usage by the constraint:

γ
t
=
∑
i
=
1
P
2
𝒫
idle
i
+
∑
v
∈
V
c
r
​
(
v
,
p
v
)
t
⋅
𝒫
work
p
v
,
0
≤
t
<
T
.
(23)
A.5Further Experimental Results
Refer to caption
Figure 10:Performance profile for tolerance factor 
2
 for the deadline (extends Figure 3).
Refer to caption
Figure 11:Cost ratios for tolerance factor 
2
 for the deadline (extends Figure 5).
Refer to caption
Figure 12:Time (in seconds) for each algorithm variant only for large workflows. Large workflows have between 20,000 and 30,000 tasks.
Refer to caption
Refer to caption
Refer to caption
Refer to caption
Figure 13:The evolution of the running time when adding more tolerance to the deadline from top to bottom.
Refer to caption
Refer to caption
Figure 14:Cost ratio for different cluster sizes.
Refer to caption
Refer to caption
Refer to caption
Refer to caption
Figure 15:Cost ratio for different power profiles.
Refer to caption
Refer to caption
Refer to caption
Refer to caption
Figure 16:Cost ratio for different sized workflows. Small workflows have between 200 and 4,000 tasks, medium workflows have between 8,000 and 18,000 tasks, and large workflows have between 20,000 and 30,000 tasks.