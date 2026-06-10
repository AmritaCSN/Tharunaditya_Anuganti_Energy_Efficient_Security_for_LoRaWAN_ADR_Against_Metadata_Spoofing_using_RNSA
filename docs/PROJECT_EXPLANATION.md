# Project Explanation: Energy Efficient Security for LoRaWAN ADR Against Metadata Spoofing

---

## What This Project Is About

LoRaWAN is a wireless protocol designed for IoT devices that run on small batteries for months or years. It uses a mechanism called **Adaptive Data-Rate (ADR)** to automatically choose the best radio settings for each device — specifically the **Spreading Factor (SF)**, which controls the trade-off between range and power consumption.

The central question this project investigates is:

> *Can a compromised gateway manipulate ADR to silently degrade the network's performance — and can we defend against it without changing devices or the protocol itself?*

---

## The Vulnerability — How ADR Can Be Exploited

### How ADR Works Normally

Each LoRaWAN gateway that receives a device's packet reports the measured Signal-to-Noise Ratio (SNR) to the Network Server. The Network Server collects a history of the last 20 received packets and uses the SNR to decide whether to assign the device a lower or higher Spreading Factor. A higher SNR reading means the signal is strong and clean, so the server pushes the device to a lower SF (e.g. SF7). A lower SF means faster transmission and less energy used per packet — which is the network's normal efficiency goal.

### The Attack — SNR Inflation

The vulnerability is that ADR **trusts the gateway's SNR report unconditionally**. A compromised gateway can report a falsely high SNR value to the Network Server — claiming the device's signal is much stronger than it actually is.

**What the attacker gains:** The Network Server, believing the device has an excellent signal, assigns it the lowest SF (SF7). But the device's true signal quality requires a higher SF (e.g. SF9 or SF11) to be decoded reliably. The device dutifully switches to SF7 and starts transmitting — but those packets cannot be decoded because the true channel is too noisy for SF7. The result is **silent packet loss**: the device thinks it is transmitting successfully, but the Network Server cannot decode the frames.

This is called an **SNR-inflation attack** and it requires only gateway firmware compromise — no physical channel manipulation, no device compromise, no changes to the network topology.

---

## Why We Started with the Wrong Attack Direction

Initially the experiment was configured with the attacker **reducing** the reported SNR (a deflation attack, using negative offsets like −20 dB). The intuition was that reporting a weaker signal would cause the Network Server to assign a higher SF, wasting energy. However, when results were analysed, the defense showed identical performance to the attack — meaning the defense was doing nothing.

**Why deflation doesn't work as expected:** In the deflation scenario, the malicious gateway at the center reports a weak signal. The Network Server's BFT median then picks a value from one of the honest corner gateways — but those gateways are physically far from the node cluster and also report weak signals (due to distance). So the defense and the attack both converge on the same weak SNR, producing no measurable difference.

The insight that unlocked the correct experiment design:

> *The attack direction that actually harms the network is **inflation**, not deflation. Inflation forces devices down to SF7, where packets fail silently. Deflation pushes devices up to higher SFs, which wastes energy but packets still arrive.*

Once the attack was corrected to positive offsets (+20 dB, +40 dB), the attack immediately showed a dramatic PDR drop — from 87% to around 44%.

---

## The Defense — ADR-Secure (BFT Median)

### The Core Idea

Instead of trusting the single "best" gateway's SNR report, the Network Server collects SNR reports from **all** gateways that received the uplink and computes the **median** value. The median has a well-known mathematical property called a **breakdown point of 0.5**: you cannot shift the median by changing any strict minority of the values. This is why it is called **Byzantine Fault Tolerant (BFT)**.

With three gateways (N=3) and one attacker (K=1), the sorted SNR values are `[low, middle, high]`. The median is always the middle value. Even if the attacker pushes their value to infinity, the middle position still belongs to an honest gateway. So the Network Server always receives a realistic SNR and assigns the correct SF.

The defense is implemented entirely at the Network Server — no changes needed to devices, gateways (honest or malicious), the join procedure, or the LoRaWAN protocol itself. It activates based on a single configuration parameter.

### The Theoretical Bound

BFT median only works when the attacker controls a **strict minority** of gateways:
- K=1 out of N=3: defense works (attacker controls 1 of 3 positions — minority)
- K=2 out of N=3: defense fails (attacker controls 2 of 3 positions — majority, can control the median)

This bound is not a weakness to hide — it is a fundamental result from distributed systems theory (Byzantine generals problem, Lamport 1982). We deliberately simulate the K=2 scenario to confirm the bound holds experimentally, which strengthens the paper by showing honest results rather than hiding the limitation.

---

## The Critical Engineering Problem — Coverage Overlap

After implementing the BFT median defense and running the corrected (positive offset) simulations, we found the defense still showed identical results to the attack. This required deeper investigation.

### Root Cause

All 100 devices are clustered near the centre of the simulation area, close to the malicious gateway. The honest gateways are placed at distant corner positions. At SF7 (which the attack forces devices onto), the radio range is limited. The honest corner gateways are too far away to receive the devices' SF7 packets.

The consequence: every uplink is received by **only one gateway** — the nearby malicious one. The BFT median requires at least two gateways to compare. If only one gateway received the packet, there is nothing to compute a median over, and the security check is bypassed entirely.

Even worse: the inflated SNR from that single malicious gateway was still being recorded into each device's ADR history every packet. After 20 packets, the history is completely poisoned with inflated values, and the ADR algorithm confidently assigns SF7.

### The Fix — Conservative Single-Source Policy

The solution is a **conservative abstention rule**: when a packet is received by only one gateway in secure mode, the Network Server simply skips updating that device's ADR history for that packet. The device keeps its current SF assignment until enough multi-gateway, verifiable packets have accumulated.

**Why this is the correct security decision:**
- A single gateway's report is unverifiable — it could be honest or inflated
- Skipping the update is harmless: a device performing well at its current SF continues to do so
- A device that needs a higher SF simply waits slightly longer for trustworthy ADR guidance
- The BFT bound is preserved: K=2 attacks still work (confirming the theoretical limit)

This policy reflects a fundamental principle in security engineering: **when in doubt, abstain rather than trust an unverifiable source**.

---

## What Each Experiment Measures and Why

### 1. Baseline (1 gateway, no attacker)
Establishes the honest-network performance ceiling: PDR ≈ 87%, average SF ≈ 7.47. All subsequent results are compared to this.

### 2. Attack (2 gateways, K=1 malicious, ADR-Avg)
Demonstrates the vulnerability. The malicious gateway inflates SNR by +20 dB or +40 dB. PDR drops to ~44% because devices are pushed to SF7 and cannot be decoded. This is the harm the paper is quantifying.

### 3. Defense (3 gateways, K=1 malicious, ADR-Secure)
Demonstrates the fix. With one honest gateway in range, BFT median fires for multi-gateway packets. The inflated report is rejected. PDR recovers toward baseline. The +20 dB and +40 dB variants both demonstrate robustness.

### 4. BFT Bound Verification (3 gateways, K=2 malicious, both ADR methods)
Deliberately breaks the defense by exceeding the theoretical tolerance. Both ADR-Avg and ADR-Secure show the same degraded PDR, confirming the bound is tight. This is an honest negative result that validates the theoretical model.

---

## Why Five Seeds Per Configuration

Each configuration is run 5 times with different random seeds (random node positions, channel realisations, traffic patterns). This gives statistical confidence that results are not due to a single lucky or unlucky placement. The two offset values (+20 dB and +40 dB) give a total of 10 runs per configuration, 60 runs across all 6 configurations.

---

## Why We Use Simulation Rather Than a Real Testbed

1. **Reproducibility:** Exact same scenario can be re-run, varied, and controlled
2. **Scale:** Deploying 100 battery-powered nodes over a real urban area is expensive and slow
3. **Ground truth:** The simulator gives direct access to the true SNR, true SF, exact packet counts — impossible to measure cleanly in a live network
4. **Safety:** Deliberately injecting attacks into a real LoRaWAN deployment would be illegal and harmful to real users

The FLoRa simulator running on OMNeT++ is the standard academic platform for LoRaWAN research and has been used in published IEEE and ACM papers.

---

## Summary of What Was Proven

| Claim | Evidence |
|-------|---------|
| SNR-inflation attack causes significant PDR loss | PDR drops from 87% to 44% under +20 dB attack |
| Higher inflation causes more harm | +40 dB shows equal or worse PDR than +20 dB |
| BFT median of gateway reports defends against K=1 attacker | Defense PDR recovers toward baseline for K=1 |
| Defense fails when attacker controls majority (K ≥ N/2) | K=2 defense PDR equals K=2 attack PDR — bound is tight |
| Defense introduces no overhead for honest networks | Baseline PDR unchanged when no malicious gateway present |

---

## Key Conceptual Contributions

1. **Identification of the threat:** SNR metadata from gateways is not authenticated. Any compromised gateway can manipulate ADR for all devices that receive it best — a realistic adversary model.

2. **Minimal defense design:** The entire defense is a change to one function in the Network Server. No protocol changes, no device firmware updates, no additional messages on air.

3. **Conservative single-source policy:** The insight that unverifiable single-gateway packets should not drive ADR updates is novel. It extends BFT median to deployment scenarios where gateways have non-overlapping coverage — which is the common real-world case, not the exception.

4. **Honest bound confirmation:** Experimentally validating that the defense fails at K=2 is as important as showing it works at K=1. It shows the result is not an artefact of the simulator but matches the theoretical prediction precisely.
