import argparse
import signal
import socket
import sys
from urllib.parse import urlparse

# Saved information on the room.

name = ''
description = ''
items = []
connections = { 
    "north" : "",
    "south" : "",
    "east" : "",
    "west" : "",
    "up" : "",
    "down" : ""
    }

# The room's socket.

room_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# List of clients currently in the room.

client_list = []

# Signal handler for graceful exiting.  We let clients know in the process so they can disconnect too.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    players=client_list_except_player('')
    message='disconnect'
    for player in players:
        client_addr = client_search(player)
        room_socket.sendto(message.encode(),client_addr) 
    sys.exit(0)

# Search the client list for a particular player.

def client_search(player):
    for reg in client_list:
        if reg[0] == player:
            return reg[1]
    return None

# Search the client list for a particular player by their address.

def client_search_by_address(address):
    for reg in client_list:
        if reg[1] == address:
            return reg[0]
    return None

# Add a player to the client list.

def client_add(player, address):
    registration = (player, address)
    client_list.append(registration)

# Remove a client when disconnected.

def client_remove(player):
    for reg in client_list:
        if reg[0] == player:
            client_list.remove(reg)
            break

# List connected players.

def client_list_except_player(player):
    players = []
    for reg in client_list:
        if reg[0] != player:
            players.append(reg[0])
    return players

# Summarize the room into text.

def summarize_room(player):

    global name
    global description
    global items
    players = client_list_except_player(player)
    combined_list = items + players

    # Pack description into a string and return it.

    summary = name + '\n\n' + description + '\n\n'
    if len(combined_list) == 0:
        summary += "The room is empty.\n"
    elif len(combined_list) == 1:
        summary += "In this room, there is:\n"
        summary += f'  {combined_list[0]}\n'
    else:
        summary += "In this room, there are:\n"
        for item in combined_list:
            summary += f'  {item}\n'

    return summary

# Print a room's description.

def print_room_summary():

    print(summarize_room('')[:-1])

# Process incoming message.

def process_message(message, addr, room_socket):

    global connections

    # Parse the message.
 
    words = message.split()

    # If player is joining the server, add them to the list of players.  Tell other players in the room that they joined.

    if (words[0] == 'join'):
        if (len(words) == 2):
            client_add(words[1],addr)
            print(f'User {words[1]} joined from address {addr}')
            players=client_list_except_player(words[1])
            message=f'{words[1]} entered the room.'
            for player in players:
                client_addr = client_search(player)
                room_socket.sendto(message.encode(),client_addr)
            return summarize_room(words[1])[:-1]            
        else:
            return "Invalid command"

    # If player is leaving the server. remove them from the list of players and notify other people in the room.

    elif (message == 'exit'):
        players=client_list_except_player(client_search_by_address(addr))
        message=f'{client_search_by_address(addr)} left the game.'
        for player in players:
            client_addr = client_search(player)
            room_socket.sendto(message.encode(),client_addr)
        client_remove(client_search_by_address(addr))
        return 'Goodbye'

    # If player looks around, give them the room summary.

    elif (message == 'look'):
        return summarize_room(client_search_by_address(addr))[:-1]
            
    # If player takes an item, make sure it is here and give it to the player.

    elif (words[0] == 'take'):
        if (len(words) == 2):
            if (words[1] in items):
                items.remove(words[1])
                return f'{words[1]} taken'
            else:
                return f'{words[1]} cannot be taken in this room'
        else:
            return "Invalid command"

    # If player drops an item, put in in the list of things here.

    elif (words[0] == 'drop'):
        if (len(words) == 2):
            items.append(words[1])
            return f'{words[1]} dropped'
        else:
            return "Invalid command"

    # If player wanted to go in a direction, respond accordingly.  If player could really go that way,
    # drop them from the server as they're going there next, and tell everyone else.

    elif (words[0] in connections):
        if (connections.get(words[0]) == ""):
            return f'You cannot go {words[0]} from this room.'   
        else:
            players=client_list_except_player(client_search_by_address(addr))
            message=f'{client_search_by_address(addr)} left the room, heading {words[0]}.'
            for player in players:
                client_addr = client_search(player)
                room_socket.sendto(message.encode(),client_addr)
            client_remove(client_search_by_address(addr))            
            return connections.get(words[0])

    # If the player wants to say something, we send it to everyone else.

    elif (words[0] == 'say'):
        if (len(words) == 1):
            return "What did you want to say?"
        else:
            thing_said = message[len(words[0])+1:]
            players=client_list_except_player(client_search_by_address(addr))
            message=f'{client_search_by_address(addr)} said \"{thing_said}\".'
            for player in players:
                client_addr = client_search(player)
                room_socket.sendto(message.encode(),client_addr)
        return f'You said \"{thing_said}\".'

    # Otherwise, the command is bad.

    else:
        return "Invalid command"

# Our main function.

def main():

    global name
    global description
    global items
    global connections
    global room_socket

    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Check command line arguments for room settings.

    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int, help="port number to list on")
    parser.add_argument("name", help="name of the room")
    parser.add_argument("description", help="description of the room")
    parser.add_argument("item", nargs='*', help="items found in the room by default")
    parser.add_argument("-n", help="connecting room to the north", metavar="room://host:port", default="")
    parser.add_argument("-s", help="connecting room to the south", metavar="room://host:port", default="")
    parser.add_argument("-e", help="connecting room to the east", metavar="room://host:port", default="")
    parser.add_argument("-w", help="connecting room to the west", metavar="room://host:port", default="")
    parser.add_argument("-u", help="connecting room upwards", metavar="room://host:port", default="")
    parser.add_argument("-d", help="connecting room downwards", metavar="room://host:port", default="")
    args = parser.parse_args()

    # Set up room based on parameters.

    port=args.port
    name = args.name
    description = args.description
    items = args.item

    # Set up connections to other rooms.

    if args.n != "":
        try:
            connection_address = urlparse(args.n)
            if ((connection_address.scheme != 'room') or (connection_address.port == None) or (connection_address.hostname == None)):
                raise ValueError
        except ValueError:
            print('Error:  Invalid server for direction north.  Enter a server as address:port.')
            sys.exit(1)
        connections.update({"north" : args.n})
    if args.s != "":
        try:
            connection_address = urlparse(args.s)
            if ((connection_address.scheme != 'room') or (connection_address.port == None) or (connection_address.hostname == None)):
                raise ValueError
        except ValueError:
            print('Error:  Invalid server for direction south.  Enter a server as address:port.')
            sys.exit(1)
        connections.update({"south" : args.s})
    if args.e != "":
        try:
            connection_address = urlparse(args.e)
            if ((connection_address.scheme != 'room') or (connection_address.port == None) or (connection_address.hostname == None)):
                raise ValueError
        except ValueError:
            print('Error:  Invalid server for direction east.  Enter a server as address:port.')
            sys.exit(1)
        connections.update({"east" : args.e})
    if args.w != "":
        try:
            connection_address = urlparse(args.w)
            if ((connection_address.scheme != 'room') or (connection_address.port == None) or (connection_address.hostname == None)):
                raise ValueError
        except ValueError:
            print('Error:  Invalid server for direction west.  Enter a server as address:port.')
            sys.exit(1)
        connections.update({"west" : args.w})
    if args.u != "":
        try:
            connection_address = urlparse(args.u)
            if ((connection_address.scheme != 'room') or (connection_address.port == None) or (connection_address.hostname == None)):
                raise ValueError
        except ValueError:
            print('Error:  Invalid server for direction up.  Enter a server as address:port.')
            sys.exit(1)
        connections.update({"up" : args.u})
    if args.d != "":
        try:
            connection_address = urlparse(args.d)
            if ((connection_address.scheme != 'room') or (connection_address.port == None) or (connection_address.hostname == None)):
                raise ValueError
        except ValueError:
            print('Error:  Invalid server for direction down.  Enter a server as address:port.')
            sys.exit(1)
        connections.update({"down" : args.d})

    # Report initial room state.
    
    print('Room Starting Description:\n')
    print_room_summary()

    # Create the socket.  We will ask this to work on any interface and to use
    # the port given at the command line.  We'll print this out for clients to use.

    room_socket.bind(('', port))
    print('\nRoom will wait for players at port: ' + str(room_socket.getsockname()[1]))

    # Loop forever waiting for messages from clients.

    while True:

        # Receive a packet from a client and process it.

        message, addr = room_socket.recvfrom(1024)

        # Process the message and retrieve a response.

        response = process_message(message.decode(), addr, room_socket)

        # Send the response message back to the client.

        room_socket.sendto(response.encode(),addr)


if __name__ == '__main__':
    main()

