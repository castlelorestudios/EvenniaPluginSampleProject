# -*- coding: utf-8 -*-
"""
Testing suite for contrib folder

"""

import sys
import datetime
from django.test import override_settings
from evennia.commands.default.tests import CommandTest
from evennia.utils.test_resources import EvenniaTest
from mock import Mock, patch

# Testing of rplanguage module

from evennia.contrib import rplanguage

mtrans = {"testing": "1", "is": "2", "a": "3", "human": "4"}
atrans = ["An", "automated", "advantageous", "repeatable", "faster"]

text = "Automated testing is advantageous for a number of reasons: " \
       "tests may be executed Continuously without the need for human " \
       "intervention, They are easily repeatable, and often faster."


class TestLanguage(EvenniaTest):
    def setUp(self):
        super(TestLanguage, self).setUp()
        rplanguage.add_language(key="testlang",
                                word_length_variance=1,
                                noun_prefix="bara",
                                noun_postfix="'y",
                                manual_translations=mtrans,
                                auto_translations=atrans,
                                force=True)
        rplanguage.add_language(key="binary",
                                phonemes="oo ii a ck w b d t",
                                grammar="cvvv cvv cvvcv cvvcvv cvvvc cvvvcvv cvvc",
                                noun_prefix='beep-',
                                word_length_variance=4)

    def tearDown(self):
        super(TestLanguage, self).tearDown()
        rplanguage._LANGUAGE_HANDLER.delete()
        rplanguage._LANGUAGE_HANDLER = None

    def test_obfuscate_language(self):
        result0 = rplanguage.obfuscate_language(text, level=0.0, language="testlang")
        self.assertEqual(result0, text)
        result1 = rplanguage.obfuscate_language(text, level=1.0, language="testlang")
        result2 = rplanguage.obfuscate_language(text, level=1.0, language="testlang")
        result3 = rplanguage.obfuscate_language(text, level=1.0, language='binary')

        self.assertNotEqual(result1, text)
        self.assertNotEqual(result3, text)
        result1, result2 = result1.split(), result2.split()
        self.assertEqual(result1[:4], result2[:4])
        self.assertEqual(result1[1], "1")
        self.assertEqual(result1[2], "2")
        self.assertEqual(result2[-1], result2[-1])

    def test_faulty_language(self):
        self.assertRaises(
            rplanguage.LanguageError,
            rplanguage.add_language,
            key='binary2',
            phonemes="w b d t oe ee, oo e o a wh dw bw",  # erroneous comma
            grammar="cvvv cvv cvvcv cvvcvvo cvvvc cvvvcvv cvvc c v cc vv ccvvc ccvvccvv ",
            vowels="oea",
            word_length_variance=4)


    def test_available_languages(self):
        self.assertEqual(rplanguage.available_languages(), ["testlang", "binary"])

    def test_obfuscate_whisper(self):
        self.assertEqual(rplanguage.obfuscate_whisper(text, level=0.0), text)
        assert (rplanguage.obfuscate_whisper(text, level=0.1).startswith(
            '-utom-t-d t-sting is -dv-nt-g-ous for - numb-r of r--sons: t-sts m-y b- -x-cut-d Continuously'))
        assert(rplanguage.obfuscate_whisper(text, level=0.5).startswith(
            '--------- --s---- -s -----------s f-- - ------ -f ---s--s: --s-s '))
        self.assertEqual(rplanguage.obfuscate_whisper(text, level=1.0), "...")

# Testing of emoting / sdesc / recog system


from evennia import create_object
from evennia.contrib import rpsystem

sdesc0 = "A nice sender of emotes"
sdesc1 = "The first receiver of emotes."
sdesc2 = "Another nice colliding sdesc-guy for tests"
recog01 = "Mr Receiver"
recog02 = "Mr Receiver2"
recog10 = "Mr Sender"
emote = "With a flair, /me looks at /first and /colliding sdesc-guy. She says \"This is a test.\""


class TestRPSystem(EvenniaTest):
    def setUp(self):
        super(TestRPSystem, self).setUp()
        self.room = create_object(rpsystem.ContribRPRoom, key="Location")
        self.speaker = create_object(rpsystem.ContribRPCharacter, key="Sender", location=self.room)
        self.receiver1 = create_object(rpsystem.ContribRPCharacter, key="Receiver1", location=self.room)
        self.receiver2 = create_object(rpsystem.ContribRPCharacter, key="Receiver2", location=self.room)

    def test_ordered_permutation_regex(self):
        self.assertEqual(
            rpsystem.ordered_permutation_regex(sdesc0),
            '/[0-9]*-*A\\ nice\\ sender\\ of\\ emotes(?=\\W|$)+|/[0-9]*-*nice\\ sender\\ '
            'of\\ emotes(?=\\W|$)+|/[0-9]*-*A\\ nice\\ sender\\ of(?=\\W|$)+|/[0-9]*-*sender\\ '
            'of\\ emotes(?=\\W|$)+|/[0-9]*-*nice\\ sender\\ of(?=\\W|$)+|/[0-9]*-*A\\ nice\\ '
            'sender(?=\\W|$)+|/[0-9]*-*nice\\ sender(?=\\W|$)+|/[0-9]*-*of\\ emotes(?=\\W|$)+'
            '|/[0-9]*-*sender\\ of(?=\\W|$)+|/[0-9]*-*A\\ nice(?=\\W|$)+|/[0-9]*-*sender(?=\\W|$)+'
            '|/[0-9]*-*emotes(?=\\W|$)+|/[0-9]*-*nice(?=\\W|$)+|/[0-9]*-*of(?=\\W|$)+|/[0-9]*-*A(?=\\W|$)+')

    def test_sdesc_handler(self):
        self.speaker.sdesc.add(sdesc0)
        self.assertEqual(self.speaker.sdesc.get(), sdesc0)
        self.speaker.sdesc.add("This is {#324} ignored")
        self.assertEqual(self.speaker.sdesc.get(), "This is 324 ignored")
        self.speaker.sdesc.add("Testing three words")
        self.assertEqual(
            self.speaker.sdesc.get_regex_tuple()[0].pattern,
            '/[0-9]*-*Testing\\ three\\ words(?=\\W|$)+|/[0-9]*-*Testing\\ '
            'three(?=\\W|$)+|/[0-9]*-*three\\ words(?=\\W|$)+|/[0-9]*-*Testing'
            '(?=\\W|$)+|/[0-9]*-*three(?=\\W|$)+|/[0-9]*-*words(?=\\W|$)+')

    def test_recog_handler(self):
        self.speaker.sdesc.add(sdesc0)
        self.receiver1.sdesc.add(sdesc1)
        self.speaker.recog.add(self.receiver1, recog01)
        self.speaker.recog.add(self.receiver2, recog02)
        self.assertEqual(self.speaker.recog.get(self.receiver1), recog01)
        self.assertEqual(self.speaker.recog.get(self.receiver2), recog02)
        self.assertEqual(
            self.speaker.recog.get_regex_tuple(self.receiver1)[0].pattern,
            '/[0-9]*-*Mr\\ Receiver(?=\\W|$)+|/[0-9]*-*Receiver(?=\\W|$)+|/[0-9]*-*Mr(?=\\W|$)+')
        self.speaker.recog.remove(self.receiver1)
        self.assertEqual(self.speaker.recog.get(self.receiver1), sdesc1)

    def test_parse_language(self):
        self.assertEqual(
            rpsystem.parse_language(self.speaker, emote),
            ('With a flair, /me looks at /first and /colliding sdesc-guy. She says {##0}',
             {'##0': (None, '"This is a test."')}))

    def parse_sdescs_and_recogs(self):
        speaker = self.speaker
        speaker.sdesc.add(sdesc0)
        self.receiver1.sdesc.add(sdesc1)
        self.receiver2.sdesc.add(sdesc2)
        candidates = (self.receiver1, self.receiver2)
        result = ('With a flair, {#9} looks at {#10} and {#11}. She says "This is a test."',
                  {'#11': 'Another nice colliding sdesc-guy for tests', '#10':
                      'The first receiver of emotes.', '#9': 'A nice sender of emotes'})
        self.assertEqual(rpsystem.parse_sdescs_and_recogs(speaker, candidates, emote), result)
        self.speaker.recog.add(self.receiver1, recog01)
        self.assertEqual(rpsystem.parse_sdescs_and_recogs(speaker, candidates, emote), result)

    def test_send_emote(self):
        speaker = self.speaker
        receiver1 = self.receiver1
        receiver2 = self.receiver2
        receivers = [speaker, receiver1, receiver2]
        speaker.sdesc.add(sdesc0)
        receiver1.sdesc.add(sdesc1)
        receiver2.sdesc.add(sdesc2)
        speaker.msg = lambda text, **kwargs: setattr(self, "out0", text)
        receiver1.msg = lambda text, **kwargs: setattr(self, "out1", text)
        receiver2.msg = lambda text, **kwargs: setattr(self, "out2", text)
        rpsystem.send_emote(speaker, receivers, emote)
        self.assertEqual(
            self.out0, 'With a flair, |bSender|n looks at |bThe first receiver of emotes.|n '
            'and |bAnother nice colliding sdesc-guy for tests|n. She says |w"This is a test."|n')
        self.assertEqual(
            self.out1, 'With a flair, |bA nice sender of emotes|n looks at |bReceiver1|n and '
            '|bAnother nice colliding sdesc-guy for tests|n. She says |w"This is a test."|n')
        self.assertEqual(
            self.out2, 'With a flair, |bA nice sender of emotes|n looks at |bThe first '
            'receiver of emotes.|n and |bReceiver2|n. She says |w"This is a test."|n')

    def test_rpsearch(self):
        self.speaker.sdesc.add(sdesc0)
        self.receiver1.sdesc.add(sdesc1)
        self.receiver2.sdesc.add(sdesc2)
        self.speaker.msg = lambda text, **kwargs: setattr(self, "out0", text)
        self.assertEqual(self.speaker.search("receiver of emotes"), self.receiver1)
        self.assertEqual(self.speaker.search("colliding"), self.receiver2)


# Testing of ExtendedRoom contrib

from django.conf import settings
from evennia.contrib import extended_room
from evennia import gametime
from evennia.objects.objects import DefaultRoom


class ForceUTCDatetime(datetime.datetime):

    """Force UTC datetime."""

    @classmethod
    def fromtimestamp(cls, timestamp):
        """Force fromtimestamp to run with naive datetimes."""
        return datetime.datetime.utcfromtimestamp(timestamp)


@patch('evennia.contrib.extended_room.datetime.datetime', ForceUTCDatetime)
class TestExtendedRoom(CommandTest):
    room_typeclass = extended_room.ExtendedRoom
    DETAIL_DESC = "A test detail."
    SPRING_DESC = "A spring description."
    OLD_DESC = "Old description."
    settings.TIME_ZONE = "UTC"

    def setUp(self):
        super(TestExtendedRoom, self).setUp()
        self.room1.ndb.last_timeslot = "afternoon"
        self.room1.ndb.last_season = "winter"
        self.room1.db.details = {'testdetail': self.DETAIL_DESC}
        self.room1.db.spring_desc = self.SPRING_DESC
        self.room1.db.desc = self.OLD_DESC
        # mock gametime to return April 9, 2064, at 21:06 (spring evening)
        gametime.gametime = Mock(return_value=2975000766)

    def test_return_appearance(self):
        # get the appearance of a non-extended room for contrast purposes
        old_desc = DefaultRoom.return_appearance(self.room1, self.char1)
        # the new appearance should be the old one, but with the desc switched
        self.assertEqual(old_desc.replace(self.OLD_DESC, self.SPRING_DESC),
                         self.room1.return_appearance(self.char1))
        self.assertEqual("spring", self.room1.ndb.last_season)
        self.assertEqual("evening", self.room1.ndb.last_timeslot)

    def test_return_detail(self):
        self.assertEqual(self.DETAIL_DESC, self.room1.return_detail("testdetail"))

    def test_cmdextendedlook(self):
        self.call(extended_room.CmdExtendedLook(), "here", "Room(#1)\n%s" % self.SPRING_DESC)
        self.call(extended_room.CmdExtendedLook(), "testdetail", self.DETAIL_DESC)
        self.call(extended_room.CmdExtendedLook(), "nonexistent", "Could not find 'nonexistent'.")

    def test_cmdextendeddesc(self):
        self.call(extended_room.CmdExtendedDesc(), "", "Details on Room", cmdstring="detail")
        self.call(extended_room.CmdExtendedDesc(), "thingie = newdetail with spaces",
                  "Set Detail thingie to 'newdetail with spaces'.", cmdstring="detail")
        self.call(extended_room.CmdExtendedDesc(), "thingie", "Detail 'thingie' on Room:\n", cmdstring="detail")
        self.call(extended_room.CmdExtendedDesc(), "/del thingie", "Detail thingie deleted, if it existed.", cmdstring="detail")
        self.call(extended_room.CmdExtendedDesc(), "thingie", "Detail 'thingie' not found.", cmdstring="detail")
        self.call(extended_room.CmdExtendedDesc(), "", "Descriptions on Room:")

    def test_cmdgametime(self):
        self.call(extended_room.CmdGameTime(), "", "It's a spring day, in the evening.")


# Test the contrib barter system

from evennia.contrib import barter


class TestBarter(CommandTest):

    def setUp(self):
        super(TestBarter, self).setUp()
        self.tradeitem1 = create_object(key="TradeItem1", location=self.char1)
        self.tradeitem2 = create_object(key="TradeItem2", location=self.char1)
        self.tradeitem3 = create_object(key="TradeItem3", location=self.char2)

    def test_tradehandler_base(self):
        self.char1.msg = Mock()
        self.char2.msg = Mock()
        # test all methods of the tradehandler
        handler = barter.TradeHandler(self.char1, self.char2)
        self.assertEqual(handler.part_a, self.char1)
        self.assertEqual(handler.part_b, self.char2)
        handler.msg_other(self.char1, "Want to trade?")
        handler.msg_other(self.char2, "Yes!")
        handler.msg_other(None, "Talking to myself...")
        self.assertEqual(self.char2.msg.mock_calls[0][1][0], "Want to trade?")
        self.assertEqual(self.char1.msg.mock_calls[0][1][0], "Yes!")
        self.assertEqual(self.char1.msg.mock_calls[1][1][0], "Talking to myself...")
        self.assertEqual(handler.get_other(self.char1), self.char2)
        handler.finish(force=True)

    def test_tradehandler_joins(self):
        handler = barter.TradeHandler(self.char1, self.char2)
        self.assertTrue(handler.join(self.char2))
        self.assertTrue(handler.unjoin(self.char2))
        self.assertFalse(handler.join(self.char1))
        self.assertFalse(handler.unjoin(self.char1))
        handler.finish(force=True)

    def test_tradehandler_offers(self):
        handler = barter.TradeHandler(self.char1, self.char2)
        handler.join(self.char2)
        handler.offer(self.char1, self.tradeitem1, self.tradeitem2)
        self.assertEqual(handler.part_a_offers, [self.tradeitem1, self.tradeitem2])
        self.assertFalse(handler.part_a_accepted)
        self.assertFalse(handler.part_b_accepted)
        handler.offer(self.char2, self.tradeitem3)
        self.assertEqual(handler.list(), ([self.tradeitem1, self.tradeitem2], [self.tradeitem3]))
        self.assertEqual(handler.search("TradeItem2"), self.tradeitem2)
        self.assertEqual(handler.search("TradeItem3"), self.tradeitem3)
        self.assertEqual(handler.search("nonexisting"), None)
        self.assertFalse(handler.finish())  # should fail since offer not yet accepted
        handler.accept(self.char1)
        handler.decline(self.char1)
        handler.accept(self.char2)
        handler.accept(self.char1)  # should trigger handler.finish() automatically
        self.assertEqual(self.tradeitem1.location, self.char2)
        self.assertEqual(self.tradeitem2.location, self.char2)
        self.assertEqual(self.tradeitem3.location, self.char1)

    def test_cmdtrade(self):
        self.call(barter.CmdTrade(), "Char2 : Hey wanna trade?", "You say, \"Hey wanna trade?\"", caller=self.char1)
        self.call(barter.CmdTrade(), "Char decline : Nope!", "You say, \"Nope!\"", caller=self.char2)
        self.call(barter.CmdTrade(), "Char2 : Hey wanna trade?", "You say, \"Hey wanna trade?\"", caller=self.char1)
        self.call(barter.CmdTrade(), "Char accept : Sure!", "You say, \"Sure!\"", caller=self.char2)
        self.call(barter.CmdOffer(), "TradeItem3", "Your trade action: You offer TradeItem3", caller=self.char2)
        self.call(barter.CmdOffer(), "TradeItem1 : Here's my offer.", "You say, \"Here's my offer.\"\n  [You offer TradeItem1]")
        self.call(barter.CmdAccept(), "", "Your trade action: You accept the offer. Char2 must now also accept")
        self.call(barter.CmdDecline(), "", "Your trade action: You change your mind, declining the current offer.")
        self.call(barter.CmdAccept(), ": Sounds good.", "You say, \"Sounds good.\"\n"
                                      "  [You accept the offer. Char must now also accept.", caller=self.char2)
        self.call(barter.CmdDecline(), ":No way!", "You say, \"No way!\"\n  [You change your mind, declining the current offer.]", caller=self.char2)
        self.call(barter.CmdOffer(), "TradeItem1, TradeItem2 : My final offer!", "You say, \"My final offer!\"\n  [You offer TradeItem1 and TradeItem2]")
        self.call(barter.CmdAccept(), "", "Your trade action: You accept the offer. Char2 must now also accept.", caller=self.char1)
        self.call(barter.CmdStatus(), "", "Offered by Char:", caller=self.char2)
        self.tradeitem1.db.desc = "A great offer."
        self.call(barter.CmdEvaluate(), "TradeItem1", "A great offer.")
        self.call(barter.CmdAccept(), ":Ok then.", "You say, \"Ok then.\"\n  [You accept the deal.", caller=self.char2)
        self.assertEqual(self.tradeitem1.location, self.char2)
        self.assertEqual(self.tradeitem2.location, self.char2)
        self.assertEqual(self.tradeitem3.location, self.char1)

    def test_cmdtradehelp(self):
        self.call(barter.CmdTrade(), "Char2 : Hey wanna trade?", "You say, \"Hey wanna trade?\"", caller=self.char1)
        self.call(barter.CmdTradeHelp(), "", "Trading commands\n", caller=self.char1)
        self.call(barter.CmdFinish(), ": Ending.", "You say, \"Ending.\"\n  [You aborted trade. No deal was made.]")

# Test wilderness


from evennia.contrib import wilderness
from evennia import DefaultCharacter


class TestWilderness(EvenniaTest):

    def setUp(self):
        super(TestWilderness, self).setUp()
        self.char1 = create_object(DefaultCharacter, key="char1")
        self.char2 = create_object(DefaultCharacter, key="char2")

    def get_wilderness_script(self, name="default"):
        w = wilderness.WildernessScript.objects.get("default")
        return w

    def test_create_wilderness_default_name(self):
        wilderness.create_wilderness()
        w = self.get_wilderness_script()
        self.assertIsNotNone(w)

    def test_create_wilderness_custom_name(self):
        name = "customname"
        wilderness.create_wilderness(name)
        w = self.get_wilderness_script(name)
        self.assertIsNotNone(w)

    def test_enter_wilderness(self):
        wilderness.create_wilderness()
        wilderness.enter_wilderness(self.char1)
        self.assertIsInstance(self.char1.location, wilderness.WildernessRoom)
        w = self.get_wilderness_script()
        self.assertEquals(w.db.itemcoordinates[self.char1], (0, 0))

    def test_enter_wilderness_custom_coordinates(self):
        wilderness.create_wilderness()
        wilderness.enter_wilderness(self.char1, coordinates=(1, 2))
        self.assertIsInstance(self.char1.location, wilderness.WildernessRoom)
        w = self.get_wilderness_script()
        self.assertEquals(w.db.itemcoordinates[self.char1], (1, 2))

    def test_enter_wilderness_custom_name(self):
        name = "customnname"
        wilderness.create_wilderness(name)
        wilderness.enter_wilderness(self.char1, name=name)
        self.assertIsInstance(self.char1.location, wilderness.WildernessRoom)

    def test_wilderness_correct_exits(self):
        wilderness.create_wilderness()
        wilderness.enter_wilderness(self.char1)

        # By default we enter at a corner (0, 0), so only a few exits should
        # be visible / traversable
        exits = [i for i in self.char1.location.contents
                 if i.destination and (
                     i.access(self.char1, "view") or
                     i.access(self.char1, "traverse"))]

        self.assertEquals(len(exits), 3)
        exitsok = ["north", "northeast", "east"]
        for each_exit in exitsok:
            self.assertTrue(any([e for e in exits if e.key == each_exit]))

        # If we move to another location not on an edge, then all directions
        # should be visible / traversable
        wilderness.enter_wilderness(self.char1, coordinates=(1, 1))
        exits = [i for i in self.char1.location.contents
                 if i.destination and (
                     i.access(self.char1, "view") or
                     i.access(self.char1, "traverse"))]
        self.assertEquals(len(exits), 8)
        exitsok = ["north", "northeast", "east", "southeast", "south",
                   "southwest", "west", "northwest"]
        for each_exit in exitsok:
            self.assertTrue(any([e for e in exits if e.key == each_exit]))

    def test_room_creation(self):
        # Pretend that both char1 and char2 are connected...
        self.char1.sessions.add(1)
        self.char2.sessions.add(1)
        self.assertTrue(self.char1.has_account)
        self.assertTrue(self.char2.has_account)

        wilderness.create_wilderness()
        w = self.get_wilderness_script()

        # We should have no unused room after moving the first account in.
        self.assertEquals(len(w.db.unused_rooms), 0)
        w.move_obj(self.char1, (0, 0))
        self.assertEquals(len(w.db.unused_rooms), 0)

        # And also no unused room after moving the second one in.
        w.move_obj(self.char2, (1, 1))
        self.assertEquals(len(w.db.unused_rooms), 0)

        # But if char2 moves into char1's room, we should have one unused room
        # Which should be char2's old room that got created.
        w.move_obj(self.char2, (0, 0))
        self.assertEquals(len(w.db.unused_rooms), 1)
        self.assertEquals(self.char1.location, self.char2.location)

        # And if char2 moves back out, that unused room should be put back to
        # use again.
        w.move_obj(self.char2, (1, 1))
        self.assertNotEquals(self.char1.location, self.char2.location)
        self.assertEquals(len(w.db.unused_rooms), 0)

    def test_get_new_coordinates(self):
        loc = (1, 1)
        directions = {"north": (1, 2),
                      "northeast": (2, 2),
                      "east": (2, 1),
                      "southeast": (2, 0),
                      "south": (1, 0),
                      "southwest": (0, 0),
                      "west": (0, 1),
                      "northwest": (0, 2)}
        for direction, correct_loc in directions.iteritems():  # Not compatible with Python 3
            new_loc = wilderness.get_new_coordinates(loc, direction)
            self.assertEquals(new_loc, correct_loc, direction)


# Testing chargen contrib
from evennia.contrib import chargen


class TestChargen(CommandTest):

    def test_ooclook(self):
        self.call(chargen.CmdOOCLook(), "foo", "You have no characters to look at", caller=self.account)
        self.call(chargen.CmdOOCLook(), "", "You, TestAccount, are an OOC ghost without form.", caller=self.account)

    def test_charcreate(self):
        self.call(chargen.CmdOOCCharacterCreate(), "testchar", "The character testchar was successfully created!", caller=self.account)
        self.call(chargen.CmdOOCCharacterCreate(), "testchar", "Character testchar already exists.", caller=self.account)
        self.assertTrue(self.account.db._character_dbrefs)
        self.call(chargen.CmdOOCLook(), "", "You, TestAccount, are an OOC ghost without form.", caller=self.account)
        self.call(chargen.CmdOOCLook(), "testchar", "testchar(", caller=self.account)


# Testing clothing contrib
from evennia.contrib import clothing
from evennia.objects.objects import DefaultRoom


class TestClothingCmd(CommandTest):

    def test_clothingcommands(self):
        wearer = create_object(clothing.ClothedCharacter, key="Wearer")
        friend = create_object(clothing.ClothedCharacter, key="Friend")
        room = create_object(DefaultRoom, key="room")
        wearer.location = room
        friend.location = room
        # Make a test hat
        test_hat = create_object(clothing.Clothing, key="test hat")
        test_hat.db.clothing_type = 'hat'
        test_hat.location = wearer
        # Make a test scarf
        test_scarf = create_object(clothing.Clothing, key="test scarf")
        test_scarf.db.clothing_type = 'accessory'
        test_scarf.location = wearer
        # Test wear command
        self.call(clothing.CmdWear(), "", "Usage: wear <obj> [wear style]", caller=wearer)
        self.call(clothing.CmdWear(), "hat", "Wearer puts on test hat.", caller=wearer)
        self.call(clothing.CmdWear(), "scarf stylishly", "Wearer wears test scarf stylishly.", caller=wearer)
        # Test cover command.
        self.call(clothing.CmdCover(), "", "Usage: cover <worn clothing> [with] <clothing object>", caller=wearer)
        self.call(clothing.CmdCover(), "hat with scarf", "Wearer covers test hat with test scarf.", caller=wearer)
        # Test remove command.
        self.call(clothing.CmdRemove(), "", "Could not find ''.", caller=wearer)
        self.call(clothing.CmdRemove(), "hat", "You have to take off test scarf first.", caller=wearer)
        self.call(clothing.CmdRemove(), "scarf", "Wearer removes test scarf, revealing test hat.", caller=wearer)
        # Test uncover command.
        test_scarf.wear(wearer, True)
        test_hat.db.covered_by = test_scarf
        self.call(clothing.CmdUncover(), "", "Usage: uncover <worn clothing object>", caller=wearer)
        self.call(clothing.CmdUncover(), "hat", "Wearer uncovers test hat.", caller=wearer)
        # Test drop command.
        test_hat.db.covered_by = test_scarf
        self.call(clothing.CmdDrop(), "", "Drop what?", caller=wearer)
        self.call(clothing.CmdDrop(), "hat", "You can't drop that because it's covered by test scarf.", caller=wearer)
        self.call(clothing.CmdDrop(), "scarf", "You drop test scarf.", caller=wearer)
        # Test give command.
        self.call(clothing.CmdGive(), "", "Usage: give <inventory object> = <target>", caller=wearer)
        self.call(clothing.CmdGive(), "hat = Friend", "Wearer removes test hat.|You give test hat to Friend.", caller=wearer)
        # Test inventory command.
        self.call(clothing.CmdInventory(), "", "You are not carrying or wearing anything.", caller=wearer)


class TestClothingFunc(EvenniaTest):

    def test_clothingfunctions(self):
        wearer = create_object(clothing.ClothedCharacter, key="Wearer")
        room = create_object(DefaultRoom, key="room")
        wearer.location = room
        # Make a test hat
        test_hat = create_object(clothing.Clothing, key="test hat")
        test_hat.db.clothing_type = 'hat'
        test_hat.location = wearer
        # Make a test shirt
        test_shirt = create_object(clothing.Clothing, key="test shirt")
        test_shirt.db.clothing_type = 'top'
        test_shirt.location = wearer
        # Make a test pants
        test_pants = create_object(clothing.Clothing, key="test pants")
        test_pants.db.clothing_type = 'bottom'
        test_pants.location = wearer

        test_hat.wear(wearer, 'on the head')
        self.assertEqual(test_hat.db.worn, 'on the head')

        test_hat.remove(wearer)
        self.assertEqual(test_hat.db.worn, False)

        test_hat.worn = True
        test_hat.at_get(wearer)
        self.assertEqual(test_hat.db.worn, False)

        clothes_list = [test_shirt, test_hat, test_pants]
        self.assertEqual(clothing.order_clothes_list(clothes_list), [test_hat, test_shirt, test_pants])

        test_hat.wear(wearer, True)
        test_pants.wear(wearer, True)
        self.assertEqual(clothing.get_worn_clothes(wearer), [test_hat, test_pants])

        self.assertEqual(clothing.clothing_type_count(clothes_list), {'hat': 1, 'top': 1, 'bottom': 1})

        self.assertEqual(clothing.single_type_count(clothes_list, 'hat'), 1)



# Testing custom_gametime
from evennia.contrib import custom_gametime


def _testcallback():
    pass


class TestCustomGameTime(EvenniaTest):
    def setUp(self):
        super(TestCustomGameTime, self).setUp()
        gametime.gametime = Mock(return_value=2975000898.46)  # does not seem to work

    def tearDown(self):
        if hasattr(self, "timescript"):
            self.timescript.stop()

    def test_time_to_tuple(self):
        self.assertEqual(custom_gametime.time_to_tuple(10000, 34, 2, 4, 6, 1), (294, 2, 0, 0, 0, 0))
        self.assertEqual(custom_gametime.time_to_tuple(10000, 3, 3, 4), (3333, 0, 0, 1))
        self.assertEqual(custom_gametime.time_to_tuple(100000, 239, 24, 3), (418, 4, 0, 2))

    def test_gametime_to_realtime(self):
        self.assertEqual(custom_gametime.gametime_to_realtime(days=2, mins=4), 86520.0)
        self.assertEqual(custom_gametime.gametime_to_realtime(format=True, days=2), (0, 0, 0, 1, 0, 0, 0))

    def test_realtime_to_gametime(self):
        self.assertEqual(custom_gametime.realtime_to_gametime(days=2, mins=34), 349680.0)
        self.assertEqual(custom_gametime.realtime_to_gametime(days=2, mins=34, format=True), (0, 0, 0, 4, 1, 8, 0))
        self.assertEqual(custom_gametime.realtime_to_gametime(format=True, days=2, mins=4), (0, 0, 0, 4, 0, 8, 0))

    def test_custom_gametime(self):
        self.assertEqual(custom_gametime.custom_gametime(), (102, 5, 2, 6, 21, 8, 18))
        self.assertEqual(custom_gametime.custom_gametime(absolute=True), (102, 5, 2, 6, 21, 8, 18))

    def test_real_seconds_until(self):
        self.assertEqual(custom_gametime.real_seconds_until(year=2300, month=11, day=6), 31911667199.77)

    def test_schedule(self):
        self.timescript = custom_gametime.schedule(_testcallback, repeat=True, min=5, sec=0)
        self.assertEqual(self.timescript.interval, 1700.7699999809265)

# Test dice module


@patch('random.randint', return_value=5)
class TestDice(CommandTest):
    def test_roll_dice(self, mocked_randint):
        # we must import dice here for the mocked randint to apply correctly.
        from evennia.contrib import dice
        self.assertEqual(dice.roll_dice(6, 6, modifier=('+', 4)), mocked_randint() * 6 + 4)
        self.assertEqual(dice.roll_dice(6, 6, conditional=('<', 35)), True)
        self.assertEqual(dice.roll_dice(6, 6, conditional=('>', 33)), False)

    def test_cmddice(self, mocked_randint):
        from evennia.contrib import dice
        self.call(dice.CmdDice(), "3d6 + 4", "You roll 3d6 + 4.| Roll(s): 5, 5 and 5. Total result is 19.")
        self.call(dice.CmdDice(), "100000d1000", "The maximum roll allowed is 10000d10000.")
        self.call(dice.CmdDice(), "/secret 3d6 + 4", "You roll 3d6 + 4 (secret, not echoed).")

# Test email-login


from evennia.contrib import email_login


class TestEmailLogin(CommandTest):
    def test_connect(self):
        self.call(email_login.CmdUnconnectedConnect(), "mytest@test.com test", "The email 'mytest@test.com' does not match any accounts.")
        self.call(email_login.CmdUnconnectedCreate(), '"mytest" mytest@test.com test11111', "A new account 'mytest' was created. Welcome!")
        self.call(email_login.CmdUnconnectedConnect(), "mytest@test.com test11111", "", caller=self.account.sessions.get()[0])

    def test_quit(self):
        self.call(email_login.CmdUnconnectedQuit(), "", "", caller=self.account.sessions.get()[0])

    def test_unconnectedlook(self):
        self.call(email_login.CmdUnconnectedLook(), "", "==========")

    def test_unconnectedhelp(self):
        self.call(email_login.CmdUnconnectedHelp(), "", "You are not yet logged into the game.")

# test gendersub contrib


from evennia.contrib import gendersub


class TestGenderSub(CommandTest):
    def test_setgender(self):
        self.call(gendersub.SetGender(), "male", "Your gender was set to male.")
        self.call(gendersub.SetGender(), "ambiguous", "Your gender was set to ambiguous.")
        self.call(gendersub.SetGender(), "Foo", "Usage: @gender")

    def test_gendercharacter(self):
        char = create_object(gendersub.GenderCharacter, key="Gendered", location=self.room1)
        txt = "Test |p gender"
        self.assertEqual(gendersub._RE_GENDER_PRONOUN.sub(char._get_pronoun, txt), "Test their gender")

# test health bar contrib

from evennia.contrib import health_bar

class TestHealthBar(EvenniaTest):
    def test_healthbar(self):
        expected_bar_str = '|[R|w|n|[B|w            test0 / 200test             |n'
        self.assertEqual(health_bar.display_meter(
            0, 200, length=40, pre_text="test", post_text="test", align="center"), expected_bar_str)
        expected_bar_str = "|[R|w     |n|[B|w       test24 / 200test            |n"
        self.assertEqual(health_bar.display_meter(
            24, 200, length=40, pre_text="test", post_text="test", align="center"), expected_bar_str)
        expected_bar_str = '|[Y|w           test100 /|n|[B|w 200test            |n'
        self.assertEqual(health_bar.display_meter(
            100, 200, length=40, pre_text="test", post_text="test", align="center"), expected_bar_str)
        expected_bar_str = '|[G|w           test180 / 200test        |n|[B|w    |n'
        self.assertEqual(health_bar.display_meter(
            180, 200, length=40, pre_text="test", post_text="test", align="center"), expected_bar_str)
        expected_bar_str = '|[G|w           test200 / 200test            |n|[B|w|n'
        self.assertEqual(health_bar.display_meter(
            200, 200, length=40, pre_text="test", post_text="test", align="center"), expected_bar_str)

# test mail contrib


from evennia.contrib import mail


class TestMail(CommandTest):
    def test_mail(self):
        self.call(mail.CmdMail(), "2", "'2' is not a valid mail id.", caller=self.account)
        self.call(mail.CmdMail(), "test", "'test' is not a valid mail id.")
        self.call(mail.CmdMail(), "", "There are no messages in your inbox.", caller=self.account)
        self.call(mail.CmdMail(), "Char=Message 1", "You have received a new @mail from Char|You sent your message.", caller=self.char1)
        self.call(mail.CmdMail(), "Char=Message 2", "You sent your message.", caller=self.char2)
        self.call(mail.CmdMail(), "TestAccount2=Message 2",
                  "You have received a new @mail from TestAccount2(account 2)|You sent your message.", caller=self.account2)
        self.call(mail.CmdMail(), "TestAccount=Message 1", "You sent your message.", caller=self.account2)
        self.call(mail.CmdMail(), "TestAccount=Message 2", "You sent your message.", caller=self.account2)
        self.call(mail.CmdMail(), "", "| ID:   From:             Subject:", caller=self.account)
        self.call(mail.CmdMail(), "2", "From: TestAccount2", caller=self.account)
        self.call(mail.CmdMail(), "/forward TestAccount2 = 1/Forward message", "You sent your message.|Message forwarded.", caller=self.account)
        self.call(mail.CmdMail(), "/reply 2=Reply Message2", "You sent your message.", caller=self.account)
        self.call(mail.CmdMail(), "/delete 2", "Message 2 deleted", caller=self.account)

# test map builder contrib


from evennia.contrib import mapbuilder


class TestMapBuilder(CommandTest):
    def test_cmdmapbuilder(self):
        self.call(mapbuilder.CmdMapBuilder(),
                  "evennia.contrib.mapbuilder.EXAMPLE1_MAP evennia.contrib.mapbuilder.EXAMPLE1_LEGEND",
                  """Creating Map...|≈≈≈≈≈
≈♣n♣≈
≈∩▲∩≈
≈♠n♠≈
≈≈≈≈≈
|Creating Landmass...|""")
        self.call(mapbuilder.CmdMapBuilder(),
                  "evennia.contrib.mapbuilder.EXAMPLE2_MAP evennia.contrib.mapbuilder.EXAMPLE2_LEGEND",
                  """Creating Map...|≈ ≈ ≈ ≈ ≈

≈ ♣-♣-♣ ≈
    ≈ ♣ ♣ ♣ ≈
  ≈ ♣-♣-♣ ≈

≈ ≈ ≈ ≈ ≈
|Creating Landmass...|""")


# test menu_login

from evennia.contrib import menu_login


class TestMenuLogin(CommandTest):
    def test_cmdunloggedlook(self):
        self.call(menu_login.CmdUnloggedinLook(), "", "======")


# test multidescer contrib

from evennia.contrib import multidescer


class TestMultidescer(CommandTest):
    def test_cmdmultidesc(self):
        self.call(multidescer.CmdMultiDesc(), "/list", "Stored descs:\ncaller:")
        self.call(multidescer.CmdMultiDesc(), "test = Desc 1", "Stored description 'test': \"Desc 1\"")
        self.call(multidescer.CmdMultiDesc(), "test2 = Desc 2", "Stored description 'test2': \"Desc 2\"")
        self.call(multidescer.CmdMultiDesc(), "/swap test-test2", "Swapped descs 'test' and 'test2'.")
        self.call(multidescer.CmdMultiDesc(), "test3 = Desc 3init", "Stored description 'test3': \"Desc 3init\"")
        self.call(multidescer.CmdMultiDesc(), "/list", "Stored descs:\ntest3: Desc 3init\ntest: Desc 1\ntest2: Desc 2\ncaller:")
        self.call(multidescer.CmdMultiDesc(), "test3 = Desc 3", "Stored description 'test3': \"Desc 3\"")
        self.call(multidescer.CmdMultiDesc(), "/set test1 + test2 + + test3", "test1 Desc 2 Desc 3\n\n"
                  "The above was set as the current description.")
        self.assertEqual(self.char1.db.desc, "test1 Desc 2 Desc 3")

# test simpledoor contrib


from evennia.contrib import simpledoor


class TestSimpleDoor(CommandTest):
    def test_cmdopen(self):
        self.call(simpledoor.CmdOpen(), "newdoor;door:contrib.simpledoor.SimpleDoor,backdoor;door = Room2",
                  "Created new Exit 'newdoor' from Room to Room2 (aliases: door).|Note: A door-type exit was "
                  "created - ignored eventual custom return-exit type.|Created new Exit 'newdoor' from Room2 to Room (aliases: door).")
        self.call(simpledoor.CmdOpenCloseDoor(), "newdoor", "You close newdoor.", cmdstring="close")
        self.call(simpledoor.CmdOpenCloseDoor(), "newdoor", "newdoor is already closed.", cmdstring="close")
        self.call(simpledoor.CmdOpenCloseDoor(), "newdoor", "You open newdoor.", cmdstring="open")
        self.call(simpledoor.CmdOpenCloseDoor(), "newdoor", "newdoor is already open.", cmdstring="open")

# test slow_exit contrib


from evennia.contrib import slow_exit
slow_exit.MOVE_DELAY = {"stroll": 0, "walk": 0, "run": 0, "sprint": 0}


class TestSlowExit(CommandTest):
    def test_exit(self):
        exi = create_object(slow_exit.SlowExit, key="slowexit", location=self.room1, destination=self.room2)
        exi.at_traverse(self.char1, self.room2)
        self.call(slow_exit.CmdSetSpeed(), "walk", "You are now walking.")
        self.call(slow_exit.CmdStop(), "", "You stop moving.")

# test talking npc contrib


from evennia.contrib import talking_npc


class TestTalkingNPC(CommandTest):
    def test_talkingnpc(self):
        npc = create_object(talking_npc.TalkingNPC, key="npctalker", location=self.room1)
        self.call(talking_npc.CmdTalk(), "", "(You walk up and talk to Char.)")
        npc.delete()


# tests for the tutorial world

# test tutorial_world/mob

from evennia.contrib.tutorial_world import mob


class TestTutorialWorldMob(EvenniaTest):
    def test_mob(self):
        mobobj = create_object(mob.Mob, key="mob")
        self.assertEqual(mobobj.db.is_dead, True)
        mobobj.set_alive()
        self.assertEqual(mobobj.db.is_dead, False)
        mobobj.set_dead()
        self.assertEqual(mobobj.db.is_dead, True)
        mobobj._set_ticker(0, "foo", stop=True)
        # TODO should be expanded with further tests of the modes and damage etc.

#  test tutorial_world/objects


from evennia.contrib.tutorial_world import objects as tutobjects
from mock.mock import MagicMock
from twisted.trial.unittest import TestCase as TwistedTestCase

from twisted.internet.base import DelayedCall
DelayedCall.debug = True


def _mockdelay(tim, func, *args, **kwargs):
    func(*args, **kwargs)
    return MagicMock()


def _mockdeferLater(reactor, timedelay, callback, *args, **kwargs):
    callback(*args, **kwargs)
    return MagicMock()


class TestTutorialWorldObjects(TwistedTestCase, CommandTest):

    def setUp(self):
        self.patch(sys.modules['evennia.contrib.tutorial_world.objects'], 'delay', _mockdelay)
        self.patch(sys.modules['evennia.scripts.taskhandler'], 'deferLater', _mockdeferLater)
        super(TestTutorialWorldObjects, self).setUp()

    def test_tutorialobj(self):
        obj1 = create_object(tutobjects.TutorialObject, key="tutobj")
        obj1.reset()
        self.assertEqual(obj1.location, obj1.home)

    def test_readable(self):
        readable = create_object(tutobjects.Readable, key="book", location=self.room1)
        readable.db.readable_text = "Text to read"
        self.call(tutobjects.CmdRead(), "book", "You read book:\n  Text to read", obj=readable)

    def test_climbable(self):
        climbable = create_object(tutobjects.Climbable, key="tree", location=self.room1)
        self.call(tutobjects.CmdClimb(), "tree", "You climb tree. Having looked around, you climb down again.", obj=climbable)
        self.assertEqual(self.char1.tags.get("tutorial_climbed_tree", category="tutorial_world"), "tutorial_climbed_tree")

    def test_obelisk(self):
        obelisk = create_object(tutobjects.Obelisk, key="obelisk", location=self.room1)
        self.assertEqual(obelisk.return_appearance(self.char1).startswith("|cobelisk("), True)

    def test_lightsource(self):
        light = create_object(tutobjects.LightSource, key="torch", location=self.room1)
        self.call(tutobjects.CmdLight(), "", "A torch on the floor flickers and dies.|You light torch.", obj=light)
        self.assertFalse(light.pk)

    def test_crumblingwall(self):
        wall = create_object(tutobjects.CrumblingWall, key="wall", location=self.room1)
        self.assertFalse(wall.db.button_exposed)
        self.assertFalse(wall.db.exit_open)
        wall.db.root_pos = {"yellow": 0, "green": 0, "red": 0, "blue": 0}
        self.call(tutobjects.CmdShiftRoot(), "blue root right",
                  "You shove the root adorned with small blue flowers to the right.", obj=wall)
        self.call(tutobjects.CmdShiftRoot(), "red root left",
                  "You shift the reddish root to the left.", obj=wall)
        self.call(tutobjects.CmdShiftRoot(), "yellow root down",
                  "You shove the root adorned with small yellow flowers downwards.", obj=wall)
        self.call(tutobjects.CmdShiftRoot(), "green root up",
                  "You shift the weedy green root upwards.|Holding aside the root you think you notice something behind it ...", obj=wall)
        self.call(tutobjects.CmdPressButton(), "",
                  "You move your fingers over the suspicious depression, then gives it a decisive push. First", obj=wall)
        # we patch out the delay, so these are closed immediately
        self.assertFalse(wall.db.button_exposed)
        self.assertFalse(wall.db.exit_open)
        wall.reset()
        wall.delete()
        return wall.deferred

    def test_weapon(self):
        weapon = create_object(tutobjects.Weapon, key="sword", location=self.char1)
        self.call(tutobjects.CmdAttack(), "Char", "You stab with sword.", obj=weapon, cmdstring="stab")
        self.call(tutobjects.CmdAttack(), "Char", "You slash with sword.", obj=weapon, cmdstring="slash")

    def test_weaponrack(self):
        rack = create_object(tutobjects.WeaponRack, key="rack", location=self.room1)
        rack.db.available_weapons = ["sword"]
        self.call(tutobjects.CmdGetWeapon(), "", "You find Rusty sword.", obj=rack)


# test tutorial_world/
from evennia.contrib.tutorial_world import rooms as tutrooms


class TestTutorialWorldRooms(CommandTest):
    def test_cmdtutorial(self):
        room = create_object(tutrooms.TutorialRoom, key="tutroom")
        self.char1.location = room
        self.call(tutrooms.CmdTutorial(), "", "Sorry, there is no tutorial help available here.")
        self.call(tutrooms.CmdTutorialSetDetail(), "detail;foo;foo2 = A detail", "Detail set: 'detail;foo;foo2': 'A detail'", obj=room)
        self.call(tutrooms.CmdTutorialLook(), "", "tutroom(", obj=room)
        self.call(tutrooms.CmdTutorialLook(), "detail", "A detail", obj=room)
        self.call(tutrooms.CmdTutorialLook(), "foo", "A detail", obj=room)
        room.delete()

    def test_weatherroom(self):
        room = create_object(tutrooms.WeatherRoom, key="weatherroom")
        room.update_weather()
        tutrooms.TICKER_HANDLER.remove(interval=room.db.interval, callback=room.update_weather, idstring="tutorial")
        room.delete()

    def test_introroom(self):
        room = create_object(tutrooms.IntroRoom, key="introroom")
        room.at_object_receive(self.char1, self.room1)

    def test_bridgeroom(self):
        room = create_object(tutrooms.BridgeRoom, key="bridgeroom")
        room.update_weather()
        self.char1.move_to(room)
        self.call(tutrooms.CmdBridgeHelp(), "", "You are trying hard not to fall off the bridge ...", obj=room)
        self.call(tutrooms.CmdLookBridge(), "", "bridgeroom\nYou are standing very close to the the bridge's western foundation.", obj=room)
        room.at_object_leave(self.char1, self.room1)
        tutrooms.TICKER_HANDLER.remove(interval=room.db.interval, callback=room.update_weather, idstring="tutorial")
        room.delete()

    def test_darkroom(self):
        room = create_object(tutrooms.DarkRoom, key="darkroom")
        self.char1.move_to(room)
        self.call(tutrooms.CmdDarkHelp(), "", "Can't help you until")

    def test_teleportroom(self):
        create_object(tutrooms.TeleportRoom, key="teleportroom")

    def test_outroroom(self):
        create_object(tutrooms.OutroRoom, key="outroroom")


# test turnbattle
from evennia.contrib.turnbattle import tb_basic, tb_equip, tb_range, tb_items, tb_magic
from evennia.objects.objects import DefaultRoom


class TestTurnBattleBasicCmd(CommandTest):

    # Test basic combat commands
    def test_turnbattlecmd(self):
        self.call(tb_basic.CmdFight(), "", "You can't start a fight if you've been defeated!")
        self.call(tb_basic.CmdAttack(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_basic.CmdPass(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_basic.CmdDisengage(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_basic.CmdRest(), "", "Char rests to recover HP.")


class TestTurnBattleEquipCmd(CommandTest):

    def setUp(self):
        super(TestTurnBattleEquipCmd, self).setUp()
        self.testweapon = create_object(tb_equip.TBEWeapon, key="test weapon")
        self.testarmor = create_object(tb_equip.TBEArmor, key="test armor")
        self.testweapon.move_to(self.char1)
        self.testarmor.move_to(self.char1)

    # Test equipment commands
    def test_turnbattleequipcmd(self):
        # Start with equip module specific commands.
        self.call(tb_equip.CmdWield(), "weapon", "Char wields test weapon.")
        self.call(tb_equip.CmdUnwield(), "", "Char lowers test weapon.")
        self.call(tb_equip.CmdDon(), "armor", "Char dons test armor.")
        self.call(tb_equip.CmdDoff(), "", "Char removes test armor.")
        # Also test the commands that are the same in the basic module
        self.call(tb_equip.CmdFight(), "", "You can't start a fight if you've been defeated!")
        self.call(tb_equip.CmdAttack(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_equip.CmdPass(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_equip.CmdDisengage(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_equip.CmdRest(), "", "Char rests to recover HP.")


class TestTurnBattleRangeCmd(CommandTest):
    # Test range commands
    def test_turnbattlerangecmd(self):
        # Start with range module specific commands.
        self.call(tb_range.CmdShoot(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_range.CmdApproach(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_range.CmdWithdraw(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_range.CmdStatus(), "", "HP Remaining: 100 / 100")
        # Also test the commands that are the same in the basic module
        self.call(tb_range.CmdFight(), "", "There's nobody here to fight!")
        self.call(tb_range.CmdAttack(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_range.CmdPass(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_range.CmdDisengage(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_range.CmdRest(), "", "Char rests to recover HP.")


class TestTurnBattleItemsCmd(CommandTest):

    def setUp(self):
        super(TestTurnBattleItemsCmd, self).setUp()
        self.testitem = create_object(key="test item")
        self.testitem.move_to(self.char1)

    # Test item commands
    def test_turnbattleitemcmd(self):
        self.call(tb_items.CmdUse(), "item", "'Test item' is not a usable item.")
        # Also test the commands that are the same in the basic module
        self.call(tb_items.CmdFight(), "", "You can't start a fight if you've been defeated!")
        self.call(tb_items.CmdAttack(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_items.CmdPass(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_items.CmdDisengage(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_items.CmdRest(), "", "Char rests to recover HP.")


class TestTurnBattleMagicCmd(CommandTest):

    # Test magic commands
    def test_turnbattlemagiccmd(self):
        self.call(tb_magic.CmdStatus(), "", "You have 100 / 100 HP and 20 / 20 MP.")
        self.call(tb_magic.CmdLearnSpell(), "test spell", "There is no spell with that name.")
        self.call(tb_magic.CmdCast(), "", "Usage: cast <spell name> = <target>, <target2>")
        # Also test the commands that are the same in the basic module
        self.call(tb_magic.CmdFight(), "", "There's nobody here to fight!")
        self.call(tb_magic.CmdAttack(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_magic.CmdPass(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_magic.CmdDisengage(), "", "You can only do that in combat. (see: help fight)")
        self.call(tb_magic.CmdRest(), "", "Char rests to recover HP and MP.")


class TestTurnBattleBasicFunc(EvenniaTest):

    def setUp(self):
        super(TestTurnBattleBasicFunc, self).setUp()
        self.testroom = create_object(DefaultRoom, key="Test Room")
        self.attacker = create_object(tb_basic.TBBasicCharacter, key="Attacker", location=self.testroom)
        self.defender = create_object(tb_basic.TBBasicCharacter, key="Defender", location=self.testroom)
        self.joiner = create_object(tb_basic.TBBasicCharacter, key="Joiner", location=None)

    def tearDown(self):
        super(TestTurnBattleBasicFunc, self).tearDown()
        self.attacker.delete()
        self.defender.delete()
        self.joiner.delete()
        self.testroom.delete()
        self.turnhandler.stop()

    # Test combat functions
    def test_tbbasicfunc(self):
        # Initiative roll
        initiative = tb_basic.roll_init(self.attacker)
        self.assertTrue(initiative >= 0 and initiative <= 1000)
        # Attack roll
        attack_roll = tb_basic.get_attack(self.attacker, self.defender)
        self.assertTrue(attack_roll >= 0 and attack_roll <= 100)
        # Defense roll
        defense_roll = tb_basic.get_defense(self.attacker, self.defender)
        self.assertTrue(defense_roll == 50)
        # Damage roll
        damage_roll = tb_basic.get_damage(self.attacker, self.defender)
        self.assertTrue(damage_roll >= 15 and damage_roll <= 25)
        # Apply damage
        self.defender.db.hp = 10
        tb_basic.apply_damage(self.defender, 3)
        self.assertTrue(self.defender.db.hp == 7)
        # Resolve attack
        self.defender.db.hp = 40
        tb_basic.resolve_attack(self.attacker, self.defender, attack_value=20, defense_value=10)
        self.assertTrue(self.defender.db.hp < 40)
        # Combat cleanup
        self.attacker.db.Combat_attribute = True
        tb_basic.combat_cleanup(self.attacker)
        self.assertFalse(self.attacker.db.combat_attribute)
        # Is in combat
        self.assertFalse(tb_basic.is_in_combat(self.attacker))
        # Set up turn handler script for further tests
        self.attacker.location.scripts.add(tb_basic.TBBasicTurnHandler)
        self.turnhandler = self.attacker.db.combat_TurnHandler
        self.assertTrue(self.attacker.db.combat_TurnHandler)
        # Set the turn handler's interval very high to keep it from repeating during tests.
        self.turnhandler.interval = 10000
        # Force turn order
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        # Test is turn
        self.assertTrue(tb_basic.is_turn(self.attacker))
        # Spend actions
        self.attacker.db.Combat_ActionsLeft = 1
        tb_basic.spend_action(self.attacker, 1, action_name="Test")
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "Test")
        # Initialize for combat
        self.attacker.db.Combat_ActionsLeft = 983
        self.turnhandler.initialize_for_combat(self.attacker)
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "null")
        # Start turn
        self.defender.db.Combat_ActionsLeft = 0
        self.turnhandler.start_turn(self.defender)
        self.assertTrue(self.defender.db.Combat_ActionsLeft == 1)
        # Next turn
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.next_turn()
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Turn end check
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.attacker.db.Combat_ActionsLeft = 0
        self.turnhandler.turn_end_check(self.attacker)
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Join fight
        self.joiner.location = self.testroom
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.join_fight(self.joiner)
        self.assertTrue(self.turnhandler.db.turn == 1)
        self.assertTrue(self.turnhandler.db.fighters == [self.joiner, self.attacker, self.defender])


class TestTurnBattleEquipFunc(EvenniaTest):

    def setUp(self):
        super(TestTurnBattleEquipFunc, self).setUp()
        self.testroom = create_object(DefaultRoom, key="Test Room")
        self.attacker = create_object(tb_equip.TBEquipCharacter, key="Attacker", location=self.testroom)
        self.defender = create_object(tb_equip.TBEquipCharacter, key="Defender", location=self.testroom)
        self.joiner = create_object(tb_equip.TBEquipCharacter, key="Joiner", location=None)

    def tearDown(self):
        super(TestTurnBattleEquipFunc, self).tearDown()
        self.attacker.delete()
        self.defender.delete()
        self.joiner.delete()
        self.testroom.delete()
        self.turnhandler.stop()

    # Test the combat functions in tb_equip too. They work mostly the same.
    def test_tbequipfunc(self):
        # Initiative roll
        initiative = tb_equip.roll_init(self.attacker)
        self.assertTrue(initiative >= 0 and initiative <= 1000)
        # Attack roll
        attack_roll = tb_equip.get_attack(self.attacker, self.defender)
        self.assertTrue(attack_roll >= -50 and attack_roll <= 150)
        # Defense roll
        defense_roll = tb_equip.get_defense(self.attacker, self.defender)
        self.assertTrue(defense_roll == 50)
        # Damage roll
        damage_roll = tb_equip.get_damage(self.attacker, self.defender)
        self.assertTrue(damage_roll >= 0 and damage_roll <= 50)
        # Apply damage
        self.defender.db.hp = 10
        tb_equip.apply_damage(self.defender, 3)
        self.assertTrue(self.defender.db.hp == 7)
        # Resolve attack
        self.defender.db.hp = 40
        tb_equip.resolve_attack(self.attacker, self.defender, attack_value=20, defense_value=10)
        self.assertTrue(self.defender.db.hp < 40)
        # Combat cleanup
        self.attacker.db.Combat_attribute = True
        tb_equip.combat_cleanup(self.attacker)
        self.assertFalse(self.attacker.db.combat_attribute)
        # Is in combat
        self.assertFalse(tb_equip.is_in_combat(self.attacker))
        # Set up turn handler script for further tests
        self.attacker.location.scripts.add(tb_equip.TBEquipTurnHandler)
        self.turnhandler = self.attacker.db.combat_TurnHandler
        self.assertTrue(self.attacker.db.combat_TurnHandler)
        # Set the turn handler's interval very high to keep it from repeating during tests.
        self.turnhandler.interval = 10000
        # Force turn order
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        # Test is turn
        self.assertTrue(tb_equip.is_turn(self.attacker))
        # Spend actions
        self.attacker.db.Combat_ActionsLeft = 1
        tb_equip.spend_action(self.attacker, 1, action_name="Test")
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "Test")
        # Initialize for combat
        self.attacker.db.Combat_ActionsLeft = 983
        self.turnhandler.initialize_for_combat(self.attacker)
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "null")
        # Start turn
        self.defender.db.Combat_ActionsLeft = 0
        self.turnhandler.start_turn(self.defender)
        self.assertTrue(self.defender.db.Combat_ActionsLeft == 1)
        # Next turn
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.next_turn()
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Turn end check
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.attacker.db.Combat_ActionsLeft = 0
        self.turnhandler.turn_end_check(self.attacker)
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Join fight
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.join_fight(self.joiner)
        self.assertTrue(self.turnhandler.db.turn == 1)
        self.assertTrue(self.turnhandler.db.fighters == [self.joiner, self.attacker, self.defender])


class TestTurnBattleRangeFunc(EvenniaTest):

    def setUp(self):
        super(TestTurnBattleRangeFunc, self).setUp()
        self.testroom = create_object(DefaultRoom, key="Test Room")
        self.attacker = create_object(tb_range.TBRangeCharacter, key="Attacker", location=self.testroom)
        self.defender = create_object(tb_range.TBRangeCharacter, key="Defender", location=self.testroom)
        self.joiner = create_object(tb_range.TBRangeCharacter, key="Joiner", location=self.testroom)

    def tearDown(self):
        super(TestTurnBattleRangeFunc, self).tearDown()
        self.attacker.delete()
        self.defender.delete()
        self.joiner.delete()
        self.testroom.delete()
        self.turnhandler.stop()

    # Test combat functions in tb_range too.
    def test_tbrangefunc(self):
        # Initiative roll
        initiative = tb_range.roll_init(self.attacker)
        self.assertTrue(initiative >= 0 and initiative <= 1000)
        # Attack roll
        attack_roll = tb_range.get_attack(self.attacker, self.defender, "test")
        self.assertTrue(attack_roll >= 0 and attack_roll <= 100)
        # Defense roll
        defense_roll = tb_range.get_defense(self.attacker, self.defender, "test")
        self.assertTrue(defense_roll == 50)
        # Damage roll
        damage_roll = tb_range.get_damage(self.attacker, self.defender)
        self.assertTrue(damage_roll >= 15 and damage_roll <= 25)
        # Apply damage
        self.defender.db.hp = 10
        tb_range.apply_damage(self.defender, 3)
        self.assertTrue(self.defender.db.hp == 7)
        # Resolve attack
        self.defender.db.hp = 40
        tb_range.resolve_attack(self.attacker, self.defender, "test", attack_value=20, defense_value=10)
        self.assertTrue(self.defender.db.hp < 40)
        # Combat cleanup
        self.attacker.db.Combat_attribute = True
        tb_range.combat_cleanup(self.attacker)
        self.assertFalse(self.attacker.db.combat_attribute)
        # Is in combat
        self.assertFalse(tb_range.is_in_combat(self.attacker))
        # Set up turn handler script for further tests
        self.attacker.location.scripts.add(tb_range.TBRangeTurnHandler)
        self.turnhandler = self.attacker.db.combat_TurnHandler
        self.assertTrue(self.attacker.db.combat_TurnHandler)
        # Set the turn handler's interval very high to keep it from repeating during tests.
        self.turnhandler.interval = 10000
        # Force turn order
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        # Test is turn
        self.assertTrue(tb_range.is_turn(self.attacker))
        # Spend actions
        self.attacker.db.Combat_ActionsLeft = 1
        tb_range.spend_action(self.attacker, 1, action_name="Test")
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "Test")
        # Initialize for combat
        self.attacker.db.Combat_ActionsLeft = 983
        self.turnhandler.initialize_for_combat(self.attacker)
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "null")
        # Set up ranges again, since initialize_for_combat clears them
        self.attacker.db.combat_range = {}
        self.attacker.db.combat_range[self.attacker] = 0
        self.attacker.db.combat_range[self.defender] = 1
        self.defender.db.combat_range = {}
        self.defender.db.combat_range[self.defender] = 0
        self.defender.db.combat_range[self.attacker] = 1
        # Start turn
        self.defender.db.Combat_ActionsLeft = 0
        self.turnhandler.start_turn(self.defender)
        self.assertTrue(self.defender.db.Combat_ActionsLeft == 2)
        # Next turn
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.next_turn()
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Turn end check
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.attacker.db.Combat_ActionsLeft = 0
        self.turnhandler.turn_end_check(self.attacker)
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Join fight
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.join_fight(self.joiner)
        self.assertTrue(self.turnhandler.db.turn == 1)
        self.assertTrue(self.turnhandler.db.fighters == [self.joiner, self.attacker, self.defender])
        # Now, test for approach/withdraw functions
        self.assertTrue(tb_range.get_range(self.attacker, self.defender) == 1)
        # Approach
        tb_range.approach(self.attacker, self.defender)
        self.assertTrue(tb_range.get_range(self.attacker, self.defender) == 0)
        # Withdraw
        tb_range.withdraw(self.attacker, self.defender)
        self.assertTrue(tb_range.get_range(self.attacker, self.defender) == 1)


class TestTurnBattleItemsFunc(EvenniaTest):

    @patch("evennia.contrib.turnbattle.tb_items.tickerhandler", new=MagicMock())
    def setUp(self):
        super(TestTurnBattleItemsFunc, self).setUp()
        self.testroom = create_object(DefaultRoom, key="Test Room")
        self.attacker = create_object(tb_items.TBItemsCharacter, key="Attacker", location=self.testroom)
        self.defender = create_object(tb_items.TBItemsCharacter, key="Defender", location=self.testroom)
        self.joiner = create_object(tb_items.TBItemsCharacter, key="Joiner", location=self.testroom)
        self.user = create_object(tb_items.TBItemsCharacter, key="User", location=self.testroom)
        self.test_healpotion = create_object(key="healing potion")
        self.test_healpotion.db.item_func = "heal"
        self.test_healpotion.db.item_uses = 3

    def tearDown(self):
        super(TestTurnBattleItemsFunc, self).tearDown()
        self.attacker.delete()
        self.defender.delete()
        self.joiner.delete()
        self.user.delete()
        self.testroom.delete()
        self.turnhandler.stop()

    # Test functions in tb_items.
    def test_tbitemsfunc(self):
        # Initiative roll
        initiative = tb_items.roll_init(self.attacker)
        self.assertTrue(initiative >= 0 and initiative <= 1000)
        # Attack roll
        attack_roll = tb_items.get_attack(self.attacker, self.defender)
        self.assertTrue(attack_roll >= 0 and attack_roll <= 100)
        # Defense roll
        defense_roll = tb_items.get_defense(self.attacker, self.defender)
        self.assertTrue(defense_roll == 50)
        # Damage roll
        damage_roll = tb_items.get_damage(self.attacker, self.defender)
        self.assertTrue(damage_roll >= 15 and damage_roll <= 25)
        # Apply damage
        self.defender.db.hp = 10
        tb_items.apply_damage(self.defender, 3)
        self.assertTrue(self.defender.db.hp == 7)
        # Resolve attack
        self.defender.db.hp = 40
        tb_items.resolve_attack(self.attacker, self.defender, attack_value=20, defense_value=10)
        self.assertTrue(self.defender.db.hp < 40)
        # Combat cleanup
        self.attacker.db.Combat_attribute = True
        tb_items.combat_cleanup(self.attacker)
        self.assertFalse(self.attacker.db.combat_attribute)
        # Is in combat
        self.assertFalse(tb_items.is_in_combat(self.attacker))
        # Set up turn handler script for further tests
        self.attacker.location.scripts.add(tb_items.TBItemsTurnHandler)
        self.turnhandler = self.attacker.db.combat_TurnHandler
        self.assertTrue(self.attacker.db.combat_TurnHandler)
        # Set the turn handler's interval very high to keep it from repeating during tests.
        self.turnhandler.interval = 10000
        # Force turn order
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        # Test is turn
        self.assertTrue(tb_items.is_turn(self.attacker))
        # Spend actions
        self.attacker.db.Combat_ActionsLeft = 1
        tb_items.spend_action(self.attacker, 1, action_name="Test")
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "Test")
        # Initialize for combat
        self.attacker.db.Combat_ActionsLeft = 983
        self.turnhandler.initialize_for_combat(self.attacker)
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "null")
        # Start turn
        self.defender.db.Combat_ActionsLeft = 0
        self.turnhandler.start_turn(self.defender)
        self.assertTrue(self.defender.db.Combat_ActionsLeft == 1)
        # Next turn
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.next_turn()
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Turn end check
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.attacker.db.Combat_ActionsLeft = 0
        self.turnhandler.turn_end_check(self.attacker)
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Join fight
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.join_fight(self.joiner)
        self.assertTrue(self.turnhandler.db.turn == 1)
        self.assertTrue(self.turnhandler.db.fighters == [self.joiner, self.attacker, self.defender])
        # Now time to test item stuff.
        # Spend item use
        tb_items.spend_item_use(self.test_healpotion, self.user)
        self.assertTrue(self.test_healpotion.db.item_uses == 2)
        # Use item
        self.user.db.hp = 2
        tb_items.use_item(self.user, self.test_healpotion, self.user)
        self.assertTrue(self.user.db.hp > 2)
        # Add contition
        tb_items.add_condition(self.user, self.user, "Test", 5)
        self.assertTrue(self.user.db.conditions == {"Test":[5, self.user]})
        # Condition tickdown
        tb_items.condition_tickdown(self.user, self.user)
        self.assertTrue(self.user.db.conditions == {"Test":[4, self.user]})
        # Test item functions now!
        # Item heal
        self.user.db.hp = 2
        tb_items.itemfunc_heal(self.test_healpotion, self.user, self.user)
        # Item add condition
        self.user.db.conditions = {}
        tb_items.itemfunc_add_condition(self.test_healpotion, self.user, self.user)
        self.assertTrue(self.user.db.conditions == {"Regeneration":[5, self.user]})
        # Item cure condition
        self.user.db.conditions = {"Poisoned":[5, self.user]}
        tb_items.itemfunc_cure_condition(self.test_healpotion, self.user, self.user)
        self.assertTrue(self.user.db.conditions == {})


class TestTurnBattleMagicFunc(EvenniaTest):

    def setUp(self):
        super(TestTurnBattleMagicFunc, self).setUp()
        self.testroom = create_object(DefaultRoom, key="Test Room")
        self.attacker = create_object(tb_magic.TBMagicCharacter, key="Attacker", location=self.testroom)
        self.defender = create_object(tb_magic.TBMagicCharacter, key="Defender", location=self.testroom)
        self.joiner = create_object(tb_magic.TBMagicCharacter, key="Joiner", location=self.testroom)

    def tearDown(self):
        super(TestTurnBattleMagicFunc, self).tearDown()
        self.attacker.delete()
        self.defender.delete()
        self.joiner.delete()
        self.testroom.delete()
        self.turnhandler.stop()

    # Test combat functions in tb_magic.
    def test_tbbasicfunc(self):
        # Initiative roll
        initiative = tb_magic.roll_init(self.attacker)
        self.assertTrue(initiative >= 0 and initiative <= 1000)
        # Attack roll
        attack_roll = tb_magic.get_attack(self.attacker, self.defender)
        self.assertTrue(attack_roll >= 0 and attack_roll <= 100)
        # Defense roll
        defense_roll = tb_magic.get_defense(self.attacker, self.defender)
        self.assertTrue(defense_roll == 50)
        # Damage roll
        damage_roll = tb_magic.get_damage(self.attacker, self.defender)
        self.assertTrue(damage_roll >= 15 and damage_roll <= 25)
        # Apply damage
        self.defender.db.hp = 10
        tb_magic.apply_damage(self.defender, 3)
        self.assertTrue(self.defender.db.hp == 7)
        # Resolve attack
        self.defender.db.hp = 40
        tb_magic.resolve_attack(self.attacker, self.defender, attack_value=20, defense_value=10)
        self.assertTrue(self.defender.db.hp < 40)
        # Combat cleanup
        self.attacker.db.Combat_attribute = True
        tb_magic.combat_cleanup(self.attacker)
        self.assertFalse(self.attacker.db.combat_attribute)
        # Is in combat
        self.assertFalse(tb_magic.is_in_combat(self.attacker))
        # Set up turn handler script for further tests
        self.attacker.location.scripts.add(tb_magic.TBMagicTurnHandler)
        self.turnhandler = self.attacker.db.combat_TurnHandler
        self.assertTrue(self.attacker.db.combat_TurnHandler)
        # Set the turn handler's interval very high to keep it from repeating during tests.
        self.turnhandler.interval = 10000
        # Force turn order
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        # Test is turn
        self.assertTrue(tb_magic.is_turn(self.attacker))
        # Spend actions
        self.attacker.db.Combat_ActionsLeft = 1
        tb_magic.spend_action(self.attacker, 1, action_name="Test")
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "Test")
        # Initialize for combat
        self.attacker.db.Combat_ActionsLeft = 983
        self.turnhandler.initialize_for_combat(self.attacker)
        self.assertTrue(self.attacker.db.Combat_ActionsLeft == 0)
        self.assertTrue(self.attacker.db.Combat_LastAction == "null")
        # Start turn
        self.defender.db.Combat_ActionsLeft = 0
        self.turnhandler.start_turn(self.defender)
        self.assertTrue(self.defender.db.Combat_ActionsLeft == 1)
        # Next turn
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.next_turn()
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Turn end check
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.attacker.db.Combat_ActionsLeft = 0
        self.turnhandler.turn_end_check(self.attacker)
        self.assertTrue(self.turnhandler.db.turn == 1)
        # Join fight
        self.turnhandler.db.fighters = [self.attacker, self.defender]
        self.turnhandler.db.turn = 0
        self.turnhandler.join_fight(self.joiner)
        self.assertTrue(self.turnhandler.db.turn == 1)
        self.assertTrue(self.turnhandler.db.fighters == [self.joiner, self.attacker, self.defender])


# Test tree select

from evennia.contrib import tree_select

TREE_MENU_TESTSTR = """Foo
Bar
-Baz
--Baz 1
--Baz 2
-Qux"""


class TestTreeSelectFunc(EvenniaTest):

    def test_tree_functions(self):
        # Dash counter
        self.assertTrue(tree_select.dashcount("--test") == 2)
        # Is category
        self.assertTrue(tree_select.is_category(TREE_MENU_TESTSTR, 1) == True)
        # Parse options
        self.assertTrue(tree_select.parse_opts(TREE_MENU_TESTSTR, category_index=2) == [(3, "Baz 1"), (4, "Baz 2")])
        # Index to selection
        self.assertTrue(tree_select.index_to_selection(TREE_MENU_TESTSTR, 2) == "Baz")
        # Go up one category
        self.assertTrue(tree_select.go_up_one_category(TREE_MENU_TESTSTR, 4) == 2)
        # Option list to menu options
        test_optlist = tree_select.parse_opts(TREE_MENU_TESTSTR, category_index=2)
        optlist_to_menu_expected_result = [{'goto': ['menunode_treeselect', {'newindex': 3}], 'key': 'Baz 1'},
        {'goto': ['menunode_treeselect', {'newindex': 4}], 'key': 'Baz 2'},
        {'goto': ['menunode_treeselect', {'newindex': 1}], 'key': ['<< Go Back', 'go back', 'back'], 'desc': 'Return to the previous menu.'}]
        self.assertTrue(tree_select.optlist_to_menuoptions(TREE_MENU_TESTSTR, test_optlist, 2, True, True) == optlist_to_menu_expected_result)

# Test field fill

from evennia.contrib import fieldfill

FIELD_TEST_TEMPLATE = [
{"fieldname":"TextTest", "fieldtype":"text"},
{"fieldname":"NumberTest", "fieldtype":"number", "blankmsg":"Number here!"},
{"fieldname":"DefaultText", "fieldtype":"text", "default":"Test"},
{"fieldname":"DefaultNum", "fieldtype":"number", "default":3}
]

FIELD_TEST_DATA = {"TextTest":None, "NumberTest":None, "DefaultText":"Test", "DefaultNum":3}

class TestFieldFillFunc(EvenniaTest):

    def test_field_functions(self):
        self.assertTrue(fieldfill.form_template_to_dict(FIELD_TEST_TEMPLATE) == FIELD_TEST_DATA)
        
# Test of the unixcommand module

from evennia.contrib.unixcommand import UnixCommand


class CmdDummy(UnixCommand):

    """A dummy UnixCommand."""

    key = "dummy"

    def init_parser(self):
        """Fill out options."""
        self.parser.add_argument("nb1", type=int, help="the first number")
        self.parser.add_argument("nb2", type=int, help="the second number")
        self.parser.add_argument("-v", "--verbose", action="store_true")

    def func(self):
        nb1 = self.opts.nb1
        nb2 = self.opts.nb2
        result = nb1 * nb2
        verbose = self.opts.verbose
        if verbose:
            self.msg("{} times {} is {}".format(nb1, nb2, result))
        else:
            self.msg("{} * {} = {}".format(nb1, nb2, result))


class TestUnixCommand(CommandTest):

    def test_success(self):
        """See the command parsing succeed."""
        self.call(CmdDummy(), "5 10", "5 * 10 = 50")
        self.call(CmdDummy(), "5 10 -v", "5 times 10 is 50")

    def test_failure(self):
        """If not provided with the right info, should fail."""
        ret = self.call(CmdDummy(), "5")
        lines = ret.splitlines()
        self.assertTrue(any(l.startswith("usage:") for l in lines))
        self.assertTrue(any(l.startswith("dummy: error:") for l in lines))

        # If we specify an incorrect number as parameter
        ret = self.call(CmdDummy(), "five ten")
        lines = ret.splitlines()
        self.assertTrue(any(l.startswith("usage:") for l in lines))
        self.assertTrue(any(l.startswith("dummy: error:") for l in lines))


import re
from evennia.contrib import color_markups


class TestColorMarkup(EvenniaTest):
    """
    Note: Normally this would be tested by importing the ansi parser and run
    the mappings through it. This is not possible since the ansi module creates
    its mapping at the module/class level; since the ansi module is used by so
    many other modules it appears that trying to overload
    settings to test it causes issues with unrelated tests.
    """

    def test_curly_markup(self):
        ansi_map = color_markups.CURLY_COLOR_ANSI_EXTRA_MAP
        self.assertIsNotNone(re.match(re.escape(ansi_map[7][0]), '{r'))
        self.assertIsNotNone(re.match(re.escape(ansi_map[-1][0]), '{[X'))
        xterm_fg = color_markups.CURLY_COLOR_XTERM256_EXTRA_FG
        self.assertIsNotNone(re.match(xterm_fg[0], '{001'))
        self.assertIsNotNone(re.match(xterm_fg[0], '{123'))
        self.assertIsNotNone(re.match(xterm_fg[0], '{455'))
        xterm_bg = color_markups.CURLY_COLOR_XTERM256_EXTRA_BG
        self.assertIsNotNone(re.match(xterm_bg[0], '{[001'))
        self.assertIsNotNone(re.match(xterm_bg[0], '{[123'))
        self.assertIsNotNone(re.match(xterm_bg[0], '{[455'))
        xterm_gfg = color_markups.CURLY_COLOR_XTERM256_EXTRA_GFG
        self.assertIsNotNone(re.match(xterm_gfg[0], '{=h'))
        self.assertIsNotNone(re.match(xterm_gfg[0], '{=e'))
        self.assertIsNotNone(re.match(xterm_gfg[0], '{=w'))
        xterm_gbg = color_markups.CURLY_COLOR_XTERM256_EXTRA_GBG
        self.assertIsNotNone(re.match(xterm_gbg[0], '{[=a'))
        self.assertIsNotNone(re.match(xterm_gbg[0], '{[=k'))
        self.assertIsNotNone(re.match(xterm_gbg[0], '{[=z'))
        bright_map = color_markups.CURLY_COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP
        self.assertEqual(bright_map[0][1], '{[500')
        self.assertEqual(bright_map[-1][1], '{[222')

    def test_mux_markup(self):
        ansi_map = color_markups.MUX_COLOR_ANSI_EXTRA_MAP
        self.assertIsNotNone(re.match(re.escape(ansi_map[10][0]), '%cr'))
        self.assertIsNotNone(re.match(re.escape(ansi_map[-1][0]), '%cX'))
        xterm_fg = color_markups.MUX_COLOR_XTERM256_EXTRA_FG
        self.assertIsNotNone(re.match(xterm_fg[0], '%c001'))
        self.assertIsNotNone(re.match(xterm_fg[0], '%c123'))
        self.assertIsNotNone(re.match(xterm_fg[0], '%c455'))
        xterm_bg = color_markups.MUX_COLOR_XTERM256_EXTRA_BG
        self.assertIsNotNone(re.match(xterm_bg[0], '%c[001'))
        self.assertIsNotNone(re.match(xterm_bg[0], '%c[123'))
        self.assertIsNotNone(re.match(xterm_bg[0], '%c[455'))
        xterm_gfg = color_markups.MUX_COLOR_XTERM256_EXTRA_GFG
        self.assertIsNotNone(re.match(xterm_gfg[0], '%c=h'))
        self.assertIsNotNone(re.match(xterm_gfg[0], '%c=e'))
        self.assertIsNotNone(re.match(xterm_gfg[0], '%c=w'))
        xterm_gbg = color_markups.MUX_COLOR_XTERM256_EXTRA_GBG
        self.assertIsNotNone(re.match(xterm_gbg[0], '%c[=a'))
        self.assertIsNotNone(re.match(xterm_gbg[0], '%c[=k'))
        self.assertIsNotNone(re.match(xterm_gbg[0], '%c[=z'))
        bright_map = color_markups.MUX_COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP
        self.assertEqual(bright_map[0][1], '%c[500')
        self.assertEqual(bright_map[-1][1], '%c[222')


from evennia.contrib import random_string_generator

SIMPLE_GENERATOR = random_string_generator.RandomStringGenerator("simple", "[01]{2}")


class TestRandomStringGenerator(EvenniaTest):

    def test_generate(self):
        """Generate and fail when exhausted."""
        generated = []
        for i in range(4):
            generated.append(SIMPLE_GENERATOR.get())

        generated.sort()
        self.assertEqual(generated, ["00", "01", "10", "11"])

        # At this point, we have generated 4 strings.
        # We can't generate one more
        with self.assertRaises(random_string_generator.ExhaustedGenerator):
            SIMPLE_GENERATOR.get()


# Tests for the building_menu contrib
from evennia.contrib.building_menu import BuildingMenu, CmdNoInput, CmdNoMatch

class Submenu(BuildingMenu):
    def init(self, exit):
        self.add_choice("title", key="t", attr="key")

class TestBuildingMenu(CommandTest):

    def setUp(self):
        super(TestBuildingMenu, self).setUp()
        self.menu = BuildingMenu(caller=self.char1, obj=self.room1, title="test")
        self.menu.add_choice("title", key="t", attr="key")

    def test_quit(self):
        """Try to quit the building menu."""
        self.assertFalse(self.char1.cmdset.has("building_menu"))
        self.menu.open()
        self.assertTrue(self.char1.cmdset.has("building_menu"))
        self.call(CmdNoMatch(building_menu=self.menu), "q")
        # char1 tries to quit the editor
        self.assertFalse(self.char1.cmdset.has("building_menu"))

    def test_setattr(self):
        """Test the simple setattr provided by building menus."""
        key = self.room1.key
        self.menu.open()
        self.call(CmdNoMatch(building_menu=self.menu), "t")
        self.assertIsNotNone(self.menu.current_choice)
        self.call(CmdNoMatch(building_menu=self.menu), "some new title")
        self.call(CmdNoMatch(building_menu=self.menu), "@")
        self.assertIsNone(self.menu.current_choice)
        self.assertEqual(self.room1.key, "some new title")
        self.call(CmdNoMatch(building_menu=self.menu), "q")

    def test_add_choice_without_key(self):
        """Try to add choices without keys."""
        choices = []
        for i in range(20):
            choices.append(self.menu.add_choice("choice", attr="test"))
        self.menu._add_keys_choice()
        keys = ["c", "h", "o", "i", "e", "ch", "ho", "oi", "ic", "ce", "cho", "hoi", "oic", "ice", "choi", "hoic", "oice", "choic", "hoice", "choice"]
        for i in range(20):
            self.assertEqual(choices[i].key, keys[i])

        # Adding another key of the same title would break, no more available shortcut
        self.menu.add_choice("choice", attr="test")
        with self.assertRaises(ValueError):
            self.menu._add_keys_choice()

    def test_callbacks(self):
        """Test callbacks in menus."""
        self.room1.key = "room1"
        def on_enter(caller, menu):
            caller.msg("on_enter:{}".format(menu.title))
        def on_nomatch(caller, string, choice):
            caller.msg("on_nomatch:{},{}".format(string, choice.key))
        def on_leave(caller, obj):
            caller.msg("on_leave:{}".format(obj.key))
        self.menu.add_choice("test", key="e", on_enter=on_enter, on_nomatch=on_nomatch, on_leave=on_leave)
        self.call(CmdNoMatch(building_menu=self.menu), "e", "on_enter:test")
        self.call(CmdNoMatch(building_menu=self.menu), "ok", "on_nomatch:ok,e")
        self.call(CmdNoMatch(building_menu=self.menu), "@", "on_leave:room1")
        self.call(CmdNoMatch(building_menu=self.menu), "q")

    def test_multi_level(self):
        """Test multi-level choices."""
        # Creaste three succeeding menu (t2 is contained in t1, t3 is contained in t2)
        def on_nomatch_t1(caller, menu):
            menu.move("whatever") # this will be valid since after t1 is a joker

        def on_nomatch_t2(caller, menu):
            menu.move("t3") # this time the key matters

        t1 = self.menu.add_choice("what", key="t1", on_nomatch=on_nomatch_t1)
        t2 = self.menu.add_choice("and", key="t1.*", on_nomatch=on_nomatch_t2)
        t3 = self.menu.add_choice("why", key="t1.*.t3")
        self.menu.open()

        # Move into t1
        self.assertIn(t1, self.menu.relevant_choices)
        self.assertNotIn(t2, self.menu.relevant_choices)
        self.assertNotIn(t3, self.menu.relevant_choices)
        self.assertIsNone(self.menu.current_choice)
        self.call(CmdNoMatch(building_menu=self.menu), "t1")
        self.assertEqual(self.menu.current_choice, t1)
        self.assertNotIn(t1, self.menu.relevant_choices)
        self.assertIn(t2, self.menu.relevant_choices)
        self.assertNotIn(t3, self.menu.relevant_choices)

        # Move into t2
        self.call(CmdNoMatch(building_menu=self.menu), "t2")
        self.assertEqual(self.menu.current_choice, t2)
        self.assertNotIn(t1, self.menu.relevant_choices)
        self.assertNotIn(t2, self.menu.relevant_choices)
        self.assertIn(t3, self.menu.relevant_choices)

        # Move into t3
        self.call(CmdNoMatch(building_menu=self.menu), "t3")
        self.assertEqual(self.menu.current_choice, t3)
        self.assertNotIn(t1, self.menu.relevant_choices)
        self.assertNotIn(t2, self.menu.relevant_choices)
        self.assertNotIn(t3, self.menu.relevant_choices)

        # Move back to t2
        self.call(CmdNoMatch(building_menu=self.menu), "@")
        self.assertEqual(self.menu.current_choice, t2)
        self.assertNotIn(t1, self.menu.relevant_choices)
        self.assertNotIn(t2, self.menu.relevant_choices)
        self.assertIn(t3, self.menu.relevant_choices)

        # Move back into t1
        self.call(CmdNoMatch(building_menu=self.menu), "@")
        self.assertEqual(self.menu.current_choice, t1)
        self.assertNotIn(t1, self.menu.relevant_choices)
        self.assertIn(t2, self.menu.relevant_choices)
        self.assertNotIn(t3, self.menu.relevant_choices)

        # Moves back to the main menu
        self.call(CmdNoMatch(building_menu=self.menu), "@")
        self.assertIn(t1, self.menu.relevant_choices)
        self.assertNotIn(t2, self.menu.relevant_choices)
        self.assertNotIn(t3, self.menu.relevant_choices)
        self.assertIsNone(self.menu.current_choice)
        self.call(CmdNoMatch(building_menu=self.menu), "q")

    def test_submenu(self):
        """Test to add sub-menus."""
        def open_exit(menu):
            menu.open_submenu("evennia.contrib.tests.Submenu", self.exit)
            return False

        self.menu.add_choice("exit", key="x", on_enter=open_exit)
        self.menu.open()
        self.call(CmdNoMatch(building_menu=self.menu), "x")
        self.menu = self.char1.ndb._building_menu
        self.call(CmdNoMatch(building_menu=self.menu), "t")
        self.call(CmdNoMatch(building_menu=self.menu), "in")
        self.call(CmdNoMatch(building_menu=self.menu), "@")
        self.call(CmdNoMatch(building_menu=self.menu), "@")
        self.menu = self.char1.ndb._building_menu
        self.assertEqual(self.char1.ndb._building_menu.obj, self.room1)
        self.call(CmdNoMatch(building_menu=self.menu), "q")
        self.assertEqual(self.exit.key, "in")
