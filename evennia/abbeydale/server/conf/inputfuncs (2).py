"""
Input functions

Input functions are always called from the client (they handle server
input, hence the name).

This module is loaded by being included in the
`settings.INPUT_FUNC_MODULES` tuple.

All *global functions* included in this module are considered
input-handler functions and can be called by the client to handle
input.

An input function must have the following call signature:

    cmdname(session, *args, **kwargs)

Where session will be the active session and *args, **kwargs are extra
incoming arguments and keyword properties.

A special command is the "default" command, which is will be called
when no other cmdname matches. It also receives the non-found cmdname
as argument.

    default(session, cmdname, *args, **kwargs)

"""

# def oob_echo(session, *args, **kwargs):
#     """
#     Example echo function. Echoes args, kwargs sent to it.
#
#     Args:
#         session (Session): The Session to receive the echo.
#         args (list of str): Echo text.
#         kwargs (dict of str, optional): Keyed echo text
#
#     """
#     session.msg(oob=("echo", args, kwargs))
#
#
# def default(session, cmdname, *args, **kwargs):
#     """
#     Handles commands without a matching inputhandler func.
#
#     Args:
#         session (Session): The active Session.
#         cmdname (str): The (unmatched) command name
#         args, kwargs (any): Arguments to function.
#
#     """
#     pass


import json
from evennia import default_cmds
from typeclasses.rooms import Room

def dungeon_info(session, *args, **kwargs):

    rooms= Room.objects.all_family()

    argsarray = []
    
    for room in rooms:
        roomdict = { 'exits': [], 'contents': [], 'id': room.dbid, 'key': room.key, 'name': room.name}

        for co in room.contents:
            mycontents= { 'id': co.dbid, 'name': co.name }
            roomdict['contents'].append(mycontents)

        for ex in room.exits:
            myexit = { 'destination': ex.destination.name, 'destinationid': ex.destination.dbid, 'name': ex.name, 'id': ex.dbid }
            roomdict['exits'].append(myexit)

        argsarray.append(roomdict)

    session.msg(dungeon_info=(argsarray,kwargs))

