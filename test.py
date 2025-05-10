import pickle 

# Load the coordinates from the pickle file
with open('output/coordinates_2d.pkl', 'rb') as f:
    coordinates = pickle.load(f) # (3052, 2) shape

import rasterfairy

#xy should be a numpy array with a shape (number of points,2) 
# grid_xy = rasterfairy.transformPointCloud2D(coordinates)
nx = 
grid_assignment = rasterfairy.transformPointCloud2D(tsne, target=(nx, ny))

print("type ", type(grid_xy))
print("")
print(grid_xy)
