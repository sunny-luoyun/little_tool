import subprocess

# 定义 sudo 命令和密码 是一个
command = "120712' | sudo -S asitop"

# 运行命令
process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

print("输出:", process.stdout)
print("错误:", process.stderr)
