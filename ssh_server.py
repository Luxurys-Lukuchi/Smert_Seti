# Установите: pip install paramiko chardet
import socket
import threading
import paramiko
import datetime
import subprocess
import os
import json
import chardet

HOST_KEY = paramiko.RSAKey.generate(2048)
LOG_DIR = 'logs'
USERS_FILE = 'users.json'

# Создаём папку для логов, если её нет
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)


class SimpleSSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.username = None

    def check_auth_password(self, username, password):
        users = load_users()
        user_data = users.get(username)
        if user_data and user_data.get("password") == password and user_data.get("active", True):
            self.username = username
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_shell_request(self, channel):
        return True


def log_message(user, message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    log_file = os.path.join(LOG_DIR, f"{user}.log")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(full_message + '\n')


def register_user(login, password):
    users = load_users()
    if login in users:
        return False, "Пользователь уже существует."
    if len(password) < 6:
        return False, "Пароль слишком короткий. Минимум 6 символов."
    users[login] = {"password": password, "active": True}
    save_users(users)
    return True, "Регистрация успешна."


def delete_user(login):
    users = load_users()
    if login not in users:
        return False, "Пользователь не найден."
    del users[login]
    save_users(users)
    return True, "Пользователь удалён."


def disable_user(login):
    users = load_users()
    if login not in users:
        return False, "Пользователь не найден."
    users[login]["active"] = False
    save_users(users)
    return True, "Пользователь отключен."


def enable_user(login):
    users = load_users()
    if login not in users:
        return False, "Пользователь не найден."
    users[login]["active"] = True
    save_users(users)
    return True, "Пользователь включен."


def run_command(command, user):
    try:
        if command.startswith("register "):
            if user != "admin":
                return "Ошибка: Вы не можете регистрировать новых пользователей."
            parts = command.split()
            if len(parts) != 3:
                return "Использование: register <логин> <пароль>"
            login, password = parts[1], parts[2]
            success, message = register_user(login, password)
            return message if success else f"Ошибка: {message}"

        elif command.startswith("delete "):
            if user != "admin":
                return "Ошибка: Вы не можете удалять пользователей."
            login = command.split()[1]
            success, message = delete_user(login)
            return message if success else f"Ошибка: {message}"

        elif command.startswith("disable "):
            if user != "admin":
                return "Ошибка: Вы не можете отключать пользователей."
            login = command.split()[1]
            success, message = disable_user(login)
            return message if success else f"Ошибка: {message}"

        elif command.startswith("enable "):
            if user != "admin":
                return "Ошибка: Вы не можете включать пользователей."
            login = command.split()[1]
            success, message = enable_user(login)
            return message if success else f"Ошибка: {message}"

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=10
        )

        stdout_encoding = chardet.detect(result.stdout)['encoding']
        stderr_encoding = chardet.detect(result.stderr)['encoding']

        stdout = result.stdout.decode(stdout_encoding or 'utf-8', errors='replace').strip()
        stderr = result.stderr.decode(stderr_encoding or 'utf-8', errors='replace').strip()

        output = stdout or stderr or "Нет вывода"
        log_message(user, f"Команда: '{command}' | Результат: '{output}'")
        return output
    except Exception as e:
        error_msg = str(e)
        log_message(user, f"Ошибка выполнения команды '{command}': {error_msg}")
        return f"Ошибка: {error_msg}"


def handle_client(transport, server):
    while True:
        channel = transport.accept(20)
        if channel is None:
            continue

        user = server.username
        log_message(user, f"[Новое соединение] {channel}")

        channel.send(f"Добро пожаловать, {user}, в тестовый SSH сервер!\n")

        buffer = ''
        while True:
            try:
                if channel.recv_ready():
                    data = channel.recv(1024).decode(errors='replace')
                    if not data:
                        break

                    buffer += data

                    if '\n' in buffer:
                        lines = buffer.split('\n')
                        for line in lines[:-1]:
                            line = line.strip()
                            if line:
                                response = f"command: {line}\n"
                                channel.send(response)
                                result = run_command(line, user=user)
                                response += f"result:\n{result}\n---\n"
                                channel.send(response)

                        buffer = lines[-1]

                elif channel.exit_status_ready():
                    break

            except Exception as e:
                log_message(user, f"[Ошибка] {e}")
                break

        channel.close()


def start_ssh_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 2200))
    sock.listen(100)
    log_message('system', "🟢 SSH-сервер запущен на порту 2200")

    while True:
        client, addr = sock.accept()
        log_message('system', f"[Подключение] {addr}")
        transport = paramiko.Transport(client)
        transport.add_server_key(HOST_KEY)
        server = SimpleSSHServer()
        transport.start_server(server=server)

        threading.Thread(target=handle_client, args=(transport, server), daemon=True).start()


if __name__ == "__main__":
    log_message('system', "Ожидание подключений... (Ctrl+C для выхода)")
    server_thread = threading.Thread(target=start_ssh_server, daemon=True)
    server_thread.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        log_message('system', "\nСервер остановлен.")