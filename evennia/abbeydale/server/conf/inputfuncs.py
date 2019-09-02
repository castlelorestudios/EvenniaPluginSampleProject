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
import json
from evennia import default_cmds
from typeclasses.rooms import Room

def dungeon_info(session, *args, **kwargs):

    rooms= Room.objects.all_family()

    data = {}

    data['world'] = []
    
    for room in rooms:
        roomdict = { 'id': room.dbid, 'name': room.name, 'key': room.key, 'exits': [], 'contents': []}

        for ex in room.exits:
            myexit = { 'id': ex.dbid, 'name': ex.name }
            roomdict['exits'].append(myexit)

        for co in room.contents:
            mycontents= { 'id': co.dbid, 'name': co.name }
            roomdict['contents'].append(mycontents)

        data['world'].append(roomdict)

    session.msg(json.dumps(data))

