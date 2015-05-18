from google.appengine.ext import ndb
			
class Log(ndb.Model):
        ts = ndb.IntegerProperty()
        msg = ndb.StringProperty()
        level = ndb.StringProperty()

class System(ndb.Model):
	description = ndb.StringProperty()