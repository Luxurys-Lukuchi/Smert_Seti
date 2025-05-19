import paramiko

def ssh_connect(host, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port=port, username=username, password=password)
        print(f"✅ Успешное подключение к {host}")
        return ssh
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None


def ssh_interactive(ssh):
    channel = ssh.invoke_shell()
    print("🟢 Интерактивная оболочка активирована. Введите 'exit' для выхода.")

    buffer = ''
    while True:
        try:
            user_input = input()
            if user_input.lower() in ['exit', 'quit']:
                break
            channel.send(user_input + '\n')

            # Буфер для хранения входящих данных
            while True:
                if channel.recv_ready():
                    data = channel.recv(1024).decode(errors='replace')
                    if not data:
                        break

                    buffer += data

                    # Разделяем по маркеру "---"
                    while '\n---\n' in buffer:
                        parts = buffer.split('\n---\n', 1)
                        line = parts[0].strip()

                        if line.startswith('command:'):
                            print(f"> {line[8:].strip()}")
                        elif line.startswith('result:'):
                            result_lines = line[8:].splitlines()
                            for res_line in result_lines:
                                print(f"→ {res_line}")

                        buffer = parts[1]

                else:
                    break

        except KeyboardInterrupt:
            print("\n❌ Соединение прервано.")
            break

    channel.close()


if __name__ == "__main__":
    host = input("Host: ")
    port = int(input("Port [22]: ") or 22)
    username = input("Username: ")
    password = input("Password: ")

    ssh = ssh_connect(host, port, username, password)
    if ssh:
        ssh_interactive(ssh)
        ssh.close()