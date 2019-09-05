"""
Wilderness system

Evennia contrib - titeuf87 2017

This contrib provides a wilderness map. This is an area that can be huge where
the rooms are mostly similar, except for some small cosmetic changes like the
room name.

Usage:

    This contrib does not provide any commands. Instead the @py command can be
    used.

    A wilderness map needs to created first. There can be different maps, all
    with their own name. If no name is provided, then a default one is used. Internally,
    the wilderness is stored as a Script with the name you specify. If you don't
    specify the name, a script named "default" will be created and used.

    @py from evennia.contrib import wilderness; wilderness.create_wilderness()

    Once created, it is possible to move into that wilderness map:

    @py from evennia.contrib import wilderness; wilderness.enter_wilderness(me)

    All coordinates used by the wilderness map are in the format of `(x, y)`
    tuples. x goes from left to right and y goes from bottom to top. So `(0, 0)`
    is the bottom left corner of the map.


Customisation:

    The defaults, while useable, are meant to be customised. When creating a
    new wilderness map it is possible to give a "map provider": this is a
    python object that is smart enough to create the map.

    The default provider, WildernessMapProvider, just creates a grid area that
    is unlimited in size.
    This WildernessMapProvider can be subclassed to create more interesting
    maps and also to customize the room/exit typeclass used.

    There is also no command that allows players to enter the wilderness. This
    still needs to be added: it can be a command or an exit, depending on your
    needs.

Customisation example:

    To give an example of how to customize, we will create a very simple (and
    small) wilderness map that is shaped like a pyramid. The map will be
    provided as a string: a "." symbol is a location we can walk on.

    Let's create a file world/pyramid.py:

    ```python
    map_str = \"\"\"
         .
        ...
       .....
      .......
    \"\"\"

    from evennia.contrib import wilderness

    class PyramidMapProvider(wilderness.WildernessMapProvider):

        def is_valid_coordinates(self, wilderness, coordinates):
            "Validates if these coordinates are inside the map"
            x, y = coordinates
            try:
                lines = map_str.split("\n")
                # The reverse is needed because otherwise the pyramid will be
                # upside down
                lines.reverse()
                line = lines[y]
                column = line[x]
                return column == "."
            except IndexError:
                return False

        def get_location_name(self, coordinates):
            "Set the location name"
            x, y = coordinates
            if y == 3:
                return "Atop the pyramid."
            else:
                return "Inside a pyramid."

        def at_prepare_room(self, coordinates, caller, room):
            "Any other changes done to the room before showing it"
            x, y = coordinates
            desc = "This is a room in the pyramid."
            if y == 3 :
                desc = "You can see far and wide from the top of the pyramid."
            room.db.desc = desc
    ```

    Now we can use our new pyramid-shaped wilderness map. From inside Evennia we
    create a new wilderness (with the name "default") but using our new map provider:

    ```
    @py from world import pyramid as p; p.wilderness.create_wilderness(mapprovider=p.PyramidMapProvider())

    @py from evennia.contrib import wilderness; wilderness.enter_wilderness(me, coordinates=(4, 1))

    ```
Implementation details:

    When a character moves into the wilderness, they get their own room. If
    they move, instead of moving the character, the room changes to match the
    new coordinates.
    If a character meets another character in the wilderness, then their room
    merges. When one of the character leaves again, they each get their own
    separate rooms.
    Rooms are created as needed. Unneeded rooms are stored away to avoid the
    overhead cost of creating new rooms again in the future.

"""

from evennia import DefaultRoom, DefaultExit, DefaultScript
from evennia import create_object, create_script
from evennia.utils import inherits_from


def create_wilderness(name="default", mapprovider=None):
    """
    Creates a new wilderness map. Does nothing if a wilderness map already
    exists with the same name.

    Args:
        name (str, optional): the name to use for that wilderness map
        mapprovider (WildernessMap instance, optional): an instance of a
            WildernessMap class (or subclass) that will be used to provide the
            layout of this wilderness map. If none is provided, the default
            infinite grid map will be used.

    """
    if WildernessScript.objects.filter(db_key=name).exists():
        # Don't create two wildernesses with the same name
        return

    if not mapprovider:
        mapprovider = WildernessMapProvider()
    script = create_script(WildernessScript, key=name)
    script.db.mapprovider = mapprovider


def enter_wilderness(obj, coordinates=(0, 0), name="default"):
    """
    Moves obj into the wilderness. The wilderness needs to exist first and the
    provided coordinates needs to be valid inside that wilderness.

    Args:
        obj (object): the object to move into the wilderness
        coordinates (tuple), optional): the coordinates to move obj to into
            the wilderness. If not provided, defaults (0, 0)
        name (str, optional): name of the wilderness map, if not using the
            default one

    Returns:
        bool: True if obj successfully moved into the wilderness.
    """
    if not WildernessScript.objects.filter(db_key=name).exists():
        return False

    script = WildernessScript.objects.get(db_key=name)
    if script.is_valid_coordinates(coordinates):
        script.move_obj(obj, coordinates)
        return True
    else:
        return False


def get_new_coordinates(coordinates, direction):
    """
    Returns the coordinates of direction applied to the provided coordinates.

    Args:
        coordinates: tuple of (x, y)
        direction: a direction string (like "northeast")

    Returns:
        tuple: tuple of (x, y) coordinates
    """
    x, y = coordinates

    if direction in ("north", "northwest", "northeast"):
        y += 1
    if direction in ("south", "southwest", "southeast"):
        y -= 1
    if direction in ("northwest", "west", "southwest"):
        x -= 1
    if direction in ("northeast", "east", "southeast"):
        x += 1

    return (x, y)


class WildernessScript(DefaultScript):
    """
    This is the main "handler" for the wilderness system: inside here the
    coordinates of every item currently inside the wilderness is stored. This
    script is responsible for creating rooms as needed and storing rooms away
    into storage when they are not needed anymore.
    """

    def at_script_creation(self):
        """
        Only called once, when the script is created. This is a default Evennia
        hook.
        """
        self.persistent = True

        # Store the coordinates of every item that is inside the wilderness
        # Key: object, Value: (x, y)
        self.db.itemcoordinates = {}

        # Store the rooms that are used as views into the wilderness
        # Key: (x, y), Value: room object
        self.db.rooms = {}

        # Created rooms that are not needed anymore are stored there. This
        # allows quick retrieval if a new room is needed without having to
        # create it.
        self.db.unused_rooms = []

    @property
    def mapprovider(self):
        """
        Shortcut property to the map provider.

        Returns:
            MapProvider: the mapprovider used with this wilderness
        """
        return self.db.mapprovider

    @property
    def itemcoordinates(self):
        """
        Returns a dictionary with the coordinates of every item inside this
        wilderness map. The key is the item, the value are the coordinates as
        (x, y) tuple.

        Returns:
            {item: coordinates}
        """
        return self.db.itemcoordinates

    def at_start(self):
        """
        Called when the script is started and also after server reloads.
        """
        for coordinates, room in self.db.rooms.items():
            room.ndb.wildernessscript = self
            room.ndb.active_coordinates = coordinates
        for item in self.db.itemcoordinates.keys():
            # Items deleted from the wilderness leave None type 'ghosts'
            # that must be cleaned out
            if item is None:
                del self.db.itemcoordinates[item]
                continue
            item.ndb.wilderness = self

    def is_valid_coordinates(self, coordinates):
        """
        Returns True if coordinates are valid (and can be travelled to).
        Otherwise returns False

        Args:
            coordinates (tuple): coordinates as (x, y) tuple

        Returns:
            bool: True if the coordinates are valid
        """
        return self.mapprovider.is_valid_coordinates(self, coordinates)

    def get_obj_coordinates(self, obj):
        """
        Returns the coordinates of obj in the wilderness.

        Returns (x, y)

        Args:
            obj (object): an object inside the wilderness

        Returns:
            tuple: (x, y) tuple of where obj is located
        """
        return self.itemcoordinates[obj]

    def get_objs_at_coordinates(self, coordinates):
        """
        Returns a list of every object at certain coordinates.

        Imeplementation detail: this uses a naive iteration through every
        object inside the wilderness which could cause slow downs when there
        are a lot of objects in the map.

        Args:
            coordinates (tuple): a coordinate tuple like (x, y)

        Returns:
            [Object, ]: list of Objects at coordinates
        """
        result = []
        for item, item_coordinates in self.itemcoordinates.items():
            # Items deleted from the wilderness leave None type 'ghosts'
            # that must be cleaned out
            if item is None:
                del self.db.itemcoordinates[item]
                continue
            if coordinates == item_coordinates:
                result.append(item)
        return result

    def move_obj(self, obj, new_coordinates):
        """
        Moves obj to new coordinates in this wilderness.

        Args:
            obj (object): the object to move
            new_coordinates (tuple): tuple of (x, y) where to move obj to.
        """
        # Update the position of this obj in the wilderness
        self.itemcoordinates[obj] = new_coordinates
        old_room = obj.location

        # Remove the obj's location. This is needed so that the object does not
        # appear in its old room should that room be deleted.
        obj.location = None

        try:
            # See if we already have a room for that location
            room = self.db.rooms[new_coordinates]
            # There is. Try to destroy the old_room if it is not needed anymore
            self._destroy_room(old_room)
        except KeyError:
            # There is no room yet at new_location
            if (old_room and not inherits_from(old_room, WildernessRoom)) or \
               (not old_room):
                # Obj doesn't originally come from a wilderness room.
                # We'll create a new one then.
                room = self._create_room(new_coordinates, obj)
            else:
                # Obj does come from another wilderness room
                create_new_room = False

                if old_room.wilderness != self:
                    # ... but that other wilderness room belongs to another
                    # wilderness map
                    create_new_room = True
                    old_room.wilderness.at_after_object_leave(obj)
                else:
                    for item in old_room.contents:
                        if item.has_account:
                            # There is still a player in the old room.
                            # Let's create a new room and not touch that old
                            # room.
                            create_new_room = True
                            break

                if create_new_room:
                    # Create a new room to hold obj, not touching any obj's in
                    # the old room
                    room = self._create_room(new_coordinates, obj)
                else:
                    # The old_room is empty: we are just going to reuse that
                    # room instead of creating a new one
                    room = old_room

        room.set_active_coordinates(new_coordinates, obj)
        obj.location = room
        obj.ndb.wilderness = self

    def _create_room(self, coordinates, report_to):
        """
        Gets a new WildernessRoom to be used for the provided coordinates.

        It first tries to retrieve a room out of storage. If there are no rooms
        left a new one will be created.

        Args:
            coordinates (tuple): coordinate tuple of (x, y)
            report_to (object): the obj to return error messages to
        """
        if self.db.unused_rooms:
            # There is still unused rooms stored in storage, let's get one of
            # those
            room = self.db.unused_rooms.pop()
        else:
            # No more unused rooms...time to make a new one.

            # First, create the room
            room = create_object(typeclass=self.mapprovider.room_typeclass,
                                 key="Wilderness",
                                 report_to=report_to)

            # Then the exits
            exits = [("north", "n"),
                     ("northeast", "ne"),
                     ("east", "e"),
                     ("southeast", "se"),
                     ("south", "s"),
                     ("southwest", "sw"),
                     ("west", "w"),
                     ("northwest", "nw")]
            for key, alias in exits:
                create_object(typeclass=self.mapprovider.exit_typeclass,
                              key=key,
                              aliases=[alias],
                              location=room,
                              destination=room,
                              report_to=report_to)

        room.ndb.active_coordinates = coordinates
        room.ndb.wildernessscript = self
        self.db.rooms[coordinates] = room

        return room

    def _destroy_room(self, room):
        """
        Moves a room back to storage. If room is not a WildernessRoom or there
        is a player inside the room, then this does nothing.

        Args:
            room (WildernessRoom): the room to put in storage
        """
        if not room or not inherits_from(room, WildernessRoom):
            return

        for item in room.contents:
            if item.has_account:
                # There is still a character in that room. We can't get rid of
                # it just yet
                break
        else:
            # No characters left in the room.

            # Clear the location of every obj in that room first
            for item in room.contents:
                if item.destination and item.destination == room:
                    # Ignore the exits, they stay in the room
                    continue
                item.location = None

            # Then delete its reference
            del self.db.rooms[room.ndb.active_coordinates]
            # And finally put this room away in storage
            self.db.unused_rooms.append(room)

    def at_after_object_leave(self, obj):
        """
        Called after an object left this wilderness map. Used for cleaning up.

        Args:
            obj (object): the object that left
        """
        # Remove that obj from the wilderness's coordinates dict
        loc = self.db.itemcoordinates[obj]
        del self.db.itemcoordinates[obj]

        # And see if we can put that room away into storage.
        room = self.db.rooms[loc]
        self._destroy_room(room)


class WildernessRoom(DefaultRoom):
    """
    This is a single room inside the wilderness. This room provides a "view"
    into the wilderness map. When an account moves around, instead of going to
    another room as with traditional rooms, they stay in the same room but the
    room itself changes to display another area of the wilderness.
    """

    @property
    def wilderness(self):
        """
        Shortcut property to the wilderness script this room belongs to.

        Returns:
            WildernessScript: the WildernessScript attached to this room
        """
        return self.ndb.wildernessscript

    @property
    def location_name(self):
        """
        Returns the name of the wilderness at this room's coordinates.

        Returns:
            name (str)
        """
        return self.wilderness.mapprovider.get_location_name(
            self.coordinates)

    @property
    def coordinates(self):
        """
        Returns the coordinates of this room into the wilderness.

        Returns:
            tuple: (x, y) coordinates of where this room is inside the
                wilderness.
        """
        return self.ndb.active_coordinates

    def at_object_receive(self, moved_obj, source_location):
        """
        Called after an object has been moved into this object. This is a
        default Evennia hook.

        Args:
            moved_obj (Object): The object moved into this one.
            source_location (Object): Where `moved_obj` came from.
        """
        if isinstance(moved_obj, WildernessExit):
            # Ignore exits looping back to themselves: those are the regular
            # n, ne, ... exits.
            return

        itemcoords = self.wilderness.db.itemcoordinates
        if moved_obj in itemcoords:
            # This object was already in the wilderness. We need to make sure
            # it goes to the correct room it belongs to.
            # Otherwise the following issue can come up:
            # 1) Player 1 and Player 2 share a room
            # 2) Player 1 disconnects
            # 3) Player 2 moves around
            # 4) Player 1 reconnects
            # Player 1 will end up in player 2's room, which has the wrong
            # coordinates

            coordinates = itemcoords[moved_obj]
            # Setting the location to None is important here so that we always
            # get a "fresh" room
            moved_obj.location = None
            self.wilderness.move_obj(moved_obj, coordinates)
        else:
            # This object wasn't in the wilderness yet. Let's add it.
            itemcoords[moved_obj] = self.coordinates

    def at_object_leave(self, moved_obj, target_location):
        """
        Called just before an object leaves from inside this object. This is a
        default Evennia hook.

        Args:
            moved_obj (Object): The object leaving
            target_location (Object): Where `moved_obj` is going.

        """
        self.wilderness.at_after_object_leave(moved_obj)

    def set_active_coordinates(self, new_coordinates, obj):
        """
        Changes this room to show the wilderness map from other coordinates.

        Args:
            new_coordinates (tuple): coordinates as tuple of (x, y)
            obj (Object): the object that moved into this room and caused the
                coordinates to change
        """
        # Remove the reference for the old coordinates...
        rooms = self.wilderness.db.rooms
        del rooms[self.coordinates]
        # ...and add it for the new coordinates.
        self.ndb.active_coordinates = new_coordinates
        rooms[self.coordinates] = self

        # Every obj inside this room will get its location set to None
        for item in self.contents:
            if not item.destination or item.destination != item.location:
                item.location = None
        # And every obj matching the new coordinates will get its location set
        # to this room
        for item in self.wilderness.get_objs_at_coordinates(new_coordinates):
            item.location = self

        # Fix the lockfuncs for the exit so we can't go where we're not
        # supposed to go
        for exit in self.exits:
            if exit.destination != self:
                continue
            x, y = get_new_coordinates(new_coordinates, exit.key)
            valid = self.wilderness.is_valid_coordinates((x, y))

            if valid:
                exit.locks.add("traverse:true();view:true()")
            else:
                exit.locks.add("traverse:false();view:false()")

        # Finally call the at_prepare_room hook to give a chance to further
        # customise it
        self.wilderness.mapprovider.at_prepare_room(new_coordinates, obj, self)

    def get_display_name(self, looker, **kwargs):
        """
        Displays the name of the object in a viewer-aware manner.

        Args:
            looker (TypedObject): The object or account that is looking
                at/getting inforamtion for this object.

        Returns:
            name (str): A string containing the name of the object,
                including the DBREF if this user is privileged to control
                said object and also its coordinates into the wilderness map.

        Notes:
            This function could be extended to change how object names
            appear to users in character, but be wary. This function
            does not change an object's keys or aliases when
            searching, and is expected to produce something useful for
            builders.
        """
        if self.locks.check_lockstring(looker, "perm(Builder)"):
            name = "{}(#{})".format(self.location_name, self.id)
        else:
            name = self.location_name

        name += " {0}".format(self.coordinates)
        return name


class WildernessExit(DefaultExit):
    """
    This is an Exit object used inside a WildernessRoom. Instead of changing
    the location of an Object traversing through it (like a traditional exit
    would do) it changes the coordinates of that traversing Object inside
    the wilderness map.
    """

    @property
    def wilderness(self):
        """
        Shortcut property to the wilderness script.

        Returns:
            WildernessScript: the WildernessScript attached to this exit's room
        """
        return self.location.wilderness

    @property
    def mapprovider(self):
        """
        Shortcut property to the map provider.

        Returns:
            MapProvider object: the mapprovider object used with this
                wilderness map.
        """
        return self.wilderness.mapprovider

    def at_traverse_coordinates(self, traversing_object, current_coordinates,
                                new_coordinates):
        """
        Called when an object wants to travel from one place inside the
        wilderness to another place inside the wilderness.

        If this returns True, then the traversing can happen. Otherwise it will
        be blocked.

        This method is similar how the `at_traverse` works on normal exits.

        Args:
            traversing_object (Object): The object doing the travelling.
            current_coordinates (tuple): (x, y) coordinates where
                `traversing_object` currently is.
            new_coordinates (tuple): (x, y) coordinates of where
                `traversing_object` wants to travel to.

        Returns:
            bool: True if traversing_object is allowed to traverse
        """
        return True

    def at_traverse(self, traversing_object, target_location):
        """
        This implements the actual traversal. The traverse lock has
        already been checked (in the Exit command) at this point.

        Args:
            traversing_object (Object): Object traversing us.
            target_location (Object): Where target is going.

        Returns:
            bool: True if the traverse is allowed to happen

        """
        itemcoordinates = self.location.wilderness.db.itemcoordinates

        current_coordinates = itemcoordinates[traversing_object]
        new_coordinates = get_new_coordinates(current_coordinates, self.key)

        if not self.at_traverse_coordinates(traversing_object,
                                            current_coordinates,
                                            new_coordinates):
            return False

        if not traversing_object.at_before_move(None):
            return False
        traversing_object.location.msg_contents("{} leaves to {}".format(
            traversing_object.key, new_coordinates),
            exclude=[traversing_object])

        self.location.wilderness.move_obj(traversing_object, new_coordinates)

        traversing_object.location.msg_contents("{} arrives from {}".format(
            traversing_object.key, current_coordinates),
            exclude=[traversing_object])

        traversing_object.at_after_move(None)
        return True


class WildernessMapProvider(object):
    """
    Default Wilderness Map provider.

    This is a simple provider that just creates an infinite large grid area.
    """
    room_typeclass = WildernessRoom
    exit_typeclass = WildernessExit

    def is_valid_coordinates(self, wilderness, coordinates):
        """Returns True if coordinates is valid and can be walked to.

        Args:
            wilderness: the wilderness script
            coordinates (tuple): the coordinates to check as (x, y) tuple.

        Returns:
            bool: True if the coordinates are valid
        """
        x, y = coordinates
        if x < 0:
            return False
        if y < 0:
            return False

        return True

    def get_location_name(self, coordinates):
        """
        Returns a name for the position at coordinates.

        Args:
            coordinates (tuple): the coordinates as (x, y) tuple.

        Returns:
            name (str)
        """
        return "The wilderness"

    def at_prepare_room(self, coordinates, caller, room):
        """
        Called when a room gets activated for certain coordinates. This happens
        after every object is moved in it.
        This can be used to set a custom room desc for instance or run other
        customisations on the room.

        Args:
            coordinates (tuple): the coordinates as (x, y) where room is
                located at
            caller (Object): the object that moved into this room
            room (WildernessRoom): the room object that will be used at that
                wilderness location
        Example:
            An example use of this would to plug in a randomizer to show different
            descriptions for different coordinates, or place a treasure at a special
            coordinate.
        """
        pass
