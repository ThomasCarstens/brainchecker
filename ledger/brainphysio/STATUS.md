# Decision status — brainphysio

Generated 2026-09-26T19:11:20 from `human_m123` @ 2b64d66b. 151 decisions: the 32 you classified in the protocol form, a seeded sample per pillar, and every decision met since in a commit.

| pillar | Unexamined · critical | Unexamined · passable | Examined · critical | Examined · passable | Don't know | Mine | Human (evidence) |
|---|---|---|---|---|---|---|---|
| modelling | 15 | 5 | 2 |  |  |  | 13 |
| fitting | 32 | 4 | 1 | 1 |  | 2 |  |
| plotting | 14 | 19 | 3 | 2 |  |  |  |
| comparison | 10 | 23 | 2 |  | 3 |  |  |

## Modelling

- **D-00fd25b1** [Unexamined · critical] activate_resistance_evolution = 1, # flag to activate the resistance evolution law, set to 0 to deac  
  `Model_3_celia/Elements.jl:83` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): The vessel element defaults to having its resistance-evolution law switched on (`activate_resistance_evolution = 1`), so dR/dV is non-zero unless a caller explicitly passes 0. Any vessel built without naming this flag inherits collapse-dependent resistance rather than a constant resistance.
- **D-0f242013** [Unexamined · critical] for id in (:m3_basinA, :m3_basinB)  
  `Model_3_celia/bistability_full_plotting.jl:103` · selection · presumed AI-written, no examination on record
  Note (AI, not an examination): The plotting deck is driven by exactly two named seeds, :m3_basinA and :m3_basinB, each settled to steady state and then run through the tilt solve. This fixes which two basins are compared side by side in every downstream panel.
- **D-5844f058** [Unexamined · critical] s_smooth3 = 6*s_lin3^5 - 15*s_lin3^4 + 10*s_lin3^3  
  `Model_3_celia/Elements.jl:376` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): Line 376 shapes the third tilt stage with a quintic smoothstep of normalised time, so the tilt angle leaves and reaches its plateaus with zero velocity and acceleration. This choice, plus the shared `duration`, sets how fast the postural change is imposed on the model.
- **D-6568f793** [Unexamined · critical] # why. θ_dynamic_1 used to be 0.0 here against M3's 70°, which made M1's angle  
  `Model_1/Params.jl:193` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): Model_1's tilt angles are no longer literal numbers here; they are read from the shared Θ_STAGES/Θ_ONSETS schedule in ../Protocol.jl, so M1 and Model_3_celia use one protocol. The comment records that M1 previously had θ_dynamic_1 = 0.0 against M3's 70°, making M1's angle protocol a no-op.
- **D-91125062** [Unexamined · critical] A3 =  8.0, t03 = 0.34, mu3 = -1.10, sigma3 = 0.40,  
  `Model_3_celia/Elements.jl:586` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): A3 = 8.0 sets the amplitude of the third Gaussian bump (at t03 = 0.34) in the prescribed arterial pressure waveform of `Pressure_BC_Descriptor_2`. It is a hand-set default shaping the inlet forcing, not a fitted quantity.
- **D-91c89849** [Unexamined · critical] #   :Cv   brain.Veins.C_v  cerebral venous compliance   (scales 0, 0.8, 1, 1.2, 2)  
  `Model_3/main_sweep.jl:19` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The header comment at Model_3/main_sweep.jl:19 states that the cerebral venous compliance sweep multiplies brain.Veins.C_v by 0, 0.8, 1, 1.2, 2. It is a documented claim about the actual scan behind the figures, including a zero-compliance case.
- **D-a15421a4** [Unexamined · critical] #                  (default: free,0.5,0.1,0.05,0.01)  
  `Model_1/dtmax_sweep.jl:37` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment documents the default solver time-step cap ladder for the dtmax sweep script (free, 0.5, 0.1, 0.05, 0.01 s), which is the list of caps solved when _DTMAX_VALUES is unset. It is a claim about the script's defaults, not about physiology.
- **D-a48d77d5** [Unexamined · critical] connect(Hs_Rvvs.out, Rt.in, Hs_Revp.in),  
  `Model_3_celia/Model.jl:253` · equation · presumed AI-written, no examination on record
  Note (AI, not an examination): Line 253 splits the post-hydrostatic vertebral venous flow into two parallel return routes: through Rt and through the epidural branch (Hs_Revp -> Rivp/Revp -> Razy) that is loaded by abdominal pressure. It sets which resistances share the vertebral venous outflow and where posture-dependent hydrostatic columns enter the venous circuit.
- **D-b0ed4f05** [Unexamined · critical] connect(Hs_Pa.in, brain.in),  
  `Model_3_celia/Model.jl:239` · equation · presumed AI-written, no examination on record
  Note (AI, not an examination): This connection puts the hydrostatic element Hs_Pa in series between the arterial pressure source Pa and the brain inlet, so cerebral inflow pressure carries a posture-dependent gravitational offset. It fixes where the arterial hydrostatic column enters the topology.
- **D-b3152f66** [Unexamined · critical] comps[:Pa].P0_base => params[:P0_Pa_v], #89.311,        # mmHg — the cycle mean, not the diastolic f  
  `Model_1/Model.jl:1184` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): Sets the arterial source's baseline offset P0 from params[:P0_Pa_v], with a comment claiming this value is the cardiac cycle mean rather than the diastolic floor, and citing a commented-out 89.311 against a stated params value of 65.0.
- **D-f31daee0** [Unexamined · critical] isfile(joinpath(PREPARED_DIR, "events.jl")) || error(  
  `Model_1/Protocol_patient.jl:49` · rule · presumed AI-written, no examination on record
  Note (AI, not an examination): Protocol_patient.jl aborts at load time if the prepared jugular recordings have no events.jl, and again if the selected patient (default "081" via _PATIENT) is not a key in JC_EVENTS. Every run of this protocol therefore requires the Python preprocessing step to have run first.
- **K02** [Unexamined · critical] Model_3 (ex-M4): periodic steady-state tolerance set to 1.3e-5, because 1e-6 never converged  
  `Model_3/Model.jl:16` · value · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): `tol = 1.3e-5` is the relative cycle-to-cycle change at which a simulation is declared periodically steady. It decides how many cardiac cycles are run before the state is accepted as the steady solution.
- **K04** [Unexamined · critical] Autoregulation exponent clamped to ±40 in the compact M7 replica (RK4 overflow)  
  `fits/m1/Model_7/ude_cs.jl:332, fits/m1/Model_7/ude_cs.jl:333` · value · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): The Ursino-Lodi autoregulation sigmoid inputs are clamped to ±40 before exponentiation, so the sigmoid saturates instead of overflowing when flow deviates far from nominal. This bounds both the compliance-range switch dC and the sigmoid argument G*x/(dC/4).
- **K05** [Unexamined · critical] Compact M6 replica: measured ABP as its boundary, plus a 20 ms jugular-area relaxation that M5 does not have  
  `fits/m3/Model_6/ude_cv.jl:141, fits/m3/Model_6/ude_cv.jl:33` · value · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): Cbuf = 0.0 sets the buffer compartment's compliance to zero, disabling the spinal buffering branch (Racc and Rbuf remain defined but inert). The default model therefore runs with no compliant buffer storage.
- **K06** [Unexamined · critical] Re-deriving a fitted M1 must use Rss's component default (212.8), not the cascade value  
  `fits/m1/Model_7/ude_cs.jl:167, Model_1/run_jc_patients.jl:239` · value · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): Rss (sagittal-sinus outflow resistance) is pinned to 212.8 dyn·s/mL, the Brain_1 build-time default, instead of the cascade-consistent (Psinus − Pcv)/Q value. This keeps M7 on the same venous outflow resistance every fitted M1 run used, so the NN compliance is trained against the same baseline.
- **D-83a8a4c1** [Unexamined · passable] genuinely_distinct = dV > 1e-3 * Vbase || dQ > 1e-3 * Qbase  
  `Model_3_celia/bistability_confirm_plot.jl:117` · value · presumed AI-written, no examination on record
- **D-b7e406b7** [Unexamined · passable] if abs(r.V - k.V) < 0.05 * k.V && abs(r.q_avg - k.q_avg) < 0.05 * k.q_avg  
  `Model_3_celia/bistability_search_third.jl:89` · rule · presumed AI-written, no examination on record
- **D-bd8464f6** [Unexamined · passable] if !NOPLOT && !SIM_MODE && PROTOCOL !== :static  
  `Model_3/main.jl:553` · rule · presumed AI-written, no examination on record
- **D-c0fd859a** [Unexamined · passable] :dCneg => (key = :ΔC_neg_v, label = "dCneg", scales = [0.5,   0.75, 1.0],  derived = true),  
  `Model_3_celia/main_sweep.jl:189` · value · presumed AI-written, no examination on record
- **D-c68f4308** [Unexamined · passable] const _GREY_RAMP = ["#cfcfcf", "#a8a8a8", "#7d7d7d", "#565656", "#2e2e2e"]  
  `Model_3_celia/main_sweep.jl:291` · selection · presumed AI-written, no examination on record
- **K01** [Examined · critical] Every pressure ramp is a quintic smootherstep 6s⁵−15s⁴+10s³ ('a smooth function that Claude implemented')  
  `Model_1/Model.jl:825, Model_1/Model.jl:836, Model_3/Model.jl:705, Model_3_celia/Model.jl:691, Model_1/Elements.jl:809` · code · your form answer, 26 Sep: Examined · critical
  Note (AI, not an examination): The dynamic external pressure input is built as a staircase of three levels whose transitions are smoothed by a quintic smoothstep over a fixed duration `dur`. This makes P_ext continuous with zero first and second derivative at each step edge, instead of a jump.
- **K03** [Examined · critical] Pulsatile runs start from a converged limit cycle, not from the flat-Pa fixed point (M5, then M1)  
  `fits/m3/Model_5/main.jl:206, Model_1/limit_cycle.jl:1` · value · your form answer, 26 Sep: Examined · critical
  Note (AI, not an examination): Defaults to running ~1000 cardiac cycles of pulsatile pre-simulation so each m5 run starts on its limit cycle instead of a transient. Setting `_M5_LIMIT_CYCLE=0` skips that and yields transient runs.
- **D-1c228083** [Human (evidence)] connect(Hs_Rvvs.out, Rt.in, Hs_Revp.in),  
  `Model_1/Model.jl:527` · equation · pre-AI baseline (commit 61b2fe36, 2026-07-02)
  Note (AI, not an examination): These connect statements set the venous-return topology below the vertebral venous system: the hydrostatic block Hs_Rvvs feeds both the transverse path (Rt) and the epidural path (Hs_Revp), the internal/external vertebral plexus resistances rejoin at the azygos branch, and the loop closes back onto the systemic Rsys/Csys node. It fixes which collateral routes carry flow when jugular outflow is impeded, and where gravity columns sit.
- **D-33d55842** [Human (evidence)] D(C) ~ 1/τ * (-C + σ)  
  `Model_3/Elements.jl:27` · equation · pre-AI baseline (commit 61b2fe36, 2026-07-02)
  Note (AI, not an examination): Vessel compliance C is not algebraic: it relaxes with first-order time constant τ toward the sigmoidal target σ (Model_3/Elements.jl:27, σ set at line 31 from the flow-error x). This adds a slow state that delays and smooths every compliance change instead of applying it instantly.
- **D-4ae1c1a3** [Human (evidence)] mu2_Pa_v          => -1.5,  
  `Model_3_celia/Params.jl:78` · value · pre-AI baseline (commit a04af978, 2026-07-02)
  Note (AI, not an examination): Sets mu2_Pa_v, the centre of the second of three components in the Pa_v pressure drive shape used by Model_3_celia. Moving it shifts where that middle component sits along its argument, so it re-places part of the driving waveform.
- **D-4bee86c0** [Human (evidence)] :Rv_v => 811.3,  # Venous resistance  
  `src/brains/params.jl:8` · value · pre-AI baseline (commit 61b2fe36, 2026-07-02)
  Note (AI, not an examination): Sets the baseline cerebral venous resistance (Rv_v = 811.3 CGS) in the shared brain parameter dictionary. It is the default drainage resistance every brain model inherits before any per-model or per-patient override.
- **D-6a4e67d6** [Human (evidence)] connect(brain.ext, Rspine.in),  
  `Model_3/Model.jl:528` · equation · pre-AI baseline (commit 61b2fe36, 2026-07-02)
  Note (AI, not an examination): This connection routes the brain compartment's external/CSF port into the spinal resistance path, so flow leaving the cranium passes Rspine and the spinal hydrostatic column before reaching the IVP and spinal outflow nodes. It fixes the craniospinal topology: cranial and spinal storage are coupled in series through Rspine rather than directly.
- **D-808237c0** [Human (evidence)] connect(brain.ext, Rspine.in),  
  `Model_1_celia/Model.jl:206` · equation · imported untouched from Celia's notebooks
  Note (AI, not an examination): This connection routes the brain compartment's external port into the spinal resistance, so craniospinal outflow passes through Rspine, Hs_spine and Cspine to the abdominal pressure node. It sets the spinal pathway as a serial branch off the brain rather than a direct coupling.
- **D-a117922e** [Human (evidence)] s_smooth2 = 6*s_lin2^5 - 15*s_lin2^4 + 10*s_lin2^3  
  `Model_1_celia/Elements.jl:516` · value · imported untouched from Celia's notebooks
  Note (AI, not an examination): Line 516 shapes the second manoeuvre transition with a quintic smoothstep (6x^5-15x^4+10x^3) of the clamped ramp fraction, so the driven quantity starts and ends with zero slope. It sets how abruptly the second onset is applied over `duration`.
- **D-b67edbf1** [Human (evidence)] N_v = 1,  
  `Model_1_celia/Elements.jl:81` · value · imported untouched from Celia's notebooks
  Note (AI, not an examination): `N_v = 1` is the default exponent in the vessel resistance-evolution law (dR/dV family) for every element built by this constructor. At 1 the resistance varies with the lowest power of volume the law allows, so any element that does not override it gets the weakest nonlinear resistance response.
- **D-b85e3665** [Human (evidence)] ext.q ~ -D(V),  
  `Model_1_celia/Elements.jl:247` · equation · imported untouched from Celia's notebooks
  Note (AI, not an examination): This makes the external port flow the negative of the vessel volume rate, fixing the sign convention by which flow through `ext` inflates or deflates the compartment. Together with line 253 it forces D(V) = C*D(Ptm).
- **D-dcb5bc4f** [Human (evidence)] A_baseline_ijvs_v => 1.2,  
  `Model_3/Params.jl:170` · value · pre-AI baseline (commit 61b2fe36, 2026-07-02)
  Note (AI, not an examination): Sets the internal jugular vein baseline cross-sectional area (A_baseline_ijvs_v) to 1.2 in the Model_3 parameter deck. With A0_ijvs_v = 0.3 on line 169 it fixes where the IJV tube law sits between collapsed and distended, so it sets the vein's reference conductance and how much collapse a given external or abdominal pressure produces.
- **D-dd684c30** [Human (evidence)] Ptm ~ in.p - ext.p,  
  `Model_1/Elements.jl:238` · equation · pre-AI baseline (commit 61b2fe36, 2026-07-02)
  Note (AI, not an examination): Transmural pressure of this vessel element is defined as the internal pressure minus the external pressure at its `ext` port, so all downstream area/compliance behaviour is driven by that difference rather than by absolute internal pressure. Every external-pressure input (Pext, Pabdo, postural, jugular compression) enters the collapsible-vessel mechanics only through this line.
- **D-eae616d1** [Human (evidence)] @named sys_raw = System(assembly, t; systems = elements_sorted)  
  `Model_1/Model.jl:298` · equation · pre-AI baseline (commit 61b2fe36, 2026-07-02)
  Note (AI, not an examination): Line 298 builds an uncompiled copy of the same assembly so the pre-simplification unknown list can be read at line 299, alongside the compiled system at line 301. The topology is constructed twice, so the two builds must stay in step.
- **D-f10a4ca9** [Human (evidence)] l = 10.0,  
  `Model_1_celia/Elements.jl:592` · value · imported untouched from Celia's notebooks
  Note (AI, not an examination): Sets the default geometry of this element: length l = 10.0 and density ρ = 1.0 in the component's own units, used when a caller does not pass them. Together they scale the ρ·l-type inertial coefficient this element contributes.

## Fitting

- **D-0a2cc697** [Unexamined · critical] DECK_CHOICE = "jugular_compression_m1_analysis"  
  `Model_1/run_jc_patients.jl:101` · selection · presumed AI-written, no examination on record
  Note (AI, not an examination): Setting DECK_CHOICE before the registry include makes EXPERIMENT strip to "jugular_compression", so the run picks up that experiment's protocol and target recordings rather than anything keyed to the "_m1_analysis" suffix. This fixes which patient traces the model output is compared against and which deck the figures land in.
- **D-0e404071** [Unexamined · critical] const MEAN_WINDOW_S = 10  
  `fits/m3/Model_5/Data.jl:141` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): MEAN_WINDOW_S = 10 declares that the data were averaged over a 10 s window on the 1 Hz grid, matching what scripts/prep_jugular_data.py applied. It is the smoothing width the fit scores against and the width quoted in panel titles.
- **D-100478aa** [Unexamined · critical] length(NN_THETA) == 25 || error("fits/m3/Model_6/fit/nn_A.jl should hold 25 weights, has $(length(NN  
  `fits/m3/Model_6/Params.jl:430` · rule · presumed AI-written, no examination on record
  Note (AI, not an examination): Params.jl:430 hard-asserts that the learned compliance law's weight file holds exactly 25 numbers, aborting the model build otherwise. It pins the NN for Veins.C_v to one fixed shape.
- **D-113d41f0** [Unexamined · critical] const DATA_AMP_POST    = _median_in(DATA_BEAT, :icp_amp, JC_MID_OFF + 10,  DATA_T1)  
  `fits/m3/Model_5/Data.jl:170` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): DATA_AMP_POST summarises the recording's post-release ICP pulse amplitude as the median over a window starting 10 s after jugular compression ends and running to the end of the record. The 10 s offset discards the release transient, so the number describes recovered amplitude, not recovery dynamics.
- **D-1267ffde** [Unexamined · critical] #        (non-pulsatile run)           8.165               —  
  `fits/m3/Model_5/verify_fit.jl:141` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment records that seeding the overlay run from a converged limit cycle, rather than the flat-Pa fixed point, moves baseline mean ICP from 8.406 to 8.181 mmHg and AMP from 2.314 to 1.872 at patient 081's fitted parameters. It justifies solving both runs so a regression shows up as a number.
- **D-1a2008cb** [Unexamined · critical] 0.3 in M1 exactly as it is in all four fits on disk here. Freeing it makes M5 differ from  
  `fits/m3/Model_5/fits/README.md:189` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The README claims M1 and M5 share a line-for-line identical compliance cascade, that α_v defaults to 0.3, and that it is pinned at 0.3 in all four M5 fits on disk. It is a prose claim about defaults and past fit configuration, not executable code.
- **D-217b36b9** [Unexamined · critical] Rva_shunt_v       => 1.4e6,  
  `fits/m3/Model_6/Params.jl:144` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): Sets the VA shunt valve resistance in Model_6 to 1.4e6, the same value as Model_1, so a fixed one-way drain from CSF to central vein whenever ICP exceeds Pcv. Because ResistorValve has no opening pressure, this number alone sets how fast CSF leaves once the gradient is positive.
- **D-223e75b5** [Unexamined · critical] spinal.q  ~ 0,          # the spinal tap stays a pure sensor either way  
  `fits/m3/Model_5/Elements.jl:916` · equation · presumed AI-written, no examination on record
  Note (AI, not an examination): The spinal port is clamped to zero flow, so the element only senses spinal pressure and never withdraws or injects volume there. All filtration efflux Qfilt is routed to the cranial node instead, gated by k_couple.
- **D-2672f6ce** [Unexamined · critical] defined_by = :Ptm,  
  `fits/m3/Model_6/Elements.jl:78` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): `defined_by = :Ptm` is the default switch for how a vessel's compliance law is parameterised — transmural pressure rather than an alternative formulation. Every vessel built with GenericVessel_Compliance that does not pass `defined_by` explicitly inherits this law and its Ptm-branch parameters.
- **D-37b0aa4f** [Unexamined · critical] error("Did not reach steady state")  
  `fits/m3/Model_5/Model.jl:1778` · rule · presumed AI-written, no examination on record
  Note (AI, not an examination): After applying a parameter change, the code re-solves the static problem to steady state and throws a hard error if the adaptive steady-state solver does not converge. So any parameter set that fails to settle aborts the run instead of producing a degraded or partially converged initial condition for the dynamic solve.
- **D-3f3dcbd6** [Unexamined · critical] @named sys_raw = System(assembly, t; systems = elements_sorted)  
  `fits/m3/Model_5/Model.jl:357` · equation · presumed AI-written, no examination on record
  Note (AI, not an examination): Line 357 builds an uncompiled copy of the same assembly only to read its unknown list, beside the compiled system on line 360. It fixes what counts as a state variable name for anything downstream that consumes vars_raw.
- **D-4d59fb15** [Unexamined · critical] | a grid that spans decades rather than a fixed step | multiply, do not add: `P0[:Ca_v] .* [0.01, 0.  
  `fits/m3/Model_5/fit_cheatsheet.md:398` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The cheatsheet prescribes how a parameter scan is run and read: a multiplicative grid over Ca_v, skipping failed points, and an amplitude statistic defined as per-cycle peak-to-trough with the median across cycles, measured only on the last 20 s. These are modelling choices about what "the" pulse amplitude means, not just coding tips.
- **D-56f780a4** [Unexamined · critical] #              and with Rvvs at 0.04 mmHg/(mL/s) the vertebral collateral takes the  
  `fits/m3/Model_5/fit.jl:23` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment claims Rvvs_v is the key fitted parameter because brain.out feeds Rijvs and Rvvs in parallel, so at Rvvs 0.04 mmHg/(mL/s) closing the jugular only diverts flow, giving +0.25 mmHg ICP instead of the patient's +10.24. It justifies fitting Rvvs_v rather than fixing it.
- **D-666d96d8** [Unexamined · critical] ext.q ~ -D(V),  
  `fits/m3/Model_6/Elements.jl:126` · equation · presumed AI-written, no examination on record
  Note (AI, not an examination): Lines 126-127 set the wall flow two ways at once: it equals minus the rate of change of vessel volume, and minus compliance times the rate of change of transmural pressure. Together they pin V to Ptm through a constant compliance C, so the vessel wall obeys a linear pressure-volume law with no independent volume state.
- **D-7c987364** [Unexamined · critical] for p in 081 083 137 150; do  
  `fits/m3/Model_6/stream_all.sh:10` · selection · presumed AI-written, no examination on record
  Note (AI, not an examination): The hardcoded patient list 081 083 137 150 fixes which four recordings are refit and streamed, with 16 windows and 45 iterations each by default. Any aggregate built from modelplots/ude_cv_m6/api is therefore a comparison over exactly this cohort and this fit budget.
- **D-85a27aa9** [Unexamined · critical] in.p - ext.p ~ k * ((A/A0)^b1 - ((A/A0)^(-b2)))  
  `fits/m3/Model_5/Elements.jl:64` · equation · presumed AI-written, no examination on record
  Note (AI, not an examination): Line 64 sets the vessel wall constitutive law: transmural pressure (in.p - ext.p) follows a two-exponent law k*((A/A0)^b1 - (A/A0)^(-b2)) in area. It defines how the collapsible segment's area responds to pressure, which feeds resistance (line 65), volume (line 66) and the wall flow ext.q (line 67).
- **D-88f99759** [Unexamined · critical] connect(Rivp.out, Revp.out, Ro_spine.out, Razy.in),  
  `fits/m3/Model_6/Model.jl:285` · equation · presumed AI-written, no examination on record
  Note (AI, not an examination): This line ties the outlets of Rivp, Revp and Ro_spine to the inlet of Razy at one shared node, so internal vertebral, epidural and spinal outflow merge into a single azygos path with one common pressure. Editing who joins this junction changes venous topology, not just a parameter.
- **D-8fa118e4** [Unexamined · critical] s_smooth2 = 6*s_lin2^5 - 15*s_lin2^4 + 10*s_lin2^3  
  `fits/m3/Model_5/Elements.jl:451` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): Line 451 converts the second event's linear ramp fraction into a quintic smoothstep (6s^5-15s^4+10s^3), so that perturbation starts and ends with zero first and second derivative instead of a kinked linear ramp. The onset shape over `duration` is fixed by this polynomial, not fitted.
- **D-9c90ac81** [Unexamined · critical] f(v) = v === nothing ? "n/a" : string(round(v, digits = 3))  
  `Model_1/verify_fit.jl:289` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): In the verification pulse-amplitude table, a missing amplitude is printed as "n/a" and any value is rounded to 3 decimals. It is a display-only formatter inside the printout, not part of the fit objective.
- **D-a8747c4c** [Unexamined · critical] activate_resistance_evolution = 1,  
  `fits/m3/Model_5/Elements.jl:148` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): The vessel component defaults `activate_resistance_evolution = 1`, so unless a caller overrides it, Poiseuille resistance is allowed to evolve with vessel state rather than staying fixed. It is a default on a component used across many vessels, not a per-case setting.
- **D-ad976280** [Unexamined · critical] # version reached (it went 0.15x to 70x of Marmarou along the trajectories).  
  `fits/m1/Model_7/ude_cs.jl:265` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): CS_RMAX=100 bounds the neural compliance multiplier through exp(log(CS_RMAX)·tanh(z)), so learned spinal compliance can range from 1/100x to 100x the per-patient M1-fitted value. The comment justifies 100 by citing an earlier unconstrained run that reached 0.15x to 70x of Marmarou.
- **D-b53108c2** [Unexamined · critical] const DATA_AMP_BASE    = _median_in(DATA_BEAT, :icp_amp, DATA_T0,          JC_MID_ON - 5)  
  `fits/m3/Model_5/Data.jl:168` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): DATA_AMP_BASE is the baseline ICP pulse amplitude taken as the median of per-beat :icp_amp over the pre-compression window from DATA_T0 up to 5 s before jugular compression onset. The same median defines fit.jl's stage-B target, so this one window choice sets both the plotted baseline and the number the fit is scored against.
- **D-d753fce3** [Unexamined · critical] - **`C_evp_v` = 1.5 is a good default.** Epidural blood-patch manometry gives a secant  
  `fits/m3/Model_5/fits/README.md:106` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The README states that epidural venous compliance defaults to 1.5 mL/mmHg with a search box of 0.4–3.5, and that azygos venous compliance is re-derived to 0.4 with bounds 0.15–1.2, both marked "Applied". It records a narrowed, literature-anchored prior for two venous compliances in the Model_5 fit.
- **D-d768d5e8** [Unexamined · critical] #     post        +0.250  
  `fits/m3/Model_5/fit.jl:183` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment records measured pulsatile-minus-non-pulsatile mean ICP offsets per window (+0.016 baseline, -2.106 plateau, +0.250 post) and argues that only the baseline term should ever be used as a correction, because the plateau term is dominated by the model's known-wrong 22 mmHg plateau pulse. It is a documented refusal to apply a plateau mean-ICP correction in stage A of the fit.
- **D-df0974a2** [Unexamined · critical] out.value ~ θ  
  `fits/m3/Model_5/Elements.jl:288` · equation · presumed AI-written, no examination on record
  Note (AI, not an examination): This element outputs a constant angle parameter θ directly on its output port, with no dynamics. It acts as a fixed tilt/orientation source for whatever downstream element consumes the angle.
- **D-f615f4c8** [Unexamined · critical] # sampling the model at tw .- s. Nearest-index lookup into a 0.01 s export grid:  
  `Model_1/Data.jl:277` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The time-shift search scores a candidate lag by sampling the drawn model at `tw .- s` with nearest-index lookup on a 0.01 s export grid, instead of interpolating. The comment asserts the sampling error stays under half a sample and justifies it by analogy to the residual panel.
- **D-fc1f1d9c** [Unexamined · critical] raise RuntimeError("no créneau found")  
  `scripts/prep_jugular_data.py:149` · rule · presumed AI-written, no examination on record
  Note (AI, not an examination): Detection of the jugular "créneau" (step plateau) requires at least one supra-threshold run longer than 20 s on the 10 s smoothed trace; if none is found the preparation aborts instead of falling back. The threshold is fixed at halfway between baseline and the signal maximum.
- **K08** [Unexamined · critical] The free parameters and their search box (7 of 24 stage-A estimates sit on a bound)  
  `fits/m3/Model_5/fit.jl:358, fits/m3/Model_5/fit.jl:364, fits/m3/Model_5/fit.jl:388` · value · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): FIT_START sets the six-parameter starting point for the log-space Nelder-Mead fit in fits/m3/Model_5/fit.jl:358. Because the search is relative to each parameter's own start, this vector fixes both where the simplex begins and the scale of its first steps.
- **K09** [Unexamined · critical] Fitted E_v lands 3–7× above Marmarou's value in all four patients, accepted as is  
  `fits/m3/Model_5/fit/081.jl:16` · value · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): E_v is the fitted elastance-like parameter for patient 081 in Model_5; this file is the stored fit output that downstream runs load as fixed values. Its value sets the pressure response to a given volume change in that patient's model.
- **K12** [Unexamined · critical] Stage B: Ca_v by expand-then-bisect; valve chatter gate CHATTER_MAX = 1.5 (0.05 killed 137's fit)  
  `fits/m3/Model_5/fit.jl:941, fits/m3/Model_5/valve_diag.jl:102` · code · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): Ca is no longer picked from a fixed grid: the search walks outward from M3's default by CA_STEP until it brackets the measured pulse amplitude, then bisects in log space (geometric midpoint), because Ca varies over decades. Non-bracketing is reported as a genuine "no compliance reproduces this amplitude" outcome rather than being silently rounded to a grid edge.
- **K15** [Unexamined · critical] M7's network starts as a factor ≡ 1 on each patient's fitted law  
  `fits/m1/Model_7/ude_cs.jl:271` · code · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): Spinal compliance is the Marmarou-style stock law multiplied by a neural-network factor bounded to exp(±log 100) via tanh, i.e. between 0.01x and 100x the baseline law. Inputs are hand-scaled transmural pressure ((ptm-8)/6) and, in the full law, jugular pressure ((j-25)/20).
- **K16** [Unexamined · critical] Corner search objective ((ratio−1.03)/0.30)² + ((ΔICP−10.23)/1.50)², with Pjc allowed up to 200 mmHg  
  `fits/m3/Model_6/target_search.jl:11` · code · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): The objective sums two squared, tolerance-normalised residuals: a pulse ratio against 1.03 (tol 0.30) and dICP against 10.23 (tol 1.50). obj < 2 is then read as "the target corner is reachable", which is the switch between "search failure, keep fitting" and "structural limit of model 6".
- **D-a129e6d7** [Unexamined · passable] DRY=0  
  `fits/m3/Model_5/fits/run_arms.sh:118` · value · presumed AI-written, no examination on record
- **D-db79bf97** [Unexamined · passable] isempty(ids) && error("No run id given — set RUN_ID_CHOICE, _RUN_ID or _RUN_IDS.")  
  `fits/m3/Model_6/main.jl:172` · rule · presumed AI-written, no examination on record
- **D-dcf17dc3** [Unexamined · passable] const NNP = 25  
  `fits/m3/Model_6/ude_cv.jl:169` · value · presumed AI-written, no examination on record
- **K13** [Unexamined · passable] One onset for every patient: model time = data time + 120 s  
  `fits/m3/Model_5/Protocol_patient.jl:47, Model_1/Protocol_patient.jl:59` · value · your form answer, 26 Sep: Unexamined · passable
- **K07** [Examined · critical] Stage A is scored on the 1 Hz respiration-free mean; the pulse only enters in stage B  
  `fits/m3/Model_5/fit.jl:280` · code · your form answer, 26 Sep: Examined · critical
  Note (AI, not an examination): The fit target is fixed to the respiration-free 1 Hz mean ICP series (DATA_MEAN, :icp) over the measured window only. Every parameter estimated in this fit is therefore constrained by mean ICP alone, not by pulsatile or out-of-window behaviour.
- **K11** [Examined · passable] Artefact rule: range clip + sustained-excursion test; gaps under 2 s interpolated  
  `scripts/prep_jugular_data.py:69` · value · your form answer, 26 Sep: Examined · passable
- **K10** [Mine] Sampling rate FS = 100 Hz in prep_jugular_data.py (probably 200 Hz)  
  `scripts/prep_jugular_data.py:53` · value · your form answer, 26 Sep: Mine — not slop
  Note (AI, not an examination): FS = 100.0 hard-codes the sampling rate assumed for the jugular recordings in data/4_exemples. Every time axis, filter design and window length built in this preparation script derives from that one number.
- **K14** [Mine] Patient 150 (D) left out; no holdout for M1 and M7  
  `fits/m1/fits/run_fits.sh:4, fits/m1/fits/run_fits.sh:31` · code · your form answer, 26 Sep: Mine — not slop

## Plotting

- **D-39534e30** [Unexamined · critical] # Three layers, bottom to top: the pulsatile band, then the recording at 0.4 opacity,  
  `plotter/panels_data.jl:153` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The ICP fit panel deliberately layers the pulsatile band at the bottom, the recording at 0.4 opacity in the middle, and the non-pulsatile mean on top, because the mean is the curve the fit was scored against. The comment also records that a rejected alternative (mean last at 0.5 with a halo) was tried.
- **D-4958de81** [Unexamined · critical] VARIANTS = ("pulsatile", "nonpulsatile")  
  `scripts/make_compliance_nb.py:75` · selection · presumed AI-written, no examination on record
  Note (AI, not an examination): VARIANTS fixes the set of pulsatility conditions the notebook builds and pairs up, so every deck is rendered and compared under exactly "pulsatile" and "nonpulsatile". A run whose pulsatility label is not one of these two names is not selected for plotting or comparison.
- **D-4ba397fe** [Unexamined · critical] :m3vpasd => _row("m3", false, :vp_asd, "M3 + VP shunt + ASD", "#7B1FA2"),  
  `plotter/registry.jl:203` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): Registers the run id :m3vpasd as model M3 with a VP shunt plus anti-siphon device, with a legend label and the shared purple colour #7B1FA2. It is a registry/value decision: it selects model, shunt variant and appearance for that run id, not the physics equations.
- **D-51613499** [Unexamined · critical] # and at RUN_ALPHA's 0.85, the band still reads as one object and the traces  
  `plotter/plotting.jl:317` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The pulsatile run is drawn first so it sits underneath the mean-level run, and the comment asserts that at RUN_ALPHA = 0.85 the pulsatile envelope still reads as one band while the traces on top of it stay visible. This is a layering/legibility claim about draw order and alpha, not a change to any simulated quantity.
- **D-62805e4b** [Unexamined · critical] #     panel. Measured: 600×400 (the Plots default, and every deck panel that doesn't  
  `plotter/plot_runs.jl:650` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment fixes the stamp font at 4 pt integer, justified by a measurement that a 600x400 panel leaves a ~6 px band that 4 pt fills exactly and 5 pt overflows. It also claims every explicit deck size is larger, so the smallest default panel is the binding case.
- **D-63b0931c** [Unexamined · critical] # outage of 115.6 s — 27.6% of the recording, model time 23.1→138.7 s — which covers the  
  `plotter/panels_data.jl:498` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment justifies plotting the Doppler traces from a gap-preserving series (NaNs kept) so Plots breaks the line across the outage instead of interpolating across it. It backs that choice with specific numbers for patient 081's outage: 115.6 s, 27.6% of the recording, model time 23.1→138.7 s, covering the compression onset.
- **D-8b00b8d7** [Unexamined · critical] # so a deck whose protocol never reaches 352 s is not annotated with a point off its curve.  
  `plotter/panels_deck.jl:710` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): DIP_TIME fixes the "dip" marker on every P-V panel at a default of 352 s, a time taken from the postural tilt transient, unless `_DIP_T` overrides it. The marker is purely an annotation: if 352 s falls outside a deck's drawn window the dot is skipped, not clamped.
- **D-8b42335a** [Unexamined · critical] # "+0.99 ms (+0.10%)" is half again as wide as "+0.99 ms", and in the baseline  
  `plotter/panels_shared.jl:821` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): Table cell text in the shared summary panel is drawn at 20 pt instead of the earlier 22 pt, because cells now carry a percentage in brackets and the wider string collided with the row label in the baseline column. It is a layout claim about string width, not a numerical result.
- **D-9315a6b0** [Unexamined · critical] #       +1.00000. Pds is an exact affine proxy for M1's own transmural pressure, and the M1  
  `plotter/plotting.jl:1897` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment asserts that on this deck Pabdo is constant, so M1's transmural pressure is an exact affine function of Pds (corr = +1.00000), while M3's trace opens into a loop about 59% of the curve height versus about 2% against its own Ptm. These are stated findings baked into prose, not values the plot computes.
- **D-a398d8d3** [Unexamined · critical] # (Drawn last at 0.5, with the halo, the mean is still legible — that was tried. This  
  `plotter/panels_data.jl:158` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment fixes the ICP panel's three-layer draw order (pulsatile band, recording at 0.4 opacity, non-pulsatile mean on top) and records that an alternative — mean last at 0.5 with a halo — was tried and rejected. It is a claim about a past visual comparison, not code that runs.
- **D-e10a9912** [Unexamined · critical] :m1vpp => _row("m1", true,  :vp,   "M1 pulsatile + VP", "#80CBC4"),  
  `plotter/registry.jl:171` · value · presumed AI-written, no examination on record
  Note (AI, not an examination): This registry row binds the run id :m1vpp to model m1 with pulsatility on and a VP shunt, plus its legend label and line colour. It is an identity and presentation binding, not a physics parameter.
- **D-e8803b5b** [Unexamined · critical] # next door. Its magnitude says the same thing: ±0.98 mL/s non-pulsatile and -4.2..57.9  
  `plotter/plotting.jl:2780` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment justifies giving Rspine₊q its own panel, separate from the outflow panel, on the grounds that it is an internal craniospinal redistribution rather than a drainage route. It backs this with cited magnitudes (±0.98 mL/s non-pulsatile, -4.2..57.9 pulsatile for p083, vs outflows ~0.005), which are the stated reason a shared or twin axis is rejected.
- **K18** [Unexamined · critical] TCD velocity against model flow on twin axes, one gain per vessel anchored before onset  
  `plotter/panels_data.jl:481` · code · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): The TCD panel draws measured velocities (cm/s) and the model's cerebral inflow brain.in.q (mL/s) on two separate axes, with no score computed. It lets a reader compare waveform shape during compression while refusing to assert a velocity-to-flow proportionality nobody measured.
- **K21** [Unexamined · critical] Arterial phase shifted at plot time (pa_phase_shift), not fixed in the model  
  `fits/m3/Model_5/Data.jl:213, Model_1/Data.jl:225, plotter/panels_data.jl:349` · code · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): Before plotting, the model trace is slid in time to best correlate with the measured ABP, capped at half a beat and rejected below r=0.3. Visual agreement in the decks therefore reflects phase-aligned traces, not raw model timing.
- **D-05d1eb92** [Unexamined · passable] for model in ("M1", "M4"):  
  `hack/build_volume_nb.py:1019` · selection · presumed AI-written, no examination on record
- **D-1b3d302b** [Unexamined · passable] GPAT = ["", "/", "x"]  
  `hack/build_volume_nb.py:212` · selection · presumed AI-written, no examination on record
- **D-23ff2295** [Unexamined · passable] if abs(v - P["defaults"].get(n, v)) > 1e-12 * max(1.0, abs(v))]  
  `hack/build_volume_nb_patients.py:924` · rule · presumed AI-written, no examination on record
- **D-2cda11b0** [Unexamined · passable] def spread_at_fixed_x(x, V, k, nbins=200):  
  `scripts/make_compliance_nb.py:963` · value · presumed AI-written, no examination on record
- **D-3c0d2251** [Unexamined · passable] CA_ANCHOR = 0.03            # mL/mmHg, P_REF[:Ca_v] — stage B's starting point  
  `scripts/plot_fit_process.py:71` · value · presumed AI-written, no examination on record
- **D-4149b8e5** [Unexamined · passable] horizontal_spacing=0.08, shared_yaxes=True)  
  `hack/build_volume_nb.py:421` · value · presumed AI-written, no examination on record
- **D-6eee7f8f** [Unexamined · passable] color=SHUNT_COLOR, lw=max(0.9, 0.6 * r.lw), akw...)  
  `plotter/plotting.jl:2634` · value · presumed AI-written, no examination on record
- **D-8258dcd6** [Unexamined · passable] FAMILY = {"m1": "#2d40bd", "m3": "#FF6B00", "m4": "#C2185B",  
  `scripts/make_compliance_nb.py:86` · value · presumed AI-written, no examination on record
- **D-964081f8** [Unexamined · passable] width=1, dash="dot"))  
  `hack/build_volume_nb_patients.py:1849` · value · presumed AI-written, no examination on record
- **D-9b530255** [Unexamined · passable] color="rgba(40,40,40,0.55)", thickness=1.2, width=3),  
  `hack/build_volume_nb_patients.py:385` · value · presumed AI-written, no examination on record
- **D-a6df7dfc** [Unexamined · passable] if np.ptp(p) <= 0 or np.ptp(v) <= 0:  
  `scripts/make_compliance_nb.py:976` · rule · presumed AI-written, no examination on record
- **D-b0446578** [Unexamined · passable] error("Could not find $fname. Looked in:\n  " * join(candidates, "\n  "))  
  `plotter/plot_runs.jl:212` · rule · presumed AI-written, no examination on record
- **D-bd38b79d** [Unexamined · passable] yanchor="bottom", x=0.28, xanchor="left",  
  `hack/build_volume_nb_patients.py:1516` · value · presumed AI-written, no examination on record
- **D-c170f6b4** [Unexamined · passable] const PDS_RATE_XL = (325.0, 365.0)  
  `plotter/panels_shared.jl:157` · value · presumed AI-written, no examination on record
- **D-e156359a** [Unexamined · passable] if ys[-1] >= 0.045 * sum(B[m][k][1][-1] for k in ORD[m]):  
  `hack/build_volume_nb.py:1069` · rule · presumed AI-written, no examination on record
- **D-e4781a15** [Unexamined · passable] for ch in (c.r, c.g, c.b))  
  `plotter/plotting_sweep.jl:307` · selection · presumed AI-written, no examination on record
- **D-ed33e520** [Unexamined · passable] function first_two_peaks(t, y; min_sep=0.3, tmin=0.0)  
  `plotter/panels_shared.jl:382` · value · presumed AI-written, no examination on record
- **D-eef3d509** [Unexamined · passable] const REF  = "#b0b0b0"  
  `scripts/plot_seed_verification.jl:29` · value · presumed AI-written, no examination on record
- **K22** [Unexamined · passable] Zeros aligned only when both axis ranges already span 0  
  `Only on M5_extended (Model_3/plotting.jl:658, align_zero!): commits 88a5ec6e and` · outside · your form answer, 26 Sep: Unexamined · passable
- **K20** [Examined · critical] Compliance drawn as V against each element's own Ptm (and against Pds in the 3-D notebooks)  
  `plotter/plotting.jl:1686, plotter/panels_deck.jl:741` · value · your form answer, 26 Sep: Examined · critical
  Note (AI, not an examination): `pv_panel` defaults to `baseline=false`, so pressure-volume panels plot absolute compartment volume; only callers passing `baseline=true` re-zero y at the window's first sample. That re-zeroing exists for the combined panel, where two different compartments' absolute levels are not comparable but their excursions are.
- **K23** [Examined · critical] Report naming: M4 shown as 'M2'/'H-M2', M5 as 'Model 2', recordings as letters A–D  
  `plotter/plot_runs.jl:403, plotter/plot_runs.jl:410` · code · your form answer, 26 Sep: Examined · critical
  Note (AI, not an examination): In TALK mode the legend rewrites any whole "M<digit>" token (M2..M9) to "M2", so a figure reads as "baseline vs comparison" instead of naming the numbered model. The comment claims this is safe because every deck is M1-vs-one-other.
- **K24** [Examined · critical] Each deck's panel choices kept in untracked layout.jl files (no history)  
  `.gitignore:105` · code · your form answer, 26 Sep: Examined · critical
  Note (AI, not an examination): The `modelplots/` directory is excluded from version control, so plots written there are never committed. Plot output is treated as regenerable build artifact rather than authored source.
- **K17** [Examined · passable] Recording drawn as slate scatter, model as lines, on every data panel  
  `plotter/panels_data.jl:11, plotter/panels_data.jl:165` · code · your form answer, 26 Sep: Examined · passable
- **K19** [Examined · passable] Model colours: M1 blue #2d40bd, M4/'M2' pink #C2185B; one colour pair per model  
  `plotter/registry.jl:166, plotter/registry.jl:188` · value · your form answer, 26 Sep: Examined · passable

## Comparison

- **D-105c4e5a** [Unexamined · critical] # The caption gives the ramp but not what happens after: the fall in ICP near t = 250 s is  
  `scripts/ursino_lodi_1997.jl:305` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment interprets Fig. 7 of Ursino & Lodi (1997): SAP drops from 100 to 90 mmHg over t=10-20 s and then stays at 90 for the whole run, so the later ICP fall near t=250 s is read as a model-generated plateau wave rather than a change in the input. That reading is what fixes the step input Pa_of(t) at line 311.
- **D-36be83cd** [Unexamined · critical] # So: M1 blue, 5.0 wide, drawn FIRST. M3 fluo orange, 2.0 wide, drawn SECOND.  
  `scripts/ursino_plots.jl:41` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): A plotting convention: model M1 is drawn first as a thick blue backdrop (5.0 pt), model M3 second as a thin fluorescent orange line (2.0 pt) on top. It fixes which curve reads as the reference in every figure from this script.
- **D-5db6c497** [Unexamined · critical] #      t_end = 160 with retcode Success, and M1's ICP excursion is 6.86 mmHg against  
  `Model_3/kmedoids_m1m3_sweep.jl:23` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): A header comment overrides an older notebook and asserts M1 over-responds to abdominal loading (ICP excursion 6.86 mmHg vs M3's 0.88, solve reaching t_end = 160 with retcode Success). That claim is the stated justification for keeping Pabdo as the discriminating ramp target in this k-medoids sweep.
- **D-68e7727a** [Unexamined · critical] experiment  = "jugular_compression",  
  `Model_3/run_jc_081.jl:199` · selection · presumed AI-written, no examination on record
  Note (AI, not an examination): This run stamps its outputs as model "m4", experiment "jugular_compression", variant JC_PATIENT, run_id "m4jc<patient>". Downstream comparison decks use these labels to decide which curve is m4 and which patient it is paired against.
- **D-79d7719e** [Unexamined · critical] # the file that enforces them, and the flag uses fit.jl:1004's own 0.98 ratio test.  
  `hack/export_volumes_patients.py:129` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The export script does not hardcode fit bounds: it parses FIT_LO/FIT_HI out of fit.jl and marks a parameter "pinned at its bound" with the same 0.98 ratio test fit.jl:1004 uses. The intent is that widening the box in fit.jl cannot leave the table asserting a stale flag.
- **D-a6d2b2ff** [Unexamined · critical] #      (t_end 160.0, ends_early=True, beside patients at 418.37/418.75). The compression  
  `scripts/run_patient_matrix.sh:20` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment claims the old M4 jugular column was not comparable to the patient columns, because the generic deck ran a 160 s Pext ramp while the patient créneaux run to ~418 s, and asserts the fix is one M4 jugular run per patient schedule while the abdominal ramp and tilt can keep a single shared M4 run.
- **D-ba572198** [Unexamined · critical] # with ends_early=True against patient columns at 418.37 and 418.75.  
  `hack/export_volumes_patients.py:371` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The panel requires a per-patient M4 run at that patient's own boundary conditions, and refuses the generic m4/jugular_compression run as a fallback. The comment records a past bug where the M4 column ran to t_end=160.0 (ends_early=True) while patient columns ran to 418.37 and 418.75 s, so the comparison mixed a Pext ramp with a patient creneau.
- **D-fdce8a05** [Unexamined · critical] #                      117 s. It also has to be many beats long -- one cardiac cycle is ~1 s  
  `hack/export_volumes.py:148` · claim · presumed AI-written, no examination on record
  Note (AI, not an examination): The comment states that the baseline mean flow q̄₀ is averaged over a 10 s window ending at BASELINE_T1 = 60 s, and that the volume integral is zeroed at 60 s rather than t = 0, so the start-up transient shows as a dip before the zero point instead of being folded into q̄₀. It also asserts specific onset times and a prior wrong result of -24 mL in M1 and M3.
- **K25** [Unexamined · critical] M1 and M4 compared under one invented schedule (Protocol.jl), not a patient's timing  
  `Protocol.jl:78, Protocol.jl:79` · value · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): P_STAGES sets the applied external pressure ramp as three stages, converting mmHg to dyn/cm² with the factor 1330 and peaking at P_PEAK_MMHG (8.0 mmHg unless _RAMP_AMP overrides it). It is the amplitude of the jugular-compression / pressure-ramp stimulus.
- **K27** [Unexamined · critical] k-medoids: ARI against model / run / phase decides whether beats can tell M1 from M3  
  `Model_3/kmedoids_m1m3_analysis.py:11` · code · your form answer, 26 Sep: Unexamined · critical
  Note (AI, not an examination): The script scores one k-medoids partition of beats against three held-out labels (model, run, phase) and treats those three ARI values as mutually exclusive at a given k. That framing is what turns the numbers into a test of what the beat descriptors encode rather than a restatement.
- **D-15940115** [Unexamined · passable] Ro::Float64   = 526.3      # mmHg*s/ml   CSF outflow resistance  
  `scripts/ursino_lodi_1997.jl:47` · value · presumed AI-written, no examination on record
- **D-17389dea** [Unexamined · passable] DESCRIPTORS = ["level", "pulse", "t_peak", "t_trough", "frac_above"]  
  `Model_3/kmedoids_m1m3_analysis.py:59` · selection · presumed AI-written, no examination on record
- **D-1e8af5bc** [Unexamined · passable] const PROTOCOL    = :pressure  
  `Model_3/kmedoids_sweep.jl:60` · value · presumed AI-written, no examination on record
- **D-298b80d0** [Unexamined · passable] shunt       = "none",  
  `Model_3/run_jc_081.jl:206` · value · presumed AI-written, no examination on record
- **D-3623b720** [Unexamined · passable] while (k + 1) * T_CARD <= last(t)  
  `scripts/ursino_waveform_match.jl:58` · rule · presumed AI-written, no examination on record
- **D-42abfeda** [Unexamined · passable] STAGE_A = ["Rvvs_v", "P_jc_amp", "Ro_tot_v", "E_v", "Psinus_v", "k_ijvs_v"]  
  `hack/export_volumes_patients.py:136` · selection · presumed AI-written, no examination on record
- **D-4f514bae** [Unexamined · passable] Can::Float64  = 0.15       # ml/mmHg     basal arterial-arteriolar compliance  
  `scripts/ursino_lodi_1997.jl:52` · value · presumed AI-written, no examination on record
- **D-58e5e715** [Unexamined · passable] romults = ["4", "5", "6"]   # the Ro panel is labelled in multiples of Ro0, not raw values  
  `scripts/ursino_lodi_1997.jl:355` · selection · presumed AI-written, no examination on record
- **D-62ad736a** [Unexamined · passable] length(POINTS) > 1 || error("Only the baseline completed — every other point was skipped.")  
  `Model_3_celia/kmedoids_sweep.jl:282` · rule · presumed AI-written, no examination on record
- **D-693b901e** [Unexamined · passable] assert len(MANIFESTS) == 2, f"expected manifests for 2 models, found {list(MANIFESTS)}"  
  `Model_3/kmedoids_m1m3_analysis.py:83` · rule · presumed AI-written, no examination on record
- **D-6d7771ba** [Unexamined · passable] ramp = cgrad([:"#2d40bd", :"#FF6B00"])  
  `scripts/ursino_lodi_1997.jl:402` · value · presumed AI-written, no examination on record
- **D-7c607bfe** [Unexamined · passable] DESCRIPTORS = ["level", "pulse", "t_peak", "t_trough", "frac_above"]  
  `Model_3_celia/kmedoids_m1m3_analysis.py:59` · selection · presumed AI-written, no examination on record
- **D-a8dc0c89** [Unexamined · passable] p3 = plot(panels...; layout = (1, length(panels)), size = (1400, 460), dpi = 160)  
  `scripts/ursino_plots.jl:172` · value · presumed AI-written, no examination on record
- **D-af446eff** [Unexamined · passable] pvi_input(t0, dur, vol = 2.0) = (t) -> (t0 <= t <= t0 + dur ? vol / dur : 0.0)  
  `scripts/ursino_lodi_1997.jl:336` · value · presumed AI-written, no examination on record
- **D-bf36daaa** [Unexamined · passable] for v in ("nonpulsatile", "pulsatile"):  
  `hack/export_volumes.py:303` · selection · presumed AI-written, no examination on record
- **D-c253cc72** [Unexamined · passable] if f.label == "k" && value <= 0  
  `Model_3/kmedoids_sweep.jl:272` · rule · presumed AI-written, no examination on record
- **D-c503cc41** [Unexamined · passable] error("variable $v absent from the export")  
  `scripts/ursino_tilt_pressures.jl:83` · rule · presumed AI-written, no examination on record
- **D-d823b531** [Unexamined · passable] t_P_dynamic_1        = 0.0,  
  `Model_3/run_jc_patients.jl:154` · value · presumed AI-written, no examination on record
- **D-da8fba98** [Unexamined · passable] simlog("\n--- [$MODEL] $label ($(key) = $value)  ->  A_baseline = $(round(A_seed; digits=4)) cm² ---  
  `Model_3_celia/kmedoids_m1m3_sweep.jl:248` · value · presumed AI-written, no examination on record
- **D-eb73d347** [Unexamined · passable] base === nothing ? error("[$MODEL] the baseline point failed — nothing to compare against.") :  
  `Model_3/kmedoids_m1m3_sweep.jl:286` · rule · presumed AI-written, no examination on record
- **D-f554166a** [Unexamined · passable] if cand[h] < best[0]:  
  `Model_3_celia/kmedoids_m1m3_analysis.py:234` · rule · presumed AI-written, no examination on record
- **D-fcf43b6a** [Unexamined · passable] kind=:pressure, ramp_target=:Pext,  overrides=Dict{Symbol,Float64}()),  
  `Model_1/run_all_m1.jl:102` · value · presumed AI-written, no examination on record
- **K26** [Unexamined · passable] Unfitted M4, driven by each patient's compression timing, as the reference column  
  `Model_3/run_jc_patients.jl:1` · code · your form answer, 26 Sep: Unexamined · passable
- **K31** [Examined · critical] M6's conclusion: 'flat pulse, big step, correct level: pick two'  
  `Stated in the fitting report (Seafile) and the M6 notebooks, not in code.` · outside · your form answer, 26 Sep: Examined · critical
- **K32** [Examined · critical] Missing compartments drawn as absent (null), not as zero, in the M1-vs-M4 volume bars  
  `hack/export_volumes.py:12` · code · your form answer, 26 Sep: Examined · critical
  Note (AI, not an examination): Compartments that M1 does not model are exported as `null` rather than `0.0`, so the dashboard draws no bar instead of an empty bar. This keeps "absent compartment" distinct from "compartment with zero volume" in the M1-vs-M4 comparison.
- **K28** [Don't know] Ursino Fig. 9: raised CSF production stands in for a constant infusion; breakpoint from a two-segment fit  
  `scripts/ursino_validation.jl:55, scripts/ursino_plots.jl:61` · value · your form answer, 26 Sep: Don't know
- **K29** [Don't know] Fit M1 vs Fit M5 compared from each fit's own trace CSV, not from deck exports (they differ by up to ~6 mmHg)  
  `scripts/plot_fit_1_vs_2.py:4` · code · your form answer, 26 Sep: Don't know
- **K30** [Don't know] Jugular h-sweeps: the overshoot ratio (1.7–2.5× vs 4.3–5.1×) as the M1/M4 discriminator  
  `Seafile rapports-de-stage-thomas-2026/cis-report/make_bc_figs.py and bc_numbers.` · outside · your form answer, 26 Sep: Don't know
