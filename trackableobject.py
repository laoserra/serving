class TrackableObject:
	def __init__(self, objectID, center):
		# store the object ID, then initialize a list of centroids
		# using the current centroid
		self.objectID = objectID
		self.center = [center]
		# initialize a boolean used to indicate if the object has
		# already been counted or not.
		self.counted = False
