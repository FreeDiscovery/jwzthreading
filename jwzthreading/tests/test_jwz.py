"""
Test script for jwzthreading.
"""

# pylint: disable=c0103,c0111,r0904

import textwrap
from email import message_from_string

import pytest

from jwzthreading import (Message, Container,
                          unique, prune_container,
                          thread, sort_threads)


def test_container():
    """Test linking of containers."""
    c = Container()
    repr(c)

    c2 = Container()
    assert c.is_dummy()
    assert c.children == []
    assert c.parent is None
    assert not c.has_descendant(c2)

    # Add a child
    c3 = Container()
    c.add_child(c2)
    c2.add_child(c3)
    assert c.children ==[c2] 
    assert c2.parent == c
    assert c.has_descendant(c2)
    assert c.has_descendant(c3)
    assert c.has_descendant(c)

    # Remove a child
    c.remove_child(c2)
    assert c.children == []
    assert c2.parent is None
    assert not c.has_descendant(c3)
    assert c2.has_descendant(c3)

    # Add child of one container to another
    c3 = Container()
    c.add_child(c3)
    c2.add_child(c3)
    assert c3.parent == c2

def test_deep_container():
    """Build a 50000-deep list of nested Containers."""
    parent = Container()
    L = [parent]

    for _ in range(50000):
        child = Container()
        parent.add_child(child)
        L.append(child)
        parent = child

    # Test finding the last child
    assert L[0].has_descendant(L[-1])

    # Test a search that fails
    assert not L[0].has_descendant(Container())


def test_unique():
    assert unique((1, 2, 3, 1, 2, 3)) ==  [1, 2, 3]


def test_email_make_message():
    text = """\
        Subject: random

        Body."""
    msg = message_from_string(textwrap.dedent(text))
    with pytest.raises(ValueError):
        Message(msg)

def test_basic_message():
    text = """\
        Subject: random
        Message-ID: <message1>
        References: <ref1> <ref2> <ref1>
        In-Reply-To: <reply>

        Body."""
    msg = message_from_string(textwrap.dedent(text))
    m = Message(msg)
    assert repr(m)
    assert m.subject == 'random'
    assert sorted(m.references) == ['ref1', 'ref2', 'reply']

    # Verify that repr() works
    repr(m)


def test_prune_empty():
    c = Container()
    assert prune_container(c) == []

def test_prune_promote():
    p = Container()
    c1 = Container()
    c1.message = Message()
    p.add_child(c1)
    assert prune_container(p) == [c1]

def test_sorting():
    """Thread two unconnected messages."""
    m1 = Message(None)
    m1.subject = 'b'
    m1.message_id = 1
    m2 = Message(None)
    m2.subject = 'a'
    m2.message_id = 2
    m3 = Message(None)
    d = thread([m2, m1, m3], group_by_subject=False)

    d_s = sort_threads(d, key='message_id', missing=-1)
    assert d_s[0].message.message_id is None
    assert d_s[1].message.message_id == 1
    d_s = sort_threads(d, key='subject', missing='z')
    assert d_s[0].message.message_id == 2
    assert d_s[1].message.message_id == 1

def test_thread_single():
    """Thread a single message."""
    m = Message(None)
    m.subject = m.message_id = 'Single'
    d = thread([m])
    assert d[0].message == m

def test_thread_unrelated():
    """Thread two unconnected messages."""
    m1 = Message(None)
    m1.subject = m1.message_id = 'First'
    m2 = Message(None)
    m2.subject = m2.message_id = 'Second'
    d = thread([m1, m2], group_by_subject=False)
    assert d[0].message == m1
    assert d[1].children == []
    assert d[1].message == m2

def test_thread_two():
    """Thread two messages together."""
    m1 = Message(None)
    m1.subject = m1.message_id = 'First'
    m2 = Message(None)
    m2.subject = m2.message_id = 'Second'
    m2.references = ['First']
    d = thread([m1, m2])
    assert d[0].message == m1
    assert len(d[0].children) == 1
    assert d[0].children[0].message == m2

def test_thread_two_reverse():
    "Thread two messages together, with the child message listed first."
    m1 = Message(None)
    m1.subject = m1.message_id = 'First'
    m2 = Message(None)
    m2.subject = m2.message_id = 'Second'
    m2.references = ['First']
    d = thread([m2, m1], group_by_subject=False)
    assert d[0].message == m1
    assert len(d[0].children) == 1
    assert d[0].children[0].message == m2

def test_thread_lying_message():
    "Thread three messages together, with other messages lying in their references."
    dummy_parent_m = Message(None)
    dummy_parent_m.subject = dummy_parent_m.message_id = 'Dummy parent'
    lying_before_m = Message(None)
    lying_before_m.subject = lying_before_m.message_id = 'Lying before'
    lying_before_m.references = ['Dummy parent', 'Second', 'First', 'Third']
    m1 = Message(None)
    m1.subject = m1.message_id = 'First'
    m2 = Message(None)
    m2.subject = m2.message_id = 'Second'
    m2.references = ['First']
    m3 = Message(None)
    m3.subject = m3.message_id = 'Third'
    m3.references = ['First', 'Second']
    lying_after_m = Message(None)
    lying_after_m.subject = lying_after_m.message_id = 'Lying after'
    #lying_after_m.references = ['Dummy parent','Third', 'Second', 'First']
    d = thread([dummy_parent_m, lying_before_m,
                m1, m2, m3, lying_after_m], group_by_subject=False)
    assert d[1].message == m1
    assert len(d[1].children) == 1
    assert d[1].children[0].message == m2
    assert len(d[1].children[0].children) == 1
    assert d[1].children[0].children[0].message == m3

def test_thread_two_missing_parent():
    "Thread two messages, both children of a missing parent."
    m1 = Message(None)
    m1.subject = 'Child'
    m1.message_id = 'First'
    m1.references = ['parent']
    m2 = Message(None)
    m2.subject = 'Child'
    m2.message_id = 'Second'
    m2.references = ['parent']
    d = thread([m1, m2])
    assert d[0].message == None
    assert len(d[0].children) == 2
    assert d[0].children[0].message == m1
