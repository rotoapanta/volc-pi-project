import subprocess

interface = "eth0"
result = subprocess.run(["ip", "addr", "show", interface], capture_output=True, text=True)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
lines = result.stdout.splitlines()
for line in lines:
    line = line.strip()
    if line.startswith("inet "):
        ip = line.split()[1].split('/')[0]
        print(f"IP encontrada: {ip}")