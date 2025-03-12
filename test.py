import subprocess

result = subprocess.run(["cmd","/c","dir", "/b"], stdout=subprocess.PIPE, text=True)
print(result.stdout)