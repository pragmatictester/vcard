#!/usr/bin/env python

""" Generate a vCard in the vCard 2.1 file format """
__author__ = "Parul Mathur"
__email__ = "parul@pragmatictester.com"

import sqlite3
import os
import sys
import random
from datetime import datetime, time, timedelta
from PIL import Image, ImageDraw, ImageOps 
import base64
import StringIO


# Construct a United States postal address
class Address:
	street_number = ""
	street_name = ""
	city = ""
	state = ""
	zipcode = ""
	country = ""

	def get_label(self):
		return u"{} {}\\n{}, {} {}\\n{}".format(self.street_number, self.street_name, self.city, self.state, self.zipcode, self.country);

	def __str__(self):
		return u"{} {};{};{};{};{}".format(self.street_number, self.street_name, self.city, self.state, self.zipcode, self.country);


# Construct a vCard in the vCard 2.1 file format
# Reference: http://en.wikipedia.org/wiki/Vcard#vCard_2.1
class Vcard:
	version = "2.1"
	first_name = ""
	last_name = ""
	company = ""
	job_title = ""
	photo = ""
	tel = {"WORK": "", "HOME": ""}
	adr = {"WORK": Address(), "HOME": Address()}
	email = ''
	rev = ''
	
	def __str__(self):
		vcard = u"BEGIN:VCARD\n"
		vcard += "VERSION:%s\n" % self.version 
		vcard += "N:{};{};;;\n".format(self.last_name, self.first_name)
		vcard += "FN:{} {};\n".format(self.first_name, self.last_name)
		vcard += "ORG:%s\n" % self.company
		vcard += "TITLE:%s\n" % self.job_title
		vcard += "TEL;WORK;VOICE:%s\n" % self.tel['WORK']
		vcard += "TEL;HOME;VOICE:%s\n" % self.tel['HOME']
		vcard += "PHOTO;ENCODING=BASE64;TYPE=%s:PNG\n" % self.photo
		vcard += "ADR;WORK:;;%s\n" % self.adr['WORK']
		vcard += "ADR;HOME:;;%s\n" % self.adr['HOME']
		vcard += "EMAIL;HOME:%s\n" % self.email
		vcard += "REV:%s\n" % self.rev
		vcard += "END:VCARD" 
		return vcard

# Query from a sqlite3 database containing data
# sourced from the United States Census Bureau
class RandomVcard:
	
	def __init__(self, con):
		self.con = con

	def get(self):
		vcard = Vcard()
		cur = con.cursor()
		cur.execute("SELECT LastNames FROM LastNames ORDER BY RANDOM() LIMIT 1;");
		vcard.last_name = cur.fetchone()[0]
		cur.execute("SELECT MaleFirstNames FROM MaleFirstNames ORDER BY RANDOM() LIMIT 1;");
		vcard.first_name = cur.fetchone()[0]
		cur.execute("SELECT Company FROM Companies ORDER BY RANDOM() LIMIT 1;");
		vcard.company = cur.fetchone()[0]
		cur.execute("SELECT JobTitle FROM JobTitles ORDER BY RANDOM() LIMIT 1;");
		vcard.job_title = cur.fetchone()[0]
		for k, v in vcard.adr.iteritems():
			vcard.adr[k].street_number = random.randint(10,9999)
			cur.execute("SELECT StreetName FROM StreetNames ORDER BY RANDOM() LIMIT 1;");
			vcard.adr[k].street_name = cur.fetchone()[0]
			cur.execute("SELECT * FROM ZipCityState ORDER BY RANDOM() LIMIT 1;");
			r = cur.fetchone()
			vcard.adr[k].city = r[1]
			vcard.adr[k].state = r[2]
			vcard.adr[k].zipcode = r[0]
			vcard.adr[k].country = "USA";

		for k, v in vcard.tel.iteritems():
			vcard.tel[k] = "+1-{}-{}-{}".format(random.randint(210,999),random.randint(100,999),random.randint(1000,9999))
		
		vcard.email = "{}{}@mail.com".format(vcard.first_name.lower(),random.randint(10,9999))
		t = datetime.now() - timedelta(seconds=random.randint(1000000,99999999))
		vcard.rev = t.strftime("%Y%m%dT%H%I%SZ")
		vcard.photo = self.get_photo(100,100)
		return vcard


	# Generate a random user profile photograph of size 100x100 pixels
	def get_photo(self, width, height):
		img = Image.new( 'RGBA', (width,height)) 
		pixels = img.load() 
		 
		for i in range(img.size[0]):    # for every pixel:
			for j in range(img.size[1]):
				red = random.randint(0,255)
				green = random.randint(0,255)
				blue = random.randint(0,255)
				pixels[j,i] = (red, green, blue) # set the colour 
			
				# Randomize the background with fancy stripes 
				block_x = random.randint(5,49)
				block_y = random.randint(10,90)
				temp_col = i
				for x in range(block_x):
					for y in range(((-1)*block_y),block_y):
						if temp_col - y >= 0:
							if temp_col - y >= img.size[1]:
								pixel_y = (temp_col - y) % img.size[1]
							else:
								 pixel_y = temp_col - y
							
						if temp_col - y < img.size[1]:
							if temp_col - y < 0:
								pixel_y = random.randint(0, img.size[1]-1)
							else:
								 pixel_y = temp_col - y

						if j + y < img.size[0]:
							if j + y < 0:
								pixel_x = random.randint(0, img.size[0]-1)
							else:
								pixel_x = j + y

						if j + y >= 0:
							if j + y >= img.size[0]:
								pixel_x = img.size[0] - 1
							else:
								pixel_x = j + y
							
						pixels[pixel_x,pixel_y] = (red, green, blue) # set the colour 
					j = j + 1 
					temp_col =  temp_col + 1 
		
					
		# Merge the background with a user profile icon
		background = Image.open("user.png")
		background.convert('RGBA')
		img.paste(background, (0, 0), background)
		img.save("out.png")
		'''
		output = StringIO.StringIO()
		img.save(output, "PNG")
		img_base64 = output.getvalue().encode("base64")
		output.close()
		img_base64 = img_base64.replace("\n","")
		return img_base64
		'''




# Read the command line parameters
# argv[1]: Number of vCards to generate
# Redirect output to a file with filename extension .vcf
# Sample command line:
# python vcard21_maker.py 10 > contacts.vcf
if __name__ == "__main__":
	max_vcards = 1
	if len(sys.argv) > 1:
		max_vcards = long(sys.argv[1])

	#Connect to sqlite3 database where contact data is stored
	con = sqlite3.connect('contacts.db')
	rvc = RandomVcard(con);
	while max_vcards > 0:
		#Generate a randon vCard
		vcard = rvc.get();
		#Write the vCard to the command line
		print vcard
		max_vcards = max_vcards - 1
	con.close()
