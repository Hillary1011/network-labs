Project 1: Small Enterprise Network with VLANs & Inter-VLAN Routing

🔧 Objective

Design a scalable enterprise LAN using VLAN segmentation and router-on-a-stick.

🧩 Network Requirements

- 1 Router (ISR)
- 2 Layer-2 Switches
- 4 VLANs:
- VLAN 10 – Admin
- VLAN 20 – HR
- VLAN 30 – IT
- VLAN 99 – Management
- Set native VLAN to an unsude vlan
- At least 2 PCs per VLAN
  
⚙️ Technical Requirements
- VLAN creation & naming
- Trunking using 802.1Q
- Inter-VLAN routing
- Static IP addressing
- Switch management IP
- Password protection (console, vty, enable secret)
- 
✅ Validation
- Successful ping between VLANs
- Verify VLANs (show vlan brief)
- Verify trunk (show interfaces trunk)
- Routing verification (show ip route)

📦 Deliverables
- .pkt file
- Network diagram
- README explaining design network