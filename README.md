# room-player-game

This was a networking course assignment 

* The game as a whole is going to be a stripped down text adventure game, like Colossal Caves Adventure or Zork.  Let's face it though, it's not going to be too much of a game -- you only have to implement a handful of commands, and there won't be any story to it.  (What you are doing is certainly extensible though, and so you could in theory add such things on your own if you like!)

* A game server represents a single room or area in the game.  It has a name, a description, a list of items currently in it, and a list of players currently in it (though that list will only contain one player for now).  This means that for this assignment, with a single server, the world is going to be small and confined to a single room.  In Assignment 3, we will add support for multiple servers and so multiple rooms or areas, along with a means for players to move between them.  For now though, a single room will suffice.

* You start the game by launching your game server.  It needs to be first so that your game client can message it to play the game.  

* Players play using the game client.  It gives them a text-based interface to send commands to the game server and display responses that come back.

* When the player is done playing, they press Ctrl-C or use the exit command to tell the server they are done, and the server no longer considers them as part of the game.  The game server should run persistently; however, it should also terminate when given a Ctrl-C signal.  The server will not, at this point at least, nicely let clients know that it is shutting down before it shuts down.

## first iteration

- Your game client and server will communicate with one another via UDP.  For our purposes here, we will assume that UDP is reliable and will not drop packets.  (When doing everything on a single computer or over a LAN, this is a reasonably safe assumption.)
- The game server will require a number of command line options, given in this order: 
  - port:  The port number that the server will wait for client messages on.
  - name:  The name of the room running on the server.
  - description:  A textual description of the room.
  - items:  A list of items to be found in the room initially.
- See the above screenshots for a sample invocation of a server.   To assist in processing parameters, you can use the argparse package in your application.
- The game client will also require a number of command line options, given in this order:
- player-name:  The single-word name of the player in the game
- server-address:  An address for the game server to message, in the form of room://host:port where host is the hostname the server is executing on and port is the port number it is listening to for requests.  If an invalid address for the server is given, an appropriate error must be reported to the user and the client terminates.  To assist in parsing the server address in URL format, I suggest you look at urlparse from the urllib package.  (You may not use any other parts of the urllib package, however.)
- See the above screenshots for a sample invocation of a client.
- As noted above, you server only needs to worry about processing messages from a single client at a time.  That said, the server should still maintain a list of clients whose players are in the room at the moment.  (The list will only have one client this assignment, but it will come in handy later.)
- The following commands need to be supported by the game client and server:
  - join:  The player enters the room, providing the name they wish to be known by.  This command happens automatically when the client is run, and the user does not need to type this message.  (This can be seen from the above screenshots.). When a server has been joined, the server gives a summary of the room to the client that should be displayed to the user.
  - look:  Display the name, description, and contents of the room.  If there are no items in the room, you should indicate that the room is empty.
  - take:  Take an item from the room and add it to the player's inventory.  The item must exist in the room to be taken.
  - drop:  Take an item from the player's inventory and add it to the room.  The item must exist in the player's inventory to be dropped.
  - inventory:  List the player's inventory.  If the player currently has nothing in their inventory, you should repot that they are holding nothing.
  - exit:  The player leaves the game, dropping any items in their inventory into the room before leaving.  The game client then terminates.
- If an invalid command is sent from the client to the server, the server must catch this and report this back to the client.  The client will then display this message to the player. If for some reason a command cannot be completed (for example, the player tries dropping an item they do not have), this should also result in a sensible error message.
- The user may also press Ctrl-C to interrupt the game client; the client must catch that signal (using a signal handler from the signal package) and exit the server as if the user used the exit command at the client.
- When the user presses Ctrl-C to interrupt the game server, the server must likewise catch that signal (again using a signal handler from the signal package).  It does not need to inform the client that it is shutting down in this assignment.
- In the absence of shutting down as noted above, both the game client and game server will run continuously, passing messages back and forth.

*Starting a room*
```bash
python3 room.py 7777 Foyer "The entry way to an old house. Weathered, but still tidy and clean." "vase" "rug"
```

*Starting player client*
```bash
python3 player.py bob room://localhost:7777
```

## second iteration

The main addition is that the game now must support multiple simultaneous players across multiple servers.  Players will be able to see and say things to one another and also move from room to room (which means from server to server).
 
* When a player receives a room description from the room server, either by joining a room or by using the look command, other players will now be listed among what they can see in the room. A player should never see themselves listed as being present in the room; only other players in the room should be visible.  For example, if Alice is in a room and Bob enters the room, Bob will see Alice in the description of the room.

* Likewise, when another player enters the room a player is in, the server should notify them of the new player so it can be reported accordingly.  Continuing the above example, when Bob enters the room and Alice is already in the room, Alice will be notified of Bob's entry.
 
* This does mean that the server must be able to send messages to the client on its own and not simply in response to messages from the client.  More on that below.
  
* Players will be able to move from room to room now, using the commands north, south, east, west, up, and down.  When a room server is started, optional parameters must now be given for those directions leading away from the room hosted by the server.  These parameters will indicate the direction and give an address of the room in that direction in the form room://host:port (like the client uses in connecting with servers.)  For example, if the Foyer was running on port 5555 on localhost, and the Study was located on port 4444, they might be executed as follows:
 
* As you can see, the -n and -s options are used for specifying rooms to the north and the south.  Likewise, -e, -w, -u, and -d will allow you to specify rooms to the east, west, up, and down directions respectively.  Rooms do not need connections to other rooms in every direction; you only need to specify the directions that are actually needed and used in the game.  Continuing the previous example, if Alice was to head north using the north command, it would appear like this:
 
* When a player leaves a room and moves to another, they take all their inventory items with them to the new room.  This does mean that players can pick something up in one room and drop it in a different room.  (Please note that players can never pick up other players though!)  In effect, moving from one room to another amounts to exiting the one server and joining the other.
  
* Players will also see other players leave the room that they share with them, being notified of such occurrences by the server.  Continuing the above example, if Alice headed north, the server would notify Bob that Alice left, indicating the direction she headed in at the same time.

* Alternatively, if a player in the same room leaves the game entirely, the server should still notify the players in that room, but use a slightly different message.  For example, if Alice had instead exited the game using the exit command, Bob would have seen a message like what is depicted below.

* Players can now say things using the "say" command.  Whatever message they write on the line following the say command is passed to the server, and the server then distributes it to all other players currently in the room, who then immediately display it.  (The player who spoke does not receive a copy of things in that fashion, but rather gets an acknowledgement that they said what they said.)  If no additional text is given, the player is given an error message notifying them of this.  For example, if Alice said something in the same room as Bob, her display would look like this.

* Bob would get immediately notified of Alice speaking by the room server, without having to enter any commands.  His display would appear as follows.
 
* Now that the room server can message clients whenever they need to, and clients will receive them and process them even if they are waiting for user input, the server can now have a signal handler that notifies players when it is shut down using a Ctrl-C signal.  When that is done, it should send a "disconnect" message to every client on the server.  Clients receiving such messages should exit right away.  For example, let's suppose the Foyer room server is shut down.  Its display would look like:

* Note that it also prints a message when shutting down.  Alice would receive the disconnect message from the server and shut down immediately.  Her display would appear as follows.

* As noted above, your game clients now need to be able to both accept new commands typed by the user and messages sent by the server at the same time.  (There is no way to tell which will be happening when ... both could happen at any time.)  Messages from the server will include activity of other players in the same room (coming, going, saying things) as well as potential disconnect messages.  To enable this, I recommend using the selectors package in Python or the lower-level select package.  This will allow you to wait from input from multiple sources (the keyboard and your client's socket) at the same time instead of just a single source (the keyboard) in the previous assignment.

*Specifying adjacent room*
```bash
python3 room.py -n room://localhost:4444 7777 Foyer "The entry way to an old house. Weathered, but still tidy and clean." "vase" "rug"
```

## third iteration

 First, clients have no proper way of handling a server disappearing unexpectedly, or not being there in the first place.  They would send off a message to the server and wait indefinitely for a reply that is never coming.  Second, keeping track of all of the addresses for all of the different rooms is painful for both players and for the rooms.  As the game world gets larger, this becomes a bigger and bigger problem.

To solve the first challenge, you will add timeouts to the player client.  That way, if it does not hear from the server after a decent amount of time, it can report an error and exit appropriately.   No more waiting around forever!  

To solve the second challenge, you will build a simple discovery service for rooms.  When a room server starts, it registers its name and address with the discovery service.  Later, when player clients or other room servers need to connect with it, they can lookup the address for the server by querying the discovery service.  This way, the various parts of the game need only identify themselves by name, and the discovery service handles the yucky part of keeping track of all of the corresponding addresses.   Convenient!

* The discovery service you create will map room names into server addresses of the form room://host:port, the same format used in previous assignments.

* Before starting any room servers or player clients, your discovery service would be started.  It will listen on a fixed UDP port for incoming requests.  This port number will be stored as a constant in the discovery service, as well as the player client and room service.  The player client and room service will also have the host address for the discovery service stored in a constant.  (Ordinarily, we would use broadcasting to find the discovery service, but the university would likely not like all of us broadcasting around quite so much ...)

* The discovery server must support the following messages:

    * REGISTER room://host:port name
    * Registers a server, with host giving the name of your server, port giving its port number, and name being the name of the room, given as a parameter to the room server on the command line.

    * DEREGISTER name
    * Deletes the registration for the server registered under the given name.

    * LOOKUP name
    * Attempts to lookup the address of a server with the given name.

* In response to messages, the discovery service will return the following responses:
    * OK result
        * The request was successful; result contains the optional results of the request.  (Nothing for REGISTER/DEREGISTER, the address for the server with LOOKUP.)

    * NOTOK msg
        * The request was not successful; msg contains an error message describing the result.

* When a room server starts, it no longer takes a port number as a command line parameter.  Instead, the server will ask the system to allocate it an available port number.  The server will then register with the discovery service by sending it a REGISTER request.  When receiving a REGISTER request, the discovery service will record the name to address mapping for the incoming server if they are unique, sending an OK response back to the server.  If the name or the address have been previously registered, the discovery service will send a NOTOK response with an appropriate error message.  In such a case, the room server reports the error to the user and terminates.

* When a room server terminates, it sends the discovery service a DEREGISTER request.  When receiving a DEREGISTER request, the discovery service will attempt to remove the registration for the named server from its records.  If the record existed and was removed, it sends an OK response back to the server.  Otherwise, it sends a NOTOK response back to the server.  (In practice, this shouldn't happen, but should things should handle errors appropriately.)

* Connections to other rooms are still specified on the command line when starting a room server using the -n, -s, -e, -w, -u, and -d parameters.  This time, however, instead of specifying these connections using the addresses of the corresponding servers, you would simply use the name of the server instead.  For example, if a room is connected to the Foyer to its north, you would indicate this by passing the parameters "-n Foyer" to the server on startup, instead of specifying the address of the other server.

* When a player client starts, it no longer takes a server address as a parameter on its command line.  Instead, it takes the name of room to start in.  For example, if player Alice wants to start in the Foyer, they would invoke their client by executing:  "python3 player.py Alice Foyer"

* In the process of joining a room, the player client first determines the address of the server hosting the room by issuing a LOOKUP request to the discovery service.  On receiving a LOOKUP request, the discovery service will attempt to find the named server in its records.  On success, it returns an OK response to the requesting client, sending along the address of the server in room://host:port format to the client.  If the named room does not exist in its records, the discovery service instead returns a NOTOK response along with an error message.  In such a case, the receiving client would print the error message to the user and terminate.

* Similarly, whenever the player moves from room to room, these new joins will follow a similar process, with a LOOKUP request to the discovery service providing the address of the new room service.

* If a room server needs to connect to another server, for example to transfer inventories of moving players if the inventories were stored server-side instead of client-side, the server will similarly use a LOOKUP request to the discovery service to get the address it needs to send it its message.

*Specifying adjacent room*
```bash
python3 room.py -n <roomname> "The entry way to an old house. Weathered, but still tidy and clean." "vase" "rug"
```

*Starting discovery service*
```bash
python3 discovery.py
```

