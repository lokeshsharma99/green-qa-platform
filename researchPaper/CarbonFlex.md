CarbonFlex: Enabling Carbon-aware Provisioning and Scheduling for Cloud Clusters

Walid A. HanafyUniversity of Massachusetts AmherstUSALi WuUniversity of Massachusetts AmherstUSADavid IrwinUniversity of Massachusetts AmherstUSAPrashant ShenoyUniversity of Massachusetts AmherstUSA

Abstract.

Accelerating computing demand, largely from AI applications, has led to concerns about its carbon footprint. Fortunately, a significant fraction of computing demand comes from batch jobs that are often delay-tolerant and elastic, which enables schedulers to reduce carbon by suspending/resuming jobs and scaling their resources down/up when carbon is high/low. However, prior work on carbon-aware scheduling generally focuses on optimizing carbon for individual jobs in the cloud, and not provisioning and scheduling resources for many parallel jobs in cloud clusters.

To address the problem, we present CarbonFlex, a carbon-aware resource provisioning and scheduling approach for cloud clusters. CarbonFlex leverages continuous learning over historical cluster-level data to drive near-optimal runtime resource provisioning and job scheduling. We implement CarbonFlex by extending AWS ParallelCluster to include our carbon-aware provisioning and scheduling algorithms. Our evaluation on publicly available industry workloads shows that CarbonFlex decreases carbon emissions by ∼57% compared to a carbon-agnostic baseline and performs within 2.1% of an oracle scheduler with perfect knowledge of future carbon intensity and job length.

†submissionid:107

1.Introduction

Data centers’ energy demand is growing at unprecedented levels (Shehabi et al., 2024), raising concerns about their carbon emissions and environmental impact. For example, a recent report predicts that global data center energy consumption will reach 1000 terrawatt-hours (TWh) by 2026 (International Energy Agency, 2024), or the equivalent of the average annual energy consumption of ∼33 million U.S. homes. This energy demand is expected to rise to 6-12% of the total U.S. electricity demand in the next 3-5 years (Shehabi et al., 2024). Beyond the technical challenges in satisfying surging data center demand (Lin et al., 2024), their operations are also raising environmental and health concerns (Han et al., 2024). The Information and Communication Technologies (ICT) sector is now responsible for an estimated 1.5-4% of global carbon emissions, with data centers contributing the largest share (World Bank, 2023). Indeed, Google recently reported a 48% increase in its carbon footprint over the past five years (Google, 2024). To address the problem, data center operators, particularly large hyperscalers, have begun taking steps to reduce their carbon footprint by optimizing their energy sources and operations.

Data centers and cloud providers have long used supply-side approaches to decrease their emissions by procuring low-carbon energy in the market (Carbon Offset Guide, 2024). For example, cloud providers often make power purchase agreements (PPAs) with low-carbon energy suppliers, such as wind farms, to procure sufficient low-carbon energy to match their annual energy consumption (Daniels, 2020; Miller, 2022). However, PPAs do not eliminate carbon emissions, as data centers still rely on grid energy and may consume high-carbon energy whenever their demand exceeds the supply of low-carbon energy, which is often from intermittent renewables (Cole et al., 2021).

To complement supply-side strategies, researchers have proposed demand-side optimizations that reduce carbon by leveraging computing’s flexibility and adapting its demand to increase the use of low-carbon energy. For example, a significant fraction of computing demand comes from batch jobs that are often delay-tolerant and elastic, which enables schedulers to reduce carbon by suspending/resuming jobs and scaling their resources down/up when carbon is high/low (Acun et al., 2023; Sukprasert et al., 2024; Radovanović et al., 2023; Hanafy et al., 2023b; Dodge et al., 2022; Gsteiger et al., 2024).

Given the potential above, there has been significant recent work on leveraging demand-side optimization to reduce carbon emissions of parallel batch jobs in the cloud (Hanafy et al., 2023b; Wiesner et al., 2021; Souza et al., 2023; Lechowicz et al., 2023). For example, recent work leverages batch jobs’ delay-tolerance to reduce carbon by simply suspending them when energy’s carbon intensity is high, i.e., above some threshold, and resuming them otherwise (Wiesner et al., 2021). Other work leverages parallel jobs’ elasticity to reduce carbon by scaling their resources down and up when energy’s carbon intensity goes up and down, respectively. However, prior work has generally focused on optimizing carbon emissions for individual parallel jobs in the cloud, and not provisioning and scheduling resources for many parallel jobs in cloud clusters (Hanafy et al., 2023b).

Designing a carbon-aware scheduler for multiple parallel jobs in cloud clusters poses new challenges not addressed by previous scheduling approaches. First, clusters have a capacity limit that prior work on optimizing individual jobs in the cloud does not consider. Considering a capacity limit is important to avoid a “thundering herd” problem (Ruane, 1990) where all jobs defer their execution to the same low-carbon time and potentially exceed the cluster’s capacity. Second, prior per-job approaches often assume that important job characteristics, such as job length, are known a priori. However, batch schedulers in practice generally do not know such detailed job-level information. For example, prior work has shown that accurately estimating per-job resource usage and duration is challenging (Kuchnik et al., 2019). Third, per-job approaches generally focus on minimizing carbon emissions while meeting the job deadline, while cluster schedulers often optimize other metrics, such as mean waiting time, makespan, and throughput.

Beyond per-job scheduling, prior work at the cluster level has explored carbon-aware cluster capacity provisioning (Radovanović et al., 2023; Lin and Chien, 2023; Hanafy et al., 2024; Zhang and Chien, 2021; Zheng et al., 2020). Given their low average utilization (Tirmazi et al., 2020; Shehabi et al., 2016, 2024), prior work adapts the cluster’s resource capacity based on energy’s carbon intensity—by opportunistically scaling cluster capacity up when carbon is low. For example, Google defines a Variable Capacity Curve (VCC) (Radovanović et al., 2023) that determines a cluster’s time-varying capacity limit. This approach implicitly shifts jobs to run when the carbon intensity is low. However, prior cluster-level techniques for reducing carbon emissions focus on resource provisioning and overlook more efficient scheduling decisions, which can lead to higher carbon emissions and job completion times (Souza et al., 2023; Hanafy et al., 2023b).

To address these limitations, we present CarbonFlex, a carbon-aware resource manager. CarbonFlex views cluster resource management as two distinct tasks: capacity provisioning and job scheduling, and applies the principle of elastic scaling to both its provisioning and scheduling decisions. In particular, CarbonFlex leverages the elastic scaling capabilities available in many parallel batch jobs (e.g., scientific simulations (Fox et al., 2017; Martín-Álvarez et al., 2024; Tarraf et al., 2024) and machine learning training), where scaling their allocated resources up or down according to the carbon intensity is beneficial in carbon optimization. Moreover, when such elastic scheduling is done in conjunction with cluster-level capacity provisioning, where the entire cluster capacity is also scaled in a similar fashion, CarbonFlex can further decrease carbon emissions.

CarbonFlex’s elastic scaling and scheduling generalizes the notion of resource scaling introduced in CarbonScaler (Hanafy et al., 2023b), by combining elastic scaling of parallel batch jobs with time-varying cluster capacity provisioning. Unlike CarbonScaler, which requires a priori knowledge of job length, CarbonFlex’s algorithms operate without this information and achieve greater savings. Furthermore, the separation of resource provisioning from job scheduling in CarbonFlex allows integration with alternative provisioning strategies–such as the VCC approach (Radovanović et al., 2023)–or the use of CarbonFlex’s capacity provisioning approach with other cluster schedulers.

A key insight in CarbonFlex is the use of continuous historical learning—learning over historical data—to drive its provisioning and scheduling decisions. Specifically, we utilize theoretical results that provide the basis for optimal carbon-aware scheduling of batch jobs in an offline setting where full future knowledge of job arrival, job lengths, and carbon intensity variations is known. In practice, while the future is unknown, the history of job arrivals, job characteristics, and carbon intensity is known. CarbonFlex uses this information to “simulate” the offline optimal algorithm over past time windows to learn the scheduling and provisioning decisions and then uses parameters from this simulated execution for its runtime scheduling and provisioning. When the distributions of job characteristics and carbon intensity variations are stable, CarbonFlex’s decisions achieve carbon savings that are close to the optimal algorithm and are significantly better than other baseline methods. Moreover, by continuously learning from historical data in this manner, CarbonFlex can adapt to changes in both job characteristics and carbon intensity variation patterns over time. Our hypothesis is that continuous learning of optimal provisioning and scheduling decisions over historical job traces is an effective approach for carbon-aware provisioning and scheduling of elastic parallel batch jobs in cloud clusters.

In designing, implementing, and evaluating CarbonFlex, our paper makes the following contributions.

(1)

We present the design of CarbonFlex, a resource manager for cloud clusters that optimizes operational carbon emissions by continuously learning provisioning and scheduling decisions from historical traces.

(2)

We implement a prototype of CarbonFlex on AWS ParallelCluster (Amazon Web Services, 2024), a cloud HPC environment, using CPU and GPU clusters, and demonstrate its efficacy for a wide range of elastic MPI-based scientific and ML training jobs.

(3)

We evaluate CarbonFlex using publicly available cluster traces, job profiles, and carbon intensity traces from different geographical regions. Our evaluation results show that CarbonFlex decreases carbon emissions by more than 57.5%, compared to a carbon-agnostic baseline and performs within 2.1% of a carbon-aware scheduling oracle.

2.Background

This section presents background on data center carbon emissions, carbon-aware scheduling, and elastic batch jobs.

2.1.Data Centers and the Electricity Grid

Data centers have traditionally focused on optimizing their energy efficiency through a variety of infrastructure-level and operational-level optimizations (Orgerie et al., 2014; Barroso and Hölzle, 2007). For example, innovations in cooling (e.g., open-air cooling) have yielded significant reductions in their Power Usage Effectiveness (PUE), a metric that captures data centers’ energy efficiency. However, since data center energy efficiency has become highly optimized, further optimizations are expected to yield diminishing marginal improvements. Thus, cloud operators have begun to focus directly on the environmental and carbon impact of data center infrastructure (Acun et al., 2023; Radovanović et al., 2023). The carbon impact of data centers consists of two main components: (i) operational emissions, which comprise the emissions generated from the energy consumed by the hardware and infrastructure during its operations, and (ii) embodied emissions, which consist of the emissions generated during the manufacturing and transporting of the computing hardware and other infrastructure components (Gupta et al., 2022; Switzer et al., 2023). Our work focuses on optimizing operational emissions through demand-side workload shifting methods, as it constitutes the majority of data center carbon emissions (Malmodin et al., 2024; Schneider et al., 2025).

Demand-side shifting methods, such as temporal and spatial shifting, are feasible in data centers because the carbon emissions from the consumption of a unit of electricity are not constant and vary continuously over time and across geographic regions. These variations are captured by energy’s carbon intensity (CI), measured in grams of CO2 per kWh of electricity or g⋅CO2eq/kWh, which captures the greenhouse gas (GHG) emissions per unit of electricity generated. The emissions from a unit of electricity generated depend on the source of generation, with fossil-based sources (e.g., natural gas and coal) having a high carbon intensity, while renewable sources (e.g., wind, solar, and hydro) have a low or zero carbon intensity.


Figure 1.Carbon Intensity Variations in four locations in the first week of April 2022.

\Description

Carbon Intensity Variations in four locations in the first week of April 2022.

Figure 1 shows an example of four regions — with different energy sources — representing carbon intensity exhibited by cloud data centers. As shown, the figure highlights that the carbon intensity varies widely among locations with up to a ∼400g⋅CO2eq/kWh difference between Virginia and Canada, Ontario, two regions equally distant from customers in the northeast of the US. Moreover, the figure shows that even at a given location, carbon intensity fluctuates over time. For instance, the figure shows that the carbon intensity in California varies daily by ∼100g⋅CO2eq/kWh, resulting in different carbon footprints as per the time of execution. Workload-shifting techniques exploit these spatial and temporal variations by opportunistically performing more work at low-carbon periods or regions to reduce their operational emissions(Acun et al., 2023; Radovanović et al., 2023; Hanafy et al., 2023b; Dodge et al., 2022; Sukprasert et al., 2024; Gsteiger et al., 2024).

Table 1.Summary of prior work

ApproachMultipleJobsUnknownJob LengthCapacityScalingCarbon-awareSchedulingResourceScalingWait Awhile (Wiesner et al., 2021) ✘✔✘✔✘DTPR (Lechowicz et al., 2023) ✘✘✘✔✘Wait and Scale (Souza et al., 2023) ✘✔✘✔✔Carbon Scaler (Hanafy et al., 2023b) ✘✘✘✔✔GAIA (Hanafy et al., 2024) ✔✔✔✔✘Green (Xu et al., 2025) ✔✔✘✔✔Risk-Aware  (Perotin et al., 2023) ✔✘✔✔✘Google VCC (Radovanović et al., 2023) ✔✔✔✘✘Adaptive Capacity (Lin and Chien, 2023) ✔✔✔✘✘CarbonFlex✔✔✔✔✔

2.2.Carbon-Aware Scheduling

Carbon-aware scheduling has focused on temporal shifting approaches that schedule jobs according to the carbon intensity and provisioning approaches that change the cluster size as per the carbon intensity.

Temporal Shifting. The temporal variations in carbon intensity have motivated researchers to utilize the inherent temporal flexibility of batch jobs by running them during low-carbon periods and suspending them during high-carbon periods (Wiesner et al., 2021; Souza et al., 2023; Hanafy et al., 2024; Acun et al., 2023; Lechowicz et al., 2023; Sukprasert et al., 2024). In addition, researchers have proposed elastic scheduling methods, where jobs are typically scaled at low carbon periods and suspended at high carbon periods, eliminating the need to extend the deadline, or increasing the savings compared to typical suspend-resume approaches (Hanafy et al., 2023b; Souza et al., 2023). The key issue for these approaches is that they typically focus on the scheduling of individual jobs. In doing so, these approaches either utilize a threshold-based approach  (Wiesner et al., 2021; Souza et al., 2023), which requires significant manual tuning to select a proper threshold and scale that balances the carbon savings and performance or assume full knowledge of the job length (Hanafy et al., 2023b; Lechowicz et al., 2023), which is typically known to be error prone in practice  (Kuchnik et al., 2019; Ambati et al., 2021). Moreover, these individual job approaches do not consider the data center-wide capacity constraints, resulting in demand bursts at low carbon periods  (Hanafy et al., 2024), also known as the stampede or the thundering herd problems.  Table 1 depicts a summary of these approaches’ key assumptions and mechanisms.

Cluster Schedulers.

At a cluster-level, carbon optimizations utilize the ability to vary the cluster capacity as well as the low average utilization of data centers (Tirmazi et al., 2020; Shehabi et al., 2016, 2024), to change the cluster capacity based on temporal variations in carbon intensity (Radovanović et al., 2023; Lin and Chien, 2023; Hanafy et al., 2024; Perotin et al., 2023; Zheng et al., 2020; Zhang and Chien, 2021). The key idea behind these approaches is varying the cluster size based on the carbon intensity of electricity—by opportunistically using larger cluster capacities in low carbon periods. For example, Google’s variable capacity curve (VCC) (Radovanović et al., 2023) computes a time-varying capacity limit for a data center cluster and then uses batch scheduling to schedule jobs in this variable capacity cluster, which forces batch jobs to move to lower carbon periods while ensuring the daily demand is met. However, despite the benefits of these approaches, they tend to focus on varying the cluster capacity rather than job scheduling. For instance, these approaches do not utilize application elasticity or explicitly address the demand bursts in low-carbon periods.  Table 1 summarizes the state-of-the-art approaches carbon-aware provisioning and scheduling. In this paper, we explore the benefits of utilizing carbon-aware provisioning and scheduling, where we vary the cluster size while scheduling jobs to reduce carbon emissions further.


Figure 2.Elastic scaling profiles of different MPI and machine learning jobs that depict the marginal increase in throughput for each additional server.

\Description

Elastic scaling profiles of different MPI and machine learning jobs that depict the marginal increase in throughput for each additional server.

2.3.Elastic Batch Jobs and Scaling Profiles

Elastic scaling, also referred to as malleability (Tarraf et al., 2024; Martín-Álvarez et al., 2024), is the ability to change the allocated resources seamlessly and has been shown to be applicable to a broad class of distributed batch jobs. For instance, machine learning frameworks (e.g., Pytorch (Paszke et al., 2019)), Data Processing frameworks (e.g., Spark (Zaharia et al., 2012)), Parallel Programming Frameworks (e.g., MPI (Comprés et al., 2016) and Charm++(Kale and Krishnan, 1993)) allow applications to adapt resources dynamically. Elastic scaling capabilities have enabled cluster operators to increase the utilization of cluster resources and avoid head-of-line blocking, fault-tolerance, and decrease energy consumption (Tarraf et al., 2024; Gupta et al., 2014; Prabhakaran et al., 2015; Xiao et al., 2020; D’Amico et al., 2019; Peng et al., 2018; Jayaram Subramanya et al., 2023; Qiao et al., 2021). In contrast, we focus on elastic scaling to optimize clusters’ operational emissions.

Elastic scaling of a batch job must consider its scaling characteristics — since batch jobs rarely scale linearly with the number of allocation servers. Typically, the scaling behavior of a distributed job depends on its compute and communication characteristics (Jayaram Subramanya et al., 2023; Hanafy et al., 2023b; Li et al., 2024). The greater the communication per unit compute, the less likely the job’s throughput will scale with increasing resources. This is because communication bottlenecks increase when the computational resources are scaled up, resulting in diminishing increases in performance.  Figure 2 shows the elastic scaling profiles of different batch applications. The setup for these profiles is detailed in  Section 6.1. As shown, applications exhibit varying elastic scaling behaviors as per their compute-to-communication ratios. For example, EffNet-S has 8.37 GFLOPs and is 82.7 MB, while ResNet18 has 1.81 GFLOPs and is 44.7MB1, making the communication (model memory footprint) per unit compute 9.8MB/GFLOPs, 24.6MB/GFLOPs for EffNet-S and ResNet18, respectively, yielding higher scalability of EffNet-S as depicted in the figures.

3.Carbon-aware Cluster Resource Management

This section describes the carbon-aware cluster provisioning and scheduling problem addressed in this paper.

Our work assumes a homogeneous cloud clusters consisting of either CPU or GPU servers and aims to optimize the operational carbon footprint of parallel batch jobs. We assume that the cluster capacity can be dynamically varied over time — using cloud interfaces to acquire or release server instances — and that the maximum allowed cluster capacity is capped by a configurable parameter M. Similar to batch cluster schedulers, the cluster is assumed to support multiple submission queues (e.g., by job priority), where we assume that each queue has a pre-configured maximum delay di associated with it. This delay parameter di indicates the maximum duration (“slack”) the job can wait or be paused during its execution. Users submit their batch jobs to a specific queue according to their willingness to delay their jobs in exchange for potentially higher carbon savings.

Our work targets elastic distributed (or parallel) batch jobs that run concurrently on multiple servers and potentially communicate across components during execution. Each job j has an arrival time aj and is submitted to job queue i that is configured with maximum delay di. The number of servers k allocated to the job can be varied at run-time between an upper and lower bound: k∈[kjm⁢i⁢n,kjm⁢a⁢x] where kjm⁢i⁢n and kjm⁢a⁢x denote the minimum and maximum numbers of servers that can be allocated to that job. Our model also supports non-elastic workloads (i.e., kjm⁢i⁢n=kjm⁢a⁢x), where only the cluster capacity is scaled (see  Section 6.4). Further, we assume that a job’s elastic scaling profile is known, which can be learned from profiling or performance models that consider the communication and computation patterns of jobs (Qi et al., 2017; Oyama et al., 2016; Pei et al., 2019; Justus et al., 2018; Cai et al., 2017; Peng et al., 2018; Shi et al., 2018). Our work considers a normalized elastic scaling profile, where the profile of a job j, denoted as pj, captures the normalized throughput increase (i.e., marginal throughput) for each additional server k where k∈[kjm⁢i⁢n,kjm⁢a⁢x], and pj⁢(kjm⁢i⁢n)=1.

Under this scenario, at each time slot t, given the set of queued up and currently executing jobs Nt, maximum cluster capacity M, delay configurations D, and carbon intensity C⁢It, our goal is to make two decisions: (i) provisioning decision: what should be the cloud cluster capacity for the next time step and (ii) scheduling decision: how many servers should be allocated to queued and running jobs, subject to the maximum allowed cluster capacity. The objective is to minimize the operational carbon emissions of the entire cluster while completing jobs within their queue-specific slacks.

4.CarbonFlex Design


Figure 3.Overview of the learning and execution phases of CarbonFlex.

\Description

Overview of CarbonFlex.


Figure 4.Representing the decisions made by CarbonFlex(Oracle) as a provisioning and scheduling policy.

\Description

Representing the decisions made by CarbonFlex Oracle.

This section presents CarbonFlex’s design and its elastic scaling-driven provisioning and scheduling algorithms.

4.1.CarbonFlex Overview

CarbonFlex is a carbon-aware resource manager for batch-oriented cloud clusters. The design of CarbonFlex is based on three key principles:

(1)

Separate Provisioning from Scheduling: CarbonFlex views cluster resource management as two distinct tasks: provisioning and scheduling. The provisioning policy ϕ⁢(⋅) determines how many servers to acquire from the cloud for the entire clusters, while the scheduling policy ψ⁢(⋅) determines which batch jobs to run on the available servers and how many servers to allocate to each. This separation of provisioning and scheduling is similar to other frameworks such as Mesos (Hindman et al., 2011).

(2)

Elastic Scaling: CarbonFlex applies the principle of elastic scaling to both its provisioning and scheduling policies, but with a carbon-aware focus. CarbonFlex dynamically adjusts the cluster capacity and scale of batch jobs in response to carbon intensity variations, workload demand, and workloads’ scalability.

(3)

Historical Learning: Lastly, CarbonFlex uses a historical learning approach to derive its provisioning and scheduling decisions. To do so, CarbonFlex simulates an offline oracle algorithm over past job arrivals to determine how such an optimal algorithm (which has full knowledge of job characteristics, carbon intensity, and future arrivals) would schedule jobs in a carbon-efficient manner. CarbonFlex continuously learns key parameters for provisioning and scheduling from this historical analysis and uses them to derive its provisioning and scheduling decisions. We argue that under the presence of a stable workload distribution, mimicking the decisions of an oracle provides similar carbon savings at runtime without any knowledge of job characteristics or future arrivals. We handle workload changes through continuous learning, which enables adaption to distribution shifting by “relearning” the parameters needed for scheduling and provisioning.

Figure 3 depicts CarbonFlex’s architecture and shows how the design principles above are instantiated through the learning and execution phases. In doing so, CarbonFlex employs a two-step approach: 1) a Learning Phase, where CarbonFlex employs continuous historical learning phase over the most recent cluster execution traces and captures the key decisions at different runtime states, and 2) an Execution phase, where CarbonFlex utilizes such knowledge to enhance its provisioning and scheduling, which we detail below.

4.2.Learning Phase

The CarbonFlex’s learning phase (see  Figure 3) employs continuous historical learning on recent cluster execution logs by replaying them to an offline oracle algorithm and learning from its provisioning and scheduling decisions. The process involves periodically (e.g., daily) tracking the job arrival logs and carbon intensity traces over a window of length T and replaying those traces to a simulated oracle algorithm. Note that the oracle algorithm can not be employed in practice since it requires full knowledge of the job arrival sequence, job characteristics, and carbon intensity variations. However, since the learning phase operates over historical traces, the entire arrival trace, characteristics of the jobs, and carbon intensity traces are known over the window T, making it possible to simulate an oracle over this past window. The oracle’s decisions can be viewed as mappings from the overall system state at each time t to the cluster capacity used for that state and the scheduling behavior in that case.

As an example, consider a simplified system state described using two parameters: a carbon intensity value at time t, denoted by C⁢It, and a job vector Nt that captures the number of jobs (running and queued) in each job queue. In this case, the tuple mapping (C⁢It,Nt)↦(mt,ρ) denotes the cluster capacity mt that was provided by the oracle for that system state, while ρ denotes the lowest marginal throughput across all scheduled jobs, indicating that no jobs with elastic scaling curves below this threshold were chosen for execution. The tuple mappings from the oracle’s simulated decisions at each time step t are then stored in a knowledge base that is later consumed during the execution phase.

Input: Jobs N, Max Resources M, Carbon Intensities 𝒞⁢ℐ.

Output: Schedule S

1 Initialization: S←{s1,…,sN} and L←[];

2for j∈N do

3      for t∈[aj,aj+lj+dj] do

4            for k∈[kjm⁢i⁢n,kjm⁢a⁢x] do

5                  L.append(j,t,k,pj⁢(k)/C⁢It,aj+lj+dj);

6                  

L← Sort(L) ; // w.r.t. pj⁢(k)/C⁢It then aj+lj+dj

7 while |L|>0 do

      j,t,k,∗,∗←L.pop(); // next highest pj⁢(k)/C⁢It

8       if ∑j′∈N∖jsj′⁢[t]+k>=M then

            continue; // I cannot scale the current job.

9            

10      if p⁢r⁢o⁢g⁢r⁢e⁢s⁢s⁢(sj)<100% then // Job not done.

11            

            sj⁢[t]=k; // allocation of j in slot t as k.

12            

13for sj∈S do

14       if p⁢r⁢o⁢g⁢r⁢e⁢s⁢s⁢(sj)<100% then

            return None // Non Feasible

15            

return S

Algorithm 1 CarbonFlex_Oracle_Algorithm()

CarbonFlex Oracle.

The oracle, depicted in Algorithm 1, is a greedy algorithm that generates an execution schedule and a time-varying cluster capacity required to execute that schedule over a past window T. The algorithm takes historical job traces of T-length (e.g., a week) containing N jobs. Each job is characterized by an arrival time aj, job length lj, allowed delay dj (based on the selected job queue), and a scaling profile pj, as explained in  Section 3. Using a resource at time slot t:t∈[0,T] incurs a constant cost C⁢It (e.g., carbon intensity), where 𝒞⁢ℐ={C⁢I1,C⁢I2,…⁢C⁢IT} is the set of carbon intensities for the T-length window. The algorithm then creates the execution schedule that optimizes the cluster’s total carbon emissions by creating a schedule s for each job while respecting its arrival and delay constraints, as well as the maximum cluster capacity M.

Algorithm 1 uses a greedy approach for elastically scaling and scheduling jobs. The key insight is that for any given carbon intensity value, doing more work per unit of energy (i.e., greedily choosing jobs with higher marginal throughput) yields better energy and carbon efficiency (Jayaram Subramanya et al., 2023; Hanafy et al., 2023b). The algorithm starts by computing the marginal throughput per unit of carbon by considering all jobs, the time allowed for each job (from aj to aj+lj+dj), and allowed scales [kjm⁢i⁢n,kjm⁢a⁢x]. Then, it sorts the list (Algorithm 1) in descending order of marginal throughput per carbon unit, using deadlines as a tie-breaking rule. For example, when two jobs have the same scalability (e.g., both at scale one), the job with the earliest deadline is prioritized. Since pj⁢(kjm⁢i⁢n)=1⁢∀j, all jobs are assigned kjm⁢i⁢n before scaling, which also ensures that no jobs are starved. The algorithm then iterates over the list, greedily assigning resources to jobs while respecting the maximum capacity until the job is completed, using the p⁢r⁢o⁢g⁢r⁢e⁢s⁢s⁢(⋅) function. Finally, it verifies that all jobs have completed; otherwise, it marks the schedule as infeasible for the specified cluster capacity and job delays. In this case, we repeat the algorithm while extending the deadline for jobs that were not finished.

Runtime Complexity and Optimality.

Algorithm 1 runs in polynomial time. To schedule a trace with N jobs and K scaling states on a cluster of M servers, the complexity of computing the marginal throughput per unit of carbon (Lines 2-5) is 𝒪⁢(N⋅K⋅T), marginal throughput list sorting (Line 6) is 𝒪⁢(N⋅K⋅T⋅log⁡(N⋅K⋅T)), and iterating over possible resource allocations (Lines 7-13) is 𝒪⁢(N⋅K⋅T), and finally, the time complexity of job completion validation (Lines 14-16) is 𝒪⁢(N). The total time complexity is 𝒪⁢(N⋅K⋅T+N⋅K⋅T⋅log⁡(N⋅K⋅T)+N) ≃𝒪⁢(N⋅K⋅T⋅log⁡(N⋅K⋅T)).

Theorem 4.1.

Algorithm 1 yields optimal carbon savings for homogeneous clusters and monotonically decreasing marginal throughput profiles.

Proof.

Algorithm 1 maps the carbon-aware scheduling problem to marginal throughput scheduling for which a greedy algorithm yields an optimal solution (Federgruen and Groenevelt, 1986). This optimality requires the following assumption: 1) scalability profiles featuring a monotonically decreasing marginal throughput curve (i.e., pj⁢(k)>pj⁢(k+1)⁢∀j,k), 2) the time-varying cost (carbon intensity in our case) is non-negative and bounded, and 3) switching cost (energy/emissions to scale the cluster or workloads) is negligible.2 ∎

Table 2.State representations and output decisions collected by CarbonFlex from the offline Oracle.

StateExplanationC⁢ItCarbon Intensity in g⋅CO2eq/kWh.C⁢ItGGradient of the CI curve at t.C⁢ItRRank of slot t compared to day-ahead CI.Queue LengthNumber of jobs (paused + running) per queue.ElasticityAverage elasticity across all jobs in the system.DecisionExplanationmtThe cluster capacity at time t.ρThe minimum used marginal throughput.

Retaining Oracle decisions.

The output of the offline oracle algorithm is visually depicted in  Figure 4 and can be viewed as (i) the provisioned cluster capacity at time t, which varies over time, and (ii) how these servers are assigned among jobs, where jobs are not scaled until all jobs are assigned a single resource. Given these decisions over the past time window T, CarbonFlex learns the provisioning policy as a mapping from the current system state at each time step t to the cluster size chosen at that step, i.e., a function that maps S⁢T⁢A⁢T⁢E↦mt. As discussed, the simplest representation of the current system state is the state of the job queues (e.g., the number of queued and running jobs in each queue) and the current carbon intensity values (C⁢It,Nt).

In practice, our approach uses several other parameters to fully capture the current state, as shown in  Table 2. These include carbon intensity gradient (whether the carbon intensity is increasing or decreasing), the day-ahead ranking of the C⁢ItR (how favorable the current slot is compared to the future CI forecast3), the number of jobs per queue, and the mean elasticity of all jobs in the system. Similarly, the scheduling threshold is computed as a mapping S⁢T⁢A⁢T⁢E↦ρ, which indicates that the oracle scheduling policy only schedules jobs with higher marginal throughput than the threshold. The provisioning and scheduling policy decisions per state mappings are then stored in a knowledge base that is later used in the execution phase. Finally, older mappings from the knowledge base are aged out over a rolling window to adapt to seasonal variations in carbon intensity and any changes in the workload distribution over time.

4.3.Run-time Provisioning and Scheduling

CarbonFlex’s execution phase implements runtime provisioning and scheduling algorithms that optimize carbon emissions while respecting the queue-specific delays. These algorithms use knowledge derived from the oracle’s decisions during the offline learning phase to make real-time decisions. At runtime, users submit their jobs to the cluster by selecting a job queue, e.g., by job length. At the start of each time slot t, the CarbonFlex computes the current system state, using the attributes in Table 2, and queries the knowledge base for the top-𝕜 closest matches in terms of similar system states that were seen in the past. CarbonFlex then mimics the decisions of these situations while considering the utility of these decisions in previous time slots.

Input: S⁢T⁢A⁢T⁢E, 𝕜, Delay violations v, Expected distance δ, Violation tolerance ϵ

Output: Provisioning Resources mt

1 ℜ←match(S⁢T⁢A⁢T⁢E, 𝕜)

2 if Distances(ℜ)>δ AND v>ϵ then

3       return M

4else if v>ϵ then

5       return Max(ℜ.mt)

return Mean(ℜ.mt)

Algorithm 2 CarbonFlex Provisioning ϕ(.)

Algorithm 2 lists how CarbonFlex determines the cluster capacity mt to provision for the next time slot. First, CarbonFlex uses the current state tuple and queries the knowledge base for the top-𝕜 best matches (e.g., using Euclidean distance). It then computes the mean provisioned capacity for the top-k matches and provisions the cluster size accordingly. Before doing so, it checks the average delay violations v experienced by recently completed jobs (e.g., in the last hour). If the violation exceeds a certain percentage ϵ, and the distance between the S⁢T⁢A⁢T⁢E and the closest cases is larger than δ, the provisioning function falls back to carbon-agnostic execution and provisions the maximum cluster capacity M.

Input: Current time t, Current jobs Nt, Available resources mt, Marginal throughput threshold ρ.

Output: Resource allocation St

1 Initialization: S←{} and L←[];

2for j∈Nt do

3      for k∈[kjm⁢i⁢n,kjm⁢a⁢x] do

4            if pj⁢(k)>ρ then

5                   L.append(j,k,pj⁢(k),aj+dj−t);

6                  

L← Sort(L) ; // w.r.t. pj⁢(k) then aj+dj−t

7 while |L|>0 and ∑j∈NtSj⁢[t]<mt do

      j,k,∗,∗←L.pop(); // next highest pj⁢(k)

       S⁢[j]=k; // increase allocation of j

8      

return S

Algorithm 3 CarbonFlex Scheduling ψ(.)

After “right-sizing” the cluster at the start of the time slot t, the scheduling algorithm in Algorithm 3 then decides which jobs to schedule and how much to allocate to each scheduled job at run (e.g., every Δ⁢t or whenever a job arrives or finishes). To do so, the algorithm iterates over the current jobs and selects all jobs with marginal throughput larger than ρ. It also computes marginal throughput at each scale and the available delay budget for each job. Then, it sorts assignments according to their marginal throughput and available delays (Algorithm 3). Finally, the algorithm iterates over the list of schedules, choosing jobs until the current capacity mt is filled. Similar to Algorithm 1, jobs are not scaled until all jobs are given kjm⁢i⁢n resources, ensuring high efficiency and avoiding starvation.

5.CarbonFlex Implementation

We implement CarbonFlex using AWS ParallelCluster (Amazon Web Services, 2024), a cluster management tool that deploys and manages high-performance computing (HPC) Slurm (Yoo et al., 2003) clusters in the cloud. AWS ParallelCluster uses EC2 instances that span various hardware configurations, networks, and accelerators. We implement CarbonFlex using PySlurm (pys, 2023) as a Slurm interface that submits workloads to the cluster according to our underlying provisioning and scheduling policies. Our prototype, available at (https://github.com/umassos/CarbonFlex), has the following components:

Continuous Learning: We implement our CarbonFlex(Oracle) on a simulation environment using Python. The CarbonFlex(Oracle) utilizes the historical workload traces, scheduling profiles, configurations, and historical carbon intensity data to calculate the carbon optimal schedule and compute the historical (S⁢T⁢A⁢T⁢E↦mt,ρ) mappings.

Runtime Provisioning: At the start of each slot, which we set as 1 hour, CarbonFlex computes the number of provisioned servers and scheduling configurations by following the decisions made by the offline oracle. Our implementation relies on Case-Based Reasoning that finds solutions by establishing similarities between current and historical states and executing similar actions while retaining the ability to interpret or understand confidence in the recommended solution (Watson and Marir, 1994). Our implementation finds similar states using KNN from the Scikit-learn library (Pedregosa et al., 2011), where we utilize Euclidean distance and represent the historical cases in a KD-Tree for fast access, select the nearest five instances 𝕜=5 and combine them as detailed in  Algorithm 2.

Elastic Scaling and Scheduling: After computing available capacity, CarbonFlex schedules workloads based on their marginal capacity, as detailed in Section 4.3. When the capacity or number of queued jobs changes or every Δ⁢t, e.g., 5 minutes, CarbonFlex computes each job’s resource assignment and scale using Algorithm 3, which can be efficiently implemented using a binary tree. To run a job, CarbonFlex submits it as a Slurm job to the appropriate job queue using PySlurm. Finally, to scale jobs, CarbonFlex uses the scancel command, which signals the job to checkpoint its state and submits a new job based on the new scale, resuming the progress. We report on these overheads in Section 6.8.

Energy and Carbon Monitoring: As stated earlier, CarbonFlex’s focuses on operational emissions, which constitute the majority of emissions in datacenters (World Bank, 2023; Malmodin et al., 2024). Considering embodied emissions in carbon-aware scheduling, is subject to the sunk cost fallacy (Bashir et al., 2024). We compute the operational carbon emissions of the cluster at time t, denoted as 𝒞t, as follows:

(1)𝒞t=∑jNtEj⁢s×ct(2)Ej⁢s=Ej⁢sR+Ej⁢sn⁢e⁢t(3)Ej⁢sn⁢e⁢t=ηn⁢e⁢t×M⁢e⁢mj⁢s

where Ej⁢s represents the energy consumption by job j at scale s, which consists of compute and network components, denoted as Ej⁢sR and Ej⁢sn⁢e⁢t, respectively.4 Ej⁢sR takes into account the number of compute resources (e.g., CPU cores) and can be augmented to include energy consumption for memory, base power, and PUE. However, due to the challenges in accurately assessing power consumption per tenant in data centers, our CPU experiments involve clusters where these numbers are often not known, and we assume a fixed value per resource, a common approach in carbon accounting (Gsteiger et al., 2024; Engineering, 2021; Lannelongue et al., 2021). Further, our results emphasize normalized savings, making absolute energy or carbon values less significant. In contrast, for GPU experiments, we utilize nvidia-smi, which allows us to measure the energy usage for each GPU and aggregate it across the scale employed by this job.

To account for the network cost Ej⁢sn⁢e⁢t, we utilize the network energy efficiency (ηn⁢e⁢t) measured in W/G⁢b⁢p⁢s and M⁢e⁢mj⁢s is the amount of data transferred by the job j at scale s. Since ηn⁢e⁢t widely varies in prior work, by up to three orders of magnitude (e.g., due to network type and topology) (Tabaeiaghdaei et al., 2023; Jacob and Vanbever, 2023; Van Heddeghem et al., 2012), our experiments utilize a value of 0.1W/G⁢b⁢p⁢s. Lastly, we compute M⁢e⁢mj⁢s based on the communication paradigm used for the workload as per its implementation and memory requirements (e.g., distributed training (Paszke et al., 2019) uses Ring-Allreduce).

Simulation Environment: Lastly, we integrate the online and offline scheduling policies and the baselines into a simulation environment, denoted as CarbonFlex-Simulator, which enables year-long evaluation.

6.Experimental Evaluation

This section evaluates the performance of our CarbonFlex prototype and its provisioning and scheduling policies based on its carbon savings and delay under different scenarios. We evaluate CarbonFlex’s carbon emissions using real-world CPU and GPU clusters on AWS ParallelCluster (Amazon Web Services, 2024). Then, we augment our prototype evaluation with additional simulations that leverage CarbonFlex-Simulator. Lastly, we present a sensitivity analysis and system overheads.


Figure 5.Diversity in selected Carbon Intensity traces.

\Description

Diversity in selected Carbon Intensity traces.

6.1.Experimental Setup

Workload Traces. Our experiments use three workload traces: a month-long Azure trace (Cortez et al., 2017); a two-month Alibaba-PAI trace (Weng et al., 2022); and a year-long SURF Lisa-HPC trace (Chu et al., 2024), each of which has different arrival patterns and job lengths. In our experiments, we focused on hour+ workloads, as shorter jobs have minor contributions to the total compute time, and they are usually not delay-tolerant. Then, we sample these traces by creating historical and evaluation traces. We split the historical trace into two week-long traces and used them for the learning phase, while the evaluation trace is a week-long trace used to evaluate our proposed approaches. We sample these traces from different parts of the trace. For instance, we utilize the first two weeks of the Azure for sampling the historical trace and the third week to sample the evaluation trace. In contrast, for more extended traces such as Alibaba-PAI traces that span two months, we utilized the first 7 weeks for learning and the 8th week for evaluation. Finally, unless otherwise stated, we randomly assign the elasticity profiles (see Table 3) to the workloads.

Table 3.Details of the elastic workloads in evaluation.

WorkloadImpl.Comm. SizeScalabilityN-body(N⁢=⁢100⁢k)  (Aarseth, 1985) MPI5.3 MB∗HighN-body(N⁢=⁢10⁢k)  (Aarseth, 1985) MPI0.53 MB∗HighN-body(N⁢=⁢3⁢k)  (Aarseth, 1985) MPI0.16 MB∗ModerateN-body(N⁢=⁢2⁢k)  (Aarseth, 1985) MPI0.1 MB∗ModerateJacobi(N⁢=⁢3⁢k) (Verschelde, 2016) MPI51.2 MB∗LowJacobi(N⁢=⁢2⁢k) (Verschelde, 2016) MPI28.6 MB∗LowJacobi(N⁢=⁢1⁢k) (Verschelde, 2016) MPI7.16 MBLow*AlexNet (Krizhevsky et al., 2012) Pytorch233.1 MBLowResNet18 (He et al., 2016) Pytorch44.7 MBLowResNet50(He et al., 2016) Pytorch97.8 MBModerateResNet101(He et al., 2016) Pytorch170.5 MBHighEffNet-S (Tan and Le, 2021) Pytorch82.7 MBHighViT-B/32(Dosovitskiy et al., 2021) Pytorch336.6 MBModerate∗ This application present our least scalable workload (See  Figure 2).

Elastic Workloads  Table 3 describes our CPU and GPU workloads implemented using MPI (Message Passing Interface Forum, 1994) and Pytorch (Paszke et al., 2019), respectively. The table presents the workload names, communication sizes in MB, and scalability, categorizing applications as High, Moderate, or Low scalability jobs. We obtain profiles through one-time profiling that iterates over possible nodes between [km⁢i⁢n,km⁢a⁢x] and runs for a brief duration (typically a few minutes). In our current experiments, we profiled workloads on AWS at various scales. CPU loads were profiled between [km⁢i⁢n=1,km⁢a⁢x=16] CPU cores, while GPU loads were profiled from [km⁢i⁢n=1,km⁢a⁢x=8] due to limitations in GPU capacity.

Carbon Traces. We used hourly carbon intensity traces from Electricity Maps (Maps, 2022) for December 2021 to December 2022 for 10 geographical regions.  Figure 5 shows the mean carbon intensity and daily variability, measured by the Coefficient of Variation (CoV) throughout this period, where regions with higher CoV often depend on intermittent energy sources such as renewables. As shown, the selected regions represent possible situations of average carbon intensity and daily variability in carbon intensity. Finally, we assume knowledge of day-ahead carbon intensity, as prior work demonstrates that such forecasts are highly accurate (Maji et al., 2022).


(a)Carbon Emissions and Savings (on-top)


(b)Delay

Figure 6.Carbon emissions (a) and delay (b) across carbon-aware scheduling approaches for the CPU cluster.

\Description

Carbon emissions (a) and delay (b) across carbon-aware scheduling approaches for the CPU cluster.

Baselines. We compare our CarbonFlex with 5 state-of-the-art carbon-aware scheduling baselines for homogeneous resources. For fairness, we assume that all baselines have access to historical traces and can use the mean job length for computing the schedule:

(1)

Carbon-Agnostic: This policy represents the status quo, where jobs are scheduled FCFS without elastic scheduling. We use this policy as a baseline to compute the carbon savings for all other policies.

(2)

GAIA (Hanafy et al., 2024): We utilize GAIA’s Lowest-Window Policy, which schedules jobs in a non-elastic manner by selecting the best start time based on the mean job length within a time window d to minimize carbon emissions. We augment the policy with resource limits and use FCFS when multiple jobs want to run in the same time slot.

(3)

Wait Awhile (Wiesner et al., 2021): We implement the threshold version of the Wait Awhile policy, which operates the job in a suspend-resume fashion according to carbon intensity. The threshold is determined by the 30th percentile of carbon intensity predictions for the next 24 hours. To meet SLO requirements, the job runs to completion after the permitted delay. We use FCFS when multiple jobs want to run in the same time slot.

(4)

CarbonScaler (Hanafy et al., 2023b): We adapted the CarbonScaler algorithm to run at a multi-job cluster, where the schedule is computed based on historical job length. In addition, to respect the cluster-wide capacity, we prioritize scaling jobs with higher marginal throughput. Lastly, when the job surpasses its allowed delay, it runs until completion.

(5)

CarbonFlex(Oracle): Finally, we added the offline oracle as a baseline that implements  Algorithm 1 and assumes full knowledge of carbon intensity and job length.

Deployment. We deployed CarbonFlex in AWS and evaluated it on a CPU and GPU cluster. In our CPU cluster, we utilize 150 C8 VMs, yielding a mean utilization of ∼50%, the common utilization across clusters  (Shehabi et al., 2024). In contrast, for the GPU cluster, our resource quota only allowed for 15 G6 GPUs, so we limited the sampling to ensure similar utilization for this cluster size. To simulate the behavior of CarbonFlex(Oracle), specifically the learning phase, we replay the available historical trace with different start times, a step that helps improve the performance of CarbonFlex. Finally, we augment our evaluation with year-long assessments using CarbonFlex-Simulator to evaluate many different scenarios and settings. Note that, in all experiments, unless otherwise stated, we utilize the carbon intensity trace of South Australia; clusters have 50% utilization as reported utilization in real-world clusters (Tirmazi et al., 2020; Shehabi et al., 2024, 2016), which results in a maximum cluster capacity of 150 for CPU clusters and 15 for GPU clusters; and that the cluster has three length-based queues with d=6⁢h⁢r⁢s,24⁢h⁢r⁢s, and 48⁢h⁢r⁢s for short (l≤2hrs), medium (2<l≤12hrs) and long (l>12hrs) jobs.

6.2.Optimizing Carbon Emissions

In this section, we evaluated CarbonFlex’s ability to optimize a cluster’s carbon emissions under different configurations and compute types.

CPU Cluster. First, we evaluate the performance of CarbonFlex using our prototype on AWS using the C8 instances CPU-cluster, with M=150.  6(b) shows the total carbon emissions of our cluster under different scheduling baselines. As shown, CarbonFlex can reduce the carbon emissions by 51.4% (only 6.6% away from the CarbonFlex(Oracle)) and achieves 17.4%, 31%, and 33.3% higher savings than CarbonScaler, Wait Awhile, and GAIA, respectively. In addition, the results show that approaches that use scaling (e.g., CarbonFlex and CarbonScaler) offer higher savings as they can better utilize variations in carbon savings, while approaches that use suspend-resume scheduling (e.g., Wait Awhile) perform better than those that do not consider preemption.

6(b) shows the delay experienced across baselines, where the Carbon-Agnostic baseline exhibits no waiting and CarbonFlex(Oracle) respects all SLOs. As shown, policies typically respect the delay, where all approaches are configured to run to completion once the allowed delay period is over. The highest delays, however, are exhibited by scale-based approaches (e.g., CarbonFlex and CarbonScaler) as the use of provisioning in CarbonFlex may limit the cluster capacity and limit how jobs are scheduled, leading to an average delay of 17.5 hours. In addition, CarbonScaler may under-predict job length and delay it beyond the allowed delay, requiring the job to run beyond its allowed delay, leading to an average delay of 22.3 hours. Finally, it is worth noting that CarbonFlex will often have a lower average delay, as CarbonFlex(Oracle) can be aggressive in its carbon-aware scheduling decisions, delaying the jobs to the maximum possible time.


Figure 7.Carbon emissions and savings (on-top) across carbon-aware scheduling approaches in a GPU cluster.

\Description

Carbon emissions and savings (on-top) across carbon-aware scheduling approaches in a GPU cluster.

GPU Cluster  Figure 7 shows the carbon emissions and savings using our prototype evaluation on 15 G6 GPU cluster on AWS. As shown, CarbonFlex significantly reduces carbon emissions, achieving 57.5% savings, which is 2.1% from the CarbonFlex(Oracle). As in the CPU cluster, CarbonFlex is able to reduce carbon emissions by 20.8%, 44%, and 47.2% compared to CarbonScaler, Wait Awhile, and GAIA. Interestingly, the results reveal that in our GPU cluster — where applications exhibit inherently heterogeneous power consumption — approaches that use scaling can achieve higher carbon savings than the baseline methods relying on temporal shifting techniques. This occurs because scaling approaches prioritize workloads with higher marginal throughput during low-carbon periods (i.e., low communication per unit compute), which typically consume more power. Consequently, directing applications with higher power usage to low-carbon periods further enhances our savings.

Key Takeaways: On CPU and GPU clusters, CarbonFlex yields carbon savings up to 57.5% and 20.8% compared to Carbon-Agnostic and CarbonScaler, respectively.

6.3.Effect of Configurations

This section demonstrates how cluster configurations (e.g., delay) affect the carbon savings and CarbonFlex’s ability to adapt its decisions per these configurations.


Figure 8.Impact of the maximum cluster capacity on the carbon savings.

\Description

Impact of the maximum cluster capacity on the carbon savings.

Effect of Cluster Capacity The maximum cluster capacity represents the headroom available to stack workloads during low-carbon periods, reducing the total carbon emissions.  Figure 8 demonstrates the effect of headroom represented in terms of the maximum allowed cluster capacity limit, denoted as M, where M = 100, 150, and 200, which represents ∼75%, ∼50%, and ∼37% utilization, respectively. As shown, CarbonFlex closely follows CarbonFlex(Oracle) across all cluster capacities, achieving between ∼3.7% from the CarbonFlex(Oracle). In addition, CarbonFlex outperforms other approaches, such as CarbonScaler with up to 12.5% savings. Moreover, the figure shows that using elastic scheduling can better utilize the available capacity and further reduce carbon emissions. In contrast, approaches that only rely on temporal shifting increase the carbon savings by 8.4%. Moreover, the results show that increasing the cluster size comes with diminishing returns, where increasing the maximum cluster capacity from 100 to 200 by 13.2% and 13% from the CarbonFlex(Oracle) and CarbonFlex, respectively. Lastly, as detailed in the previous work (Hanafy et al., 2023a, b), elastic scaling introduces cost overheads, where increasing the cluster comes with increases in the total operational cost as applications run with lower marginal throughput. However, such overheads were negligible where the carbon overheads across all methods and cluster sizes were lower than 3.2%.


(a)Carbon Savings (%)


(b)Waiting Time

Figure 9.Impact of the allowed delay (slack) on the carbon savings (a) and waiting time (b).

Effect of Delay The delay represents the scheduling flexibility of workloads, a key aspect of carbon savings. Figure 9 shows the impact of extending the delay on the carbon savings and waiting time of CarbonFlex and other baselines, assuming that queues have the same delay. We change the allowed delay per job from 0 hrs (using only elasticity) to 36hrs. 9(a) shows that increasing the allowed delay to d=36hrs results in carbon savings of 18.3% and 13.8% for CarbonFlex(Oracle) and CarbonFlex, respectively. Notably, the figure shows that CarbonFlex follows the CarbonFlex(Oracle), where it achieves carbon savings within 3.6% of CarbonFlex(Oracle)’s savings. The figure also shows how other baselines behave under different temporal flexibilities. For instance, approaches such as Wait Awhile, which only depend on temporal shifting, result in no carbon savings when d=0 and only reduce carbon savings by 19.7% when d=36. In contrast, approaches that utilize elasticity (e.g., CarbonFlex(Oracle)) achieve much higher savings compared to non-elastic baselines.

9(b) shows the average waiting time across the cluster across different baselines. As expected, as the allowed delay increases, so does the waiting time. The figure shows that for the small allowed delays, CarbonFlex and CarbonScaler violate the allowed delay by 3.4 and 1.6 hours, which explains the increase of carbon savings over CarbonFlex in  9(a). Moreover, although not visible, some of the jobs in the oracle also exceed the deadline (i.e., a non-feasible schedule), which we fix by extending the delay for these specific jobs. However, as the allowed delay increases, CarbonFlex requires less delay as it greedily schedules resources at the first possible moment resources are available. Lastly, the figure shows that, across baselines, increasing the delay increases carbon savings but with diminishing returns  (Hanafy et al., 2023b; Sukprasert et al., 2024).

Key Takeaways: CarbonFlex can incorporate different configurations in its provisioning and scheduling decisions, outperforming other baselines and achieving savings that are within 3.6% of the CarbonFlex(Oracle).

6.4.Effect of Workload Characteristics

Besides the scheduling configuration, the characteristics of the workload traces (e.g., arrival rates or job scalability) affect the potential carbon savings. In this section, we assess the impact of workloads’ elasticity and workload traces.


Figure 10.Workload elasticity impact on carbon.

\Description

Impact workload elasticity on carbon savings.

Effect of Jobs Elasticity The elasticity of workloads is crucial for achieving significant carbon savings, as it enables workloads to take advantage of periods of low carbon intensity.  Figure 10 illustrates the impact of workload elasticity, comparing carbon savings across workloads with varying characteristics. We explore three scenarios in which we assume that all jobs exhibit specific scaling behaviors using N-body(N⁢=⁢100⁢k), N-body(N⁢=⁢2⁢k), and Jacobi(N⁢=⁢1⁢k) denoted as high, moderate, and low elasticity, (see  Table 3). Additionally, we use our primary scenario of randomly assigning profiles to workloads, referred to as “Mix,” and a “NoScaling” scenario, which highlights the benefits of CarbonFlex’s resource provisioning, in situations where jobs can only be paused but not scaled. As demonstrated, workloads with enhanced scaling can attain greater carbon savings, reducing carbon savings of up to 56.1% and 49.5% for the highly scalable workloads under CarbonFlex(Oracle), and CarbonFlex, respectively. In addition, aside from the scaling profile, CarbonFlex resembles CarbonFlex(Oracle)’s performance, achieving within 3.4% and 6.6% of its savings.

Moreover, the figure shows the benefits of CarbonFlex’s historical learning approach, where even without scaling, CarbonFlex can achieve higher carbon savings than baselines, achieving 1.4% more savings than CarbonScaler, which acts suspend-resume. Lastly, the figure illustrates how different approaches perform under different elasticity profiles. For instance, it shows that CarbonScaler cannot take advantage of high elasticity, performing significantly worse than other baselines. The reason is that all workloads adopt similar schedules, causing them to run during higher carbon periods and default to the lowest scale run-to-completion behavior. In contrast, baselines that do not use scaling (e.g., Wait Awhile) have a consistent behavior apart from the workloads’ elasticity behavior.


Figure 11.Carbon Savings across workload traces.

\Description

Carbon Savings across workload traces with different job lengths and arrival patterns.

Workload Traces The characteristics of the trace (e.g., average job length) dictate the potential carbon savings and the benefits of elastic scaling. Figure 11 illustrates the carbon savings across the Azure trace (Cortez et al., 2017), Alibaba trace (Weng et al., 2022), and SURF trace (Chu et al., 2024), where a maximum cluster capacity is selected to achieve 50% utilization. As shown, CarbonFlex can attain significant carbon savings across traces, ranging from 43.7% (3.6% from CarbonFlex(Oracle)) for the Azure trace to 36.9% (5.7% from CarbonFlex(Oracle)) for the Alibaba trace. The reason for these differences can be traced back to variations in job length, as Azure has a higher average job length compared to the other traces. This is also reflected in the disparities between elastic and non-elastic scheduling approaches, as shorter jobs do not benefit from scaling or interruptibility. This is evident in the difference in carbon savings between CarbonFlex and GAIA, which decreases from 22.3% in Azure to 11.6% in Alibaba, as well as between Wait Awhile and GAIA.

Key Takeaways: CarbonFlex achieves high carbon savings across workloads with different elasticity and length distributions. Our results demonstrate that our historical learning approach is beneficial without elastic scaling.


Figure 12.Carbon Savings (%) across locations under multiple job queues.

\Description

Carbon Savings (%) across locations under multiple job queues.


Figure 13.Impact of distribution shifts.

\Description

Impact of distribution shifts.


Figure 14.Comparing CarbonFlex with carbon-aware capacity provisioning.

6.5.Effect of Cloud Location

As noted in  Section 2.1, the supply mix significantly affects optimizing carbon emissions, where locations with a variable carbon intensity typically result in higher carbon savings. Figure 12 shows the carbon savings across ten locations sorted by the achievable carbon savings. As shown, CarbonFlex highly matches the carbon savings of CarbonFlex(Oracle), where it achieves 0.9% and 6.31% within its carbon savings. Moreover, as shown, the carbon savings are strictly a function of the carbon intensity variability, where locations with highly variable carbon intensity (see  Figure 5) have higher savings than locations such as Virginia, US, where in 2022, 85% of its electricity consumption came from non-variable sources (Natural Gas 54% and Nuclear 31%)  (U.S. Energy Information Administration, 2025), resulting in limited saving opportunities. Lastly, the figure also shows that as the variability increases, the difference between CarbonFlex and CarbonScaler also increases, highlighting the impact of CarbonFlex in reducing carbon.

6.6.Effect of Workload Distribution Shifts

Another key assumption in CarbonFlex is that historical and real-time workload traces share some resemblance. Although this is mostly true, CarbonFlex’s continuous learning strategy will quickly pick up on such changes. Figure 13 illustrates the case where we alter distribution shifts by increasing the inter-arrival rate and job length between -20% and 20%, leading to changes in cluster utilization, where zero means the original trace. As shown, the decreases in arrival rates and job lengths allow CarbonFlex to reduce carbon emissions further as the average utilization of the cluster becomes lower, where carbon savings increase by 10.1%. In contrast, when the arrival rate is higher, the potential carbon savings decrease, reaching 26%.

6.7.Carbon-aware Provisioning

In addition to carbon-aware scheduling approaches, researchers have proposed carbon-aware provisioning to reduce the total emissions of data centers, which include both interactive and batch applications  (Radovanović et al., 2023) and demonstrate the impact of load shifting on the grid (Lin and Chien, 2023). Despite the differences in scope, we illustrate that CarbonFlex is interoperable with other provisioning approaches, which highlights the benefit of CarbonFlex’s separation of provisioning and scheduling.  Figure 14 presents the performance of carbon-aware provisioning approaches. Our baselines include a carbon-aware provising approach, which computes the provisioning based on the VCC approach (Radovanović et al., 2023) and schedules workloads in an FCFS manner, and VCC (Scaling) that creates a VCC curve while allowing elastic scaling. We include the results from CarbonFlex (where we set the delay for 24 hours for all jobs to ensure a fair comparison) for reference. As shown, our proposed elastic scaling approaches enhance the performance of VCC by lowering the carbon emissions by 1.6%, while decreasing the average waiting time by 36%.

6.8.System Overheads

Lastly, we used our prototype to quantify the cost and system overheads of CarbonFlex. We found that running the offline oracle for a week-long trace typically took between 2 and 10 minutes, depending on the trace size and the number of jobs. Matching the current system state with the closest states from the oracle required between 1 and 2 ms. Our one-time profiling of workloads used 30 seconds for each of the maximum allowed 16 servers for CPU workloads and 1 minute for the maximum allowed 8 GPU workloads, resulting in 8 minutes per workload and totaling approximately 2 hours. The overhead of Checkpoint/Restore utilized in scaling depends on the application’s memory footprint (Sharma et al., 2016). The application with the highest memory usage, ViT-B/32 (see Table 3), took 2 seconds and 0.3 seconds for checkpoint and restore, respectively. Lastly, provisioning EC2 instances incurs time overheads, taking 3 minutes for our C8 CPU instances and 5 minutes for our G6 GPU instances.

7.Related Work

We discuss related work in carbon-aware and elastic workload scheduling.

Carbon-aware Scheduling.  Prior work has implemented carbon-aware schedulers for batch workloads, where researchers proposed workload-shifting methods to optimize the carbon emissions of an individual job  (Hanafy et al., 2023b; Souza et al., 2023; Sukprasert et al., 2024; Dodge et al., 2022; Wiesner et al., 2021; Lechowicz et al., 2023), a data center  (Radovanović et al., 2023; Zhang and Chien, 2021; Perotin et al., 2023; Lin and Chien, 2023), or cloud clusters  (Hanafy et al., 2024). In contrast to these approaches, which either focus on carbon-aware scheduling or capacity provisioning, CarbonFlex, combines these approaches to optimize carbon emissions further.

Elastic Workload Scheduling.Previous work utilized elastic scheduling (Tarraf et al., 2024; Gupta et al., 2014; Prabhakaran et al., 2015), to optimize the makespan and job completion (Peng et al., 2018; D’Amico et al., 2019; Jayaram Subramanya et al., 2023; Xiao et al., 2020; Qiao et al., 2021), energy consumption (D’Amico et al., 2019; You et al., 2023; Xu et al., 2025) of compute clusters. However, CarbonFlex prioritizes carbon-aware scheduling, which often conflicts with the traditional makespan, as highlighted in earlier work (Hanafy et al., 2024, 2023a). Moreover, CarbonFlex focuses on cloud clusters, where both the workload and cluster can be scaled dynamically. Furthermore, in contrast to conventional clusters that are often heterogeneous, cloud users typically opt for homogeneous clusters by deliberately selecting the most efficient and cost-effective resources. Lastly, we note that, although our continuous learning-based approach can work for heterogeneous clusters, by expanding the decision criteria to include the number of resources per type, evaluating this approach is left for future work.

8.Conclusion

This paper presented CarbonFlex, a carbon-aware resource manager for cloud clusters. CarbonFlex employs a continuous learning approach to guide near-optimal scheduling and provisioning decisions while supporting elastic CPU and GPU workloads. Our evaluation showed that CarbonFlex reduces carbon emissions by 57% and performs within 2.1% of an oracle scheduler. In the future, we plan to extend our carbon-aware provisioning and scheduling approaches with batch and inte