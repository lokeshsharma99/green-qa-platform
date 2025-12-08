Carbon-Aware Optimal Power Flow with Data-Driven Carbon Emission Tracing
Zhentong Shao
Nanpeng Yu
Abstract
Quantifying locational carbon emissions in power grids is crucial for implementing effective carbon reduction strategies for customers relying on electricity. This paper presents a carbon-aware optimal power flow (OPF) framework that incorporates data-driven carbon tracing, enabling rapid estimation of nodal carbon emissions from electric loads. By developing generator-to-load carbon emission distribution factors through data-driven technique, the analytical formulas for both average and marginal carbon emissions can be derived and integrated seamlessly into DC OPF models as linear constraints. The proposed carbon-aware OPF model enables market operators to optimize energy dispatch while reducing greenhouse gas emissions. Simulations on IEEE test systems confirm the accuracy and computational efficiency of the proposed approach, highlighting its applicability for real-time carbon-aware system operations.

IIntroduction
The decarbonization of power systems is a top priority to combat climate change. In 2023, the U.S. electric power sector emitted 1,427 million metric tons of 
CO
2
, accounting for over 29.7% of the nation’s total energy-related emissions [1]. Effective grid decarbonization relies on accurate measurement of carbon emissions associated with both electricity production and consumption, commonly referred to as carbon tracing. This process quantifies emissions, providing a useful signal for decisions related to decarbonization strategies. Since the demand for electricity drives fossil fuel consumption from power generation stations, it is essential to calculate not only carbon emission from generation but also end-user carbon footprints by attributing generation-based emissions to consumers in proportion to their electricity usage.

Existing literature explores various methods for quantifying carbon emissions within power grids, emphasizing the need for tools that measure emissions at the nodal level to guide effective carbon reduction practices. Traditional methods for calculating system-level carbon emissions across all generators without considering geographical or load-specific variations. Virtual carbon flow models [2] have emerged to track carbon transfers between regions, while statistical [3, 4] and machine learning [5] forecasting models utilize factors like weather and load to predict network or region-wide emissions. However, they fail to provide location-specific insights.

Recent research has focused on developing tools for nodal emission calculations to support real-time operation by grid operators [6]. Two key metrics are nodal average carbon emissions, which reflect the overall carbon intensity of power consumption, and nodal marginal carbon emissions, which measure increase in overall carbon emission due to incremental load changes. Specifically, reference [7] establishes an incremental optimal power flow (OPF) model to evaluate the marginal carbon emissions for a given power flow scenario. Reference [8] quantifies the changes in system-wide carbon emissions resulting from the activation of local demand response resource. Reference [9] implements a load control strategy that uses a lookup table to evaluate nodal marginal carbon emissions. Reference [10] proposes a load-shifting algorithm with an incremental OPF model to capture the marginal carbon emissions of data centers. These methods typically require solving an incremental OPF near a specified operating point to capture locational carbon emissions, yet solving an integrated system optimization problem with carbon awareness remains challenging.

Analytical methods using carbon emission flow have also been explored. Reference [11] established carbon emission flow equations and employed iterative algorithms to trace carbon emissions back to specific generators, though the solution lacks convergence guarantees, limiting its practical application. Reference [12] calculates the nodal power flow mix through analytical derivations and employs matrix inversion to map carbon emissions from generators to demands. However, the invertibility of the matrix cannot be guaranteed in the presence of loop flows and bilateral contracts. More recent innovations address these limitations by directly linking generator emissions to individual nodal loads using computationally efficient depth-first search algorithms [13], which calculate both average and marginal carbon emissions. However, this approach serves primarily as an evaluation tool for given system states and is challenging to integrate into an OPF problem. To address this, [14] introduces a carbon-aware OPF model with nonlinear carbon flow equations, offering a promising carbon accounting tool for economic dispatch, though its non-convex formulation significantly increases computational costs.

In response to the limitations of existing studies, this paper presents a data-driven method to determine both the average nodal carbon emission (ANCE) rate and the locational marginal carbon emission (LMCE) rate. Given that carbon flow is physically coupled with power flow, we trained an affine mapping to trace power flows from individual generators to nodal loads, which are called generator-to-load distribution factors. Using these factors, the analytical forms of ANCE and LMCE are derived. The resulting carbon emission quantification tool is linear, making it straightforward to integrate into optimal power flow models. Accordingly, this paper proposes a carbon-aware OPF model based on the data-driven carbon tracing approach. The proposed method is verified using several IEEE test systems. The test results demonstrated the effectiveness of the proposed method.

IIMethodology
II-ATracing Nodal Carbon Emission
Consider a power network with 
N
 nodes and 
L
 transmission lines. Let 
𝒩
 denote the set of all nodes, 
ℒ
 the set of lines, and 
𝒢
 the set of generators. At each time period, 
d
n
 represents the load demand at node 
n
. For a node without load, 
d
n
=
0
. The system operator solves the OPF problem to determine the power dispatch 
p
g
 for 
G
 generators. Each generator 
g
 has a carbon emission rate 
γ
g
, expressed in units of lbs CO2/MWh. The goal of this paper is to model carbon emissions in the OPF framework and calculate the nodal carbon emission 
e
n
 attributed to the loads at each node 
n
.

The carbon emissions in a power system are created by the generators and subsequently allocated to the electric loads. The power consumed is not inherently tied to any specific generator. To facilitate carbon tracing, we assume the power flow is divisible and it follows a consistent allocation rule. This is formally stated in Assumption 1, which enables a proportional division of power flow.

Assumption 1.
For any node 
n
, the proportion of power inflow attributable to generator 
g
 is equal to the proportion of the power outflow attributable to generator 
g
.

Assumption 1 implies that generators’ contributions are proportionally allocated across the network, ensuring consistency in carbon tracing of power flows. Under Assumption 1, the contribution of each generator 
g
 to the nodal load 
n
 is denoted as 
d
n
,
g
, and the nodal carbon emission 
e
n
 is computed using (1), where 
F
g
→
n
​
(
⋅
)
 denotes the mapping used to calculate the contribution of generator 
g
 to load 
n
.

d
n
,
g
=
F
g
→
n
​
(
p
g
)
(1a)
e
n
=
∑
g
=
1
G
γ
g
​
d
n
,
g
(1b)
By introducing the nodal carbon emission, we can incorporate carbon-aware constraints into the OPF problem, as shown in (2), where 
e
n
,
t
 denotes the carbon emission of node 
n
 on time period 
t
. Also, the nodal average carbon emission rate 
δ
n
 can be computed using (3).

∑
t
=
1
T
e
n
,
t
≤
E
n
max
(2)
δ
n
=
e
n
/
d
n
(3)
II-BData-Driven Estimation of Nodal Carbon Emission
It is shown in (1) that the key to calculating the nodal carbon emission is determining the specific form of the generator-to-load function 
F
g
→
n
​
(
⋅
)
. In fact, existing literature has investigated formulations for 
F
g
→
n
​
(
⋅
)
. For instance, reference [14] utilizes a non-convex mapping known as carbon flow equations, while [13] proposes a tree search algorithm based on a given flow result to determine the generator-to-load allocation. These studies indicate that there exist an approximately linear mapping between 
p
g
 and 
d
n
. In this paper, we assume this mapping to be affine and employ a data-driven approach to determine it. Compared to existing methods, the proposed carbon tracing formula can be seamlessly integrated into the OPF framework as linear constraints, maintaining the computational efficiency of the OPF model and enabling a carbon-aware OPF solution.

We define the generator-to-load contribution mapping 
F
g
→
d
​
(
⋅
)
 with an affine formulation, given by 
d
n
,
g
=
α
n
,
g
​
p
g
, where 
α
n
,
g
∈
[
0
,
1
]
 represents the generator-to-load contribution factor of generator 
g
 to the nodal load 
n
. The total carbon emission of node 
n
 can then be estimated as:

e
n
=
∑
g
=
1
G
α
n
,
g
​
γ
g
​
p
g
(4)
Here, the term 
α
n
,
g
​
γ
g
 is referred to as the carbon emission distribution factor. The carbon emission rate 
γ
g
 is given for each generator 
g
. Our objective is to determine 
α
n
,
g
 through data-driven techniques. To ensure the physical relevance of the data-driven results, we adopt Assumption 2. Assumption 2 essentially represents a lossless scenario, where all generated power is ultimately allocated to the nodal loads.

Assumption 2.
Under a lossless DC power flow model, the generator-to-load distribution factors satisfy: 
∑
n
=
1
N
α
n
,
g
=
1
,
∀
g
∈
𝒢
.

A constrained regression problem is defined to determine 
α
n
,
g
. Given the power flow set 
𝒮
, (5) can be solved for each generator to obtain the generator-to-load distribution factors.

min
α
n
,
g
⁡
J
g
=
∑
s
=
1
S
(
d
n
(
s
)
−
α
n
,
g
​
p
g
(
s
)
)
2
(5a)
s.t. 
​
∑
n
=
1
N
α
n
,
g
=
1
(5b)
(5) is a convex non-linear programming problem, which can be efficiently tackled by the commercial solvers like Gurobi.

II-CLocational Marginal Carbon Emission
After obtaining the factors 
α
n
,
g
, we can express nodal demand in terms of generator output using (6). By combining (4) and (6), we can derive the locational marginal carbon emission rate for each node.

d
n
=
∑
g
=
1
G
α
n
,
g
​
p
g
.
(6)
Let 
μ
n
 denote the LMCE rate at node 
n
, which can be calculated using (7).

μ
n
=
∂
e
n
∂
d
n
.
(7)
The closed form solution for the LMCE rate is shown in (8). Details of the derivation for (8) are provided in Appendix -A.

μ
n
=
∂
e
n
∂
d
n
=
∑
g
=
1
G
α
n
,
g
2
​
γ
g
∑
g
=
1
G
α
n
,
g
2
.
(8)
The LMCE rate 
μ
n
 can be interpreted as the weighted carbon emission rate of generators 
γ
g
, with weighting factors 
α
n
,
g
2
. Since the generator-to-load distribution factor 
α
n
,
g
 is computed through a data-driven method, 
μ
n
 is referred to as the data-driven LMCE rate.

Remark 1.
The data-driven LMCE rate (8) acts as a tool to approximate the actual carbon emissions. The power flow scenario considered for the LMCE should be adequately represented by the power flow scenarios in the training dataset. In practical applications, (8) should be adjusted to (9), where 
𝒢
∗
 represents the set of generators in service within the evaluated power flow scenario.

μ
n
=
∂
e
n
∂
d
n
=
∑
g
∈
𝒢
∗
α
n
,
g
2
​
γ
g
∑
g
∈
𝒢
∗
α
n
,
g
2
(9)
II-DCarbon-Aware OPF with Carbon Distribution Factors
This subsection incorporates data-driven carbon emission distribution factors into the OPF problem, keeping it as an efficient linear programming (LP) problem with carbon-aware OPF solutions. The resulting carbon-aware OPF model is presented in (10).

min
p
g
,
e
n
⁡
f
power
​
(
p
g
,
∀
g
)
+
f
carbon
​
(
p
g
,
∀
g
)
(10a)
s.t.	
∑
g
∈
𝒢
p
g
−
∑
n
∈
𝒩
d
n
=
0
(10b)
p
l
=
Γ
l
,
n
​
(
∑
g
∈
𝒢
​
(
n
)
p
g
−
d
n
)
,
∀
l
∈
ℒ
(10c)
−
P
l
max
≤
p
l
≤
P
l
max
,
∀
l
∈
ℒ
(10d)
P
g
min
≤
p
g
≤
P
g
max
,
∀
g
∈
𝒢
(10e)
e
n
=
∑
g
∈
𝒢
α
n
,
g
​
γ
g
​
p
g
,
∀
n
∈
𝒩
(10f)
∑
n
∈
𝒩
e
n
≤
E
total
(10g)
The objective (10a) minimizes the overall cost, which includes the power-related cost 
f
power
 and the carbon emission-related cost 
f
carbon
. Depending on the specific application, 
f
power
 may represent generation costs, network losses and etc. The term 
f
carbon
 is is defined to capture the equivalent costs for carbon emissions associated with either the generation or demand side, such as carbon emission permit fees for generators. A sample cost function is provided in (11).

f
power
:=
∑
g
∈
𝒢
(
a
g
​
p
g
2
+
b
g
​
p
g
+
c
g
)
,
(11a)
f
carbon
:=
c
emp
​
∑
g
∈
𝒢
γ
g
​
p
g
,
(11b)
where (11a) denotes the total generation cost in quadratic form with parameters 
a
g
, 
b
g
, and 
c
g
, and (11b) denotes the carbon emission cost for generators with permit price 
c
emp
.

(10b) represents the system-wide power balance constraint under a lossless DC power flow model. (10c) calculates line power flows using the power transfer distribution factors 
Γ
l
,
n
, where 
𝒢
​
(
n
)
 denotes the set of generators located at node 
n
. Constraints (10d) limit the allowable range for line power flows, while constraints (10e) enforce the capacity limits for generators. (10f) calculates nodal carbon emissions based on data-driven carbon emission distribution factors, and (10g) regulates the allowable system-level carbon emission. (10g) provides a basic carbon constraint for illustration purposes. With (10f), various customized carbon constraints can be developed as those in reference [14].

The proposed carbon-aware OPF framework (10) has a computationally efficient LP structure, allowing direct extension to a multi-period dispatch model or integration into the unit commitment problem. This formulation provides a carbon-aware generalization of the DC-OPF model and can be efficiently solved through linear programming solvers such as CPLEX and Gurobi.

IIICase Study
The proposed carbon-aware OPF is evaluated on several IEEE test systems, including the 5-bus, 24-bus, 30-bus, and 118-bus system from MATPOWER 7.1 [15]. Numerical simulations are conducted based on the DC-OPF solver in MATPOWER. Load demands are adjusted according to a uniform distribution within the range [0.7, 1], and sample generation follows the method specified in [16]. Each test system is accompanied by 1,000 data samples, with 80% of the samples randomly selected as the training dataset and the remaining 20% as the testing dataset. Generators are assumed to be powered by fossil fuels, with carbon emission rates 
γ
g
 ranging from 113 to 2,388 lbs CO2/MWh. The specific settings for generator carbon emissions can be found in [13].

III-AData-driven Generator-to-load Distribution Factors
The generator-to-load distribution factors, 
α
n
,
g
, are fundamental for calculating nodal carbon emissions. In this subsection, we estimate the data-driven generator-to-load distribution factors 
α
n
,
g
 and present the load approximation errors using the estimated 
α
n
,
g
 and generator outputs in Table I. The accuracy metrics include the mean absolute error (MAE) and maximum absolute error (Max-AE), both measured in megawatts (MW). As shown in Table I, the trained model demonstrates minimal load approximation errors, with an average MAE of 
6.64
×
10
−
7
 MW and a Max-AE of 
2.81
×
10
−
5
 MW. These results indicate that 
α
n
,
g
 effectively distributes generator output to meet load demands, which is crucial for accurate carbon tracing. The data also reveals a correlation between accuracy and system size: the highest Max-AE occurs in the 118-bus system, while the 5-bus system shows near-perfect result, with negligible error. This suggests that system complexity may impact the distribution factor’s precision, with smaller systems exhibiting more accurate results.

TABLE I:Error of Load Demands Approximated by Data-driven Generator-to-load Factors
Systems
 	
MAE (MW)
Max-AE (MW)
5-bus
 	
3.81
×
10
−
9
1.12
×
10
−
8
24-bus
 	
2.37
×
10
−
6
2.58
×
10
−
5
30-bus
 	
1.30
×
10
−
8
1.23
×
10
−
6
118-bus
 	
2.68
×
10
−
7
8.53
×
10
−
5
Tol. Avg.
 	
6.64
×
10
−
7
2.81
×
10
−
5
The trained generator-to-load distribution factors for the 5-bus system are examined in detail. This system includes three generators located at buses 1, 3, and 5. As shown in Table II, generators G-1, G-2, and G-3 supply the loads at buses 2, 3, and 4, using distribution factors that reflect the load-sharing dynamics among generators. Notably, bus-4 receives the highest contributions from all generators, with distribution factors around 0.4, indicating a balanced load-sharing across the generators. In contrast, buses 2 and 3 exhibit greater variability, with slightly lower impacts from G-2 at Bus-2 and G-1 at Bus-3, respectively. Buses 1 and 5 do not serve load and thus has zero generator-to-load factors. This data-driven analysis highlights the spatio distribution of generator-to-load distribution factors across the network.

TABLE II:Data-driven Generator-to-load Factors of the 5-bus System
Indices
 	
G-1
G-2
G-3
Bus-1
 	
0
0
0
Bus-2
 	
0.3154
0.2931
0.3021
Bus-3
 	
0.2775
0.3099
0.2979
Bus-4
 	
0.4071
0.3970
0.4000
Bus-5
 	
0
0
0
III-BData-driven Locational Marginal Carbon Emission Rate
In this subsection, we use (8) to calculate the LMCE rate, 
μ
n
 for a 30-bus system with 6 generators and settings of 
γ
g
 detailed in Table III. The resulting data-driven LMCE rates, 
μ
n
, are shown in Fig. 1, alongside benchmark values derived from sensitivity analysis [13, 6] for each node. The node indices in Fig. 1 are sorted by 
μ
n
 values. From the test results in Fig. 1, it is evident that the calculated LMCE rates 
μ
n
 for the 30-bus system closely align with the benchmark values, demonstrating high accuracy. This data-driven approach effectively captures emission variations across the network, facilitating effective customer level carbon reduction in the power system.

TABLE III:Carbon Emission Rate of Generators in the 30-Bus System
Gen. Index	G-1	G-2	G-3	G-4	G-5	G-6
γ
g
 (lbs CO2/MWh)	565	1890	1145	1446	644	961
Refer to caption
Figure 1:The locational marginal carbon emission of the 30-bus system (with the indices on the x-axis sorted by the values of 
μ
n
).
TABLE IV:Performance of the Carbon-Aware OPF on 30-Bus System
Metric	Baseline-OPF	Carbon-OPF
Power Cost ($)	
3.58
×
10
3
3.70
×
10
3
Carbon Emission Cost ($)	
1.82
×
10
3
1.71
×
10
3
Total Cost ($)	
5.40
×
10
3
5.41
×
10
3
Total Emission (CO2)	101.5 ton	95 ton
Solution Time (s)	0.082	0.089
III-CEvaluation of Carbon-Aware OPF
In this subsection, the performance of the proposed carbon-aware OPF problem (10) with objective function (11) is evaluated. We define the OPF problem (10)-(11) without carbon constraints (10f)-(10g) as the baseline-OPF problem, while the version incorporating carbon constraints represents the proposed carbon-aware OPF. The parameter 
c
emp
 is set as 0.009$/lbs CO2. The carbon-aware OPF includes a carbon constraints with 
E
total
=
95
 ton CO2.

The results of the two OPF problems on the 30-bus system are presented in Table IV. As shown in Table IV, by introducing the carbon emission constraint, the carbon-aware OPF successfully identifies a generator dispatch scheme with reduced emissions, lowering emitted CO2 from 101.5 tons to 95 tons. This reduction led to a slightly increased generation cost, from 
$
​
3.58
×
10
3
 to 
$
​
3.70
×
10
3
. The carbon-aware approach also results in a decrease in carbon emission cost, from 
$
​
1.82
×
10
3
 to 
$
​
1.71
×
10
3
, partially offsetting the higher power cost. Consequently, the total operational cost remains nearly unchanged, with only 0.19% or $10 increase in total cost. The OPF solution time experiences a slight increase from 0.082 to 0.089 seconds, indicating that the proposed method maintains computational efficiency. The carbon-aware OPF achieves a significant reduction in emissions with minimal cost impact, demonstrating the effectiveness of emission constraints in aligning power dispatch with environmental objectives while maintaining cost stability.

IVConclusion
This paper developed a data-driven approach to formulate and solve carbon-aware OPF problem, providing valuable locational marginal carbon emission rate signals to end-use customers to effectively reduce their carbon footprint. By estimating generator-to-load distribution factors, the proposed method enables the derivation of closed-form solution for both average and marginal nodal carbon emission rates. The integration of generator-to-load distribution factors into the OPF framework yields carbon-aware energy resource dispatch decisions, balancing power system operation cost and emissions reduction objectives. Simulation results on IEEE test systems demonstrate that the proposed method achieves significant emissions reductions with minimal impact on total operational costs, while maintaining computational efficiency. The proposed method serves as a valuable tool for supporting real-time carbon accounting and facilitating carbon-oriented demand management. Future work will focus on extending the model to incorporate multi-period and stochastic OPF scenarios, further enhancing its applicability to dynamically changing and uncertain grid conditions.

-ADerivation of Locational Marginal Carbon Emission
Applying the chain rule to (4), we have:

∂
e
n
∂
d
n
=
∑
g
=
1
G
(
∂
e
n
∂
p
g
⋅
∂
p
g
∂
d
n
)
(12)
Since 
d
n
 is a function of 
p
g
, we need to find 
∂
p
g
∂
d
n
. However, directly computing 
∂
p
g
∂
d
n
 is difficult because 
d
n
 depends on all 
p
g
. Instead, we can consider the relationship between 
e
n
 and 
d
n
 via their gradients with respect to 
p
g
. Let us define the gradient vectors of 
e
n
 and 
d
n
 with respect to 
p
g
, which are shown in (13) and (14), respectively.

∇
p
e
n
=
(
∂
e
n
∂
p
1
,
…
,
∂
e
n
∂
p
G
)
=
(
α
n
,
1
​
γ
1
,
α
n
,
2
​
γ
2
,
…
,
α
n
,
G
​
γ
G
)
(13)
∇
p
d
n
=
(
∂
d
n
∂
p
1
,
…
,
∂
d
n
∂
p
G
)
=
(
α
n
,
1
,
α
n
,
2
,
…
,
α
n
,
G
)
(14)
Now we can derive 
∂
p
g
∂
d
n
 by using the gradient vectors as:

∂
e
n
∂
d
n
=
∇
p
e
n
⋅
∇
p
d
n
‖
∇
p
d
n
‖
2
,
(15)
where 
∇
p
e
n
⋅
∇
p
d
n
 is the dot product of the two gradient vectors and 
‖
∇
p
d
n
‖
2
 is the squared magnitude (norm) of the gradient 
∇
p
d
n
.

The numerator and denominator of (15) are computed as:

∇
p
e
n
⋅
∇
p
d
n
=
∑
g
=
1
G
(
α
n
,
g
​
γ
g
)
​
(
α
n
,
g
)
=
∑
g
=
1
G
α
n
,
g
2
​
γ
g
(16a)
‖
∇
p
d
n
‖
2
=
∑
g
=
1
G
(
α
n
,
g
)
2
(16b)
Substituting them back into (15), we can finally obtain the locational marginal carbon emission rate:

∂
e
n
∂
d
n
=
∑
g
=
1
G
α
n
,
g
2
​
γ
g
∑
g
=
1
G
α
n
,
g
2
(17)
-BNomenclature
p
g
 	
Power output of generator 
g
.
γ
g
 	
Carbon emission rate of generator 
g
.
e
n
 	
Carbon emission amount of node 
n
.
e
n
,
t
 	
Carbon emission amount of node 
n
 at time period 
t
.
d
n
 	
Power demand of node 
n
.
d
n
,
g
 	
Power demand of node 
n
 that is served by generator 
g
.
δ
n
 	
Average carbon emission rate of node 
n
.
α
n
,
g
 	
Generator-to-load distribution factor for generator 
g
 to the load located on node 
n
.
p
l
 	
Power flow on transmission line 
l
.
 
Acknowledgment
We gratefully acknowledge funding support from the California Energy Commission (Award EPC-20-025-FP12037) and the National Science Foundation (Award 2324940).