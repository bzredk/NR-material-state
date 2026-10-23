# Recovery memory: first acquisition

Figueroa lab | One specimen | 24 core records + 6 reference anchors

Operator: __________  Date/session: __________  Specimen: __________
Frozen parameter version: __________  Controller/calibration ID: __________

## Question and setup

Does preload amplitude, loading path or unloaded waiting change the response to the same later compression? Use one slow-recovery open-cell PU coupon, rigid flat platen, calibrated normal force and actual platen-to-base displacement. Keep one controller configuration and interface. A side view helps measure free recovery; airborne TCP position is not foam surface height.

## Before the formal block

1. **Calibrate:** unloaded force baseline; reference loads; normal-axis sign, TCP/parallelism and fixture compliance; independently measured clock mapping and filter/transport delays. Retain raw clocks.
2. **Pretest:** find informative, repeatable compressions and speeds. Validate recovery after the strongest intended overshoot. Choose low/high terminal amplitudes A_L/A_H, peak factor kappa, one common probe and three waits.
3. **Freeze:** fill `parameter_form.csv`, then build the resolved plan. Record the lab's actual limits. No simulated gains, loads or times are defaults. Condition the formal coupon consistently; verify its reference response.

## One core record

**Reset -> baseline -> preload -> hold -> retract -> wait -> common probe -> rehold -> withdraw/reset.**

- `slow`: monotone ramp to A. `overshoot`: ramp to kappa*A, return to A at the same preload speed. Use the scheduled unloaded lead-in for slow trials; both terminal holds have the same duration.
- Wait starts at the common air clearance. Also log the actual loss-of-contact and recontact times: travel contributes to total free recovery.
- Execute the same probe target, speed and hold for every cell. Record actual motion and any override. Log the recovery/washout after withdrawal.
- Zero force alone does not establish reset. Use the frozen height/reference-response rule. An extra touch changes history; log it and re-establish washout.

## Run order and time

**a01 -> e00-e05 -> a02 -> e06-e11 -> a03 | break | a04 -> e12-e17 -> a05 -> e18-e23 -> a06**

Each block covers all 12 amplitude x history x wait cells. Anchors are identical small reference loads, each followed by full reset. Priority cases are e09/e23 (high/overshoot/short); keep all other cells. Do not reorder by response.

Reserve **5 hours** initially: about 110 min preparation, measured block durations, 10 min break, 15 min handoff and 30 min contingency. The compiled timetable governs feasibility. If needed, continue at a complete-block boundary; never shorten washout to fit the booking.

## Save and hand back

Minimum CSV: `episode_id, specimen_id, session_id, timestamp, command_position, actual_position, normal_force, phase`.

Phases: baseline / preload / hold / retract / wait / recontact / rehold / recovery. Record actual events; `forecast_start_s` is actual retract onset relative to the record start. Use a fixed surface reference, declared units/signs/offsets, and common-clock controller/event timestamps.

Keep all attempts and original device logs. Retry with a new ID linked to the same planned_id; do not replace an inconvenient valid response. Fill episodes.csv and metadata.json; save controller context, precommitted plans and events. Inspect the first exported core record, then each block. Follow existing laboratory stop procedures.

Detailed setup and pretest: FIRST_SESSION_PLAN_EN.md | Schedule: run_order_30.csv
