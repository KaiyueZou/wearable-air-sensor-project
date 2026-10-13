# A Watch Mounted Optical Air Sensor

## Overview

I’m exploring how a watch could measure airborne particles close to its wearer. This concept places a shallow, open air channel at the watch’s upper edge, with two lasers and two cameras protected behind sealed windows. One laser illuminates particles; the cameras also inspect the windows for contamination. Closely timed laser-on and laser-off exposures reduce ambient-light interference, while repeated measurements build a more useful reading.

The intended output is a local particulate estimate or trend, accompanied by a measurement-quality indicator. This is an independent design study inspired by the Apple Watch form factor. The Blender animation explains the proposed mechanism; it does not demonstrate measurement accuracy, production fit, water resistance, or laser safety.

## Outline

- [The physical layout](#the-physical-layout)
- [Rejecting ambient light](#rejecting-ambient-light)
- [Taking multiple measurements](#taking-multiple-measurements)
- [Checking both optical windows](#checking-both-optical-windows)
- [Separating useful light from reflections](#separating-useful-light-from-reflections)
- [Air exchange and wrist motion](#air-exchange-and-wrist-motion)
- [From scattered light to a particulate estimate](#from-scattered-light-to-a-particulate-estimate)
- [Operating states and wearable integration](#operating-states-and-wearable-integration)
- [Other approaches considered](#other-approaches-considered)
- [What needs to be tested](#what-needs-to-be-tested)
- [How to read the animation](#how-to-read-the-animation)
- [References](#references)

## The physical layout

The sensing recess sits at the 12 o’clock edge of the watch. It is shallow and open at both ends so ambient air can pass through without entering the electronics enclosure. Sealed window facets, W1 and W2, separate the exposed channel from the dry optical compartments.

| Component | Proposed role |
| --- | --- |
| L1 | Main laser, illuminating the air through W1 |
| W1 | Transmitter-side protective window |
| C1 | Camera observing L1’s illuminated footprint on W1 |
| W2 | Receiver-side protective window |
| C2 | Camera collecting particle-scattered light through W2 and inspecting W2 in a separate exposure |
| L2 | Auxiliary laser illuminating W2 for its diagnostic check |
| Beam trap | Shielded absorber receiving the main beam after it passes through W2 |

The main route is **L1 → W1 → exposed air → W2 → absorbing trap**. C2 looks off-axis at a selected airborne region along that beam. Its particle-measurement region excludes the bright beam-interception spot on W2 and the downstream trap.

An opaque divider separates the internal compartments. Baffles and receiver shielding limit unwanted paths, while the exposed windows remain accessible for cleaning. The model’s near-vertical, reverse-raked window facets refine the original sloping recess, with the aim of reducing an obvious upward reflection path. Their final angles still require optical analysis.

## Rejecting ambient light

An exposed channel sees sunlight and room lighting as well as the sensor’s own illumination. The proposed acquisition therefore contrasts closely spaced exposures:

1. **Laser off:** record the ambient background with both lasers off.
2. **L1 on:** record while the main laser is emitting.
3. **Subtract:** compare matched exposures to estimate the additional light associated with L1. This cancels the ambient component only to the extent that it stays similar between exposures; changing background light can leave residuals.

Scattered light must be collected during the laser pulse. Recording only after the pulse has ended would miss ordinary elastic scattering. Rapid source modulation and synchronized detection are established techniques for reducing ambient interference. [Analog Devices explains this approach](https://www.analog.com/en/resources/technical-articles/optimizing-precision-photodiode-sensor-circuit-design.html).

A balanced **off–on–on–off** group is another candidate: averaging the two on exposures and subtracting the averaged off exposures can suppress approximately linear background drift when timing and exposure settings are matched. The actual sequence must accommodate detector settling, lighting flicker, and changing wrist orientation.

Subtraction has limits. Laser-induced window glare and housing reflections also appear only during the on exposure, so they survive. Ambient photon noise remains, and saturated measurements cannot be recovered by subtraction. [Hamamatsu’s photodiode technical note](https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/99_SALES_LIBRARY/ssd/si_pd_kspd9001e.pdf) describes the photocurrent-dependent shot noise behind this limitation.

The proposed hardware therefore also needs narrowband filtering around the selected laser wavelength, restricted collection optics, suitable detector headroom, and an explicit overbright or saturation flag.

## Taking multiple measurements

Each reported reading would combine multiple synchronized exposure groups over an acquisition interval. This can improve repeatability and provide opportunities to identify inconsistent or corrupted samples. It also allows window checks to be interleaved with particle measurements.

There are two separate timing choices:

- **Within a reading:** pulse timing, exposure length, diagnostic phases, and averaging.
- **Between readings:** how often to wake the sensing system, balancing battery use against missed short pollution events.

Shorter pulses reduce the received signal at fixed peak power. More pulses can improve noise averaging, but do not guarantee more independent particle observations: several exposures might see the same particle or the same poorly refreshed air. Acquisition duration and sampling independence must be measured rather than inferred from frame count.

## Checking both optical windows

The revised design checks both exposed optical paths. A deposit on W1 matters before it blocks the beam completely: it can attenuate, redirect, defocus, or scatter the outgoing light. Contamination on W2 can similarly alter the collected signal.

The proposed diagnostic sequence is:

1. **W1 check:** C1 observes the relevant illuminated footprint while L1 is on, comparing its spatial pattern and intensity with a clean baseline.
2. **W2 check:** L1 is off; L2 illuminates W2 and C2 records a separate diagnostic exposure, with its own background reference and appropriate gain.
3. **Quality decision:** compare both diagnostics with experimentally validated acceptance limits.

Imaging could distinguish contamination within a critical optical footprint from a deposit elsewhere. Full cameras are not mandatory, however: small segmented detectors or photodiodes may suffice if spatial detail adds little value.

C2’s two jobs remain an engineering question. Collecting weak particle scattering and inspecting a nearby window may need different focus, gain, exposure, or collection paths. A selected image region alone cannot guarantee separation from glare. The physical baffle must also preserve the required diagnostic view of W2.

The initial purpose is **acceptance, rejection, and a cleaning prompt**. A reflected “dirt signal” does not uniquely reveal transmission loss or measurement error. An absorbing film, reflective dust, and a clear droplet can produce very different relationships between diagnostic return and particle sensitivity. Numerical stain compensation would require separate validation across those conditions. A clean-looking diagnostic is not automatically proof of an unaffected optical path.

L1 and L2 are intended to operate in separate time slots at the same wavelength. Their different animation colors identify functions. Separate wavelengths would introduce another calibration question. L2’s power can be chosen for its own diagnostic exposure rather than made arbitrarily weak to avoid a simultaneous particle measurement.

## Separating useful light from reflections

The beam trap must absorb the transmitted main beam behind W2; transparent glass itself is not a beam stop. The receiver’s useful view should avoid the trap and direct window-interception spot.

Proposed refinements include a receiver lens and field stop, wavelength-appropriate coatings, opaque isolation, and surfaces characterized at the actual laser wavelength. A surface that looks black in visible light may still reflect strongly at another wavelength. Internal separation also cannot remove every stray path through the exposed channel.

Keeping the main beam below the rim is helpful, but reflected light, window contamination, and water can change accessible emission. The complete optical assembly needs laser-safety assessment. The model specifies no validated power, wavelength, divergence, tolerance, or safety classification.

## Air exchange and wrist motion

The open-through channel is intended to encourage passive sample renewal while avoiding a deep pocket that retains air, droplets, or deposits. No fan is assumed, and illustrated particle motion does not establish constant flow.

Motion sensors could request additional measurements after wrist movement or a change of environment. They cannot establish local airflow: orientation, wind, sleeves, the wrist, and recirculation around the housing all matter. A stationary watch can encounter moving air; a moving watch can remain sheltered.

A sensible candidate schedule would retain occasional stationary readings, add motion-triggered acquisitions, allow each acquisition to finish, and defer measurements during known invalid conditions. Recording only active periods would leave a selectively sampled history that could miss exposure while sitting or resting.

If the chosen measurement method requires air velocity, it needs optical velocity estimation, characterized flow, or another validated sampling model. An accelerometer trigger cannot substitute for that information.

## From scattered light to a particulate estimate

This optical channel targets particles. It does not provide a complete measurement of gaseous pollutants. A PM2.5 value would be an inferred mass concentration, not a direct weighing of collected material. Optical sensor response and environmental influences require calibration; [EPA’s Enhanced Air Sensor Guidebook](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1017AWL.TXT) provides relevant background.

Two processing routes remain open:

- **Particle counting:** detect individual events and relate them to detection efficiency and effective sampled air volume.
- **Bulk scattering:** infer concentration from aggregate scattered light in a defined optical volume, using a calibrated response.

Either route must address particle size, composition, optical properties, and representative sampling. Humidity can change airborne particles as well as wet the windows; these are separate effects. Ambient temperature and humidity sensing near the channel would be useful, with placement that limits body and electronics heating.

The first defensible output would describe conditions at the wrist. Interpreting it as inhaled exposure requires comparison with a breathing-zone reference.

## Operating states and wearable integration

A proposed user interface would distinguish **acquiring**, **valid reading**, **unavailable**, and **clean the windows**, with a timestamp and quality information. Invalid or stale data should not silently appear as a current low-pollution reading.

Immersion should suspend air measurements. After drainage and drying, both window checks must pass before measurements resume. Manual wiping is the initial cleaning approach; the concept includes no demonstrated automatic cleaning mechanism.

The watch could supply processing, logging, display, connectivity, and motion context, but this design calls for dedicated optical hardware. Reusing existing health sensors or iPhone depth hardware has not been demonstrated here as a software-only route.

Packaging must still accommodate seals, electronics, thermal management, optical tolerances, and battery cost. Fanless operation does not imply negligible power, especially with two imaging receivers. An optional source-monitor photodiode could track laser-output drift, but one placed before W1 would not detect transmission loss on W1 itself.

## Other approaches considered

My original alternative placed the optics in a darker speaker-adjacent cavity, using speaker motion to exchange air and potentially clean the windows. That remains a separate experiment: an acoustic opening does not establish representative particle transport, and oscillation does not automatically provide fresh samples. Apple documents [speaker water ejection using tones](https://support.apple.com/en-au/108352); this does not demonstrate cleaning of optical-window oil, salt, or dust. A purpose-built air mover or window-coupled actuator would need its own tests.

A commercial comparison is [Bosch’s BMV080](https://www.bosch-sensortec.com/en/products/environmental-sensors/particulate-matter-sensor/bmv080), a compact fanless sensor. Its [datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmv080-ds000.pdf) describes particle counts and relative particle velocities in free space. This is a different optical architecture; its performance cannot be assigned to this recess design.

Bosch’s [wearables page](https://www.bosch-sensortec.com/en/applications-solutions/wearables) also shows an exploded **smartwatch** illustration and animation identifying the BMV080 for PM2.5 monitoring. I reference it as Bosch’s smartwatch application example: the page does not identify a retail watch model or document a working hardware demonstrator.

Apple’s [portable particulate-sensor patent](https://patents.google.com/patent/US10788308B2/en) and [contamination-detection patent](https://patents.google.com/patent/US11680788B2/en) also explore external sensing and identifying unwanted returns. They are useful technical references, not evidence that this concept is new, validated, or planned for a future Apple product.

## What needs to be tested

The next useful step is a larger bench prototype, before watch-scale integration:

- **Optical separation:** filtered air with clean and dirty windows, isolating false signals from the device itself.
- **Sensitivity:** known particles, low concentrations, and different aerosol types, including loss of signal through dirty optics.
- **Lighting:** direct sun, changing angles, shade, and flickering indoor light.
- **Contamination:** W1 alone, W2 alone, then both; fingerprints, sunscreen, dust, salt residue, and droplets.
- **Sampling:** still air, controlled flow, wrist-like movement, different orientations, and sleeves.
- **Recovery and endurance:** wetting, drying, cleaning, temperature changes, and repeated use.
- **Energy and availability:** measurement schedules, response time, missed peaks, and the fraction of time readings remain valid.

Calibration and diagnostic thresholds should be evaluated on independent test cases, with a suitable reference instrument. Report bias, repeatability, response and recovery time, rejection reasons, and energy per useful reading. The goal is to establish when the sensor can provide a trustworthy result and when it should withhold one.

## How to read the animation

The 174-second mechanism film illustrates structure, clean-window particle sensing, contamination of both windows, separate inspection phases, rejection, cleaning, and rechecking. The shorter structural GIFs show the layout rather than this full sequence. Neither depicts a calibrated threshold or proves the optical arrangement works.

Mint represents primary illumination, amber the W2 diagnostic, and blue camera collection paths. Particles are enlarged. The outlined air region is illustrative, not a calibrated sampling volume. Faint dashed routes explain paths hidden by opaque hardware; they do not show light passing through solid parts. Timing is slowed for explanation.

The cutaway removes housing sections for visibility. Filters, focusing arrangements, timing electronics, calibration software, sealing performance, and manufacturing details remain development work. This is a concept visualization, not manufacturer CAD, medical equipment, or a certified laser assembly.

## References

Existing patents, sensor products, and smartwatch application examples are part of the context for this design study. These references acknowledge that work and the technical guidance cited above. My proposed layout and animation remain an unvalidated concept.

1. **Bosch Sensortec. [Sensing solutions for wearables](https://www.bosch-sensortec.com/en/applications-solutions/wearables).** Smartwatch application illustration and [embedded animation](https://www.bosch-sensortec.com/media/boschsensortec/wearables/res/wearables_video.mp4) featuring the BMV080 particulate sensor. This is the smartwatch example discussed above; the page does not establish a retail smartwatch product.
2. **Bosch Sensortec. [Particulate matter sensor BMV080](https://www.bosch-sensortec.com/en/products/environmental-sensors/particulate-matter-sensor/bmv080).** Existing commercial sensor product used for comparison with the proposed optical recess.
3. **Bosch Sensortec. [BMV080 Ultra-mini Particulate Matter Sensor — Datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmv080-ds000.pdf).** Revision 1.4, August 2025; document BST-BMV080-DS000-12, section 1.3. Describes the fanless measurement principle using particle counts and relative particle velocities in free space.
4. **Apple Inc. [Particulate matter sensors for portable electronic devices](https://patents.google.com/patent/US10788308B2/en).** US10788308B2, granted September 29, 2020. Published patent reference for compact, external particulate sensing.
5. **Apple Inc. [Handling obstructions and transmission element contamination for self-mixing particulate matter sensors](https://patents.google.com/patent/US11680788B2/en).** US11680788B2, granted June 20, 2023. Published patent reference for detecting obstructions and contaminated optical transmission elements.
6. **Luis Orozco, Analog Devices. [Optimizing Precision Photodiode Sensor Circuit Design](https://www.analog.com/en/resources/technical-articles/optimizing-precision-photodiode-sensor-circuit-design.html).** August 1, 2014. Background on modulation and synchronized detection for reducing ambient-light interference.
7. **Hamamatsu Photonics. [Si photodiodes](https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/99_SALES_LIBRARY/ssd/si_pd_kspd9001e.pdf), technical note.** Section 2-4, Noise characteristics. Background on photocurrent-dependent shot noise.
8. **U.S. Environmental Protection Agency. [The Enhanced Air Sensor Guidebook](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1017AWL.TXT).** EPA/600/R-22/213, September 2022. Background on sensor performance, environmental influences, collocation, correction, and data quality.
9. **Apple Support. [How to use Water Lock and eject water from your Apple Watch](https://support.apple.com/en-au/108352).** Published September 19, 2026. Documents speaker water ejection using tones, the limited comparison used in the alternative cavity discussion.

Sources checked October 13, 2026. Manufacturer illustrations and patent disclosures are credited as references, without implying manufacturer endorsement or validation of this design.
