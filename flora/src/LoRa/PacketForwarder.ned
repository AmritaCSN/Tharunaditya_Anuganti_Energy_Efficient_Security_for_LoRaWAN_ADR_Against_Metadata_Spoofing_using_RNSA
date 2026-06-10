//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
// 

package flora.LoRa;


import inet.applications.contract.IApp;

simple PacketForwarder like IApp
{
    @signal[LoRa_GWPacketReceived](type=long); // optional
    @statistic[LoRa_GWPacketReceived](source=LoRa_GWPacketReceived; record=count);
    int localPort = default(-1);  // local port (-1: use ephemeral port)
    string destAddresses = default(""); // list of IP addresses, separated by spaces ("": don't send)
    string localAddress = default("");
    int destPort;
    bool isMalicious = default(false);   // Byzantine attack: tamper with RSSI/SNR before forwarding
    double rssiOffset = default(0.0);    // dBm added to measured RSSI (negative = report weaker signal)
    double snrOffset  = default(0.0);    // dB applied to measured SNR in fixed mode
    // Adaptive attack mode parameters
    string snrOffsetMode   = default("fixed");  // "fixed" | "step" | "random"
    double snrOffsetMin    = default(0.0);       // min dB offset for adaptive modes
    double snrOffsetMax    = default(40.0);      // max dB offset for adaptive modes
    double snrOffsetStep   = default(5.0);       // dB increment per period (step mode)
    int    snrOffsetPeriod = default(10);        // packets forwarded between each step increment

    gates:
        output socketOut @labels(UdpControlInfo/up);
        input socketIn @labels(UdpControlInfo/down);

        input lowerLayerIn @labels(PacketForwarder/up);
        output lowerLayerOut @labels(PacketForwarder/down);  

}