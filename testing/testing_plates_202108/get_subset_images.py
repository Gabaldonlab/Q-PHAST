#!/usr/bin/env python

# gets a subset of the images
import os, numpy

raw_images_dir = "./raw_images"
processed_images_dir = "./previous_processed_images"
for f in [raw_images_dir, processed_images_dir]: 
	if not os.path.isdir(f): os.mkdir(f)

for plate_set in os.listdir("./all_raw_images"):
	print("\n\n", plate_set)

	# make folders
	for d in [raw_images_dir, processed_images_dir]:
		full_d = "%s/%s"%(d, plate_set)
		if not os.path.isdir(full_d): os.mkdir(full_d)

	# get all images
	all_images_raw = sorted([x for x in os.listdir("all_raw_images/%s"%plate_set) if x.startswith("_0_")])
	all_images_processed = sorted([x for x in os.listdir("all_processed_images/%s"%plate_set) if x.startswith("_0_")])
	shared_images = set(all_images_raw).intersection(set(all_images_processed))

	# check that they are the same
	if len(set(all_images_processed).difference(set(all_images_raw)))>0: raise ValueError("missing raw images")
	#print("images missing in processed", set(all_images_raw).difference(set(all_images_processed)))
	print("There are %i/%i shared images"%(len(shared_images), len(all_images_raw)))


	# get, from the shared images (from 24h), only 5 for eaach
	def get_sorting_tuple(x):

		ymd = x.split("_")[2]
		t = x.split("_")[3].split(".")[0]
		tuple_x = tuple([int(val) for val in [ymd[0:4], ymd[4:6], ymd[6:], t[0:2], t[2:]]])
		return tuple_x

	sorted_shared_images = sorted(shared_images, key=get_sorting_tuple)

	# keep only a subset of 5 images
	final_images = [sorted_shared_images[int(idx)] for idx in numpy.linspace(0, len(sorted_shared_images)-1, 5)]

	# keep these
	for image in final_images:
		print(image)

		out_stat = os.system("rsync all_raw_images/%s/%s %s/%s/%s"%(plate_set, image, raw_images_dir, plate_set, image))
		if out_stat!=0: error_in_cmd

		out_stat = os.system("rsync all_processed_images/%s/%s %s/%s/%s"%(plate_set, image, processed_images_dir, plate_set, image))
		if out_stat!=0: error_in_cmd
