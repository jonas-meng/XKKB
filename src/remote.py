import shlex
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor


def execute_cmd(cmd):
    print(cmd)
    subprocess.run(shlex.split(cmd))


def remote_execute(cmd):
    with open("res/server.json") as reader:
        servers = json.load(reader)
        cmds = [
            f"ssh root@{server['ip']} {cmd}"
            for server in servers['servers']
        ]
    with ThreadPoolExecutor(max_workers=16) as executor:
        executor.map(execute_cmd, cmds)


def set_up():
    cmd = "git clone https://github.com/jonas-meng/XKKB.git /root/cryptolab &&" \
          "add-apt-repository ppa:deadsnakes/ppa && apt-get update && apt-get install -y python3.9 python3-pip &&" \
          "pip3 install -r /root/cryptolab/requirements.txt"
    remote_execute(cmd)


def execute_main():
    cmd = "cd /root/cryptolab && git pull https://github.com/jonas-meng/XKKB.git &&" \
          "python3 src/main.py"
    remote_execute(cmd)


if __name__ == "__main__":
    execute_main()