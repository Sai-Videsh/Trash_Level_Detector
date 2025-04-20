# Trash_Level_Detector
The project mainly focuses on measuring trash level in the bin, and perrform some analysis with that data. This mainly uses Python, for all the main purpose, and Firebase as a basic backend system to store data.

The project starts, when you show any object to ultra sonic sensor , you have two options to increase lvl of trash in the bin due to that. it'll give both options like manual entry of weight, or detecting a weight according to the distance measured from the sensor. in first option, it just asks the weight when any object is detected , and according to that , it'll update the trash level(Wt/capacity of bin *  100). when 2nd option is choosed, it'll first mesure the distance from the bin, and according to that, it'll update the level.

in the same way, the bin gets filled. whe the bin gets filled (100%), then if you still add trash, it'll automatically unload trash and reaches to 15%, and then it'll add the newly loaded trash. Here, I added some things, that give essence to project, like buzzer sounds when loading , unloading , and when we get warning messages (at 70%, 90% and 100%) in different patterns (like 2 to 3 small beep, one long and one small beep, etc...) 

 after this, the data will be stored in firebase software in a organised manner. then the data will be collected from Firebase and plot graphs and a pie Chart on that data. For some security reasons, Packet Encryption is also enabled, like using cryptography module , the data while sending and collecting from firebase, it'll be encrypted with a header, that prevents from misuse of packets from others.

files and their use:\n
  \twaste_detec.py : main file , that operate wiht IOT pro kit and connect sensors with software\n
  graph.py: for showing some visual data interpretation
  current_level.txt : this shows the current updated level of trash can
  secret.key : a .key file downloaded from firebase
  trash_data.db : a database file, that shows the encrypted dadta that is extracted from firebase
  trash_data_1.xlsx : this shows the decrypted information , of that database file
  ESIOT_connections.jpg : the image of the connections in IoT pro kit , with sensors and raspberry pi card
  trash_level.......  .json : this is the file downloaded from firebase , that have the stored data in object form
