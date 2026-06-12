# Bar-Graph-Generator

## What It Does

Takes user input data and turns it into a bar graph with an optional target line and shaders that will change based on the input values.


## How to use

Place all three files in a common folder.
Replace the file path on line 13 in main.py with your file path.
Run in maya script editor tab.
Replace values and move sliders to match the result you want.

## Project Structure

Bar_Graph_Generator
	Geometry_utils.py	# Geometry creation functions
	Material_utils.py	# Material creation functions based on stats
	main.py	# Main execution file

## Features

- [x] Procedural bar graph generation
- [x] Support for a predefined average line
- [x] UI for the script
- [x] Custom geometry builder functions
- [x] Material assignment based on stat values
- [x] Automatic color assignment
