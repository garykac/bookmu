#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt
import os.path
import re
import sys

class Formatter():
	@staticmethod
	def format(str):
		# Handle {_xxx_} for italics.
		m = re.match(r'^(.*)\{_(.+?)_\}(.*)$', str)
		if m:
			pre = m.group(1)
			content = m.group(2)
			post = m.group(3)
			str = Formatter.format(pre)
			str += '<i>' + Formatter.format(content) + '</i>'
			str += Formatter.format(post)

		# Convert 3 or more dashes into a long dash.
		m = re.match(r'^(?P<pre>.*[^-])?(?P<dashes>[-]{3,})(?P<post>[^-].*)?$', str)
		if m:
			pre = m.group('pre')
			dashes = m.group('dashes')
			post = m.group('post')
			str = ''
			if pre:
				str += Formatter.format(pre)
			str += '<span class="longdash">' + ('–' * len(dashes)) + '</span>'
			if post:
				str += Formatter.format(post)
			
		# Handle {/} for line break.
		str = str.replace("{/}", "<br/>")

		# Force non-breaking spaces around some punctuation.
		str = str.replace("« ", "«&nbsp;")
		str = str.replace(" »", "&nbsp;»")

		return str

# Tables are structured as follows:
#   ++-----+-----+-----+   <-- start of table
#   +| x1  | x2  | x3a |   <-- start of row 1 'x'
#    |     |     | x3b |
#   +| y1  | y2  | y3  |   <-- start of row 2 'y'
#   ++-----+-----+-----+   <-- end of table
#
# New rows start with '+|'.
# Cells are separated by '|' (except for start/end table, which use '+')
# Cell data can span multiple rows.
class TableParser():
	"""Parser for table in BookMu."""
	def __init__(self, parser):
		self.parent = parser
		self.reset()

	def reset(self):
		self.data = []
		self.num_cols = 0
		self.formatting = []
		self.reset_row()
	
	def reset_row(self):
		self.curr_row = ['' for i in range(0, self.num_cols)]
		self.valid_row = False

	def start_table(self, line):
		cols = line[2:-1].split('+')
		self.num_cols = len(cols)
		self.reset_row()
	
	def end_table(self):
		self.add_row_to_table()

	def add_row_to_table(self):
		if not self.valid_row:
			return
		self.data.append(self.curr_row)
		self.reset_row()
		
	def add_line_to_row(self, line):
		data = line[2:-1].split('|')
		if len(data) != self.num_cols:
			self.parent.error('Incorrect num of columns in table row')
		for i in range(0, self.num_cols):
			self.curr_row[i] += Formatter.format(data[i])
		self.valid_row = True
	
	# Formatting info:
	# Formatting line has alignment info for each column:
	#   @|H        V|
	#
	# H = horizontal alignment:
	#     '<' (left), ':' (center), '.' (split), '>' (right)
	# V = vertical alignment:
	#     '^' (top), '-' (center), 'v' (bottom)
	#
	# The 'split' horizontal alignment requires that a split point be specified
	# with ':':
	#   @|.    :   v|
	#   +|    20    |
	#   +|  1370    |
	#   +|     0.5  |
	def record_formatting_info(self, line):
		# Ignore formatting info for now.
		pass
		
	# Return True when the last line of the table is read.
	def process_line(self, line):
		m = re.match(r'^\+\+[-+]+\+', line)
		if m:
			self.end_table()
			return True

		if '\t' in line:
			self.parent.error('Tab characters are not allowed in tables')
		
		prefix = line[0:2]
		if prefix == '+|':
			self.add_row_to_table()
		elif prefix == ' |':
			self.add_line_to_row(line)
		elif prefix == '@|':
			self.record_formatting_info(line)
		else:
			self.parent.error('Unrecognized table line')
			
		return False
	
	def generate_html(self):
		html = '<table class="dataTable">'
		for row in self.data:
			html += '<tr>'
			for col in row:
				html += '<td>%s</td>' % re.sub(r'[ \t]+', ' ', col).strip()
			html += '</tr>'
		html += '</table>'
		return html

class Parser():
	"""Build script for parsing BookMu texts."""

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
		
		self.table = TableParser(self)
		self.in_table = False
		
	def error(self, msg):
		print 'Error (line %d): %s' % (self.line_num, msg)
		print 'Line: %s' % self.curr_line
		sys.exit(1)

	def reset_paragraph(self):
		self.in_paragraph = False
		self.paragraph = []

	def reset_note(self):
		self.in_note = False
		self.note = []

	def write_paragraph(self):
		text = ' '.join([x.strip() for x in self.paragraph])
		text = Formatter.format(text)

		if '{' in text or '}' in text:
			self.error("Unhandled { brace }: " + text)
	
		self.paragraph_id += 1
		id = self.paragraph_id
		self.outfile.write('<p id="b%d"><a class="plink" href="#b%d"></a>' % (id, id))
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

	def write_table(self):
		self.outfile.write(self.table.generate_html())
		self.outfile.write('\n')
		
	def record_page_num(self, page_num):
		if self.page_num != None or self.add_page_num:
			self.error('Unprocessed page number: %s' % self.page_num)
		self.page_num = page_num
		self.add_page_num = True
	
	def calc_page_num_link(self):
		if not self.add_page_num:
			self.error('Attempting to add undefined page num')
		p = int(self.page_num)

		# Reset page num when we calc the link.
		self.page_num = None
		self.add_page_num = False

		return '<span class="pagenum" id="pg%d"><a href="#pg%d">[p.%d]</a></span>' % (p, p, p)

	# Process an entire line from the file.
	def process_line(self, line):
		self.line_num += 1
		self.curr_line = line
		line = line.rstrip()

		# Process comments.
		m = re.match(r'^--', line)
		if m:
			# Page number.
			# Note that page numbers can occur in the middle of a paragraph.
			m = re.match(r'^--page (\d+)\s*$', line)
			if m:
				self.record_page_num(m.group(1))
				return

			m = re.match(r'^---$', line)
			if m:
				if self.in_paragraph:
					self.error('Horizontal rule lines may only occur between paragraphs: %s' % line)
				self.outfile.write('<hr/>\n')
				return

			# All other '--' comments are ignored.
			return

		if self.in_table:
			done = self.table.process_line(line)
			if done:
				self.write_table()
				self.in_table = False
			return
		
		# A figure in the text.
		# Figures are added to the current paragraph. If there is no current paragraph,
		# a new one is started.
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

		# ----------------
		# Frontmatter tags
		# ----------------
		# These should only occur in the frontmatter section at the start of the document.
		
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

		# ---------------
		# Footnote markup
		# ---------------
		# These should only occur within a paragraph.
		
		# Footnotes/endnotes.
		# Must be indented with tab.
		if len(line) != 0 and line[0] == '\t':
 			mNote = re.match(r'^\t\{\^(.+)\^\}$', line)
			if mNote:
				self.note.append(mNote.group(1))
				self.write_note()
				return
			else:
				mNoteStart = re.match(r'^\t\{\^(.+)$', line)
				if mNoteStart:
					self.note.append(mNoteStart.group(1))
					self.in_note = True
					return
				
				mNoteEnd = re.match(r'^\t(.+)\^\}$', line)
				if mNoteEnd:
					self.note.append(mNoteEnd.group(1))
					self.write_note()
					return
			if self.in_note:
				self.note.append(line)
				return;
			
			self.error("Unexpected tab-indent line: " + line)

		# --------------
		# Top-level tags
		# --------------
		# These should only occur outside a paragraph.
		
		# Section heading.
		m = re.match(r'^{section "(.+)"}\s*$', line)
		if m:
			section_name = m.group(1)

			if self.in_paragraph:
				self.error('Section tags may only occur between paragraphs: %s' % line)
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
				self.error('Image tags may only occur between paragraphs: %s' % line)
			self.outfile.write('<a href="img/%s.jpg"><img src="img/%s.png" class="block-image-%s"/></a>\n' % (filename, filename, size))
			return
		
		# ------------
		# Table markup
		# ------------

		m = re.match(r'^\+\+[-+]+\+', line)
		if m:
			# Start new table
			self.in_table = True
			self.table.reset()
			self.table.start_table(line)
			return
		
		# ------------------
		# Paragraph handling
		# ------------------
		# Fall-through case to handle basic paragraph text.
		
		line = line.lstrip()		
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
			self.error('File "%s" doesn\'t exist' % src)

		try:
			infile = open(src, 'r')
		except IOError as e:
			self.error('Unable to open "%s" for reading: %s' % (src, e))

		try:
			outfile = open(dst, 'w')
		except IOError as e:
			self.error('Unable to open "%s" for writing: %s' % (dst, e))

		self.outfile = outfile
		self.write_html_header('City of Carcassonne')
		self.line_num = 0
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
			self.error('Unable to open "%s" for writing: %s' % (dst, e))

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
		print('Error - Unable to open config file "%s": %s' % (file, e))
		sys.exit(1)
	
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
