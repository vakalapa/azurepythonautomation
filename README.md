# azurepythonautomation


This automation illustrates how we can pull available CSR1000v versions from Azure market place and create a quick IPSEC topology with two linux boxes and two CSR1000v as given below

 ________     ________               ________     ________
|        |   |        |             |        |   |        |
| LINUX1 | --|  CSR1  |  -- IPSEC --|  CSR2  |-- | LINUX2 |
|________|   |________|             |________|   |________|


Use either Service Principle login or User Login.

This script is interactive. Usage: python main.py