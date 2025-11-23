import threading
import socket

host = '127.0.0.1'  # localhost
port = 55556

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
nicknames = []
message_log = []  # Store messages
max_clients = 10


def broadcast(message, save=True):
    if save:
        message_log.append(message.decode('utf-8'))
    for client in clients:
        client.send(message)


def send_private(sender_client, sender_name, target_name, content):
    if target_name not in nicknames:
        sender_client.send(f"ERROR: User '{target_name}' not found.".encode('ascii'))
        return

    target_index = nicknames.index(target_name)
    target_client = clients[target_index]

    # Message to target
    target_client.send(f"[DM from {sender_name}]: {content}".encode('ascii'))

    # Confirmation to sender
    sender_client.send(f"[DM to {target_name}]: {content}".encode('ascii'))


def handle(client, nickname):
    while True:
        try:
            message = client.recv(1024).decode('ascii')

            # normalizer
            text = message.strip()
            cmd = text.upper()

            # logout
            if cmd == 'LOGOUT':
                broadcast(f"{nickname} has logged out!".encode('ascii'))
                clients.remove(client)
                client.close()
                nicknames.remove(nickname)
                break

            # POST
            elif cmd.startswith("POST|"):
                content = message.split("|", 1)[1].strip()
                msg = f"{nickname}: {content}"
                broadcast(msg.encode('ascii'))
                client.send("OK".encode('ascii'))

            # GET
            elif cmd.startswith("GET|"):
                command = message.split("|", 1)[1].strip().lower()
                if command == "latest":
                    last_messages = message_log[-5:]
                    response = "\n".join(last_messages) if last_messages else "No messages yet."
                    client.send(response.encode('ascii'))
                else:
                    client.send("ERROR: Unknown GET command".encode('ascii'))

            # HEAD
            elif cmd.startswith("HEAD"):
                if nicknames:
                    users = "\n".join(nicknames)
                    response = f"Active users:\n{users}"
                else:
                    response = "Active users:\nNone"
                client.send(response.encode('ascii'))

            # OPTIONS
            elif cmd.startswith("OPTIONS"):
                options = "POST, GET, HEAD, OPTIONS, DM, LOGOUT"
                client.send(options.encode('ascii'))

            # DM
            elif cmd.startswith("DM|"):
                parts = message.split("|", 2)
                if len(parts) < 3:
                    client.send("ERROR: Correct format is DM|username|message".encode('ascii'))
                else:
                    target_name = parts[1].strip()
                    content = parts[2].strip()
                    send_private(client, nickname, target_name, content)

            # DEFAULT
            else:
                broadcast(f"{nickname}: {message}".encode('ascii'))

        except:
            if client in clients:
                clients.remove(client)
            client.close()
            if nickname in nicknames:
                nicknames.remove(nickname)
            broadcast(f"--- {nickname} has left the chat ---".encode('ascii'), save=False)
            break


def receive():
    while True:
        client, address = server.accept()

        if len(clients) >= max_clients:
            print(f"Connection attempt from {address}, but server is full.")
            client.send("Server full. Try again later.".encode('ascii'))
            client.close()
            continue

        print(f"Connected with {str(address)}")

        client.send("NICK".encode('ascii'))
        nickname = client.recv(1024).decode('ascii')

        clients.append(client)
        nicknames.append(nickname)

        print(f"Nickname of new client: {nickname}")
        broadcast(f"{nickname} has joined the chat room".encode('ascii'))
        client.send("Connected to server".encode('ascii'))

        thread = threading.Thread(target=handle, args=(client, nickname))
        thread.start()


print("Server is running...")
receive()
