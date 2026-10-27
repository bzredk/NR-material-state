# First session: recovery memory in a real foam specimen

**Discussion and execution plan for the Figueroa lab | 20 October 2026**

**Book five hours with an operator and a working force/pose logger.** Aim to finish calibration, a focused pretest, and all 24 core records plus six reference anchors on one specimen. Actual feasibility depends mostly on the measured washout time. Once pretest parameters are known, `session.py build` computes the timetable. If all 24 will not fit, finish the first complete 12-condition block and its three anchors, then book the second block. Do not shorten reset or remove long-wait/low-amplitude conditions to meet the booking.

The scientific question is whether preload amplitude and history change the response to the **same later compression**, and whether changing the unloaded wait exposes dynamics that a broad fixed relaxation spectrum or static nonlinearity cannot explain. The latest simulation bridge found useful historical prediction information but no useful extra action benefit after shared feedback. This session therefore measures the material phenomenon first; it is not a robot-controller contest.

## 1. Bring and mount

**Primary specimen:** traceable, uncoated, slow-recovery open-cell polyurethane foam. Prepare one pretest coupon P0 and one formal coupon S1 from the same sheet/batch; retain a spare. Start fixture planning around a 30 × 30 × 20 mm coupon and a roughly 50 mm rigid flat platen, then adjust area/thickness to the available sensor and stable deformation. These are fixture suggestions, not fixed test dimensions. Measure the actual dimensions, mass, cutting/rise direction and relaxed height. Keep the sides free and ventilated, and use one documented dry interface throughout.

**Optional later comparison:** fast-recovery open-cell PU of the same geometry. Do not split the 24 records across foam types. If the slow foam cannot reset within a workable session, preserve its pretest and use a separately identified specimen/material for a new complete design; do not switch mid-block.

**Recommended configuration:** one available FR3/Panda or iiwa, rigid full-face platen, calibrated normal force sensor below the sample, and actual platen displacement relative to the rigid base. A wrist F/T sensor is a practical alternative after tool-weight, orientation and free-motion compensation. Use metal for the load path; printed parts locate the sample or camera without squeezing the sides. Place the normal axis through the sensor/platen center.

Use robot pose only after measuring TCP, mounting compliance and relative-base errors over the intended travel. OptiTrack can cross-check rigid platen/base motion if its measured precision is adequate; it does not automatically resolve the deforming foam surface. A calibrated side camera or laser is preferred for passive recovery-height observation. Without it, use separately reset single-touch pretests and the reference-response washout route below.

**Keep one control mode and configuration for all 24 records.** Record accessible gains, mode/version, interpolation, filtering and actual rates. An unavailable gain stays unknown; no simulation stiffness, damping, force cap, or clock rate is substituted.

## 2. Settle only five items before the booking

| Item | Minimum answer from the lab |
|---|---|
| Arm and operator | Which arm, trained operator, booking length, tool mount and established execution limits? |
| Command/pose interface | Can it issue the normal-axis profile and log commanded and actual platen pose, with timestamps and phase events? Which controller mode and interpolation? |
| Force measurement | Base load cell or wrist F/T; model/range, calibrated noise and bandwidth, raw access and device clock? |
| Geometry and recovery view | Which coupon/batch and platen; base-relative displacement measurement; side camera/laser or reference-touch alternative? |
| Clock/export path | Shared trigger or independently measured clock mapping; acquisition versus arrival timestamps; common-time CSV export and raw archive? |

Start with the lab's established protection and stop procedure. The worksheet records those limits; it is not an additional approval process. None of these decisions requires a new learning architecture or a second robot.

## 3. Calibration and focused pretest

**0–20 min: mount and describe.** Photograph the setup and specimen orientation. Enter IDs and dimensions. Retain the original surface reference for the session. Do not set a new contact zero for each trial.

**20–50 min: verify the measurement chain.** Record about 30 s unloaded. Apply known reference loads across the expected force range, including unloading, to establish offset, gain, repeatability and drift. Check normal-axis sign, platen parallelism, base motion and fixture compliance against a rigid reference or independent displacement measurement. With wrist force, record the unloaded motion used later, so gravity/inertia or acceleration artifacts can be recognized. Establish a common clock using a shared trigger or an independent timing event, not by aligning foam force peaks. Retain raw clocks and filter/transport delays.

Raw force at 500–1000 Hz is a useful starting acquisition target **if available**, not a requirement copied from the simulation. The actual force, pose and command rates are recorded separately. Resolve the fastest transient of interest with roughly 20 samples and adequate sensor bandwidth; if that is not achieved, slow the relevant ramp or restrict the claim to resolved dynamics. More interpolated samples do not increase bandwidth.

**50–100 min: P0 pretest and S1 conditioning.** This is a planning allowance, not a deadline that justifies skipping recovery. Save every pretest record.

1. **Find a useful amplitude range.** On P0, explore several increasing compressions with one moderate, resolved ramp. Extend the loaded hold enough to see both the initial drop and slower evolution. Inspect actual displacement, force, slip/buckling and the recovered reference response. Seek clear reproducible deformation, not the smallest measurable motion. Determine the largest operationally recoverable peak before choosing terminal amplitudes `A_L < A_H` and overshoot factor `κ > 1`, with `κ A_H` inside that range.
2. **Choose the fixed speeds.** At a representative amplitude, compare two practical speeds. Pick a preload speed that gives adequate tracking and resolves the transient; the monotone and overshoot histories use that same speed. Select one common retraction speed and one common probe speed. Record acceleration/jerk/interpolation too: the plan's ideal linear ramp is not a request for an instantaneous velocity jump.
3. **Observe recovery, not only loaded relaxation.** Prefer a passive surface trace after the highest intended overshoot. Otherwise use separately reset preload–wait–single-touch episodes at increasing waits. A series of touches in one recovery interval changes the state and is not passive observation. Start loaded observations in the tens-of-seconds range when suitable; if a longer observation is required, budget it explicitly. These times do not become formal settings until measured locally.
4. **Choose three waits and one common future probe.** Span early, intermediate and late recovery. If a reliable unloaded recovery half-time exists, approximately `0.2 t50, t50, 5 t50` is a starting spacing, not a mandatory formula. Here `wait_s` means dwell **after the platen reaches clearance**. The actual no-contact interval also contains parts of withdrawal and approach; check that these do not overwhelm the shortest recovery window. Freeze the same probe target, approach and hold for all 12 cells.
5. **Establish washout from the worst preload.** Find a duration after return to clearance for which repeated relaxed-height/reference responses return to their pretest band. Validate it after high/overshoot loading, not only a low compression. Zero force alone is insufficient. `optical_and_reference` uses passive height plus reference responses; `reference_washout` uses separately reset reference-response pretests and the six formal anchors. For the latter, do not touch before every core record and then silently call the state undisturbed.
6. **Condition S1 consistently and freeze.** Apply the recorded conditioning sequence and the established washout to S1. Check its reference response; do not copy P0's zero or force curve as S1's measurement. Fill the parameter form, lab limits and reset bands, and save a version before the formal block. If S1 falls outside the pretested working range, resolve that before starting, rather than revising settings halfway through the 24.

**100–110 min: create the resolved plan and test the logger.** Use the filled parameter form to generate the 30-record schedule and batch folder. Review the longest/highest planned trajectory with the lab operator. A short exported record must retain correct IDs, units, time, force, actual motion and phase events. No material fitting is required to start collection.

## 4. Execute the fixed sequence

The existing seed-20261019 order is preserved. Each block is a full `2 amplitudes × 2 histories × 3 waits` cross; the second block is a technical repeat on S1.

`a01 → e00…e05 → a02 → e06…e11 → a03 → break → a04 → e12…e17 → a05 → e18…e23 → a06`

High/overshoot/short appears at **e09 and e23**. Give these the predeclared main visualization, but collect every other cell and keep the chronological order. They are not extra repeats and are not moved to the front.

One core record:

1. Verify the previous washout and start the unloaded baseline.
2. `slow`: monotone ramp to `A`; `overshoot`: ramp to `κA`, return to `A` at the same preload speed.
3. Hold at `A` for the same duration. The monotone program has an extra unloaded lead-in `2(κ−1)A/v` so terminal holds begin at matched relative times. This does **not** isolate peak depth from all loading-path/duration effects.
4. Retract to common clearance, then dwell for the assigned short/middle/long wait.
5. Execute the identical precommitted recontact trajectory and rehold. Record actual motion even if the robot cannot perfectly track it.
6. Withdraw and log the recovery/washout. Enter actual phase events, reset evidence, any override and run status. The next record begins only after the frozen reset rule.

Each `aXX` is the **same small reference load** fixed in pretest, followed by its own full washout. Anchors diagnose drift and reset; they are excluded from the 24-condition constitutive fit. If an anchor leaves its pretest band, inspect the concrete cause, extend recovery if appropriate and document it. Do not retroactively change the zero, delete unfavorable responses or silently lower all amplitudes.

Keep every attempt. A retry gets a new episode ID such as `e09_try2` and retains `planned_id=e09`; add it to the manifest. Select the first predeclared QC-valid completed attempt, never the one with the strongest effect. A material-response surprise is not itself a logging failure.

## 5. Time and stopping boundaries

| Part | Booking allowance |
|---|---:|
| Mount, calibrate, pretest and freeze | 110 min initially; extend if recovery requires it |
| Block 1: 12 core + 3 anchors | Calculated from measured settings |
| Break between blocks | 10 min |
| Block 2: 12 core + 3 anchors | Calculated from measured settings |
| Data handoff and raw inspection | 15 min |
| Contingency | 30 min |

`session.py build` adds one initial washout and each of the 30 records' active profile, post-record washout and handling. It includes the overshoot return, matched lead-in, withdrawal, probe, rehold and final withdrawal. Motion times are nominal distances/speeds; acceleration limits and implementation can add time.

For booking sensitivity only: if each active record averages 50 s, handling averages 15 s, and washout is 60 / 180 / 300 s, the full visit is approximately **3 h 49 / 4 h 51 / 5 h 53**. These are arithmetic examples, **not specimen or robot settings**. The compiled timetable replaces them.

If the full plan no longer fits, finish a complete block when practical and retain the remaining order for the next session. Record a new session/calibration ID if resuming another day. Repeat is then partly confounded with day: do not describe the two blocks as independent same-day repeats. An unexpected interruption can leave a partial block; keep it and resume missing cells rather than pretending it is balanced.

## 6. Hand back a directly usable batch

Use the generated `data/` folder. The minimum sample columns are:

`episode_id,specimen_id,session_id,timestamp,command_position,actual_position,normal_force,phase`

Prefer SI units and compression-positive coordinates. Explicitly fill the measured offset, signs, units and clock mapping in `metadata.json`. If the logger already exports calibrated relative SI values, the corresponding offsets can be recorded as zero **because the transformation was performed**, not because calibration is unknown.

Phases: `baseline, preload, hold, retract, wait, recontact, rehold, recovery`. Mark overshoot rise/return and matched lead-in as substage events. The phase changes and `forecast_start_s` must reflect recorded execution, not just nominal planned times. `forecast_start_s` is relative to episode start; controller/event/plan timestamps are common-clock seconds.

Use the pretest force threshold and persistence to label operational detachment/recontact, and retain the criterion and timing uncertainty. These are force-based proxies, not an unobserved geometric ground truth; use the recovery view for confirmation when available.

Keep a per-attempt CSV plus the unchanged original device logs. Save controller context once at the start of each record and at any change; do not fill gains you cannot read. `planned_commands.csv` contains plans actually available at the stated time. The relative timing segments generated here are not an executed controller program and do not by themselves establish a precommitted absolute-time plan.

Fill the actual disposition in `episodes.csv`; planned and unrecorded rows remain planned. The assembly tool preserves records and does not automatically mark trials valid. Inspect after the first anchor/core export, and again after each block; fitting can wait until the full 24 and calibration fields are ready.

The first analysis is measured-motion-conditioned material prediction. Command-conditioned force and motion prediction requires independent actuator/observation calibration later. The first session does not establish a learned-state or closed-loop action advantage.

Portable entry points (Python with `requirements.txt`; commands run inside this package):

```text
python session.py build --parameters session_plan/parameter_form.csv --output collection/day1
python session.py assemble --prepared collection/day1 --recordings recordings/day1 --output data/day1_batch
python first_batch.py inspect data/day1_batch --output runs/day1_inspect
python plot_intake.py runs/day1_inspect --output figures/day1_raw
```

If the logger already produced a combined `raw.csv` in the batch folder, omit assembly. Keep outputs in a new folder for each inspection; existing records are not overwritten.
