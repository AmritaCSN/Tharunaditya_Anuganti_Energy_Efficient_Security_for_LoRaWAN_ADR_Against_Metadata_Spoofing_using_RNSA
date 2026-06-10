"""Generate n100-3gw-uniform.ini: uniform 1000x1000m deployment."""
import random, os

random.seed(12345)
OUT_DIR = r"C:\omnet-workspace\flora\simulations\examples"

SF_WEIGHTS = {7: 0.35, 8: 0.25, 9: 0.15, 10: 0.10, 11: 0.10, 12: 0.05}
TP_OPTIONS = [2, 5, 8, 11, 14]
SFS = list(SF_WEIGHTS.keys())
SF_PROBS = list(SF_WEIGHTS.values())

positions = [(round(random.uniform(0, 1000), 2),
              round(random.uniform(0, 1000), 2)) for _ in range(100)]
sf_tp = [(random.choices(SFS, weights=SF_PROBS, k=1)[0],
          random.choice(TP_OPTIONS)) for _ in range(100)]

rn = "${runnumber}"
ao = "${attackOffset = 20.0, 40.0}"
ao_ref = "${attackOffset}"
adr_var = '${adrMethod = "avg", "secure"}'

lines = []
lines.append("[General]")
lines.append("# 100 nodes / 3 GWs / K=1 / Uniform 1000x1000m / ADR-Avg + ADR-Secure")
lines.append("network = flora.simulations.LoRaNetworkTest")
lines.append(f"output-vector-file = ../results/n100-3gw-uniform-s{rn}.ini.vec")
lines.append(f"output-scalar-file  = ../results/n100-3gw-uniform-s{rn}.ini.sca")
lines.append("**.maxTransmissionDuration = 4s")
lines.append("**.energyDetection = -110dBm")
lines.append("**.vector-recording = false")
lines.append('rng-class = "cMersenneTwister"')
lines.append("**.loRaGW[*].numUdpApps = 1")
lines.append("")

# GW[0] at (250,250)
lines.append("# GW[0] - Honest (250,250)")
lines.append("**.loRaGW[0].packetForwarder.localPort = 2000")
lines.append("**.loRaGW[0].packetForwarder.destPort = 1000")
lines.append('**.loRaGW[0].packetForwarder.destAddresses = "networkServer"')
lines.append("**.loRaGW[0].packetForwarder.indexNumber = 0")
lines.append("**.loRaGW[0].packetForwarder.isMalicious = false")
lines.append("**.loRaGW[0].**.initialX = 250m")
lines.append("**.loRaGW[0].**.initialY = 250m")
lines.append("")

# GW[1] at (750,250)
lines.append("# GW[1] - Honest (750,250)")
lines.append("**.loRaGW[1].packetForwarder.localPort = 2000")
lines.append("**.loRaGW[1].packetForwarder.destPort = 1000")
lines.append('**.loRaGW[1].packetForwarder.destAddresses = "networkServer"')
lines.append("**.loRaGW[1].packetForwarder.indexNumber = 1")
lines.append("**.loRaGW[1].packetForwarder.isMalicious = false")
lines.append("**.loRaGW[1].**.initialX = 750m")
lines.append("**.loRaGW[1].**.initialY = 250m")
lines.append("")

# GW[2] at (500,750) - Malicious
lines.append("# GW[2] - Malicious (500,750)")
lines.append("**.loRaGW[2].packetForwarder.localPort = 2000")
lines.append("**.loRaGW[2].packetForwarder.destPort = 1000")
lines.append('**.loRaGW[2].packetForwarder.destAddresses = "networkServer"')
lines.append("**.loRaGW[2].packetForwarder.indexNumber = 2")
lines.append("**.loRaGW[2].packetForwarder.isMalicious = true")
lines.append(f"**.loRaGW[2].packetForwarder.snrOffset  = {ao}")
lines.append(f"**.loRaGW[2].packetForwarder.rssiOffset = {ao_ref}")
lines.append("**.loRaGW[2].**.initialX = 500m")
lines.append("**.loRaGW[2].**.initialY = 750m")
lines.append("")

# NS — iterates over both ADR methods
lines.append("**.networkServer.numApps = 1")
lines.append("**.networkServer.**.evaluateADRinServer = true")
lines.append('**.networkServer.app[0].typename = "NetworkServerApp"')
lines.append('**.networkServer.app[0].destAddresses = "loRaGW[0] loRaGW[1] loRaGW[2]"')
lines.append("**.networkServer.app[0].destPort = 2000")
lines.append("**.networkServer.app[0].localPort = 1000")
lines.append(f"**.networkServer.app[0].adrMethod = {adr_var}")
lines.append("")

# Common
lines.append("**.numberOfPacketsToSend = 0")
lines.append("**.numberOfNodes = 100")
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
lines.append("**.constraintAreaMaxX = 1000.0m")
lines.append("**.constraintAreaMaxY = 1000.0m")
lines.append("")

# Node positions
lines.append("# ---- Node positions (100 nodes, uniform random in 1000x1000m) ----")
for i, (x, y) in enumerate(positions):
    lines.append(f"**.loRaNodes[{i}].**.initialX = {x}m")
    lines.append(f"**.loRaNodes[{i}].**.initialY = {y}m")
lines.append("")

# SF/TP
lines.append("# ---- Initial SF/TP ----")
for i, (sf, tp) in enumerate(sf_tp):
    lines.append(f"**.loRaNodes[{i}].**initialLoRaSF = {sf}")
    lines.append(f"**.loRaNodes[{i}].**initialLoRaTP = {tp}dBm")

fpath = os.path.join(OUT_DIR, "n100-3gw-uniform.ini")
with open(fpath, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"[CREATED] n100-3gw-uniform.ini  ({len(lines)} lines)")
