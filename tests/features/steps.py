# -*- coding: utf-8 -*-
from lettuce import  *
import journal

@step(r"Given my post title is misspelled '(\w+)'")
def  given_my_post_title_is_misspelled(step, title):
    world.title = str(title)
    connect.db()

@step("I edit it '(\w+)'" )
def  change_title(step, newtitle):
    world.title = str(newtitle)
    
@step(r"Then it will be spelled correctly '(\w+)'")
def then_it_will_be_spelled_correctly(step, expected):
    expected = str(expected)
    assert world.title == expected, \
            "Got %s" % world.title
