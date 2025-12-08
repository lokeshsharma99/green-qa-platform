MAIZX: A Carbon-Aware Framework for Optimizing Cloud Computing Emissions
Federico Ruilova
fedra@kth.se
0000-0002-3577-2065
KTH Royal Institute of TechnologyStockholmSweden;
Technische Universität BerlinBerlinGermany
Ernst Gunnar Gran
ernst.g.gran@ntnu.no
0000-0002-0349-3643
Norwegian University of Science and Technology (NTNU)GjøvikNorway
Sven-Arne Reinemo
svenar@simula.no
0000-0002-6167-4784
Simula Metropolitan Centre for Digital EngineeringOsloNorway
(2024)
Abstract.
Cloud computing drives innovation but also poses significant environmental challenges due to its high energy consumption and carbon emissions. Data centers account for 2-4% of global energy usage, and the ICT sector’s share of electricity consumption is projected to reach 40% by 2040.As the goal of achieving net-zero emissions by 2050 becomes increasingly urgent, there is a growing need for more efficient and transparent solutions, particularly for private cloud infrastructures, which are utilized by 87% of organizations, despite the dominance of public-cloud systems.

This study evaluates the MAIZX framework, designed to optimize cloud operations and reduce carbon footprint by dynamically ranking resources, including data centers, edge computing nodes, and multi-cloud environments, based on real-time and forecasted carbon intensity, Power Usage Effectiveness (PUE), and energy consumption. Leveraging a flexible ranking algorithm, MAIZX achieved an 85.68% reduction in CO2 emissions compared to baseline hypervisor operations. Tested across geographically distributed data centers, the framework demonstrates scalability and effectiveness, directly interfacing with hypervisors to optimize workloads in private, hybrid, and multi-cloud environments. MAIZX integrates real-time data on carbon intensity, power consumption, and carbon footprint, as well as forecasted values, into cloud management, providing a robust tool for enhancing climate performance potential while maintaining operational efficiency.

carbon reduction in cloud, carbon-aware computing, energy-aware clouds, private cloud optimization, sustainable cloud computing,carbon performance potential
†conference: 1st International Workshop on Low Carbon Computing; December 3, 2024; Glasgow/Online
†isbn:
†copyright: rightsretained
†booktitle: [LOCO ’24]1st International Workshop on Low Carbon ComputingDecember 3, 2024Glasgow/Online
†journalyear: 2024
†ccs: Information systems Data mining
1.Introduction
Cloud computing drives innovation across sectors but raises concerns about its environmental impact, particularly due to high energy consumption and carbon emissions.Currently Data centers account for 2-4% of the global energy usage, with the broader ICT sector consuming 6% (Ross and Christie, 2023),(Independent, 2016),(Ahvar et al., 2022). This is projected to rise to nearly 40% of total global electricity consumption by 2040 (Agency, 2021), underscoring the urgent need for sustainable solutions, carbon-aware computing and energy-aware frameworks(Laplante and Voas, 2023), (Woodruff et al., 2023),(Radovanović et al., 2023), (Maji et al., 2023),(Lannelongue and Inouye, 2023), (Hanafy et al., 2023a). Achieving net-zero emissions by 2050 is critical for limiting global warming, and while cloud providers focus on carbon neutrality through grid carbon intensity awareness and renewable energy integration, more transparent and effective methods are needed, especially for private cloud setups, used by 87% of organizations(Flexera, 2024),(Cisco, 2022),(Arora et al., 2023).

This research explores the MAIZX framework to revisit its potential and evaluate its climate performance(Ruilova Alfaro, 2024); the framework uses a ranking algorithm that allocates resources based on scores of computing nodes. The framework’s scalability and effectiveness were empirically tested by implementations across geographically distributed data centers and validated via simulations. By integrating these metrics into cloud management, MAIZX offers a robust tool for enhancing climate performance and assessing environmental impact in private, hybrid and multi-cloud approaches.

2.Background and Related Work
Cloud computing enables scalable and flexible computing resource allocation via Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS) (Mell and Grance, 2011). These services operate over different deployment models—public, private, hybrid, and multi-cloud—each offering varying levels of control, scalability, and resource management (Stanoevska-Slabeva and Wozniak, 2010).

Recent industry trends indicate that 72% of organizations prefer hybrid cloud environments, while 87% employ a multi-cloud approach, balancing performance, cost, and regulatory compliance (Flexera, 2024; Cisco, 2022). However, rising energy demands associated with cloud infrastructures, particularly those running artificial intelligence (AI) workloads, have amplified concerns about sustainability (Wadhwani, 2025; Bray, 2025). AI-driven data centers could consume up to 8% of global electricity by 2030, with private cloud deployments accounting for a significant share due to their role in enterprise data governance (Wadhwani, 2025).

As a result, carbon-aware computing has emerged as a crucial paradigm, integrating energy efficiency with dynamic workload allocation (Arora et al., 2023). Public cloud providers, such as AWS, Google Cloud, and Microsoft Azure, have introduced carbon tracking services, yet private and hybrid clouds lack similar transparency and adaptation mechanisms (Arora et al., 2023; Maji et al., 2023). Addressing this gap, agent-oriented frameworks offer a promising direction, enabling autonomous, AI-driven energy management (Ruilova Alfaro, 2024).

To mitigate cloud computing’s environmental impact, carbon-aware computing seeks to align workload scheduling with energy grid conditions, optimizing operations based on real-time carbon intensity data (Wiesner et al., 2022; Radovanović et al., 2023). Strategies include temporal shifting of workloads to periods of lower emissions (Wiesner et al., 2024; James and Schien, 2019), geographic scheduling by allocating workloads to data centers in regions with cleaner energy sources (Eilam et al., 2023; Radovanović et al., 2023), and intelligent scaling mechanisms that dynamically adjust compute resources (Kim et al., 2023; Subramanian, 2023).

Building upon prior research, the MAIZX framework introduces an agent-based ranking mechanism designed for private, hybrid, and multi-cloud infrastructures (Ruilova Alfaro, 2024). Unlike conventional carbon-aware strategies, MAIZX operates across multiple levels of abstraction, integrating agent-driven resource allocation, multi-cloud adaptability, and real-time energy forecasting in coordination with the hypervisor of the cloud where it runs. The ranking MAIZX ranking algorithm dynamically scores computing nodes based on carbon footprint, CPU efficiency, and workload compatibility, while the agent-oriented approach enables autonomous decision-making in cloud scheduling. MAIZX also integrates with hypervisor-based schedulers, leveraging the hypervisor’s capabilities to optimize workload distribution and also interconnect with other hybrid approaches such as multicloud or hybryd (public and private)·

Preliminary studies indicate that MAIZX can reduce emissions by up to 85.68%, outperforming baseline cloud scheduling approaches in carbon-aware workload distribution (Ruilova Alfaro, 2024). This aligns with broader industry trends, where AI-based cloud optimization is increasingly necessary. Training and inference of large-scale AI models, such as GPT-4, require substantial computing power, intensifying demand for sustainable AI operations (Wadhwani, 2025).

In order to have an idea of the impact, the concept of carbon performance potential (CPP) provides a framework for evaluating the capability of organizations and technologies to manage carbon emissions effectively while optimizing economic outputs. Historically evolving from simplistic assessments to sophisticated multi-indicator metrics, CPP has become essential in guiding organizations toward a low-carbon economy (MP.org, 2024; Panwar et al., 2022). Recent research highlights a positive correlation between digital transformation and improved carbon management, as organizations leverage digital technologies for greater resource efficiency and sustainable innovation (Eilam et al., 2023; Wadhwani, 2025). Despite these advancements, substantial barriers remain, including technological limitations, economic constraints, regulatory uncertainty, and social resistance, underscoring the need for standardized metrics and robust policy frameworks to foster sustainable innovation and carbon reduction practices (Wadhwani, 2025).

This research builds upon previous work in carbon-aware cloud computing by addressing key limitations in workload scheduling for private and hybrid cloud environments. The MAIZX framework leverages an agent-oriented, AI-driven approach to dynamically optimize workload distribution based on real-time carbon intensity, enhancing both sustainability and operational efficiency. Unlike existing models such as GreenScale, FedZero, and CarbonScaler—which primarily focus on different layers of abstraction (Kim et al., 2023; Wiesner et al., 2024; Hanafy et al., 2023b)—MAIZX extends these principles to private clouds, hybrid architectures, and multi-cloud federations. By integrating seamlessly with hypervisors, MAIZX’s agentic components can coordinate across diverse infrastructures, enabling adaptive workload placement and proactive energy-aware scheduling across multiple cloud environments.

3.MAIZX Ranking Algorithm
The MAIZX framework uses a hybrid architecture that centralizes control while distributed agents collect power consumption and carbon intensity data, both at each distributed node and at the core (Ruilova Alfaro, 2024).

Refer to caption
\Description
Diagram of the MAIZX Framework Architecture.

Figure 1.MAIZX Framework Architecture
The ranking algorithm dynamically allocates workloads to nodes with the lowest carbon intensity, prioritizing environmental impact without compromising performance. Centralized components coordinate with the hypervisor using carbon efficiency and power data as it could be observed in Figure 1.

3.1.Key Functionalities of Carbon-Aware allocation
Agents gather real-time energy and carbon intensity data, supporting carbon footprint calculations and forecasting.

The algorithm evaluates nodes on carbon footprint and efficiency, optimizing workload distribution to reduce emissions. It integrates with hypervisors like OpenNebula (OpenNebula, 2023) for efficient scheduling.

The ranking system calculates a node’s efficiency by considering key environmental and operational parameters. The algorithm, 
M
⁢
A
⁢
I
⁢
Z
⁢
_
⁢
R
⁢
A
⁢
N
⁢
K
⁢
I
⁢
N
⁢
G
, is defined as:

(1)		
MAIZ_RANKING
=
w
1
⁢
CFP
+
w
2
⁢
FCFP
+
w
3
⁢
CP
⁢
_
⁢
RATIO
+
w
4
⁢
SCHEDULE
⁢
_
⁢
WEIGHT
.
In this equation, CFP refers to the node’s Carbon Footprint, while FCFP denotes the Forecasted Carbon Footprint based on historical data. The Computing Power Ratio (CP_RATIO) reflects the node’s energy efficiency, and the Scheduling Weight (SCHEDULE_WEIGHT) accounts for workload priorities and deadlines. Adjustable weights (
w
1
, 
w
2
, 
w
3
, 
w
4
) are assigned to each factor, enabling the framework to balance environmental impact, performance, and operational needs. This flexible approach ensures that MAIZX can maintain a balance between sustainability and efficiency across various cloud environments.

4.Methodology and Experimental Design
This study evaluates the MAIZX framework’s climate performance in private and multi-cloud oriented environments by optimizing operations based on data center locations, hardware usage, and regional energy profiles. The assessment builds on prior MAIZX research(Ruilova Alfaro, 2024), using 2022 carbon intensity data(electricitymaps.com, 2024) to simulate various scenarios: the Baseline Scenario evenly distributes loads without any consideration of carbon intensity or footprint data, serving as a comparison for carbon footprint analysis.; Scenario A directs all computing power to the node with the lowest carbon intensity; Scenario B concentrates tasks on a single node while powering off others to measure energy savings; and Scenario C dynamically shifts loads based on daily carbon intensity fluctuations, highlighting MAIZX’s adaptability for reducing emissions.

Data collection consists of power consumption measured every 20 seconds, while carbon intensity is recorded hourly across three regions: Spain, the Netherlands, and Germany. The carbon footprint for each node across the scenarios is calculated using a standard methodology (Eilam, 2021; GESI, 2024), applying the formula:

(2)		
C
⁢
F
=
E
⁢
C
×
P
⁢
U
⁢
E
×
C
⁢
I
where CF is the carbon footprint, EC is energy consumption, PUE is Power Usage Effectiveness, and CI is carbon intensity

In order to calculate the climate performance potential (CPP), the impact forecast tool was used, together with the corresponding EU taxonomy group for ICT. The calculation model uses functional unit or (FU) to calculate life cicle analys (impact forecast.com, 2024), (ecocostsvalue.com, 2024),(Vogtländer, 2010), (Valenzuela and Višević, 2021).

5.Results and Analysis
In Scenario C (active load-shifting over one year), the MAIZX framework reduces CO2 emissions by 85.68% compared to the baseline, optimizing workloads using real-time carbon intensity data, (Figure 2). Each unit, consisting of 60 servers in a 3-node private cloud, reduces emissions by 713.5 kg of CO2 annually. The main difference between Scenario B and Scenario C is the use of real-time carbon data: Scenario B evenly distributes workloads without considering carbon intensity, whereas Scenario C actively shifts workloads to the nodes with the lowest carbon intensity once, and scenario A as well but leaving the other nodes available. While both scenarios B and C achieve similar reductions, Scenario C is more sustainable long-term due to its dynamic response to fluctuations in carbon intensity, consistently maintaining lower emissions when variations occur.

Refer to caption
Figure 2.MAIZX Framework Architecture
\Description
Diagram showing the architecture of the MAIZX framework.

To evaluate the broader impact, if 1% of the EU Taxonomy target for data-driven climate change monitoring and ICT data processing is considered, it totals 19.754 Mt CO2eq (Commission, 2024),(impact forecast.com, 2024). Over a 10-year period, implementing the MAIZX framework with its 85% reduction capability would yield the following:

• Total reduction target: 19.754 Mt CO2eq (19,754,000,000 kg).
• Annual CO2 reduction per unit: 713.5 kg.
• Units required: 27,686,054.
This showcases the scalability of the MAIZX framework for reducing emissions in large-scale cloud operations, potentially reaching 19.754 Mt CO2eq in 10 years targeting shifted units. The results highlight MAIZX’s potential for substantial environmental and cost savings, particularly in private and multi-cloud environments with optimized power consumption and associated carbon footprint.

6.Conclusion
The framework demonstrates significant potential to reduce CO2 emissions, particularly in private or multi-cloud setups. Despite being tested in regions with non-renewable energy matrices, MAIZX achieved considerable emission reductions. Empirical data validated the framework’s carbon footprint calculations, affirming its methodology and accuracy. Conservative 10-year projections suggest that MAIZX could reduce emissions by 20 Mt CO2eq—equivalent to planting 90 million trees or removing 2.44 million cars from the road annually. Additionally, MAIZX provides significant eco-cost savings, including €3 billion in human health impacts, €4.65 billion in eco-toxicity, and €2.63 billion in carbon footprint-related costs(impact forecast.com, 2024). These findings underscore MAIZX’s potential to support sustainability goals (Nations, 2023) in the ICT sector by optimizing cloud infrastructure for sustainability.