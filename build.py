#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt
import os.path
import re
import sys

def error(msg):
	print 'Error: %s' % (msg)
	sys.exit(1)

class Parser():
	"""Build script for texts"""

	def __init__(self):
		self.page_num = None
		self.add_page_num = False

		self.section_id = 0

		self.paragraph_id = 0
		self.reset_paragraph()

		self.note_id = 0
		self.reset_note()
		
		# Dictionary with count of all words found in doc.
		self.dict = {}
		
	def reset_paragraph(self):
		self.in_paragraph = False
		self.paragraph_class = ""
		self.paragraph = []

	def reset_note(self):
		self.in_note = False
		self.note = []

	# Paragraph level formatting.
	# These formatting marks must be at the beginning/end of the paragraph.
	def paragraph_format(self, str):
		# Handle {"xxx"} for blockquote
		m = re.match(r'^\{"(.+)"\}$', str)
		if m:
			pre = m.group(1)
			content = m.group(2)
			post = m.group(3)
			self.paragraph_class = "blockquote"
			str = self.paragraph_format(content)

		return str

	def format(self, str):
		# Handle {_xxx_} for italics.
		m = re.match(r'^(.*)\{_(.+?)_\}(.*)$', str)
		if m:
			pre = m.group(1)
			content = m.group(2)
			post = m.group(3)
			str = self.format(pre) + '<i>' + self.format(content) + '</i>' + self.format(post)

		# Handle {/} for line break.
		str = str.replace("{/}", "<br/>")

		return str
	
	def write_paragraph(self):
		text = ' '.join([x.strip() for x in self.paragraph])
		text = self.format(text)
		text = text.replace("« ", "«&nbsp;")
		text = text.replace(" »", "&nbsp;»")

		if '{' in text or '}' in text:
			error("Unhandled { brace }: " + text)
	
		self.paragraph_id += 1
		id = self.paragraph_id
		p_class = ""
		if self.paragraph_class == "blockquote":
			p_class = ' class="blockquote"'
		self.outfile.write('<p id="b%d"%s><a class="plink" href="#b%d"></a>' % (id, p_class, id))
		self.outfile.write(text + '</p>\n')

		self.reset_paragraph()

	def write_note(self):
		self.note_id += 1
		note = '<label for="n%d" class="note-label"></label>' % self.note_id
		note += '<input type="checkbox" id="n%d" class="note-checkbox"/>' % self.note_id
		note += '<span class="note">'
		note += ' '.join([x.strip() for x in self.note])
		note += '</span>'
		self.paragraph.append(note)
		self.reset_note()

	def record_page_num(self, page_num):
		if self.page_num != None or self.add_page_num:
			error('Unprocessed page number: %s' % self.page_num)
		self.page_num = page_num
		self.add_page_num = True
	
	def calc_page_num_link(self):
		if not self.add_page_num:
			error('Attempting to add undefined page num')
		p = int(self.page_num)

		# Reset page num when we calc the link.
		self.page_num = None
		self.add_page_num = False

		return '<span class="pagenum" id="pg%d"><a href="#pg%d">[p.%d]</a></span>' % (p, p, p)

	# Process an entire line from the file.
	def process_line(self, line):
		initial_tab = len(line) != 0 and line[0] == '\t'
		line = line.strip()

		# Process comments.
		m = re.match(r'^--', line)
		if m:
			# Page number.
			m = re.match(r'--page (\d+)\s*$', line)
			if m:
				self.record_page_num(m.group(1))
				return

			# All other '--' comments are ignored.
			return

		# A figure in the text.
		# Figures are added to the current paragraph, or a new paragraph
		# is started.
		m = re.match(r'^{figure (large) "(.+)" "(.+)"}\s*$', line)
		if m:
			size = m.group(1)
			caption = m.group(2)
			filename = m.group(3)
			if self.add_page_num:
				self.paragraph.append(self.calc_page_num_link())
			figure = '<span class="figure"><a href="img/%s.jpg"><img class="block-image-%s" src="img/%s.png"/></a><br/><span class="caption">%s</span></span>' % (filename, size, filename, caption)
			self.paragraph.append(figure)
			self.in_paragraph = True
			return

		# A title may only occur in the frontmatter section.
		m = re.match(r'^{title (x-small|small|medium|large) "(.+)"}\s*$', line)
		if m:
			size = m.group(1)
			title = m.group(2)
			self.outfile.write('<div class="title frontmatter-%s"/>%s</div>\n' % (size, title))
			return

		m = re.match(r'^{frontmatter (x-small|small|medium|large) "(.+)"}\s*$', line)
		if m:
			size = m.group(1)
			title = m.group(2)
			self.outfile.write('<div class="frontmatter frontmatter-%s"/>%s</div>\n' % (size, title))
			return

		# Footnotes/endnotes.
		# Must be indented with tab.
		if initial_tab:
 			mNote = re.match(r'^\{\^(.+)\^\}$', line)
			if mNote:
				self.note.append(mNote.group(1))
				self.write_note()
				return
			else:
				mNoteStart = re.match(r'^\{\^(.+)$', line)
				if mNoteStart:
					self.note.append(mNoteStart.group(1))
					self.in_note = True
					return
				
				mNoteEnd = re.match(r'^(.+)\^\}$', line)
				if mNoteEnd:
					self.note.append(mNoteEnd.group(1))
					self.write_note()
					return
			if self.in_note:
				self.note.append(line)
				return;
			
			error("Unexpected tab-indent line: " + line)
				
		# Section heading.
		m = re.match(r'^{section "(.+)"}\s*$', line)
		if m:
			section_name = m.group(1)

			if self.in_paragraph:
				error('Section tags may only occur between paragraphs: %s' % filename)
			self.section_id += 1
			self.outfile.write('<h1 id="s%d">' % (self.section_id))
			if self.add_page_num:
				self.outfile.write(self.calc_page_num_link())
			self.outfile.write('%s</h1>\n' % (section_name))

			return

		# An unnumbered image in the text.
		m = re.match(r'^{image (small) "(.+)"}\s*$', line)
		if m:
			size = m.group(1)
			filename = m.group(2)

			if self.in_paragraph:
				error('Image tags may only occur between paragraphs: %s' % filename)
			self.outfile.write('<a href="img/%s.jpg"><img src="img/%s.png" class="block-image-%s"/></a>\n' % (filename, filename, size))
			return
		
		if line == '':
			if self.in_paragraph:
				self.write_paragraph()
			return

		if self.add_page_num:
			self.paragraph.append(self.calc_page_num_link())

		self.paragraph.append(line)
		self.in_paragraph = True;

	def write_html_header(self, title):
		self.outfile.write('<!DOCTYPE html>\n')
		self.outfile.write('<html lang="en">\n')
		self.outfile.write('<head>\n')
		self.outfile.write('\t<meta charset="utf-8" />\n')
		self.outfile.write('\t<meta http-equiv="X-UA-Compatible" content="IE=edge" />\n')
		self.outfile.write('\t<meta name="viewport" content="width=device-width, initial-scale=1" />\n')
		self.outfile.write('\t<title>%s</title>\n' % title)
		self.outfile.write('\t<link href="https://fonts.googleapis.com/css?family=Old+Standard+TT:400,400italic,700" rel="stylesheet" type="text/css" />\n')
		self.outfile.write('\t<link href="book.css" rel="stylesheet" type="text/css" />\n')
		self.outfile.write('</head>\n')
		self.outfile.write('<body>\n')

		self.outfile.write('<div class="container">\n')

	def write_html_footer(self):
		self.outfile.write('</div>\n')
		self.outfile.write('</body>\n')
		self.outfile.write('</html>\n')

	def process(self, src, dst):
		if not os.path.isfile(src):
			error('File "%s" doesn\'t exist' % src)

		try:
			infile = open(src, 'r')
		except IOError as e:
			error('Unable to open "%s" for reading: %s' % (src, e))

		try:
			outfile = open(dst, 'w')
		except IOError as e:
			error('Unable to open "%s" for writing: %s' % (dst, e))

		self.outfile = outfile
		self.write_html_header('City of Carcassonne')
		for line in infile:
			self.process_line(line)
		self.write_html_footer()

		outfile.close()
		infile.close()

	def add_to_dict(self, word, line):
		# Print entire line for word.
		# Useful for tracking down short typo words.
		#if word == 'hom':
		#	print self.id, line

		if not word in self.dict:
			self.dict[word] = 0
		self.dict[word] += 1

	def write_dict(self):
		dst = 'dict.txt'
		try:
			outfile = open(dst, 'w')
		except IOError as e:
			error('Unable to open "%s" for writing: %s' % (dst, e))

		for word in sorted(self.dict, key=self.dict.get, reverse=True):
			outfile.write('%d %s\n' % (self.dict[word], word))

		outfile.close()

def usage():
	print 'Usage: %s <options>' % sys.argv[0]
	print 'where <options> are:'
	print '  --config <config-file-name>'
	print '  --dict'  # write word frequency dict
	print '  --verbose'  # verbose debug output
	
def load_config(file):
	config = {}
	try:
		config_file = open(file, 'r')
	except IOError as e:
		error('Unable to open config file "%s": %s' % (file, e))
	
	for line in config_file:
		line = line.strip()
		if line == '' or line[0] == '#':
			continue
		(k,v) = line.split('=')
		if v == 'True':
			config[k] = True
		elif v == 'False':
			config[k] = False
		elif ',' in v:
			config[k] = v.split(',')
		else:
			config[k] = v
		
	config_file.close()
	return config

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:],
			'c:dv',
			['config=', 'dict', 'verbose'])
	except getopt.GetoptError:
		usage()
		exit()

	config_file = None
	write_dict = False
	verbose = False
	
	for opt, arg in opts:
		if opt in ('-c', '--config'):
			config_file = arg
		elif opt in ('-d', '--dict'):
			write_dict = True
		elif opt in ('-v', '--verbose'):
			verbose = True

	if config_file:
		config = load_config(config_file)
	else:
		# Default configuration
		config = {}
		config['output_file'] = 'out.html'
	#print config
		
	# The raw input file (with the Plotto text).
	infilename = 'cityofcarcassonn00viol.txt'

	print 'Building', config['output_file'], '...'
	
	parser = Parser()
	parser.process(infilename, config['output_file'])
	if write_dict:
		parser.write_dict()
	
if __name__ == '__main__':
	main()
