A Novel Hierarchical Co-Optimization Framework for Coordinated Task Scheduling and Power Dispatch in Computing Power Networks
Haoxiang Luo, Kun Yang, Qi Huang, , Schahram Dustdar
H. Luo is with the School of Information and Communication Engineering, University of Electronic Science and Technology of China, Chengdu 611731, China (e-mail: lhx991115@163.comn).K. Yang is with the Leshan Power Supply Company, State Grid Sichuan Electric Power Company, Leshan 613100, China (e-mail: 112676539@qq.com). Q. Huang is with the School of Mechanical and Electrical Engineering, University of Electronic Science and Technology of China, Chengdu 611731, China, and also with the Institute of Scientific and Technical Information of China, Beijing 100038, China (e-mail: hwong@uestc.edu.cn). S. Dustdar is with the Distributed Systems Group of the TU Wien, Vienna 1040, Austria, and also with ICREA, Barcelona 08002, Spain (e-mail: dustdar@dsg.tuwien.ac.at).
Abstract
The proliferation of large-scale artificial intelligence and data-intensive applications has spurred the development of Computing Power Networks (CPNs), which promise to deliver ubiquitous and on-demand computational resources. However, the immense energy consumption of these networks poses a significant sustainability challenge. Simultaneously, power grids are grappling with the instability introduced by the high penetration of intermittent renewable energy sources (RES). This paper addresses these dual challenges through a novel Two-Stage Co-Optimization (TSCO) framework that synergistically manages power system dispatch and CPN task scheduling to achieve low-carbon operations. The framework decomposes the complex, large-scale problem into a day-ahead stochastic unit commitment (SUC) stage and a real-time operational stage. The former is solved using Benders decomposition for computational tractability, while in the latter, economic dispatch of generation assets is coupled with an adaptive CPN task scheduling managed by a Deep Reinforcement Learning (DRL) agent. This agent makes intelligent, carbon-aware decisions by responding to dynamic grid conditions, including real-time electricity prices and marginal carbon intensity. Through extensive simulations on an IEEE 30-bus system integrated with a CPN, the TSCO framework is shown to significantly outperform baseline approaches. Results demonstrate that the proposed framework reduces total carbon emissions and operational costs, while simultaneously decreasing RES curtailment by more than 
60
%
 and maintaining stringent Quality of Service (QoS) for computational tasks.

Index Terms: Computing Power Network (CPN), renewable energy, data center, carbon-aware scheduling, deep reinforcement learning.
IIntroduction
I-ABackground
The digital transformation of the global economy is fueling an unprecedented demand for computational power. The rise of artificial intelligence (AI), big data analytics, and the Internet of Things (IoT) has pushed traditional centralized cloud computing architectures to their limits [1]. In response, a new paradigm known as the Computing Power Network (CPN) has emerged [2]. A CPN aims to interconnect vast, geographically distributed, and heterogeneous computing resources, spanning from large-scale data centers to edge nodes, into a unified, programmable fabric [3]. The core vision of CPN is to break down resource silos and enable the flexible, on-demand scheduling and allocation of computing, storage, and network resources, thereby improving efficiency and enabling novel, low-latency applications.

Concurrently, the global energy sector is undergoing a profound transition towards sustainability, marked by massive investments in Renewable Energy Sources (RES) such as wind and solar power [4]. This shift presents a powerful, yet challenging, symbiotic relationship with the burgeoning CPN paradigm. On one hand, CPNs are voracious consumers of electricity; data centers alone are projected to account for a significant portion of global electricity load growth, with AI workloads being a primary driver. Globally, data centers already account for 
1
−
2
%
 of total electricity consumption, a figure comparable to the aviation industry. Driven by the explosive growth of AI, this demand is projected to double by 2030 [5]. In the United States, data center electricity usage is forecast to climb from 
4.4
%
 of the national total in 2023 to as high as 
12
%
 by 20281, with AI workloads shifting from a minor component to a primary driver of this expansion. The availability of clean, renewable energy offers a direct path to decarbonize this massive computational infrastructure[6]. On the other hand, the very nature of CPNs, with their inherent flexibility in workload scheduling, presents a unique opportunity to support and stabilize a grid increasingly reliant on intermittent RES [7].

I-BResearch Motivation
The central challenge lies in a fundamental misalignment between the operational dynamics of CPNs and RES-dominated power grids. CPNs are designed to host a wide array of computational tasks, from latency-sensitive services like cloud virtual reality to compute-intensive, batch-processing jobs like large model training [8], [9]. These tasks demand a highly reliable and stable power supply to ensure Quality of Service (QoS). However, RES are inherently variable, non-dispatchable, and dependent on weather conditions. This intermittency introduces significant volatility into the power grid, leading to challenges in maintaining frequency and voltage stability, and often results in the wasteful curtailment of clean energy when generation exceeds demand [10], [11].

Simply connecting a CPN to a grid with high RES penetration without intelligent coordination creates a direct conflict. During periods of low RES output, the CPN’s demand would force the grid to rely on expensive and carbon-intensive fossil-fuel peaker plants to maintain balance. Conversely, during periods of high RES output, the grid may be forced to curtail wind or solar generation to prevent overload, even as CPNs continue to draw power from a mixed-carbon source. This decoupled operation leads to a suboptimal outcome: either unreliable computation or high operational costs and carbon emissions. The problem is not merely about sourcing green energy, but about managing the flexibility of CPN workloads as a grid-stabilizing asset. The inherent ability to shift CPN tasks in time (delaying non-critical jobs) and space (migrating workloads to regions with abundant RES) constitutes a powerful form of Demand Response (DR) [12]. This reframes the problem from ”how to power the CPN cleanly” to ”how to leverage the CPN’s flexibility to enable a cleaner, more stable grid”. This symbiotic relationship is the core motivation for the co-optimization framework proposed in this paper.

I-CContributions of the Paper
This paper proposes a holistic, hierarchical co-optimization framework that treats the power system and the CPN as a single, integrated entity. By breaking down the silos between power system operators and CPN schedulers, the framework unlocks significant economic and environmental benefits. It coordinates power generation dispatch with computational task scheduling across multiple timescales to align CPN energy demand with the availability of low-cost, low-carbon renewable energy. As far as we know, this is one of the first efforts to jointly optimize the power grid and the CPN. The main contributions of this work are summarized as follows:

• A Comprehensive Integrated System Model: A detailed model is developed that captures the intricate interplay between a heterogeneous CPN and a modern power grid. The model incorporates conventional thermal generators, stochastic RES, and battery energy storage systems (BESS), while explicitly modeling the spatio-temporal dynamics of electricity prices and carbon intensity.
• A Novel Two-Stage Co-Optimization (TSCO) Framework: A hierarchical framework is designed to decompose the computationally intractable joint optimization problem into two manageable stages. A day-ahead planning stage addresses long-term unit commitment and resource reservation, while a real-time operational stage handles dynamic economic dispatch and adaptive task scheduling.
• Scalable Optimization with Benders Decomposition: To address the large-scale, mixed-integer nature of the day-ahead Stochastic Unit Commitment (SUC) problem, Benders decomposition is employed. This technique effectively decouples the integer commitment decisions from the continuous dispatch variables, ensuring the problem remains computationally tractable even for large systems and numerous uncertainty scenarios.
• Adaptive Real-Time Scheduling with Deep Reinforcement Learning (DRL): A DRL agent is developed for the real-time CPN task scheduling subproblem. This model-free approach enables fast, adaptive, and carbon-aware scheduling decisions in response to the highly dynamic and complex state of the joint CPN-grid system, complementing the model-based optimization of the power dispatch.
• Extensive High-Fidelity Performance Evaluation: The efficacy of the proposed TSCO framework is validated through extensive simulations using realistic data. The evaluation demonstrates significant improvements in carbon emissions, operational costs, and RES utilization when compared against decoupled and carbon-agnostic baseline strategies.
I-DPaper Structure
The remainder of this paper is structured as follows. Section II provides a critical review of related work in CPN scheduling, integrated energy systems, and carbon-aware computing. Section III presents the detailed mathematical formulation of the CPN and power system models, defining the joint optimization problem. Section IV describes the proposed TSCO framework, including the Benders decomposition algorithm and the DRL-based scheduler. Section V details the simulation setup and presents a comprehensive performance evaluation against several baseline methods. Finally, Section VI concludes the paper with a summary of findings and directions for future research.

IIRelated Works
This section provides a structured review of the literature across four key domains that intersect in this work, Computing Power Network (CPN) architectures, integrated energy system management, carbon-aware workload scheduling, and optimization under uncertainty in power systems. This analysis serves to contextualize our contribution and highlight the research gap that our proposed framework aims to fill.

II-AComputing Power Network Architectures and Scheduling
The concept of the CPN has evolved from earlier paradigms like cloud, fog, and edge computing, with the primary goal of creating a unified network for ubiquitous computing resources. Early research focused on defining the architecture and core features of CPNs, such as intent-driven operation, closed-loop autonomy, and elastic scheduling. Architectures have been proposed with both centralized control planes, which possess a global view for unified scheduling, and distributed schemes, where decisions are made locally by network nodes.

A significant body of research in CPNs has concentrated on task scheduling [13]. The primary objectives have traditionally been to optimize QoS metrics. For instance, studies have focused on developing scheduling policies to minimize task completion delay and enhance reliability, often formulating the problem as a Continuous-Time Markov Decision Process (CMDP) and solving it with DRL techniques. Other works have explored task offloading in terminal-side CPNs or the joint selection of routing paths and computing nodes [14]. While some research considers energy consumption as a constraint or a secondary objective, the explicit, primary optimization of carbon emissions based on the real-time state of the power grid remains largely unexplored. Existing CPN scheduling literature typically treats the power grid as an external, static entity, overlooking the potential for dynamic, symbiotic interaction.

II-BIntegrated Energy System Management
In the power systems domain, the concept of coordinating generation, transmission, and consumption has been studied extensively under the ”Generation-Grid-Load-Storage” integrated operation model [11]. This paradigm seeks to improve system safety, economy, and reliability through the coordinated interaction of all system components. Research in this area includes the development of multi-timescale optimal dispatching strategies [15], economic dispatch models that incorporate DR, and optimal power flow (OPF) formulations that aim to minimize generation costs while respecting network constraints [16].

The integration of flexible loads and DR has been identified as a key enabler for grids with high RES penetration. Studies have explored how to coordinate data centers as flexible loads with a load aggregator to minimize electricity costs and absorb grid volatility [17]. However, these studies often rely on simplified models of the flexible load, such as an abstract ability to shift power consumption in time, without capturing the complex internal constraints, dependencies, and heterogeneous resource requirements of a CPN workload. They treat the CPN as a ”black box” load, missing the opportunity to optimize its internal operations in concert with the grid.

II-CCarbon-Aware Workload Scheduling
The field of green computing has produced a significant body of work on carbon-aware scheduling for geo-distributed data centers. A common strategy is spatio-temporal scheduling [18], which involves shifting computational workloads in time (”temporal flexibility”) or space (”geographical flexibility”) to data centers with lower electricity prices or cleaner energy mixes. These methods often leverage real-time carbon intensity signals from services like WattTime2 to guide scheduling decisions.

To manage carbon emissions over the long term, some works have proposed online algorithms based on Lyapunov optimization [19]. This technique transforms a long-term average constraint, e.g., a carbon budget, into a series of real-time optimization subproblems by maintaining a ”virtual queue” that tracks the deviation from the budget. The scheduler is then penalized for actions that increase this queue length [20]. While powerful, this line of research suffers from a critical limitation. It almost universally treats the power grid as an exogenous system. The price and carbon intensity signals are assumed to be external inputs that are unaffected by the scheduling decisions. This assumption breaks down at scale, as the collective actions of large CPNs can and will influence grid operations, market prices, and the generation mix, thereby altering the very signals they are responding to.

II-DResearch Gap Summary
The existing body of work, while extensive in its respective domains, reveals a significant research gap at the intersection of CPNs and power systems. Current research either:

• Simplifies the power grid: CPN and carbon-aware scheduling studies treat the grid as a static source of price and carbon signals, ignoring the feedback loop where scheduling decisions impact the grid.
• Simplifies the CPN: Power system and DR studies model flexible loads like data centers in an overly simplistic manner, failing to capture the rich internal complexity of CPN workloads, resource heterogeneity, and QoS constraints.
This leads to a new class of control problem where the decision variables are distributed across two separate domains. The system dynamics are characterized by a mix of well-understood physics (the power grid) and complex, stochastic behavior (the CPN). A model-based optimization approach is ill-suited for the fast, dynamic CPN scheduling, while a model-free AI approach cannot guarantee adherence to the hard physical constraints of the power grid. Consequently, there is a clear need for a hybrid framework that endogenously models the bi-directional interactions between the two systems. Our TSCO framework, which combines large-scale, model-based optimization for slow, physics-heavy planning with a model-free, adaptive AI technique for fast, complex real-time scheduling, is designed specifically to fill this gap.

IIISystem Architecture and Problem Formulation
This section presents the mathematical models for the CPN and the integrated power system. These models form the basis of our co-optimization framework, as shown in Fig. 1.

Refer to caption
Figure 1:CPN and power grid co-optimization architecture.
III-AComputing Power Network (CPN) Model
The CPN is modeled as a directed graph 
𝒢
C
​
P
​
N
=
(
𝒩
,
ℒ
)
, where 
𝒩
 is the set of geographically distributed CPN nodes, representing data centers, and 
ℒ
 is the set of communication links connecting them.

III-A1CPN Node Model
Each CPN node 
n
∈
𝒩
 is characterized by its available computational resources, such as CPUs, GPUs, and TPUs. For simplicity in this formulation, we aggregate these into a single measure of computing capacity, 
C
n
c
​
o
​
m
​
p
, expressed in Floating Point Operations Per Second (FLOPS). The power consumption of a CPN node is modeled as a linear function of its utilization [21], varying between an idle power 
P
n
i
​
d
​
l
​
e
 and a peak power 
P
n
p
​
e
​
a
​
k
 at full utilization. The total power consumed by node 
n
 at time 
t
 is a decision variable, 
P
n
,
t
C
​
P
​
N
, determined by the scheduled tasks.

III-A2Task Model
We model incoming computational jobs as Directed Acyclic Graphs (DAGs), a common representation for parallel applications with precedence constraints [22], [23]. A job 
k
∈
𝒥
 is represented by 
J
k
=
(
𝒯
k
,
ℰ
k
)
, where 
𝒯
k
 is the set of sub-tasks and 
ℰ
k
 is the set of directed edges representing dependencies. An edge 
(
τ
i
,
τ
j
)
∈
ℰ
k
 implies that sub-task 
τ
j
 cannot begin until 
τ
i
 is complete. Each sub-task 
τ
∈
𝒯
k
 is defined by its total computational workload 
w
τ
 (in floating-point operations) and its resource requirement 
r
τ
 (e.g., number of processing units). The execution time of sub-task 
τ
 on node 
n
 is thus 
t
τ
,
n
=
w
τ
/
C
n
c
​
o
​
m
​
p
. Each job 
k
 has an arrival time 
A
k
 and a hard end-to-end deadline 
D
k
.

III-BIntegrated Power System Model
The power grid is modeled based on the IEEE 30-bus test system3, a standard benchmark for power system studies. The system consists of a set of buses 
ℐ
 connected by transmission lines. Each CPN node 
n
∈
𝒩
 is co-located with a specific load bus 
i
∈
ℐ
.

III-B1Conventional Generation
The set of conventional thermal generators, 
𝒢
C
, forms the dispatchable backbone of the system. The fuel cost of each generator 
g
∈
𝒢
C
 is represented by a quadratic function of its power output 
P
g
,
t
:

C
g
​
(
P
g
,
t
)
=
a
g
​
P
g
,
t
2
+
b
g
​
P
g
,
t
+
c
g
,
(1)
where 
a
g
,
b
g
,
c
g
 are cost coefficients. These generators are subject to operational constraints, including minimum and maximum power output limits (
P
g
m
​
i
​
n
,
P
g
m
​
a
​
x
), and ramp-up/ramp-down rate limits (
R
​
U
g
,
R
​
D
g
) that constrain how quickly their output can change between time periods [24].

III-B2RES
The set of RES generators, 
𝒢
R
, includes wind and solar farms. Their power output is non-dispatchable and uncertain. We model their available power at time 
t
 in scenario 
ω
, 
P
g
,
t
,
ω
R
,
a
​
v
​
a
​
i
​
l
, as a stochastic parameter derived from historical weather data. The actual dispatched power 
P
g
,
t
,
ω
 can be less than or equal to the available power.

III-B3BESS
BESS units, located at specific buses, provide crucial flexibility for managing RES intermittency. Each BESS 
b
∈
ℬ
 is modeled by its state-of-charge (SOC) dynamics [25]:

S
​
O
​
C
b
,
t
,
ω
=
S
​
O
​
C
b
,
t
−
1
,
ω
+
(
η
b
c
​
P
b
,
t
,
ω
c
​
h
​
g
−
1
η
b
d
​
P
b
,
t
,
ω
d
​
i
​
s
)
​
Δ
​
t
.
(2)
The model is subject to constraints on the SOC level (
S
​
O
​
C
b
m
​
i
​
n
≤
S
​
O
​
C
b
,
t
,
ω
≤
S
​
O
​
C
b
m
​
a
​
x
), where 
E
b
m
​
a
​
x
 is the energy capacity, and maximum charging/discharging power (
P
b
c
,
m
​
a
​
x
,
P
b
d
,
m
​
a
​
x
).

III-CUncertainty and Carbon Modeling
III-C1Uncertainty Modeling
The uncertainties in RES generation and CPN job arrivals are critical to the problem. We adopt a scenario-based stochastic programming approach [26]. A set of discrete scenarios 
Ω
 is generated, where each scenario 
ω
∈
Ω
 represents a plausible joint realization of RES power availability and CPN workload over the time horizon 
T
. Each scenario is assigned a probability 
π
ω
, with 
∑
ω
∈
Ω
π
ω
=
1
.

III-C2Carbon Intensity Modeling
The environmental impact is quantified through carbon emissions. The carbon intensity of the grid is not static but depends on the real-time generation mix. The total carbon emission rate at time 
t
 in scenario 
ω
, 
E
t
,
ω
, is calculated as the sum of emissions from all active generators:

E
t
,
ω
=
∑
g
∈
𝒢
C
ϵ
g
​
P
g
,
t
,
ω
,
(3)
where 
ϵ
g
 is the emission factor (e.g., in tons of 
C
​
O
2
 per MWh) of generator 
g
. For RES, 
ϵ
g
 is zero. This endogenous calculation is crucial, as it directly links dispatch decisions to carbon output. We also leverage real-world marginal carbon intensity data, such as that provided by WattTime, to inform the real-time DRL agent about the emissions impact of consuming an additional unit of electricity at a specific location and time.

III-DJoint Optimization Problem Formulation
The overarching goal is to co-optimize the power system operation and CPN task scheduling to minimize the total expected system cost over a planning horizon 
T
. The total cost comprises the operational costs of the power system and the monetized cost of carbon emissions. The problem is formulated as a large-scale, two-stage stochastic mixed-integer linear program (MILP).

Objective Function:

min
​
∑
ω
∈
Ω
π
ω
​
∑
t
=
1
T
(
∑
g
∈
𝒢
C
+
λ
C
​
O
2
​
E
t
,
ω
)
.
(4)
The objective minimizes the expected sum of three components across all scenarios: (1) the quadratic fuel costs of conventional generators, (2) the costs associated with starting up (
S
​
U
g
) and shutting down (
S
​
D
g
) these generators based on their commitment status 
u
g
,
t
, and (3) a carbon tax, where 
λ
C
​
O
​
2
 is the price of carbon and 
E
t
,
ω
 is the total emissions.

Key Constraints: The optimization is subject to a comprehensive set of constraints that couple the two systems:

• Power System Constraints (for each 
t
,
ω
):
Power Balance (DC-OPF): At each bus 
i
∈
ℐ
, the total power injected must equal the total power withdrawn. This is the core DC power flow equation [27].

∑
g
∈
𝒢
​
(
i
)
P
g
,
t
,
ω
+
∑
b
∈
ℬ
​
(
i
)
(
P
b
,
t
,
ω
d
​
i
​
s
−
P
b
,
t
,
ω
c
​
h
​
g
)
−
(
P
i
,
t
D
+
P
i
,
t
,
ω
C
​
P
​
N
)
=
∑
j
∈
ℐ
B
i
​
j
​
(
θ
i
,
t
,
ω
−
θ
j
,
t
,
ω
)
,
(5)
where, 
𝒢
​
(
i
)
 and 
ℬ
​
(
i
)
 are generators and BESS at bus 
i
, 
P
i
,
t
,
ω
C
​
P
​
N
 is the CPN power demand at that bus, and the right-hand side represents the net power flow out of the bus.

Transmission Line Limits: The power flow 
F
i
​
j
 on each line 
(
i
,
j
)
 must not exceed its thermal limit 
F
i
​
j
m
​
a
​
x
.

−
F
i
​
j
m
​
a
​
x
≤
B
i
​
j
​
(
θ
i
,
t
,
ω
−
θ
j
,
t
,
ω
)
≤
F
i
​
j
m
​
a
​
x
.
(6)
Generator Constraints: Including commitment logic, min/max output, and ramping limits for all 
g
∈
𝒢
C
.

BESS Constraints: Including SOC dynamics, capacity limits, and charge/discharge power limits for all 
b
∈
ℬ
.

• CPN Task Scheduling Constraints (for each 
t
,
ω
):
Task Assignment: Each sub-task 
τ
 of each job 
k
 must be scheduled exactly once.

∑
n
∈
𝒩
∑
t
=
A
k
D
k
x
k
,
τ
,
n
,
t
=
1
∀
k
,
τ
∈
𝒯
k
.
(7)
Precedence Constraints: For any dependency 
(
τ
i
,
τ
j
)
∈
ℰ
k
, the start time of 
τ
j
 must be after the finish time of 
τ
i
.

Deadline Satisfaction: The completion time of the final sub-task of job 
k
 must be no later than its deadline 
D
k
.

Node Resource Capacity: The total resource demand of tasks scheduled on node 
n
 at time 
t
 cannot exceed its capacity.

∑
k
∈
𝒥
∑
τ
∈
𝒯
k
r
τ
​
x
k
,
τ
,
n
,
t
≤
C
n
c
​
o
​
m
​
p
∀
n
,
t
.
(8)
• Coupling Constraint: This is the critical link. The power consumed by a CPN node 
n
 (co-located at bus 
i
) is determined by the tasks scheduled on it.
P
i
,
t
,
ω
C
​
P
​
N
=
P
n
i
​
d
​
l
​
e
+
(
P
n
p
​
e
​
a
​
k
−
P
n
i
​
d
​
l
​
e
)
​
∑
k
,
τ
r
τ
​
x
k
,
τ
,
n
,
t
C
n
c
​
o
​
m
​
p
.
(9)
This equation makes the CPN load term 
P
i
,
t
,
ω
C
​
P
​
N
 in the power balance equation an endogenous variable dependent on the scheduling decisions 
x
k
,
τ
,
n
,
t
.
• Carbon Budget Constraint: A long-term constraint on total carbon emissions is imposed to ensure sustainability goals are met.
∑
ω
∈
Ω
π
ω
​
∑
t
=
1
T
E
t
,
ω
≤
E
b
​
u
​
d
​
g
​
e
​
t
.
(10)
Due to its long-term nature, this constraint is difficult to handle directly in a short-term optimization. It will be managed implicitly through the design of the DRL agent’s reward function, as detailed in the next section.
IVTwo-Stage Co-Optimization (TSCO) Framework
The joint optimization problem formulated in Section III is a large-scale, non-convex, mixed-integer stochastic program, which is computationally intractable to solve directly [28]. To address this challenge, we propose a Two-Stage Co-Optimization (TSCO) framework that decomposes the problem by decision timescale and complexity. The framework combines model-based optimization for long-term, system-wide planning with a model-free, AI-based approach for fast, adaptive real-time control, as shown in Fig. 2.

Refer to caption
Figure 2:Two-Stage Co-Optimization (TSCO) framework for CPN and power grid collaborative optimization.
IV-AHierarchical Stochastic Optimization Structure
The TSCO framework decomposes the problem into two distinct stages, reflecting the natural hierarchy of power system operations:

• Stage 1 (Day-Ahead Planning): This stage solves an SUC problem for the upcoming 24-hour horizon. It makes the ”here-and-now” decisions, which are binding across all potential future scenarios. These decisions include the commitment (on/off) status 
u
g
,
t
 of conventional generators and high-level energy reservation for BESS and CPN workload classes. The objective is to minimize the total expected cost over all scenarios, setting the operational envelope for the next stage. This stage is computationally intensive but is performed only once per day.
• Stage 2 (Real-Time Operation): This stage operates at a much faster timescale (e.g., 5-15 minute intervals) and makes ”wait-and-see” recourse decisions as uncertainty unfolds. As the actual RES generation and CPN task arrivals are revealed, this stage executes two parallel, tightly coupled processes:
1. Real-Time Economic Dispatch (ED): Solves for the optimal power output of the committed generators and the charge/discharge schedule of BESS to meet the actual load at minimum cost, while respecting all grid constraints.
2. Real-Time CPN Task Scheduling: A DRL agent makes granular, second-by-second scheduling decisions, assigning individual tasks to specific resources within the CPN nodes. Its decisions are informed by the real-time grid state, namely prices and carbon intensity, provided by the ED.
This hierarchical structure allows the framework to be both economically optimal from a long-term planning perspective and highly adaptive to short-term dynamics.

IV-BBenders Decomposition for the Day-Ahead SUC
The day-ahead SUC problem is a large-scale MILP due to the combination of binary commitment variables and a large number of scenarios representing RES uncertainty. To solve it efficiently, we employ Benders decomposition [29], a classic technique for problems with this structure. The method iteratively decomposes the problem into a simpler master problem and a set of independent subproblems.

• Master Problem: The master problem determines the integer variables in the first stage, the unit commitment schedules 
{
u
g
,
t
}
 for all 
g
∈
𝒢
C
 over the horizon 
T
. It is a pure integer program that minimizes the sum of startup/shutdown costs and an estimated future cost, 
θ
, which represents the expected operational cost from the subproblems.
min
​
∑
t
=
1
T
∑
g
∈
𝒢
C
(
S
​
U
g
​
(
u
g
,
t
)
+
S
​
D
g
​
(
u
g
,
t
)
)
+
θ
.
(11)
Subject to: Generator minimum up/down time constraints; Benders optimality and feasibility cuts (added iteratively).
• Subproblems: For a given commitment schedule 
{
u
¯
g
,
t
}
 provided by the master problem, a separate, continuous linear program (LP) is solved for each scenario 
ω
∈
Ω
. Each subproblem represents the economic dispatch problem for that scenario, minimizing the fuel and carbon costs subject to grid constraints.
min
​
∑
t
=
1
T
(
∑
g
∈
𝒢
C
C
g
​
(
P
g
,
t
,
ω
)
+
λ
C
​
O
​
2
​
E
t
,
ω
)
.
(12)
Subject to: Power balance, line limits, generator output limits (for committed units), BESS constraints.
• Algorithm Flow and Cut Generation: The algorithm proceeds iteratively:
1. The master problem is solved to obtain a candidate commitment schedule.
2. This schedule is passed to the subproblems, which are solved in parallel for all scenarios.
3. If any subproblem is infeasible (i.e., the commitment schedule cannot satisfy the load), its dual rays are used to construct a Benders feasibility cut, which is added to the master problem to exclude this infeasible solution.
4. If all subproblems are feasible, their optimal dual variable values are used to construct a Benders optimality cut. This cut is a linear inequality that provides a lower bound on the recourse cost 
θ
 and is added to the master problem.
5. The process repeats until the lower bound from the master problem and the upper bound from the subproblems converge within a specified tolerance.
IV-CDRL-based Real-Time CPN Task Scheduling
While the SUC/ED provides an economically optimal power dispatch plan, it is far too slow for the dynamic, fine-grained scheduling required within the CPN. For this, we propose a DRL-based approach. A DRL agent can learn a complex scheduling policy through interaction with the environment [30], enabling it to make near-instantaneous decisions that are adaptive to both CPN and grid conditions.

Markov Decision Process (MDP) Formulation: The CPN scheduling problem is formulated as an MDP defined by the tuple 
(
𝒮
,
𝒜
,
𝒫
,
ℛ
,
γ
)
:

• State (
s
t
∈
𝒮
): The state provides a comprehensive snapshot of the entire system at time 
t
. It is a high-dimensional vector including:
1. CPN State: Characteristics of tasks in the queue (e.g., resource requirements, deadlines), current resource utilization and power consumption of each CPN node.
2. Grid State: Real-time RES generation levels, BESS state-of-charge, and crucially, the real-time locational marginal price (LMP) and marginal carbon intensity (MCI) for each bus hosting a CPN node. These signals are provided by the real-time ED solution.
• Action (
a
t
∈
𝒜
): For the task at the head of the queue, the agent selects an action from a discrete set. An action is a tuple 
(
n
,
τ
t
​
y
​
p
​
e
)
 representing the decision to assign the task to node 
n
 to be processed by resource type 
τ
t
​
y
​
p
​
e
 (e.g., CPU, GPU). The action space also includes deferring the task.
• Reward (
R
t
∈
ℛ
): The reward function is carefully designed to guide the agent towards the overall optimization objective. It is a weighted sum of multiple components:
R
t
=
w
r
​
e
​
v
⋅
Revenue
t
−
w
c
​
o
​
s
​
t
⋅
Cost
t
(13)
−
w
c
​
a
​
r
​
b
⋅
Carbon
t
−
w
p
​
e
​
n
⋅
Penalty
t
,
where 
Revenue
t
 is a positive reward for successfully completing a job; 
Cost
t
 is the electricity cost of executing the scheduled task, calculated as 
P
n
,
t
C
​
P
​
N
×
LMP
i
,
t
; 
Carbon
t
 denotes the carbon cost, calculated as 
P
n
,
t
C
​
P
​
N
×
MCI
i
,
t
. To enforce the long-term budget 
E
b
​
u
​
d
​
g
​
e
​
t
, this term is augmented using the Lyapunov optimization technique. A virtual carbon queue 
Q
t
 is maintained, updating as
Q
t
+
1
=
max
⁡
(
0
,
Q
t
+
Carbon
t
−
E
b
​
u
​
d
​
g
​
e
​
t
/
T
)
.
(14)
The reward is then penalized by an additional term proportional to 
Q
t
×
Carbon
t
, which strongly discourages carbon-intensive actions when the system is already over its carbon budget. And the 
Penalty
t
 represents a large negative penalty for missing a task’s deadline.
Given the large, continuous state space and discrete action space, a value-based DRL algorithm such as Deep Q-Network (DQN) or its advanced variants (e.g., Dueling DQN, Rainbow) is suitable [31]. The agent’s policy 
π
​
(
a
t
|
s
t
)
 is represented by a deep neural network that approximates the optimal action-value function 
Q
∗
​
(
s
,
a
)
. The agent is trained offline on a rich dataset of historical system states and transitions, and then deployed for fast online inference.

IV-DOverall TSCO Algorithm and Its Complexity Analysis
The complete operational flow of the TSCO framework integrates the day-ahead planning and real-time control stages. The step-by-step procedure is outlined in Alg. 1.

Input : Set of RES/CPN scenarios 
Ω
 with probabilities 
π
ω
Output : 24-hour unit commitment 
{
u
g
,
t
∗
}
, Real-time power dispatch, Real-time CPN task schedule
Stage 1: Day-Ahead SUC (solved once daily):
1. Initialize Benders master problem with generator constraints
2. repeat
    3. Solve MILP master problem to get candidate commitment 
{
u
¯
g
,
t
}
    4. for each scenario 
ω
∈
Ω
 in parallel do
       5. Solve LP dispatch subproblem with fixed commitments 
{
u
¯
g
,
t
}
       6. if subproblem is infeasible then
          Generate and add a feasibility cut to the master problem
      else
          Generate and add an optimality cut to the master problem
      
   
until lower and upper bounds converge;
7. Obtain final 24-hour unit commitment schedule 
{
u
g
,
t
∗
}
Stage 2: Real-Time Operation (for 
t
=
1
,
…
,
T
):
1. for 
t
=
1
,
…
,
T
 do
    2. Observe actual RES generation 
P
g
,
t
R
,
a
​
c
​
t
​
u
​
a
​
l
 and new CPN job arrivals
    3. Update CPN task queue
    4. Solve real-time Economic Dispatch for 
{
u
g
,
t
∗
}
 and BESS
    5. Obtain real-time LMPs and MCIs for all CPN node locations
    6. Construct state vector 
s
t
←
 (CPN state + Grid state)
    7. DRL agent takes action 
a
t
←
π
​
(
s
t
)
 to schedule next CPN task
    8. Update CPN power demand 
P
i
,
t
C
​
P
​
N
 based on action 
a
t
    9. Execute scheduled task and power dispatch
    10. Update BESS SOC and CPN resource status
Algorithm 1 Two-Stage Co-Optimization (TSCO) Framework
Additionally, the computational complexity of the TSCO framework is best analyzed by examining its two stages separately.

IV-D1Stage 1: Day-Ahead SUC
The SUC problem is a mixed-integer programming (MIP) problem, which is NP-hard. Solving the full extensive form directly is computationally prohibitive for realistic system sizes and a large number of scenarios. Benders decomposition is employed to manage this complexity.

• Master Problem: The master problem is a MILP. Its complexity is, in the worst case, exponential in the number of integer variables, which is proportional to the number of conventional generators and the length of the time horizon (
|
𝒢
C
|
×
T
). The size of the master problem also grows with each iteration as Benders cuts are added.
• Subproblems: For each of the 
|
Ω
|
 scenarios, a linear program (LP) is solved. The complexity of solving an LP with modern interior-point methods is polynomial in the number of variables and constraints. Since the subproblems are independent for a given commitment schedule, they can be solved in parallel. The time taken per iteration for this step is thus equivalent to solving a single LP.
IV-D2Stage 2: Real-Time Operation
This stage must operate quickly at each time step 
t
.

• Real-Time Economic Dispatch: This is a standard LP, similar in structure to a Benders subproblem but for a single realized scenario. As an LP, it can be solved very efficiently in polynomial time, which is essential for real-time control.
• DRL-based CPN Scheduling: The online decision-making process involves a single forward pass through the trained deep neural network. The complexity of a forward pass is approximately 
O
​
(
∑
l
=
1
L
N
l
×
N
l
−
1
)
, where 
L
 is the number of layers and 
N
l
 is the number of neurons in layer 
l
. This computation is extremely fast and independent of the complexity of the underlying system dynamics, making it highly suitable for real-time, low-latency scheduling decisions. Also, the computationally intensive training of the DRL agent is performed offline and does not impact the online operational complexity.
In summary, the TSCO framework strategically manages computational complexity by solving the NP-hard, large-scale planning problem (SUC) offline on a day-ahead basis, where longer computation times are acceptable. It then leverages highly efficient, polynomial-time algorithms (LP for ED) and fast neural network inference (DRL for scheduling) for the real-time operational stage, ensuring the framework is viable for practical deployment.

VPerformance Evaluation
This section presents a comprehensive empirical validation of the proposed Two-Stage Co-Optimization (TSCO) framework. A high-fidelity simulation environment is developed to assess its performance in terms of economic efficiency, environmental impact, grid stability, and CPN QoS.

V-ASimulation Setup
The simulation framework is implemented in Python. The power system dynamics are modeled using PyPSA, a powerful open-source library for power system analysis. The CPN and the scheduling logic are implemented as a custom discrete-event simulator. The DRL agent is developed using PyTorch. For solving the MILP and LP problems in the Benders decomposition, we use the Gurobi optimizer.

The simulation is based on a modified IEEE 30-bus test system. It includes 6 conventional thermal generators, 4 utility-scale BESS units, and 5 large-scale renewable generation sites (3 solar, 2 wind).To ensure realism, we use real-world time-series data to model the stochastic RES generation. Solar irradiance data for locations in California is sourced from the National Renewable Energy Laboratory’s (NREL) National Solar Radiation Database (NSRDB)4. Wind power generation profiles for locations in Germany are obtained from the ENTSO-E Transparency Platform5. These datasets are used to generate 100 distinct 24-hour scenarios for the SUC problem.

Refer to caption
Figure 3:Baseline performance comparison. (a) Total operational cost; (b) Total carbon emissions; (c) RES curtailment; (d) CPN job success rate; (d) Average job tardiness.
The CPN consists of 5 geo-distributed nodes, each co-located with a major load bus in the IEEE 30-bus system. The arrival patterns and resource requirements of computational jobs are derived from processed Google Cluster Data traces6, which provide a realistic representation of large-scale data center workloads. The precedence constraints and dependency structures within jobs are modeled based on common scientific workflow patterns, such as pipeline workflow, available from the Pegasus Workflow Management System7.

To ground our environmental and economic calculations in reality, we incorporate two external data sources. Real-time marginal carbon intensity (MCI) data is obtained via the WattTime API, which provides 5-minute resolution data on the emissions impact of consuming an additional MWh of electricity in various grid regions8. Historical hourly locational marginal price (LMP) data is sourced from the California Independent System Operator (CAISO) public database9.

V-BComparison Schemes
To rigorously evaluate the performance of our TSCO framework, we compare it against three baseline methods that represent alternative approaches to the problem:

• Cost-Only Optimizer (CO-Opt) [32]: This baseline uses the same two-stage optimization architecture as TSCO but with the carbon price set to zero. This represents the current industry-standard approach of economic dispatch, which focuses exclusively on minimizing direct economic costs without explicit consideration for environmental impact.
• Renewable-Greedy Scheduler (RG-Sched) [33]: This is a heuristic-based CPN scheduling approach where tasks are always dispatched to the CPN node with the highest instantaneous RES power availability. The power system is not co-optimized; it simply reacts to the resulting CPN load profile. This baseline tests the efficacy of a simple “follow the renewables” strategy that ignores grid constraints and economic signals.
• Decoupled Framework (DC-Frame) [34]: This baseline represents the state-of-the-art in carbon-aware computing, where the power system and CPN are optimized separately. The power system operation is optimized first to generate a fixed 24-hour profile of electricity prices and carbon intensities. Subsequently, the CPN scheduler optimizes its task scheduling based on these static, pre-computed signals. This approach is carbon-aware but lacks the tight, real-time feedback loop of our co-optimization framework.
V-CSimulation Results
Refer to caption
Figure 4:Sensitivity analysis with varying carbon price. (a) Total operational cost; (b) Total carbon emissions; (c) RES curtailment; (d) CPN job success rate; (d) Average job tardiness.
V-C1Baseline Performance Comparison
In this scenario, all four methods were simulated over one week (168 hours) with the carbon price set at a representative value of 
$
50
/ton. Each data point presented is the result of 
10
 independent simulation runs, from which we calculate the mean and standard deviation and present in Fig. 3.

TSCO simultaneously achieves the lowest total operational cost and the lowest carbon emissions. The CO-Opt baseline, being carbon-agnostic, minimizes only direct fuel costs, resulting in 
41.5
%
 higher emissions and 
17.5
%
 higher total costs once the carbon price is factored in. This is because it relies heavily on the cheapest available thermal generators, regardless of their carbon intensity. The RG-Sched heuristic, while intuitive, performs poorly across the board. By myopically chasing renewables, it ignores grid congestion and the economic cost of dispatching thermal generators to support its decisions, leading to the highest operational cost and only modest emission reductions. The DC-Frame performs better than the naive baselines but is still significantly outperformed by TSCO. Its reliance on static, day-ahead signals prevents it from adapting to real-time deviations between forecasted and actual grid conditions, leading to 
12.7
%
 higher costs and 
16.2
%
 higher emissions. A key finding is TSCO’s ability to significantly reduce RES curtailment. By treating the CPN as a flexible load that can absorb surplus renewable generation in real-time, TSCO reduces curtailment by over 
60
%
 compared to DC-Frame and CO-Opt. This demonstrates the value of co-optimization in turning a major energy consumer into a valuable grid-stabilizing asset.

Additionally, the economic and environmental gains from TSCO do not come at the expense of computational performance. TSCO maintains a high job success rate 
98.5
%
 and low average tardiness 
12.3
 s, nearly on par with the cost-only optimizer. This is a direct result of the DRL agent’s reward function, which is designed to penalize deadline violations, forcing it to learn a policy that balances sustainability goals with QoS requirements. In contrast, the RG-Sched baseline suffers from a poor job success rate 
85.2
%
 and high tardiness because its singular focus on RES availability often leads it to schedule tasks on nodes that are already congested, highlighting the need for a holistic system view.

V-C2Sensitivity to Carbon Price
To analyze the trade-off between economic and environmental objectives, we varied the carbon price 
λ
C
​
O
2
 from 
$
25
/ton to 
$
150
/ton. This analysis focuses on the TSCO and DC-Frame methods, as the other two baselines are insensitive to carbon price by design. The comprehensive results are presented in Fig. 4.

The TSCO framework consistently achieves a better trade-off. For any given carbon emission level, it operates at a lower cost than the DC-Frame. As the carbon price increases, both methods are incentivized to reduce emissions, but TSCO does so more efficiently. This superior performance is a direct result of the real-time feedback loop between the grid and the CPN, which allows the system to find more efficient operating points. The RG-Sched method is shown as fixed points, as their operational strategy does not adapt to the carbon price.

It also shows how RES curtailment is affected by the carbon price. For both carbon-aware methods, increasing the price of carbon incentivizes greater utilization of zero-emission renewable energy, thus reducing curtailment. However, the TSCO framework’s ability to react to real-time conditions allows it to absorb significantly more renewable energy across all price points, maintaining a curtailment level that is less than half that of the DC-Frame. This again underscores the value of tight system integration for maximizing the use of clean energy resources.

VIConclusion
This paper has addressed the critical and intertwined challenges of rising energy consumption in CPNs and the increasing instability of power grids due to high renewable energy penetration. We have argued that treating these two complex systems in a decoupled manner leads to suboptimal outcomes, characterized by high costs, significant carbon emissions, and wasted renewable energy. To overcome these limitations, a novel TSCO framework was proposed, designed to synergistically manage power system operations and CPN task scheduling. The results clearly demonstrate that by enabling the CPN to act as an active, flexible participant in grid operations, significant benefits can be realized. Compared to a decoupled approach, our integrated TSCO framework reduced total operational costs and carbon emissions. Most notably, it slashed renewable energy curtailment by over 
60
%
 compared to conventional cost-only optimization, all while maintaining a high job success rate of over 
98.5
%
 for computational tasks.

The findings of this research have significant practical implications for both power system operators and the owners of large-scale computational infrastructure. For grid operators, flexible CPNs can serve as a valuable source of ancillary services, reducing the need for expensive battery storage or fossil-fuel reserves. For CPN operators, participating in such programs can create new revenue streams and drastically reduce operational expenditures and carbon footprints.