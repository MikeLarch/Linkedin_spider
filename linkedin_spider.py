import module
# unique to module
import time, re#, requests, libxml2
from lxml import etree, html
from io import StringIO, BytesIO
#from optparse import OptionParser

class Module(module.Module):
	
	def __init__(self, params):
		module.Module.__init__(self, params)
		self.register_option('url', None, 'yes', 'public linkedin seed url of employee for targeted company')
		self.register_option('company', None, 'no', 'company name to compare against rather than the seed \'URL\' company name')
		self.register_option('wait', 1, 'no', 'wait time between http requests in seconds')
		self.register_option('verbose','F','no','verbose output, T or F')
		self.info = {'Name': 'Linkedin Contact Enumerator','Author':'Mike Larch','Description': 'Harvests contacts from linkedin.com by spidering through "Viewers of this profile also viewed" links, adding them to the \'contacts\' table of the database. URL must be for a public linkedin page. The User of that page must currently be working at the targeted company. ','Comments': []}
		
	def module_run(self):
		company = self.getCompany()
		self.heading('Getting contacts from ' + company)
		self.getInfo(company)
			
	def getCompany(self):
		if self.options['company'] is None:		
			resp = self.request(self.options['url'])
			parser = etree.HTMLParser()
			tree = etree.parse(StringIO(resp.text), parser)
			try: 
				company = tree.xpath('//ul[@class="current"]/li/a/span[@class="org summary"]/text()')[0]
			except IndexError:
				try:
					company = (tree.xpath('//ul[@class="current"]/li/text()')[1]).strip()
				except IndexError:
					try:
						titleatCompany = (tree.xpath('//p[@class="headline-title title"]/text()')[0]).strip()
						company = titleatCompany.split("at ",1)[1]					
					except IndexError:
						self.error('No company found on seed url page')
		else:
			company = self.options['company']
		return(company)
		
	def getInfo(self, company):
		verbose = self.options['verbose']
		tempURLList = []
		accepted = []
		rejected = []
		tempURLList.append(self.options['url'])
		i= len(tempURLList)
		while i > 0:
			tempURL = tempURLList.pop(0)		
			time.sleep(self.options['wait'])
			if verbose == 't' or verbose == 'T': self.output('Parsing: ' + tempURL)
			resp = self.request(tempURL)
			parser = etree.HTMLParser()
			tree   = etree.parse(StringIO(resp.text), parser)
			tempCompany = ''
			try: 
				tempCompany = tree.xpath('//ul[@class="current"]/li/a/span[@class="org summary"]/text()')[0]
			except IndexError:
				try:
					tempCompany = (tree.xpath('//ul[@class="current"]/li/text()')[1]).strip()
				except IndexError:
					try:
						tempCompany = ((tree.xpath('//p[@class="headline-title title"]/text()')[0]).strip()).split("at ",1)[1]				
					except IndexError:
						if verbose == 't' or verbose == 'T': self.verbose('No current company found on page')
						
			if company in tempCompany:
				fname = (tree.xpath('//span[@class="given-name"]/text()')[0]).split(' ',1)[0]
				lname = (tree.xpath('//span[@class="family-name"]/text()')[0]).split(',',1)[0]
				try:
					title = (tree.xpath('//ul[@class="current"]/li/text()')[0]).strip()
				except IndexError:
					try:
						title = (tree.xpath('//p[@class="headline-title title"]/text()')[0]).strip()
					except IndexError:
						title = 'unknown'
				moreLinks = tree.xpath('//li[@class="with-photo"]/a/@href')
				
				for j in moreLinks:
					if j not in tempURLList:
						if j not in accepted:
							if j not in rejected:
								tempURLList.append(j)
				title = title + ' at ' + tempCompany
				accepted.append(tempURL)
				self.verbose('Added: '+ fname + ' ' + lname + ', ' + title)# + ' at ' + company)
				self.add_contact(fname, lname, title, email=None, region=None, country=None)
			else:
				fname = (tree.xpath('//span[@class="given-name"]/text()')[0]).split(' ',1)[0]
				lname = (tree.xpath('//span[@class="family-name"]/text()')[0]).split(',',1)[0]
				rejected.append(tempURL)
				if verbose == 't' or verbose == 'T': self.verbose('Rejected: ' + fname + ' ' + lname + ', doesn\'t work at ' + company)
			
			i = len(tempURLList)
			if verbose == 't' or verbose == 'T': self.verbose(str(i) + ' url\'s left to try')
		return
