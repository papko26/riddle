#!/usr/bin/python3
import sys
import os
import hashlib
import argparse
import getpass
import subprocess
import tempfile
import json
from concurrent.futures import ThreadPoolExecutor
from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor
import tornado.web
import tornado.httpserver




def local_execute(command, local_env=None, cwd=None, shell=False):
    env = os.environ.copy()
    env['PATH'] = "/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin"
    std_out = tempfile.TemporaryFile()
    std_err = tempfile.TemporaryFile()
    if local_env is not None:
        shell = True
        local_env['PATH'] = env['PATH']
    if type(command) != list and not shell:
        command = command.split()
    try:
        process = subprocess.Popen(command,
                                   stdout=std_out,
                                   stderr=std_err,
                                   env=local_env,
                                   cwd=cwd,
                                   shell=shell)
    except Exception as error:
        return (1, error)
    process.wait()
    std_err.seek(0)
    std_out.seek(0)
    out = (std_out.read()).decode()
    err = (std_err.read()).decode()
    std_err.close()
    std_out.close()
    return (err,out)

def token_check(token_orig, token_provided):
    token_riddle = hashlib.md5(token_provided.encode('utf-8')).hexdigest()
    if token_orig != token_riddle:
        print("Token mismatch" )
        return False
    elif token_orig == token_riddle:
        return True
    else:
        print ("Authentification error. Exiting now")
        sys.exit(1)


MAX_WORKERS = 16

class RiddleHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def preload(self):
        try:
            knocker = self.get_arguments('server')
            if len(knocker) == 1 and knocker[0] == 'knock-knock':
                self.riddle_server = knocker[0]
                return True
            else:
                self.riddle_token = self.get_argument('token')
                self.riddle_server = self.get_argument('server')
                self.riddle_salt_applet = self.get_argument('salt_applet')
                self.riddle_command = self.get_argument('command')
                return True
        except tornado.web.MissingArgumentError as args_mismatch_err:
            self.write(str({'err':True,'out':"Missing args: " +str(args_mismatch_err)}))
            return False

    @run_on_executor
    def local_executor(self):
        cmd = ["/usr/bin/salt", self.riddle_server, self.riddle_salt_applet, self.riddle_command]
        try:
            reply = local_execute(cmd)
            err = reply[0]
            out = reply[1]
            return json.dumps({'err':err, 'out':out})
        except Exception as error:
            return json.dumps({'err':True, 'out':error})


    def alive_answer(self):
        if self.riddle_server == 'knock-knock':
            self.write(str({'err':False,'out':"alive"}))
            return True
        else:
            return False

    @tornado.gen.coroutine
    def post(self):
        if self.preload():
            if not self.alive_answer():
                if token_check(token_hashed, self.riddle_token):
                    res = yield self.local_executor()
                    self.write(str(res))
                else:
                    self.write(str({'err':True, 'out':"Token Mismatch"}))
        else:
            self.write(str({'err':True, 'out':"Arguments Mismatch"}))


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--cert", help="path to cert file", required=True)
    parser.add_argument("--key", help="path to key file", required=True)
    parser.add_argument("--port", help="port to start", required=True)
    parser.add_argument("--token",help="token as argument (insecure)",required=False)
    args = parser.parse_args()

    if os.path.exists(args.cert) and os.path.exists(args.key):
        print("riddle 0.5: salt 'one tenth REST' api starting.")
        if not args.token:
            token_userdefined = getpass.getpass("Enter token (for remote clients):")
        else:
            token_userdefined = args.token

        token_hashed = hashlib.md5(token_userdefined.encode('utf-8')).hexdigest()

        application = tornado.web.Application([(r"/riddle", RiddleHandler),])
        http_server = tornado.httpserver.HTTPServer(application,
                                                    ssl_options={"certfile": args.cert,
                                                                 "keyfile": args.key})
        http_server.listen(int(args.port))
        print("Ok,ok I would work. Just do not hit me!")
        tornado.ioloop.IOLoop.instance().start()
        IOLoop.instance().start()
    else:
        print("whoopsy, cant find SSL certificates")
        sys.exit (1)
