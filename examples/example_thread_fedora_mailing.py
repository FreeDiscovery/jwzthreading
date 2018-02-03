# -*- coding: utf-8 -*-
"""
Email threading of the Fedora mailing list
==========================================

This example illustrates email threading with
`JWZ algorithm <http://www.jwz.org/doc/threading.html>`_ on the
Fedora mailing list `archive from January 2010
 <https://www.redhat.com/archives/fedora-devel-list/2010-January/thread.html>`_
"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from jwzthreading import (Message, thread, print_container,
                          sort_threads)
from jwzthreading.utils import parse_mailbox

data_path = os.path.join('..', "jwzthreading", "tests", "data",
                         "fedora-devel-mailman", "2010-January.txt.gz")


msglist = parse_mailbox(data_path,
                        encoding='latin1', headersonly=True)

threads = thread([Message(el, message_idx=idx)
                  for idx, el in enumerate(msglist)],
                 group_by_subject=False)
"""
Let's sort the resulting threads alphabetically by subject,
"""
threads = sort_threads(threads, key='subject', missing='Z')

"""
We can visualize the first 20 threads,
"""

for container in threads[:20]:
    print_container(container)
"""
and compare with `the threading done by Mailman
 <https://www.redhat.com/archives/fedora-devel-list/2010-January/thread.html>`_.

The sorting of threads is not the same (we would need to extend the
``Message`` class to store the message date in order to also sort by date)
however generally the agreement if fairly good.

The most noticeable differences is that Mailman,
 * has a maximum email depth of 2 (presumably for better visualization)
 * occasionally displays uncertainty regarding the correct threading with the
   "Possible follow-ups" tag.

If you are interested in more subtle difference between these threading
results, see ``jwzthreading/tests/test_newsgroups.py`` that performs
a more systematic validation of both results.
"""
