#!/usr/bin/env python

# gets a subset of the images
import os, numpy

# make images
raw_images_dir = "./raw_images" # images from the paper
reduced_raw_images = "./subset_raw_images"
if not os.path.isdir(reduced_raw_images): os.mkdir(reduced_raw_images)

for plate_set in os.listdir(raw_images_dir):
	print("\n\n", plate_set)

	# define folders for this set
	raw_images_dir_set = "%s/%s"%(raw_images_dir, plate_set)
	reduced_raw_images_set = "%s/%s"%(reduced_raw_images, plate_set)
	if not os.path.isdir(reduced_raw_images_set): os.mkdir(reduced_raw_images_set)

	# get all images
	all_images_raw = sorted([x for x in os.listdir(raw_images_dir_set) if x.startswith("_0_")])

	# get, from the shared images (from 24h), only 5 for eaach
	def get_sorting_tuple(x):

		ymd = x.split("_")[2]
		t = x.split("_")[3].split(".")[0]
		tuple_x = tuple([int(val) for val in [ymd[0:4], ymd[4:6], ymd[6:], t[0:2], t[2:]]])
		return tuple_x

	sorted_raw_images = sorted(all_images_raw, key=get_sorting_tuple)

	# keep only a subset of 5 images
	final_images = [sorted_raw_images[int(idx)] for idx in numpy.linspace(0, len(sorted_raw_images)-1, 5)]

	# keep these
	for image in final_images:
		print(image)

		out_stat = os.system("rsync %s/%s %s/%s"%(raw_images_dir_set, image, reduced_raw_images_set, image))
		if out_stat!=0: error_in_cmd
