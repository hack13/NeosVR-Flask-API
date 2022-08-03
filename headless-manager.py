# This version is for neosvr server
# ChangeLog
# June 3, 2021: Intial creation of management script
# June 4, 2021: Added shutdown and start functions
# June 8, 2021: Switched to subprocess lib and fixed output of the patch info
# June 14, 2021: Made proto be a little more polite...
# July 3, 2021: Made windows version
# Oct 31, 2021: Added som comments and error handling for bad requests
# Jan 29, 2022: Updated to support docker and not depend on a second script as well as multiple headlesses on the same machine
# Jul 3, 2022: Added a check for check world destroyed at request of ScarsTRF
# Aug 3, 2022: Did some clean up and fixing syntax issues...

import subprocess
import sys
import time
import psutil
from flask import Flask, json, request, jsonify
from flask_httpauth import HTTPTokenAuth
from markupsafe import escape
from waitress import serve
from werkzeug.exceptions import HTTPException


# Variables
serverName = "servername"
headlesspath = "/home/hack13"

# Define the flask API
app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Bearer', header='X-API-Key')

tokens = {
    "00000000-0000-0000-0000-000000000000": "testing"
}

@auth.verify_token
def verify_token(token):
    if token in tokens:
        return tokens[token]

# Define the function to execute commands
def headlessManager(headless, command, opts=''):
	safeToProceed = True
	if(safeToProceed == True):
    		subprocess.run([f"echo {command} {opts} | socat EXEC:'docker attach {headless}',pty STDIN"], shell=True)
	else:
		subprocess.run([f"echo status | socat EXEC:'docker attach {headless}',pty STDIN"], shell=True)
		subprocess.run([f"echo {command} {opts} | socat EXEC:'docker attach {headless}',pty STDIN"], shell=True)

# Get response from container
def getResponse(headless, lines):
    proc = subprocess.run(["docker", "logs", "-n", f"{lines}", f"{headless}"], stdout=subprocess.PIPE)
    stdout = proc.stdout
    cleanout = str(stdout, 'UTF-8').replace('\u001b', '').replace('[32m','').replace('[37m','').replace('[33m','').replace('[6n',' ').replace('\r\n',' ').replace('\t',', ')
    parsed = cleanout.split('>')
    return parsed
	
# Check for world destroyed
def getWorldDestroyed(headless):
	response = getResponse(headless, 1)
	if(response == "World has been destroyed in the meantime"):
		return True
	else:
		return False

# Low level docker commands
def runDockerCompose(headless, command):
    proc = subprocess.run([f"cd {headlesspath}/{headless} && docker-compose {command}"], shell=True)
    stdout = proc.stdout
    return stdout

# Default response
@app.route("/")
def hello():
    return jsonify({"name:":f"{serverName}","error":"You shouldn't be here..."})

# Start a headless server
@app.route('/start/<headless>')
@auth.login_required
def start(headless):
    try:
        eheadless = f"{escape(headless)}"
        runDockerCompose(f'{eheadless}', 'up -d')
        return jsonify({"server":f"{eheadless}","state":"Starting, please give up to 3 minutes to start"})
    except:
        return jsonify({"error":"Invalid Request"})

# Stop a headless server
@app.route('/stop/<headless>')
@auth.login_required
def stop(headless):
    try:
        eheadless = f"{escape(headless)}"
        runDockerCompose(f'{eheadless}', 'down')
        return jsonify({"server":f"{eheadless}","state":"Stopping the headless server"})
    except:
        return jsonify({"error":"Invalid Request"})

# Restart a headless server
@app.route('/restart/<headless>')
@auth.login_required
def restart(headless):
    try:
        eheadless = f"{escape(headless)}"
        runDockerCompose(f'{eheadless}', 'down')
        runDockerCompose(f'{eheadless}', 'up -d')
        return jsonify({"server":f"{eheadless}","state":"Starting, please give up to 3 minutes to start"})
    except:
        return jsonify({"error":"Invalid Request"})

##########################################
### World/Session Commands
##########################################

# Get session url for active world
@app.route('/sessionurl/<headless>')
@auth.login_required
def sessionurl(headless):
    try:
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'sessionURL')
        feedback = getResponse(f'{eheadless}', 2)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1].lstrip(' sessionURL').rstrip()}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Get session id for active world
@app.route('/sessionid/<headless>')
@auth.login_required
def sessionid(headless):
    try:
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'sessionID')
        feedback = getResponse(f'{eheadless}', 2)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1].lstrip(' sessionID').rstrip()}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Save the world
@app.route('/save/<headless>')
@auth.login_required
def save(headless):
    try:
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'save')
        feedback = getResponse(f'{eheadless}', 2)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1]}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Get list of worls on headless server
@app.route('/worlds/<headless>')
@auth.login_required
def worlds(headless):
    try:
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}','worlds')
        feedback = getResponse(f'{eheadless}', 3)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1].lstrip(' worlds').replace('   ','').rstrip()}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Close active world
@app.route('/closeworld/<headless>')
@auth.login_required
def closeworld(headless):
    try:
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}','close')
        feedback = getResponse(f'{eheadless}', 2)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":"closed"})
    except:
        return jsonify({"error":"Invalid Request"})

# Get World status
@app.route('/status/<headless>')
@auth.login_required
def status(headless):
    try:
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'status')
        feedback = getResponse(f'{eheadless}', 13)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1].lstrip(' status')}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Focus to specific world
@app.route('/focus/<headless>/<world>')
@auth.login_required
def focus(headless, world):
    try:
        eworld = int(f"{escape(world)}")
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'focus', f'{eworld}')
        headlessManager(f'{eheadless}', ' ')
        feedback = getResponse(eheadless, 1)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Change World Name
# Currently only supports basic name changes, no special chars
@app.route('/worldname/<headless>/<worldname>')
@auth.login_required
def worldname(headless, worldname):
    try:
        eworldname = f"{escape(worldname)}"
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'name', f'{eworldname}')
        feedback = getResponse(eheadless, 1)
        headlessManager(f'{eheadless}', ' ')
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Change World Description
# Needs Fixing as description can contain spaces and special characters
#@app.route('/worlddescription/<headless>/<description>')
#@auth.login_required
#def worlddescription(headless, description):
#    try:
#        edescripiton = f"{escape(description)}"
#        eheadless = f"{escape(headless)}"
#        headlessManager(f'{eheadless}', 'description', f'{edescripiton}')
#        feedback = getResponse(eheadless, 1)
#        return jsonify({"server":f"{eheadless}","state":f"{feedback}"})
#    except:
#        return jsonify({"error":"Invalid Request"})

# Change World Max Users
@app.route('/maxusers/<headless>/<usercount>')
@auth.login_required
def maxusers(headless, usercount):
    try:
        eusercount = int(f"{escape(usercount)}")
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'maxUsers', f'{eusercount}')
        feedback = getResponse(eheadless, 1)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1].lstrip().rstrip()}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Change World Away Kick Time
@app.route('/awaykick/<headless>/<count>')
@auth.login_required
def awaykick(headless, count):
    try:
        ecount = int(f"{escape(count)}")
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'awayKickInterval', f'{ecount}')
        feedback = getResponse(eheadless, 1)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1].lstrip().rstrip()}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Change World Access Level
@app.route('/accesslevel/<headless>/<level>')
@auth.login_required
def accesslevel(headless, level):
    try:
        elevel = f"{escape(level)}"
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'accessLevel', f'{elevel}')
        feedback = getResponse(eheadless, 1)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1].lstrip().rstrip()}"})
    except:
        return jsonify({"error":"Invalid Request"})

##########################################
### World/Session User Commands
##########################################

# Get list of users in session
@app.route('/getusers/<headless>')
@auth.login_required
def getusers(headless):
    try:
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}','users')
        feedback = getResponse(f'{eheadless}', 10)
        response = feedback[1].split('users')
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{response[1].lstrip()}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Invite user to active world
@app.route('/invite/<headless>/<username>')
@auth.login_required
def invite(headless, username):
    try:
        eusername = f"{escape(username)}"
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'invite', f'{eusername}')
        feedback = getResponse(f'{eheadless}', 2)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1].lstrip(' invite')}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Get list of pending friend requests
@app.route('/pendingFriends/<headless>')
@auth.login_required
def pendingFriends(headless):
    try:
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}','friendRequests')
        feedback = getResponse(f'{eheadless}', 1)
        if (feedback[1].lstrip('friendRequests') == ''):
            return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":"No Pending Friends"}) # Needs fixing
        else:
            return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1]}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Accept a pending friend request
@app.route('/afr/<headless>/<username>')
@auth.login_required
def afr(headless, username):
    try:
        eusername = f"{escape(username)}"
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'afr', f'{eusername}')
        feedback = getResponse(f'{eheadless}', 2)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1]}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Kick user from headless session
@app.route('/kick/<headless>/<username>')
@auth.login_required
def kick(headless, username):
    try:
        eusername = f"{escape(username)}"
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'kick', f'{eusername}')
        feedback = getResponse(f'{eheadless}', 2)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1]}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Ban user from headless session
@app.route('/ban/<headless>/<username>')
@auth.login_required
def ban(headless, username):
    try:
        eusername = f"{escape(username)}"
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'ban', f'{eusername}')
        feedback = getResponse(f'{eheadless}', 1)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1]}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Unban user from headless session
@app.route('/unban/<headless>/<username>')
@auth.login_required
def unban(headless, username):
    try:
        eusername = f"{escape(username)}"
        eheadless = f"{escape(headless)}"
        headlessManager(f'{eheadless}', 'ban', f'{eusername}')
        feedback = getResponse(f'{eheadless}', 1)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1]}"})
    except:
        return jsonify({"error":"Invalid Request"})

# Change a user's role for world
@app.route('/updaterole/<headless>/<username>/<role>')
@auth.login_required
def updaterole(headless, username, role):
    try:
        eusername = f"{escape(username)}"
        eheadless = f"{escape(headless)}"
        erole = f"{escape(role)}"
        headlessManager(f'{eheadless}', 'ban', f'{eusername} {erole}')
        feedback = getResponse(f'{eheadless}', 1)
        return jsonify({"server":f"{eheadless}","world":f"{feedback[0]}","state":f"{feedback[1]}"})
    except:
        return jsonify({"error":"Invalid Request"})

##########################################
### Server Commands
##########################################

# Server resource usage
@app.route('/sysinfo/<type>')
def show_sysinfo(type=''):
    etype = f'{escape(type)}'
    if etype == 'cpu':
        return jsonify({"server":f"{serverName}","state":f"{psutil.cpu_percent()}%"})
    elif etype == 'mem':
        return jsonify({"server":f"{serverName}","state":f"{psutil.virtual_memory()[2]}%"})
    else:
        return jsonify({"error":"Invalid Request"})

# Health check address
@app.route('/healthz')
def api_health():
    return jsonify({'name':f'{serverName}','state':'OK'})

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "server": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

if __name__ == "__main__":
    #Please pay attention to the url_prefix and be sure to put this behind a reverse proxy!
    serve(app, host="0.0.0.0", port=8080, threads=1, url_scheme='http', url_prefix='') 