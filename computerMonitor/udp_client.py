import socket

server = None
unicast_port = None
unicast_ip = "255.255.255.255"


def send(message):
    if server:
        server.sendto(message, (unicast_ip, unicast_port))
        retry_times = 2
        while retry_times > 0:
            retry_times -= 1
            try:
                data, client_address = server.recvfrom(1024)
                data = eval(data.decode())
                if client_address[0] != unicast_ip: continue

                if not isinstance(data, dict): return "Invalid payload data"
                elif data.get("code", 500) == 200: return "Sent successfully."
                else: return f"Device receive error ({data.get('error', 'Unknown error')})"
            except socket.timeout: continue
        return "Send timeout."
    else:
        return "Service not started."

def init(port=32123):
    global server, unicast_port
    unicast_port = port

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Enable port reusage so we will be able to run multiple clients and servers on single (host, port).
    # Do not use socket.SO_REUSEADDR except you using linux(kernel<3.9): goto https://stackoverflow.com/questions/14388706/how-do-so-reuseaddr-and-so-reuseport-differ for more information.
    # For linux hosts all sockets that want to share the same address and port combination must belong to processes that share the same effective user ID!
    # So, on linux(kernel>=3.9) you have to run multiple servers and clients under one user to share the same (host, port).
    # Thanks to @stevenreddie
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Enable broadcasting mode
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Set a timeout so the socket does not block
    # indefinitely when trying to receive data.
    server.settimeout(2)
