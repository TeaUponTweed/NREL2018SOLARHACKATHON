import random
import sys

import shapefile as shp  # Requires the pyshp package
import matplotlib.pyplot as plt

sf = shp.Reader(sys.argv[1])
cmap=plt.get_cmap('magma')
fig, ax = plt.subplots()

for shape in sf.shapeRecords():
    x = [i[0] for i in shape.shape.points[:]]
    y = [i[1] for i in shape.shape.points[:]]
    ax.fill(x, y, color=cmap(random.random()))

plt.show()
