import json
import matplotlib.pyplot as plt
import numpy


tracks = {"x":[], "y":[], "ids":[]}
colors = list("rgbcmyk")

plt.figure(figsize=(10,8))
plt.title('Pedestrians tracks', fontsize=20)
plt.xlabel('x', fontsize=1)
plt.ylabel('y', fontsize=1)


with open('/home/mz54t/Desktop/TensorFlow2/CCTV_Project/tensorflow_object_counting_api/data_backup.json') as f:
    data = json.load(f)
    
# display scatter plot data


for ids, coord in data.items():
    #print(coord)
    for points in coord:
        tracks["x"].append(points[0])
        tracks["y"].append(-points[1])
        tracks["ids"].append(ids)
    plt.scatter(tracks["x"], tracks["y"], color=numpy.random.rand(len(tracks["ids"]),3), s = 0.1, linewidths=1)
    #plt.pause(1)



plt.show()
