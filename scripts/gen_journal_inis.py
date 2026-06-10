#!/usr/bin/env python3
"""
Generate new INI files for journal-level extension experiments.
Uses n100-gw3-K1-attack.ini as template (common node positions / SF / TP).
Writes to flora/simulations/examples/
"""

import os
import re

TEMPLATE = os.path.join(os.path.dirname(__file__),
    '..', 'flora', 'simulations', 'examples', 'n100-gw3-K1-attack.ini')
OUT_DIR  = os.path.join(os.path.dirname(__file__),
    '..', 'flora', 'simulations', 'examples')

# ─────────────────────────────────────────────────────────────────────────────
# Read template and extract the common tail (from node positions onwards)
# ─────────────────────────────────────────────────────────────────────────────
with open(TEMPLATE, encoding='utf-8') as fh:
    template_text = fh.read()

# Everything from the node-positions comment to end of file
tail_match = re.search(
    r'(# ---- Node positions.*)', template_text, re.DOTALL)
if not tail_match:
    raise RuntimeError("Could not locate node-positions block in template")
COMMON_TAIL = tail_match.group(1)  # includes node positions + SF/TP block

# ─────────────────────────────────────────────────────────────────────────────
# Helper: GW block (one gateway entry)
# ─────────────────────────────────────────────────────────────────────────────
def gw_block(idx, x, y, malicious=False, honest_dest="",
             snr_offset_expr="0.0", rssi_offset_expr="0.0",
             snr_mode=None, snr_min=None, snr_max=None,
             snr_step=None, snr_period=None, total_gw=None):
    """Return the INI lines for a single GW module."""
    if honest_dest == "":
        total_gw = total_gw or (idx + 1)
        honest_dest = " ".join(f"loRaGW[{i}]" for i in range(total_gw))

    lines = [
        f"# GW[{idx}]",
        f"**.loRaGW[{idx}].packetForwarder.localPort = 2000",
        f"**.loRaGW[{idx}].packetForwarder.destPort = 1000",
        f"**.loRaGW[{idx}].packetForwarder.destAddresses = \"networkServer\"",
        f"**.loRaGW[{idx}].packetForwarder.indexNumber = {idx}",
        f"**.loRaGW[{idx}].packetForwarder.isMalicious = {'true' if malicious else 'false'}",
    ]
    if malicious:
        lines.append(f"**.loRaGW[{idx}].packetForwarder.snrOffset  = {snr_offset_expr}")
        lines.append(f"**.loRaGW[{idx}].packetForwarder.rssiOffset = {rssi_offset_expr}")
        if snr_mode and snr_mode != "fixed":
            lines.append(f"**.loRaGW[{idx}].packetForwarder.snrOffsetMode = \"{snr_mode}\"")
            lines.append(f"**.loRaGW[{idx}].packetForwarder.snrOffsetMin  = {snr_min}")
            lines.append(f"**.loRaGW[{idx}].packetForwarder.snrOffsetMax  = {snr_max}")
            if snr_mode == "step":
                lines.append(f"**.loRaGW[{idx}].packetForwarder.snrOffsetStep   = {snr_step}")
                lines.append(f"**.loRaGW[{idx}].packetForwarder.snrOffsetPeriod = {snr_period}")
    lines.append(f"**.loRaGW[{idx}].**.initialX = {x}m")
    lines.append(f"**.loRaGW[{idx}].**.initialY = {y}m")
    lines.append("")
    return "\n".join(lines)


def server_block(gw_count, adr_method, adr_device_margin=10):
    gw_list = " ".join(f"loRaGW[{i}]" for i in range(gw_count))
    return f"""**.networkServer.numApps = 1
**.networkServer.**.evaluateADRinServer = true
**.networkServer.app[0].typename = "NetworkServerApp"
**.networkServer.app[0].destAddresses = "{gw_list}"
**.networkServer.app[0].destPort = 2000
**.networkServer.app[0].localPort = 1000
**.networkServer.app[0].adrMethod = "{adr_method}"
**.networkServer.app[0].adrDeviceMargin = {adr_device_margin}
"""


def common_sim_params(gw_count):
    return f"""**.numberOfPacketsToSend = 0
**.numberOfNodes = 100
**.numberOfGateways = {gw_count}
sim-time-limit = 1d
simtime-resolution = -11
repeat = 5
**.timeToFirstPacket = exponential(1000s)
**.timeToNextPacket = exponential(1000s)
**.alohaChannelModel = false
**.loRaNodes[*].**.initFromDisplayString = false
**.loRaNodes[*].**.evaluateADRinNode = true
**.loRaNodes[*].**initialLoRaBW = 125 kHz
**.loRaNodes[*].**initialLoRaCR = 4
**.loRaNodes[*].numApps = 1
**.loRaNodes[*].app[0].typename = "SimpleLoRaApp"
**.LoRaGWNic.radio.iAmGateway = true
**.loRaGW[*].**.initFromDisplayString = false
**.loRaNodes[*].LoRaNic.radio.energyConsumer.typename = "LoRaEnergyConsumer"
**.loRaNodes[*].**.energySourceModule = "^.IdealEpEnergyStorage"
**.loRaNodes[*].LoRaNic.radio.energyConsumer.configFile = xmldoc("../energyConsumptionParameters.xml")
**.sigma = 3.57
**.constraintAreaMinX = 0m
**.constraintAreaMinY = 0m
**.constraintAreaMinZ = 0m
**.constraintAreaMaxZ = 0m
LoRaNetworkTest.**.radio.separateTransmissionParts = false
LoRaNetworkTest.**.radio.separateReceptionParts = false
**.ipv4Delayer.config = xmldoc("../cloudDelays.xml")
**.radio.radioMediumModule = "LoRaMedium"
**.LoRaMedium.pathLossType = "LoRaLogNormalShadowing"
**.minInterferenceTime = 0s
**.displayAddresses = false
**.constraintAreaMaxX = 2376.0m
**.constraintAreaMaxY = 1090.0m
"""


def write_ini(fname, header_comment, gw_blocks_str, adr_method, gw_count):
    content = f"""[General]
{header_comment}
network = flora.simulations.LoRaNetworkTest
output-vector-file = ../results/{fname}-s${{runnumber}}.ini.vec
output-scalar-file  = ../results/{fname}-s${{runnumber}}.ini.sca
**.maxTransmissionDuration = 4s
**.energyDetection = -110dBm
**.vector-recording = false
rng-class = "cMersenneTwister"
**.loRaGW[*].numUdpApps = 1

{gw_blocks_str}
{server_block(gw_count, adr_method)}
{common_sim_params(gw_count)}
{COMMON_TAIL}
"""
    path = os.path.join(OUT_DIR, fname + '.ini')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(content)
    print(f"  Wrote {fname}.ini")


# ─────────────────────────────────────────────────────────────────────────────
# GW positions for 3-GW layout (matches existing configs)
# ─────────────────────────────────────────────────────────────────────────────
GW3 = [
    {'x': 350, 'y': 300},  # GW[0]
    {'x': 800, 'y': 800},  # GW[1]
    {'x': 544, 'y': 544},  # GW[2] — center (malicious when K>=1)
]

# 4-GW layout: 3 honest at corners, 1 malicious
GW4 = [
    {'x': 350, 'y': 300},   # GW[0] honest
    {'x': 800, 'y': 800},   # GW[1] honest
    {'x': 200, 'y': 700},   # GW[2] honest
    {'x': 544, 'y': 544},   # GW[3] malicious (K=1) — cluster centre (CORRECTED v2)
]

# 5-GW layout: honest subset + malicious
GW5 = [
    {'x': 350, 'y': 300},   # GW[0] honest
    {'x': 800, 'y': 700},   # GW[1] honest
    {'x': 200, 'y': 700},   # GW[2] honest
    {'x': 680, 'y': 200},   # GW[3] malicious (K=2 and K=3)
    {'x': 544, 'y': 544},   # GW[4] malicious (K=2 and K=3)
]


def build_gw_blocks(gw_positions, malicious_indices,
                    snr_offset_expr="0.0", rssi_offset_expr="0.0",
                    snr_mode="fixed", snr_min=0, snr_max=40,
                    snr_step=5, snr_period=10):
    parts = []
    for idx, pos in enumerate(gw_positions):
        mal = idx in malicious_indices
        parts.append(gw_block(
            idx, pos['x'], pos['y'],
            malicious=mal,
            snr_offset_expr=snr_offset_expr if mal else "0.0",
            rssi_offset_expr=rssi_offset_expr if mal else "0.0",
            snr_mode=snr_mode if mal else "fixed",
            snr_min=snr_min if mal else 0,
            snr_max=snr_max if mal else 40,
            snr_step=snr_step if mal else 5,
            snr_period=snr_period if mal else 10,
            total_gw=len(gw_positions),
        ))
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# 1. ABLATION STUDY — 3 GWs, K=1 (GW[2] malicious), fixed +20/+40 dB
#    Compare: avg (no defense) vs abstain_only vs median_only vs secure
#    The "avg" and "secure" cases are the existing n100-gw3-K1-attack/defense.
# ─────────────────────────────────────────────────────────────────────────────
print("Generating ablation INIs …")

for variant, label in [("median_only", "Median-Only"), ("abstain_only", "Abstain-Only")]:
    gw_str = build_gw_blocks(
        GW3, malicious_indices=[2],
        snr_offset_expr="${attackOffset = 20.0, 40.0}",
        rssi_offset_expr="${attackOffset}",
    )
    write_ini(
        f"n100-gw3-K1-{variant.replace('_', '-')}",
        f"# 100 nodes / 3 GWs / K=1 malicious / ADR Ablation: {label}\n"
        f"# Ablation: tests \"{variant}\" to isolate contribution of each defense component.",
        gw_str,
        adr_method=variant,
        gw_count=3,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. ADAPTIVE ATTACKER — 3 GWs, K=1, step and random modes
#    Paired attack (avg) + defense (secure) per mode.
# ─────────────────────────────────────────────────────────────────────────────
print("Generating adaptive attacker INIs …")

# Step attacker: ramps 0 → 40 dB in 5 dB steps every 20 packets
for adr_m, label_m in [("avg", "attack"), ("secure", "defense")]:
    gw_str = build_gw_blocks(
        GW3, malicious_indices=[2],
        snr_offset_expr="0.0",   # overridden by mode
        rssi_offset_expr="20.0",
        snr_mode="step",
        snr_min=0, snr_max=40, snr_step=5, snr_period=20,
    )
    write_ini(
        f"n100-gw3-K1-adaptive-step-{label_m}",
        f"# 100 nodes / 3 GWs / K=1 malicious / Adaptive Step Attacker / {adr_m}\n"
        f"# Attacker ramps SNR offset 0\u219240 dB (5 dB/20 pkts). adrMethod={adr_m}.",
        gw_str,
        adr_method=adr_m,
        gw_count=3,
    )

# Random attacker: uniform [10, 40] dB per packet
for adr_m, label_m in [("avg", "attack"), ("secure", "defense")]:
    gw_str = build_gw_blocks(
        GW3, malicious_indices=[2],
        snr_offset_expr="0.0",
        rssi_offset_expr="20.0",
        snr_mode="random",
        snr_min=10, snr_max=40,
    )
    write_ini(
        f"n100-gw3-K1-adaptive-random-{label_m}",
        f"# 100 nodes / 3 GWs / K=1 malicious / Adaptive Random Attacker / {adr_m}\n"
        f"# Attacker draws SNR offset uniformly from [10, 40] dB each packet. adrMethod={adr_m}.",
        gw_str,
        adr_method=adr_m,
        gw_count=3,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. GATEWAY DENSITY STUDY
#    N=4 GWs K=1 (25% Byzantine) — within BFT bound
#    N=5 GWs K=2 (40% Byzantine) — within BFT bound
#    N=5 GWs K=3 (60% Byzantine) — beyond BFT bound (security should fail)
# ─────────────────────────────────────────────────────────────────────────────
print("Generating gateway density INIs …")

# 4 GWs, K=1 — GW[3] is malicious
for adr_m, label_m in [("avg", "attack"), ("secure", "defense")]:
    gw_str = build_gw_blocks(
        GW4, malicious_indices=[3],
        snr_offset_expr="${attackOffset = 20.0, 40.0}",
        rssi_offset_expr="${attackOffset}",
    )
    write_ini(
        f"n100-gw4-K1-{label_m}",
        f"# 100 nodes / 4 GWs / K=1 malicious GW (25%) / {adr_m}\n"
        f"# BFT bound: K=1 < N/2=2  \u21d2 defense provably holds.",
        gw_str,
        adr_method=adr_m,
        gw_count=4,
    )

# 5 GWs, K=2 — GW[3] and GW[4] are malicious (40%, within bound)
for adr_m, label_m in [("avg", "attack"), ("secure", "defense")]:
    gw_str = build_gw_blocks(
        GW5, malicious_indices=[3, 4],
        snr_offset_expr="${attackOffset = 20.0, 40.0}",
        rssi_offset_expr="${attackOffset}",
    )
    write_ini(
        f"n100-gw5-K2-{label_m}",
        f"# 100 nodes / 5 GWs / K=2 malicious GWs (40%) / {adr_m}\n"
        f"# BFT bound: K=2 < N/2=2.5  \u21d2 defense provably holds.",
        gw_str,
        adr_method=adr_m,
        gw_count=5,
    )

# 5 GWs, K=3 — GW[2], GW[3], GW[4] malicious (60%, beyond bound)
for adr_m, label_m in [("avg", "attack"), ("secure", "defense")]:
    gw_str = build_gw_blocks(
        GW5, malicious_indices=[2, 3, 4],
        snr_offset_expr="${attackOffset = 20.0, 40.0}",
        rssi_offset_expr="${attackOffset}",
    )
    write_ini(
        f"n100-gw5-K3-{label_m}",
        f"# 100 nodes / 5 GWs / K=3 malicious GWs (60%) / {adr_m}\n"
        f"# BFT bound VIOLATED: K=3 >= N/2=2.5  \u21d2 defense expected to degrade.",
        gw_str,
        adr_method=adr_m,
        gw_count=5,
    )

print("Done. All INI files written to flora/simulations/examples/")
