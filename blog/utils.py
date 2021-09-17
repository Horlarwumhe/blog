import base64
from binascii import Error as BinasciiError
import re
import os
from math import ceil
from glass import request,redirect


class Paginator:

    def __init__(self, object_list, per_page):
        self.object_list = object_list
        self.per_page = int(per_page)

    def validate_number(self, number):
        """Validate the given 1-based page number."""
        try:
            number = int(number)
        except ValueError:
            number = 1
        if number < 0:
            number = 1
        if number > self.num_pages:
            number = self.num_pages
        return number

    def get_page(self, number):
        """
        Return a valid page, even if the page argument isn't a number or isn't
        in range.
        """
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top >= self.count:
            top = self.count
        return Page(self.object_list[bottom:top], number, self)

    @property
    def count(self):
        """Return the total number of objects, across all pages."""
        c = getattr(self.object_list, 'count', None)
        if callable(c):
            return c()
        return len(self.object_list)

    @property
    def num_pages(self):
        """Return the total number of pages."""
        if self.count == 0:
            return 0
        hits = max(1, self.count)
        return ceil(hits / self.per_page)


class Page:

    def __init__(self, object_list, number, paginator):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def __repr__(self):
        return '<Page %s of %s>' % (self.number, self.paginator.num_pages)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError(
                'Page indices must be integers or slices, not %s.'
                % type(index).__name__
            )
        # The object_list is converted to a list so that if it was a QuerySet
        # it won't be a database hit per __getitem__.
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]

    def __iter__(self):
        return iter(self.object_list)

    @property
    def has_next(self):
        return self.number < self.paginator.num_pages
    
    @property
    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    @property
    def next_page_number(self):
        return self.paginator.validate_number(self.number + 1)

    @property
    def previous_page_number(self):
        return self.paginator.validate_number(self.number - 1)

    def start_index(self):
        """
        Return the 1-based index of the first object on this page,
        relative to total objects in the paginator.
        """
        # Special case, return zero if no items.
        if self.paginator.count == 0:
            return 0
        return (self.paginator.per_page * (self.number - 1)) + 1

    def end_index(self):
        """
        Return the 1-based index of the last object on this page,
        relative to total objects found (hits).
        """
        # Special case for the last page because there can be orphans.
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page



def login_require(func):
    def inner(*args,**kwargs):
        if not request.user:
            return redirect('/user/login?next=%s'%request.path)
        return func(*args,**kwargs)
    return inner


def url_b64encode(s):
    """
    Encode a bytestring to a base64 string for use in URLs. Strip any trailing
    equal signs.
    """
    s = s.encode()
    return base64.urlsafe_b64encode(s).rstrip(b'\n=').decode('ascii')


def url_b64decode(s):
    """
    Decode a base64 encoded string. Add back any trailing equal signs that
    might have been stripped.
    """
    s = s.encode()
    try:
        return base64.urlsafe_b64decode(s.ljust(len(s) + len(s) % 4, b'='))
    except (LookupError, BinasciiError) as e:
        raise ValueError(e)


def secure_filename(filename):
    #Werkzeug
    _filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_.-]")
    if isinstance(filename, str):
        from unicodedata import normalize

        filename = normalize("NFKD", filename).encode("ascii", "ignore")
        filename = filename.decode()
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")
    filename = str(_filename_ascii_strip_re.sub("", "_".join(filename.split()))).strip(
        "._"
    )
    return filename