# Trash_Level_Detector
The project mainly focusses on measuring trash level in the bin, and perrform some analysis with that data. This mainly uses Python, for all the main purpose, and Firebase as a basic backend system to store data.

The project starts, when you show any object to ultra sonic sensor , you have two options to increase lvl of trash in the bin due to that. it'll give both options like manual entry of weight, or detecting a weight according to the distance measured from the sensor. in first option, it just asks the weight when any object is detected , and according to that , it'll update the trash level(Wt/capacity of bin *  100). when 2nd option is choosed, it'll first mesure the distance from the bin, and according to that, it'll update the level.

in the same way, the bin gets filled. whe the bin gets filled (100%), then if you still add trash, it'll automatically unload trash and reaches to 15%, and then it'll add the newly loaded trash. Here, I added some things, that give essence to project, like buzzer sounds when loading , unloading , and when we get warning messages (at 70%, 90% and 100%) in different patterns (like 2 to 3 small beep, one long and one small beep, etc...) 

 after this, the data will be stored in firebase software in a very organised way
