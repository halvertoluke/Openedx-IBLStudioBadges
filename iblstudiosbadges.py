"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources
import datetime

# from xblock.fields import Integer, Scope, String, Any, Boolean, Dict
from xblock.core import XBlock
from xblock.fields import Scope, Integer, String
from xblock.fragment import Fragment
from xmodule.fields import RelativeTime

import iblstudiosbadges_client
import edxappCourseData

class IBLstudiosbadges(XBlock):
	"""
	TO-DO: document what your XBlock does.
	"""
	
	## xblock module name is the name of field set in mongodb
	xblock_name_field	= 'iblstudiosbadges'
	
	## general data
	display_name		= String(display_name="Display Name", default="Consigue tu insignia", scope=Scope.settings, help="Name of the component in the edxplatform")
	form_text			= String(display_name="text_desc", default=" ", scope=Scope.content, help="Badge text description")	
	congratulations_text= String(display_name="congratulations_desc", default=" ", scope=Scope.content, help="Congratulations text description")	
	enough_text			= String(display_name="enough_desc", default=" ", scope=Scope.content, help="Not-enough-score text description")	
	bg_id				= String(display_name="id", default="1", scope=Scope.content, help="Id of the Badge")	
	n_course_id			= String(display_name="CourseId", default="0", scope=Scope.user_state, help="Id of teh current course")	
	n_user_id			= String(display_name="UserId", default="0", scope=Scope.user_state, help="Id of the current user")	
	user_score			= String(display_name="UserScore", default="0", scope=Scope.user_state, help="Current section user score")	
	required_score		= String(display_name="RequiredScore", default="50", scope=Scope.content, help="Requireds core")	
	debug_mode			= String(display_name="debug", default="0", scope=Scope.content, help="Enable debug mode")	
	
	## provider data
	claim_prov_usr			= String(display_name="ProviderUSER", default="ibldemo-8CaZSS", scope=Scope.content, help="Badge provider user")
	claim_prov_pwd			= String(display_name="ProviderPass", default="4c46d8a1-70b4-43d9-87da-cdf06b049bea", scope=Scope.content, help="Badge provider pass")

	claim_prov_url			= "http://insignias.educalab.es" 
	claim_prov_url_token	= claim_prov_url+'/api/token.php' 
	claim_prov_url_list		= claim_prov_url+'/api/badgedata.php' 
	claim_prov_url_claim	= claim_prov_url+'/api/claim_badge.php'
	claim_prov_url_checkearn= claim_prov_url+'/api/checkearn.php'

	## user data	
	claim_name			= String(display_name="ClaimUserName", default="Jhon", scope=Scope.user_state, help="")	
	claim_mail			= String(display_name="ClaimUserMail", default="sils@iblstudios.com", scope=Scope.user_state, help="")	
	claim_db_user_data		= 'None'
	claim_db_user_id		= 'None'
	claim_db_user_course		= 'None'
	claim_db_user_name		= 'None'
	claim_db_user_email		= 'None'
	claim_db_user_score		= '0'

	#control errors
	claim_badge_errors		= ''
	
	def resource_string(self, path):
		"""Handy helper for getting resources from our kit."""
		data = pkg_resources.resource_string(__name__, path)
		return data.decode("utf8")
	
	# TO-DO: change this view to display your data your own way
	def student_view(self, context):
		#setup data to claim a badge
		self.n_user_id = self.get_student_id()
		self.claim_db_user_data = self.DB_get_user_data()
		self.claim_db_user_id = self.claim_db_user_data[0]
		self.claim_db_user_course = self.claim_db_user_data[1]
		self.claim_db_user_name = self.claim_db_user_data[2]
		self.claim_db_user_email = self.claim_db_user_data[3]
		self.claim_db_user_score = self.claim_db_user_data[4]
		self.claim_db_problems_lists = self.claim_db_user_data[5]
		self.claim_db_problems_total_score = self.claim_db_user_data[6]
		self.claim_db_problems_partial_score = self.claim_db_user_data[7]
		self.claim_db_problems_percent_score = self.claim_db_user_data[8]
		self.claim_db_badge_problems_score = self.claim_db_user_data[9]

		#need to be calc
		self.user_score = self.claim_db_user_data[4]
		"""
		Test mongodb connection
		Test course data tree
		"""
		# Mongo DB Connect
		from pymongo import Connection
		xmoduledb = "edxapp"
		connection = Connection()
		db = connection[xmoduledb]
		mongo_modulestore = db['modulestore']
		self.claim_db_course_id	= ''
		if self.claim_db_user_course!='None':
			self.claim_db_course_id	= self.claim_db_user_course
		""" Test """

		claim_name = self.claim_db_user_name
		claim_mail = self.claim_db_user_email
		self.claim_badge_errors = self.claim_badge_errors
		self.claim_badge_form   = ''
		self.check_earned	= ''
		self.preview_badge	= ''

		#checkout provider badge
		if self.claim_badge_errors == "":
			self.claim_prov_access_token = iblstudiosbadges_client.get_auth_token(self.claim_prov_url_token,self.claim_prov_usr,self.claim_prov_pwd)
			if self.claim_prov_access_token !="":
				badge_info	= iblstudiosbadges_client.get_badge_data(self.claim_prov_url_list,self.claim_prov_access_token,self.bg_id,'info')
				badge_params	= iblstudiosbadges_client.get_badge_data(self.claim_prov_url_list,self.claim_prov_access_token,self.bg_id,'params')
				obj_badge	= iblstudiosbadges_client.create_obj_badge(badge_info,badge_params)
				self.check_earned  = iblstudiosbadges_client.check_earn_badge(self.claim_prov_url_checkearn,self.claim_prov_access_token,self.claim_db_user_email,self.bg_id)
				self.preview_badge = iblstudiosbadges_client.build_badge_preview(obj_badge)

				if obj_badge :
					#check exists earned
					if self.check_earned!='':
						self.award_earn_prov  = iblstudiosbadges_client.get_award_result ( self.check_earned )
						self.award_earned     = iblstudiosbadges_client.get_award_result_formatted(self.award_earn_prov,self.congratulations_text)
					else:
						self.claim_badge_form = iblstudiosbadges_client.build_badge_form(self.claim_db_user_name,self.claim_db_user_email,self.form_text,obj_badge)
				else:
					# self.claim_badge_errors = 'Could not retrieve the information associated with the Badge ID selected. Please, verify your data.'
					print self.claim_prov_url_token
					print self.claim_prov_usr
					print self.claim_prov_pwd
			else:
				self.claim_badge_errors = 'Could not connect to provider. Please, verify your credentials.'

		"""
		The primary view for the students
		"""
		self.claim_data = ""
		
		if self.claim_badge_errors == "":
			if self.debug_mode == "1":
				html = self.resource_string("static/html/debug.html")
			else:
				if int(self.user_score) < int(self.required_score):
					html = self.resource_string("static/html/student_view_noscore.html")
				else:
					if self.check_earned!='':
						html = self.resource_string("static/html/student_view_earn_badge.html")
					else:
						html = self.resource_string("static/html/student_view_claim_badge.html")
					
			frag = Fragment(html.format(self=self))
			frag.add_css(self.resource_string("static/css/style.css"))
			if self.check_earned =='':
				frag.add_javascript(self.resource_string("static/js/src/student_view_scripts.js"))
			frag.initialize_js('StudentViewBadge')
		else:
			if self.debug_mode == "1":
				html = self.resource_string("static/html/result_errors_debug.html")
			else:
				html = self.resource_string("static/html/result_errors.html")
			frag = Fragment(html.format(self=self))
			frag.add_css(self.resource_string("static/css/style.css"))
			
		return frag


	# get data from student_id
	def get_student_id(self):
		if hasattr(self, "xmodule_runtime"):
			s_id = self.xmodule_runtime.anonymous_student_id  # pylint:disable=E1101
		else:
			if self.scope_ids.user_id is None:
				s_id = "None"
			else:
				s_id = unicode(self.scope_ids.user_id)
		return s_id

	# get student_data from db
	def DB_get_user_data(self):
		import appmysqldb, CommonFunc
		user_id = "None"
		course_id  = "None"
		user_name = "None"
		user_email = "None"
		user_score = "0"
		
		#ids : user and course
		db = appmysqldb.mysql('localhost', 3306, 'edxapp', 'root', '')
		q = "SELECT id, user_id, course_id FROM student_anonymoususerid WHERE anonymous_user_id='" + self.n_user_id + "'"
		CommonFunc.debug("QUERY: %s" %(q))
		db.query(q)
		res = db.fetchall()
		for row in res:
			user_id   = row[1]
			course_id = row[2]

		#username
		q = "SELECT name FROM auth_userprofile WHERE user_id='%s' " % (user_id)
		CommonFunc.debug("QUERY: %s" %(q))
		db.query(q)
		res = db.fetchall()
		for row in res:
			user_name   = row[0]

		#email
		q = "SELECT email FROM auth_user WHERE id='%s' " % (user_id)
		CommonFunc.debug("QUERY: %s" %(q))
		db.query(q)
		res = db.fetchall()
		for row in res:
			user_email   = row[0]

		""" getting course data from mongodb """
		# Mongo DB Connect
		from pymongo import Connection
		xmoduledb = "edxapp"
		connection = Connection()
		db_mongo = connection[xmoduledb]
		mongo_modulestore = db_mongo['modulestore']
		badge_list_problems = edxappCourseData.getListProblemsFromBadgeId(mongo_modulestore,self.bg_id,course_id, self.xblock_name_field)
		badge_problems_score = edxappCourseData.getScoreFromBadgeId(mongo_modulestore,self.bg_id,course_id,  self.xblock_name_field)
		""" """

		#calculate badge_score
		user_score = 0
		partial_user_score = []
		badge_partial_user_score = 0
		badge_percent_user_score = 0
		#calculate user partials
		if badge_problems_score>0:
			if len(badge_list_problems)>0:
				for problem in badge_list_problems:
					if 'problem_score' in problem:
						problem_score 	= problem['problem_score']
						problem_id 	= problem['problem_id']
						#getting partial values
						if int(problem_score)>0:
							q = "SELECT ((%s/max_grade)*grade) FROM courseware_studentmodule WHERE course_id='%s' AND student_id='%s' AND module_id='%s'" % (problem_score,course_id,user_id,problem_id)
							CommonFunc.debug("QUERY: %s" %(q))
							db.query(q)
							res = db.fetchall()
							for row in res:
								if row[0]>0:
									partial_user_score.append( float(row[0]) )

						badge_partial_user_score = sum(partial_user_score)

		#calculate total percent
		if round(badge_partial_user_score,2)>0 and int(badge_problems_score)>0:
			badge_percent_user_score = ( badge_partial_user_score * 100.0 ) / badge_problems_score
			badge_percent_user_score = round(badge_percent_user_score,2)
		if int(badge_percent_user_score)>0:
			user_score = badge_percent_user_score

		#show results
		results = [user_id,course_id,user_name,user_email,user_score,badge_list_problems,badge_problems_score,badge_partial_user_score,badge_percent_user_score,badge_problems_score]
		return results


	# studio_view
	def studio_view(self, context=None):
		"""
		The primary view for Studio
		"""
		html = self.resource_string("static/html/studio_view_edit.html")
		frag = Fragment(html.format(self=self))
		frag.add_css(self.resource_string("static/css/style.css"))
		frag.add_javascript(self.resource_string("static/js/src/studio_view_edit.js"))
		frag.initialize_js('StudentEditBadge')
		return frag


	@XBlock.json_handler
	def student_claim_save(self,claimdata,suffix=''):
		#parse data to claim badge
		import json
		award_result = 'error'
		#award_result = 'pending'
		""" """
		if claimdata:
			#get new token
			self.claim_prov_access_token = iblstudiosbadges_client.get_auth_token(self.claim_prov_url_token,self.claim_prov_usr,self.claim_prov_pwd)
			#parse returned data
			claimdata_dict= dict( entry.split('=') for entry in claimdata.split('&') )
			award_data = iblstudiosbadges_client.set_form_data_to_award(claimdata_dict)
			set_award_single = iblstudiosbadges_client.claim_and_award_single_badge(self.claim_prov_url_claim,self.claim_prov_access_token,award_data)

			#debug provider
			if self.debug_mode == "1":
				debug_result = award_data +'<hr>'+set_award_single
				return { 'result' : debug_result }

			#result award
			award_result_prov	= iblstudiosbadges_client.get_award_result ( eval(set_award_single) )
			award_result		= iblstudiosbadges_client.get_award_result_formatted(award_result_prov,self.congratulations_text)

		return { 'result' :  award_result }


	@XBlock.json_handler
	def studio_save(self, data, suffix=''):
		"""
		Called when submitting the form in Studio
		"""
		self.debug_mode = data['debug_mode']
		self.bg_id = data['bg_id']
		self.form_text = data['form_text']
		self.congratulations_text = data['congratulations_text']
		self.enough_text = data['enough_text']
		self.required_score = data['required_score']
		self.claim_prov_usr = data['badge_pro_user']
		self.claim_prov_pwd = data['badge_pro_pwd']
		return { 'result': 'success' }


	# TO-DO: change this to create the scenarios you'd like to see in the
	# workbench while developing your XBlock.
	@staticmethod
	def workbench_scenarios():
		"""A canned scenario for display in the workbench."""
		return [
			("IBLStudiosBadges",
			"""<vertical_demo>
				<iblstudiosbadges/>
				<iblstudiosbadges/>
				<iblstudiosbadges/>
				</vertical_demo>
			"""),
		]
