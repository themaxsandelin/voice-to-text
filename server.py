from bottle import route, run

@route('/')
def index():
  return 'Hello, world!'

run(host='localhost', port=5550)