# A python3 script to run the pipeline from any OS

# imports
import os, sys, argparse

description = """
This is a pipeline to measure antifungal susceptibility from image data in any OS. Run with: 

	In linux and mac: 'python3 main.py --module <module> --os <os> --input <input folder> --output <output folder> --docker_image mikischikora/qcast:<tag>'

	In windows: 'py main.py --module <module> --os <os> --input <input folder> --output <output folder> --docker_image mikischikora/qcast:<tag>'

Check the github repository (https://github.com/Gabaldonlab/qCAST) to know how to use this script.
"""

# arguments              
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--os", dest="os", required=True, type=str, help="The Operating System. It should be 'windows', 'linux' or 'mac'")
parser.add_argument("--module", dest="module", required=True, type=str, help="The module to run. It may be 'get_plate_layout' or 'analyze_images'")
parser.add_argument("--input", dest="input", required=True, type=str, help="The input directory.")
parser.add_argument("--output", dest="output", required=True, type=str, help="The output directory.")
parser.add_argument("--docker_image", dest="docker_image", required=True, type=str, help="The name of the docker image in the format <name>:<tag>. All the versions of the images are in https://hub.docker.com/repository/docker/mikischikora/qcast. For example, you can set '--docker_image mikischikora/qcast:v1' to run version 1.")

opt = parser.parse_args()


print(opt)