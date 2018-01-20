# riddle
**Terribly simple monolithic async (tornado based) "half" REST API for saltstack.**


## REQS:
- [tornado](https://github.com/tornadoweb/tornado) 


## Usage:
On saltstack master:
```
python3 riddle.py --cert /home/certs/cert.pem --key /home/certs/key.pem --port 8765
riddle 0.5: salt 'one tenth REST' api starting.
Enter token (for remote clients): ******(secret)
Ok,ok I would work. Just do not hit me!
```

On remote side(valid request):
```
curl --insecure --data "token=secret;server=my-salt-server.com;salt_applet=cmd.run;command=echo hello" https://my-salt-server.com:8765/riddle
```
Response:
```
{"out": "my-salt-server.com:\n    hello\n", "err": ""}
```

On remote side(alive check):
```
curl --insecure --data "server=my-salt-server.com;" https://my-salt-server.com:8765/riddle
```
Response:
```
{"out": "alive", "err": ""}
```

On remote side(invalid request):
```
curl --insecure --data "token=secret;COMPUTER=my-salt-server.com;salt_applet=cmd.run;command=echo hello" https://my-salt-server.com:8765/riddle
```
Response:
```
{'err': True, 'out': 'Arguments Mismatch'}
```

On remote side(Wrong request):
```
curl --insecure --data "token=secret;server=my-salt-server.com;salt_applet=cmd.run;command=echoh hello" https://my-salt-server.com:8765/riddle
```
Response:
```
{"err": "ERROR: Minions returned with non-zero exit code\n", "out": "my-salt-server.com:\n    /bin/sh: echoh: command not found\n"}
```

TODO:

Finish and add client.
