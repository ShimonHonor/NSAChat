import threading
import socket

host = '127.0.0.1'  # localhost
port = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
max_clients = 10
nicknames = []
message_log = []  # Store messages


def broadcast(message, save=True):
    if save:
        message_log.append(message.decode('utf-8'))  # store as str
    for client in clients:
        client.send(message)


def handle(client, nickname):
    while True:
        try:
            message = client.recv(1024).decode('ascii')

            if message == 'logout':
                broadcast(f'{nickname} has logged out!'.encode('ascii'))
                clients.remove(client)
                client.close()
                break

            elif message.startswith("POST|"):
                content = message.split("|", 1)[1].strip()
                msg = f"{nickname}: {content}"
                broadcast(msg.encode('ascii'))
                client.send("OK".encode('ascii'))

            elif message.startswith("GET|"):
                command = message.split("|", 1)[1].strip()
                if command == "latest":  # Sends last 5 messages
                    last_messages = message_log[-5:]
                    response = "\n".join(last_messages) if last_messages else "No messages yet."
                    client.send(response.encode('ascii'))
                else:
                    client.send("ERROR: Unknown GET command".encode('ascii'))

            else:
                # Regular chat message
                broadcast(f"{nickname}: {message}".encode('ascii'))

        except:
            clients.remove(client)
            client.close()
            broadcast(f"--- {nickname} has left the chat ---".encode('ascii'), save=False)
            nicknames.remove(nickname)
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

        client.send('Nickname: '.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        nicknames.append(nickname)
        clients.append(client)
        print(f"Nickname of the new client: {nickname}")
        broadcast(f"{nickname} has joined the chat room".encode('ascii'))
        client.send("Connected to server".encode('ascii'))

        thread = threading.Thread(target=handle, args=(client, nickname))
        thread.start()


print("Server is running...")
receive()
