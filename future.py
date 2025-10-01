class Future : 
	WAITING = 0
	RUNNING = 1
	def __init__(self) : 
		self.state = Future.WAITING

		#onDoned is here to be executed when the action is finished
		self.onDoned = None

	def running(self) : 
		return self.state