#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Convert a heightmap image file into a text data file.
# This is used as a workaround for System.Drawing.Image not loading correctly in OSX Mono.

import argparse
from PIL import Image  # https://pypi.python.org/pypi/Pillow/2.2.1
import struct
import sys

#  image   scaled
#   imax    smax
#    |       |
#   imin    smin
# scaled = (((orig - imin) / (imax-imin)) * (smax - smin)) + smin

class ConvertImage:
	def __init__(self):
		self.img = None
		self.imgdata = None
		
		# width and height of map
		self.x_size = None
		self.y_size = None

	def open(self, input):
		self.img = Image.open(input)
		
	def grayscale(self):
		# Convert image to greyscale if necessary.
		# For a list of modes, see end of:
		#   http://svn.effbot.org/public/tags/pil-1.1.4/libImaging/Unpack.c
		mode = self.img.mode
		#valid = False
		#if mode == 'RGB' or mode == 'RGBA':
		if mode != 'L':
			self.img = self.img.convert('L')
		#	valid = True
		#if mode == 'I;16' or mode == 'I':
		#	valid = True
		#if not valid:
		#	print 'Unrecognized image format', mode
		print 'Image format', mode, '->', self.img.mode

	def load(self):
		(self.x_size, self.y_size) = self.img.size
		self.imgdata = self.img.load()

	def resize(self):
		max_width = 1000
		(self.x_size, self.y_size) = self.img.size
		if self.x_size > max_width:
			new_y = int(max_width * float(self.y_size) / float(self.x_size))
			self.img = self.img.resize((max_width, new_y))
			(self.x_size, self.y_size) = self.img.size

	def save(self, output, cmdArgs):
		print self.x_size, self.y_size
		img = Image.new('LA', (self.x_size, self.y_size), (0, 0))
		pixels = img.load()
		for y in xrange(0, self.y_size):
			for x in xrange(0, self.x_size):
				val = self.imgdata[x, y]
				#print val
				pixels[x,y] = (0, 255-val)
				
		img.save(output, "PNG")


def main():
	parser = argparse.ArgumentParser(
		description='Load image and convert to XML heightmap')
	parser.add_argument('terrainIn',
		help = 'The name of the input image file to convert to terrain heightmap')
	parser.add_argument('terrainOut',
		help = 'The name of the terrain XML output file')
	args = parser.parse_args()

	conv = ConvertImage()
	conv.open(args.terrainIn)
	conv.grayscale()
	conv.resize()
	conv.load()
	conv.save(args.terrainOut, args)

if __name__ == '__main__':
	main()
