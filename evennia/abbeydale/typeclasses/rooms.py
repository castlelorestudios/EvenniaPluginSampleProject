"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
from utils import send_multimedia, get_visible_things


class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    def at_object_receive(self, new_arrival, source_location):
        """this isn't a good place to send the multimedia, because it seems that when 
        a player "connects"(logs in), his character is first placed into the world 
        (and this is called) and only then is the player's session assigned to it. """
        print("Room: at object_receive; has_account:" + str(new_arrival.has_account))
        new_arrival.msg("Room: at_object_receive")
        super(Room, self).at_object_receive(new_arrival, source_location)

    def at_desc(self, looker=None, **kwargs):
        """
        This is called whenever someone looks at this object.

        Args:
            looker (Object, optional): The object requesting the description.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).

        """
        super(Room, self).at_desc(looker, **kwargs)
        print ("Room at_desc", self, looker, kwargs)
    
        visible_things = list(get_visible_things(self.contents, looker))
        multimedia_sent = False
        for thing in visible_things:
            print("Room at_desc you see:", thing)
            if send_multimedia(thing, looker, "foreground"):
                multimedia_sent = True
        if not multimedia_sent:
            # clear the foreground pane
            looker.msg(text=(" ",{"type": "foreground"}))




#we can also only have this functionality on a specialized class...
#class MediaRoom(Room):
#    """
#    MediaRooms are like Rooms, except you can optionally add a
#    theme image and sound.
#    """
#...