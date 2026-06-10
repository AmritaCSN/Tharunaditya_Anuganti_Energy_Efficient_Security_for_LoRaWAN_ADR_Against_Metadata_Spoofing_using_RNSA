"""Generate N=200 and N=500 INI config files for scalability experiments."""
import random, os

random.seed(42)

SF_WEIGHTS = {7: 0.35, 8: 0.25, 9: 0.15, 10: 0.10, 11: 0.10, 12: 0.05}
TP_OPTIONS = [2, 5, 8, 11, 14]
SFS = list(SF_WEIGHTS.keys())
SF_PROBS = list(SF_WEIGHTS.values())

OUT_DIR = r"C:\omnet-workspace\flora\simulations\examples"

def gen_positions(n, area=500.0):
    return [(round(random.uniform(0, area), 2),
             round(random.uniform(0, area), 2)) for _ in range(n)]

def gen_sf_tp(n):
    return [(random.choices(SFS, weights=SF_PROBS, k=1)[0],
             random.choice(TP_OPTIONS)) for _ in range(n)]

def write_ini(N, cfg_type, positions, sf_tp):
    rn = "${runnumber}"
    ao = "${attackOffset = 20.0, 40.0}"
    ao_ref = "${attackOffset}"

    if cfg_type == "baseline":
        prefix = f"n{N}-3gw-k0-baseline"
        desc = f"{N} nodes / 3 GWs / K=0 baseline (no attack)"
        mal2 = "false"
        adr = '"avg"'
    elif cfg_type == "attack":
        prefix = f"n{N}-3gw-K1-attack"
        desc = f"{N} nodes / 3 GWs / K=1 malicious / ADR-Baseline"
        mal2 = "true"
        adr = '"avg"'
    else:
        prefix = f"n{N}-3gw-K1-defense"
        desc = f"{N} nodes / 3 GWs / K=1 malicious / ADR-Secure"
        mal2 = "true"
        adr = '"secure"'

    lines = []
    lines.append("[General]")
    lines.append(f"# {desc}")
    lines.append("network = flora.simulations.LoRaNetworkTest")
    lines.append(f"output-vector-file = ../results/{prefix}-s{rn}.ini.vec")
    lines.append(f"output-scalar-file  = ../results/{prefix}-s{rn}.ini.sca")
    lines.append("**.maxTransmissionDuration = 4s")
    lines.append("**.energyDetection = -110dBm")
    lines.append("**.vector-recording = false")
    lines.append('rng-class = "cMersenneTwister"')
    lines.append("**.loRaGW[*].numUdpApps = 1")
    lines.append("")

    # GW[0]
    lines.append("# GW[0] - Honest")
    lines.append("**.loRaGW[0].packetForwarder.localPort = 2000")
    lines.append("**.loRaGW[0].packetForwarder.destPort = 1000")
    lines.append('**.loRaGW[0].packetForwarder.destAddresses = "networkServer"')
    lines.append("**.loRaGW[0].packetForwarder.indexNumber = 0")
    lines.append("**.loRaGW[0].packetForwarder.isMalicious = false")
    lines.append("**.loRaGW[0].**.initialX = 125m")
    lines.append("**.loRaGW[0].**.initialY = 125m")
    lines.append("")

    # GW[1]
    lines.append("# GW[1] - Honest")
    lines.append("**.loRaGW[1].packetForwarder.localPort = 2000")
    lines.append("**.loRaGW[1].packetForwarder.destPort = 1000")
    lines.append('**.loRaGW[1].packetForwarder.destAddresses = "networkServer"')
    lines.append("**.loRaGW[1].packetForwarder.indexNumber = 1")
    lines.append("**.loRaGW[1].packetForwarder.isMalicious = false")
    lines.append("**.loRaGW[1].**.initialX = 375m")
    lines.append("**.loRaGW[1].**.initialY = 125m")
    lines.append("")

    # GW[2]
    lines.append("# GW[2] - Malicious (center)")
    lines.append("**.loRaGW[2].packetForwarder.localPort = 2000")
    lines.append("**.loRaGW[2].packetForwarder.destPort = 1000")
    lines.append('**.loRaGW[2].packetForwarder.destAddresses = "networkServer"')
    lines.append("**.loRaGW[2].packetForwarder.indexNumber = 2")
    lines.append(f"**.loRaGW[2].packetForwarder.isMalicious = {mal2}")
    lines.append(f"**.loRaGW[2].packetForwarder.snrOffset  = {ao}")
    lines.append(f"**.loRaGW[2].packetForwarder.rssiOffset = {ao_ref}")
    lines.append("**.loRaGW[2].**.initialX = 250m")
    lines.append("**.loRaGW[2].**.initialY = 375m")
    lines.append("")

    # NS
    lines.append("**.networkServer.numApps = 1")
    lines.append("**.networkServer.**.evaluateADRinServer = true")
    lines.append('**.networkServer.app[0].typename = "NetworkServerApp"')
    lines.append('**.networkServer.app[0].destAddresses = "loRaGW[0] loRaGW[1] loRaGW[2]"')
    lines.append("**.networkServer.app[0].destPort = 2000")
    lines.append("**.networkServer.app[0].localPort = 1000")
    lines.append(f"**.networkServer.app[0].adrMethod = ${{{adr}}}")
    lines.append("")

    # Common params
    lines.append("**.numberOfPacketsToSend = 0")
    lines.append(f"**.numberOfNodes = {N}")
    lines.append("**.numberOfGateways = 3")
    lines.append("sim-time-limit = 1d")
    lines.append("simtime-resolution = -11")
    lines.append("repeat = 5")
    lines.append("**.timeToFirstPacket = exponential(1000s)")
    lines.append("**.timeToNextPacket = exponential(1000s)")
    lines.append("**.alohaChannelModel = false")
    lines.append("**.loRaNodes[*].**.initFromDisplayString = false")
    lines.append("**.loRaNodes[*].**.evaluateADRinNode = true")
    lines.append("**.loRaNodes[*].**initialLoRaBW = 125 kHz")
    lines.append("**.loRaNodes[*].**initialLoRaCR = 4")
    lines.append("**.loRaNodes[*].numApps = 1")
    lines.append('**.loRaNodes[*].app[0].typename = "SimpleLoRaApp"')
    lines.append("**.LoRaGWNic.radio.iAmGateway = true")
    lines.append("**.loRaGW[*].**.initFromDisplayString = false")
    lines.append('**.loRaNodes[*].LoRaNic.radio.energyConsumer.typename = "LoRaEnergyConsumer"')
    lines.append('**.loRaNodes[*].**.energySourceModule = "^.IdealEpEnergyStorage"')
    lines.append('**.loRaNodes[*].LoRaNic.radio.energyConsumer.configFile = xmldoc("../energyConsumptionParameters.xml")')
    lines.append("**.sigma = 3.57")
    lines.append("**.constraintAreaMinX = 0m")
    lines.append("**.constraintAreaMinY = 0m")
    lines.append("**.constraintAreaMinZ = 0m")
    lines.append("**.constraintAreaMaxZ = 0m")
    lines.append("LoRaNetworkTest.**.radio.separateTransmissionParts = false")
    lines.append("LoRaNetworkTest.**.radio.separateReceptionParts = false")
    lines.append('**.ipv4Delayer.config = xmldoc("../cloudDelays.xml")')
    lines.append('**.radio.radioMediumModule = "LoRaMedium"')
    lines.append('**.LoRaMedium.pathLossType = "LoRaLogNormalShadowing"')
    lines.append("**.minInterferenceTime = 0s")
    lines.append("**.displayAddresses = false")
    lines.append("**.constraintAreaMaxX = 500.0m")
    lines.append("**.constraintAreaMaxY = 500.0m")
    lines.append("")

    # Node positions
    lines.append(f"# ---- Node positions ({N} nodes, uniform random in 500x500m) ----")
    for i, (x, y) in enumerate(positions):
        lines.append(f"**.loRaNodes[{i}].**.initialX = {x}m")
        lines.append(f"**.loRaNodes[{i}].**.initialY = {y}m")
    lines.append("")

    # SF/TP
    lines.append(f"# ---- Initial SF/TP ({N} nodes) ----")
    for i, (sf, tp) in enumerate(sf_tp):
        lines.append(f"**.loRaNodes[{i}].**initialLoRaSF = {sf}")
        lines.append(f"**.loRaNodes[{i}].**initialLoRaTP = {tp}dBm")

    fname = f"{prefix}.ini"
    fpath = os.path.join(OUT_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[CREATED] {fname}  ({N} nodes, {len(lines)} lines)")

# Generate same positions for all config types at same N
for N in (200, 500):
    random.seed(N * 7919)
    positions = gen_positions(N)
    sf_tp = gen_sf_tp(N)
    for cfg_type in ("baseline", "attack", "defense"):
        write_ini(N, cfg_type, positions, sf_tp)

print("\nDone — 6 INI files created.")
