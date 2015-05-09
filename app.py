from google.appengine.ext import ndb
from google.appengine.ext.db import BadValueError
from google.appengine.api import channel
from google.appengine.api import users


import webapp2
import jinja2

import os
import json
from datetime import datetime
import time


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class MainHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		systems = System.query().fetch()	
		template_values = {"systems": systems, "user": user, "users": users}
		template = JINJA_ENVIRONMENT.get_template("templates/index.html")
		self.response.write(template.render(template_values))



class SystemHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		system_param = self.request.get('system')
		if not system_param:
			template = JINJA_ENVIRONMENT.get_template("templates/not_found.html")
			template_values = {"user": user, "users": users, "not_found_msg": "Please select a system"}
			self.response.write(template.render(template_values))
			return
		
		system = System.get_by_id(system_param)
		if system is None:
			template = JINJA_ENVIRONMENT.get_template("templates/not_found.html")
			template_values = {"user": user, "users": users, "not_found_msg": "The system #{0} not exists".format(system_param)}
			self.response.write(template.render(template_values))
			return

		#logs = Log.query(ancestor = system.key).fetch()

		logs = []

		template_values = {"system":system, "logs": logs, "token": channel.create_channel(system.key.id()), "user": user, "users": users}
		template = JINJA_ENVIRONMENT.get_template("templates/logs.html")
		self.response.write(template.render(template_values))
		return
		
class AdminSystemListHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if not user:
			self.redirect(users.create_login_url())

		systems = System.query().fetch()
		template_values = {"systems": systems, "message":{"type":"success", "payload":""},"user": user, "users": users}
		template = JINJA_ENVIRONMENT.get_template("templates/list_system.html")
		self.response.write(template.render(template_values))
		return

class AdminSystemCreateHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if not user:
			self.redirect(users.create_login_url())

		template = JINJA_ENVIRONMENT.get_template("templates/create_system.html")
		self.response.write(template.render({"user": user, "users": users}))
		return

	def post(self):
		user = users.get_current_user()
		if not user:
			self.redirect(users.create_login_url())

		system_name = self.request.get("name")
		system_description = self.request.get("description")
		system = System(id = system_name, description = system_description)
		key = system.put()
		
		# This is correct but is a hack, other solution is to use a sleep()
		must_stop = False
		systems = []
		
		while not must_stop:
			systems = System.query().fetch()
			for system in systems:
				if system.key.id() == system_name:
					must_stop = True

		systems = System.query().fetch()
		template_values = {"systems": systems,"message":{"type":"success", "payload":"Created system #{0}".format(key.id())}, "user": user, "users": users}
		template = JINJA_ENVIRONMENT.get_template("templates/list_system.html")
		self.response.write(template.render(template_values))
		return

class AdminSystemDeleteHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if not user:
			self.redirect(users.create_login_url())

		system_id = self.request.get("system")

		if not system_id:
			template = JINJA_ENVIRONMENT.get_template("templates/not_found.html")
			template_values = {"user": user, "users": users, "not_found_msg": "Please select a system"}
			self.response.write(template.render(template_values))
			return
		
		sys = System.get_by_id(system_id)
		if sys is None:
			template = JINJA_ENVIRONMENT.get_template("templates/not_found.html")
			template_values = {"user": user, "users": users, "not_found_msg": "The system #{0} not exists".format(system_id)}
			self.response.write(template.render(template_values))
			return
		
		sys.key.delete()

		# Hack to not use sleep solution
		found = True
		systems = []
		
		while found:
			found = False
			systems = System.query().fetch()
			print(systems)
			for system in systems:
				print(system.key.id(),sys.key.id())
				if system.key.id() == sys.key.id():
					found = True
					break

		systems = System.query().fetch()
		template_values = {"systems": systems, "message":{"type":"success", "payload":"Deleted system #{0}".format(system_id)}, "user": user, "users": users}
		template = JINJA_ENVIRONMENT.get_template("templates/list_system.html")
		self.response.write(template.render(template_values))
		return


class AdminLogHandler(webapp2.RequestHandler):
	def post(self):
		try:
			log_param = json.loads(self.request.body)
		except ValueError as e:
			self.response.out.write(e)
			self.response.set_status(400)
			return
		except:
			self.response.set_status(500)
			return

		if not isinstance(log_param, list):
			log_param = [log_param]

		for log_item in log_param:
			log_system = log_item.get("system")
			if not log_system:
				self.response.out.write("System not found")
				self.response.set_status(404)
			
			system = System.get_by_id(log_system)

			if not system:
				self.response.out.write("System not found")
				self.response.set_status(404)
				return
			try:
				log_key = ndb.Key("Log", log_item.get("id"), parent = system.key)
				log_msg = log_item.get("msg")
				log_level = log_item.get("level")
				log_ts = log_item.get("ts")
				log = Log(key = log_key, msg = log_msg, level = log_level, ts = log_ts)
				
				# CHANNEL API
				channel.send_message(system.key.id(), json.dumps(log.to_dict()))

			except BadValueError as e:
				self.response.out.write(e)
				self.response.set_status(400)
				return
		return

class HelpHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		template_values = {"user": user, "users": users}
		template = JINJA_ENVIRONMENT.get_template("templates/help.html")
		self.response.write(template.render(template_values))














app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/systems', SystemHandler),
	('/admin/systems', AdminSystemListHandler),
	('/admin/systems/create', AdminSystemCreateHandler),
	('/admin/systems/delete', AdminSystemDeleteHandler),
	('/admin/logs', AdminLogHandler),
	('/help', HelpHandler)
	], debug = False)


			
class Log(ndb.Model):
        ts = ndb.IntegerProperty()
        msg = ndb.StringProperty()
        level = ndb.StringProperty()

class System(ndb.Model):
	description = ndb.StringProperty()
