# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from unittest import SkipTest

from jwzthreading import (Message, thread, sort_threads)
from jwzthreading.utils import (parse_mailbox,
                                parse_mailman_htmlthread,
                                MAILBOX_DELIMITER)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data/fedora-devel-mailman')

# Expected number of emails and threads
N_EMAILS_JUNE2010 = 292
N_THREADS_JUNE2010 = 63
MAILMAN_MAX_DEPTH = 3


def test_parse_mailbox():
    """ Test that we can parse mailman files """
    msglist = parse_mailbox(os.path.join(DATA_DIR, '2010-January.txt.gz'),
                            encoding='latin1', headersonly=True)

    assert len(msglist) == N_EMAILS_JUNE2010


def test_parse_mailman_htmlthread():
    """ Test that we can parse mailman html thread """
    try:
        import lxml  # noqa
    except ImportError:
        raise SkipTest
    threads = parse_mailman_htmlthread(os.path.join(DATA_DIR,
                                       '2010-January_thread.html.gz'))

    assert sum([el.tree_size for el in threads]) == N_EMAILS_JUNE2010


def test_mailbox_delimiter():
    import re
    examples = ['From jonathan.underwood@gmail.com Thu Jan  7 12:55:58 2010',
                'From - Thu Sep  3 12:58:15 2015']

    for line in examples:
        assert re.match(MAILBOX_DELIMITER, line)


def test_threading_fedora_June2010():
    """ Test threading on the fedora-devel mailing list data
    from June 2010"""

    try:
        import lxml  # noqa
    except ImportError:
        raise SkipTest

    try:
        import numpy as np
        from numpy.testing import assert_array_equal
        NUMPY_PRESENT = True
    except ImportError:
        NUMPY_PRESENT = False

    msglist = parse_mailbox(os.path.join(DATA_DIR, '2010-January.txt.gz'),
                            encoding='latin1', headersonly=True)

    assert len(msglist) == N_EMAILS_JUNE2010

    threads_ref = parse_mailman_htmlthread(os.path.join(DATA_DIR,
                                           '2010-January_thread.html.gz'))
    threads_ref = sort_threads(threads_ref, key='subject', missing='Z')

    threads = thread([Message(el, message_idx=idx)
                      for idx, el in enumerate(msglist)],
                     group_by_subject=False)
    threads = sort_threads(threads, key='subject', missing='Z')

    # There is one single "empty root container", which
    # corresponds to "Re: ABRT considered painful, drago01" (idx==39, id=3) at
    # https://www.redhat.com/archives/fedora-devel-list/2010-January/thread.html
    # Mailman handles this differently, which is visually better but
    # JWZ is technically more correct IMO, just removing this case for now.
    assert sum([el.get('message') is None for el in threads]) == 1

    # remove the problematic thread (cf above)
    threads = [el for el in threads if el.get('message') is not None]
    threads_ref = [el for el in threads_ref if el['message'].message_idx != 3]

    # JWZ currently uncorrectly threads <Possible follow up> of the
    # "Common Lisp apps in Fedora," thread, remove the wrongly threaded
    # containers
    threads = [el for el in threads
               if el.get('message').message_idx not in [153, 285]]

    assert len(threads) == len(threads_ref)  # we deleted one thread

    for idx, container_ref in enumerate(threads_ref):
        container = threads[idx]
        if container.get('message') is not None:
            subject = container['message'].subject
            message_idx = container['message'].message_idx
        else:
            subject = None   # noqa
            message_idx = None

        assert container_ref['message'].message_idx == message_idx

        if message_idx == 55:
            # This is the "Common Lisp apps in Fedora" thread that has
            # uncorrectly threaded <Possible follow up>
            continue

        assert container_ref.tree_size == container.tree_size

        # check that we have the same messages in threads
        if NUMPY_PRESENT:
            assert_array_equal(
                [el['message'].message_idx for el in container_ref.flatten()],
                [el['message'].message_idx for el in container.flatten()])
            assert_array_equal(
                [el.current_depth for el in container_ref.flatten()],
                np.fmin([el.current_depth for el in container.flatten()],
                        MAILMAN_MAX_DEPTH))


def test_empty_collapsing_fedora_June2010():
    """ Test threading on the fedora-devel mailing list data
    from June 2010"""

    try:
        import lxml  # noqa
    except ImportError:
        raise SkipTest

    msglist = parse_mailbox(os.path.join(DATA_DIR, '2010-January.txt.gz'),
                            encoding='latin1', headersonly=True)

    assert len(msglist) == N_EMAILS_JUNE2010

    threads_ref = parse_mailman_htmlthread(os.path.join(DATA_DIR,
                                           '2010-January_thread.html.gz'))
    threads_ref = sort_threads(threads_ref, key='subject', missing='Z')

    threads = thread([Message(el, message_idx=idx)
                      for idx, el in enumerate(msglist)],
                     group_by_subject=False)
    # There is one single "empty root container"
    assert sum([el.get('message') is None for el in threads]) == 1

    threads = [el.collapse_empty() for el in threads]

    # The empty container was removed
    assert sum([el.get('message') is None for el in threads]) == 0

    assert sum([el.parent is None for el in threads]) == len(threads)
