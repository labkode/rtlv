import webapp2
import handlers

app = webapp2.WSGIApplication([
	('/', handlers.MainHandler),
	('/systems', handlers.SystemHandler),
	('/admin/systems', handlers.AdminSystemListHandler),
	('/admin/systems/create', handlers.AdminSystemCreateHandler),
	('/admin/systems/delete', handlers.AdminSystemDeleteHandler),
	('/admin/logs', handlers.AdminLogHandler),
	('/help', handlers.HelpHandler)
	], debug = False)


