#!/usr/bin/python3
import socket
import signal
import sys
import argparse
from urllib.parse import urlparse
import selectors

# Discovery Service Address

HOST = ''
PORT = 5000
SERVER = (HOST, PORT)

# Selector for helping us select incoming data from the server and messages typed in by the user.

sel = selectors.DefaultSelector()

# Socket for sending messages.

discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Dictionary to map room names with room uri

roomList = dict()

# Signal handler for graceful exiting.  We let clients know in the process so they can disconnect too.


def signal_handler(sig, frame):
    print('\nInterrupt received, shutting down ...')
    sys.exit(0)

# Process incoming message.


def process_message(message, addr, discovery_socket):

    global roomList

    # Parse the message.

    words = message.split()

    # If room is trying to register itself with discovery service, create an entry for room name with their uri.

    if (words[0] == 'register'):
        if (len(words) == 3):
            roomAddr = f"room://{addr[0]}:{words[2]}"
            if words[1] not in roomList.keys() and roomAddr not in roomList.values():
                print(f'{words[1]} -> {roomAddr} has been registered with service ')
                roomList[words[1]] = roomAddr
                print(roomList)
                return "OK"
            else:
                return "NOTOK Room already registered"
        else:
            return "NOTOK Invalid Command"

    # Room is trying to unregister itself with discovery service, delete roomname and roomuri entry

    if (words[0] == 'deregister'):
        if (len(words) == 2):
            if words[1] in roomList.keys():
                print(f'{words[1]} has been deregistered with discovery service')
                del roomList[words[1]]
                print(roomList)
                return "OK"
            else:
                print(f'{words[1]} is not registered with discovery service')
                return "NOTOK Room not registered"
        else:
            return "NOTOK Invalid Command"

    # Someone has made a look up request in the discovery service, return uri or error

    if (words[0] == 'lookup'):
        if (len(words) == 2):
            if words[1] in roomList.keys():
                print(f'{words[1]} address returned {roomList[words[1]]}')
                return f"OK {roomList[words[1]]}"
            else:
                return "NOTOK Room not registered"
        else:
            return "Invalid Command"

    # Command was not known by discovery service

    return "NOTOK Unknown Command"


def main():
    signal.signal(signal.SIGINT, signal_handler)

    discovery_socket.bind(SERVER)
    print('\nDiscovery Service will wait for requests at port: ' +
          str(discovery_socket.getsockname()[1]))
    
    # Loop forever waiting for messages from clients.

    while True:

        # Receive a packet from a client and process it.

        message, addr = discovery_socket.recvfrom(1024)

        # Process the message and retrieve a response.
        print(message.decode(),addr)
        response = process_message(message.decode(), addr, discovery_socket)

        # Send the response message back to the client.

        discovery_socket.sendto(response.encode(), addr)


if __name__ == '__main__':
    main()
