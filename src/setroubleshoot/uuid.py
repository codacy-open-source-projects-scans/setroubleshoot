r"""UUID objects (universally unique identifiers) according to RFC 4122.

This module provides immutable UUID objects (class UUID) and the functions
uuid1(), uuid3(), uuid4(), uuid5() for generating version 1, 3, 4, and 5
UUIDs as specified in RFC 4122.

If all you want is a unique ID, you should probably call uuid1() or uuid4().
Note that uuid1() may compromise privacy since it creates a UUID containing
the computer's network address.  uuid4() creates a random UUID.

Typical usage:

    >>> import uuid

    # make a UUID based on the host ID and current time
    >>> uuid.uuid1()
    UUID('a8098c1a-f86e-11da-bd1a-00112444be1e')

    # make a UUID using an MD5 hash of a namespace UUID and a name
    >>> uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org')
    UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e')

    # make a random UUID
    >>> uuid.uuid4()
    UUID('16fd2706-8baf-433b-82eb-8c7fada847da')

    # make a UUID using a SHA-1 hash of a namespace UUID and a name
    >>> uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')
    UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d')

    # make a UUID from a string of hex digits (braces and hyphens ignored)
    >>> x = uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e0f}')

    # convert a UUID to a string of hex digits in standard form
    >>> str(x)
    '00010203-0405-0607-0809-0a0b0c0d0e0f'

    # get the raw 16 bytes of the UUID
    >>> x.bytes
    '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f'

    # make a UUID from a 16-byte string
    >>> uuid.UUID(bytes=x.bytes)
    UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')

This module works with Python 2.3 or higher."""

__author__ = 'Ka-Ping Yee <ping@zesty.ca>'
__date__ = '$Date: 2006/08/24 19:08:53 $'.split()[1].replace('/', '-')
__version__ = '$Revision: 1.2 $'.split()[1]

RESERVED_NCS, RFC_4122, RESERVED_MICROSOFT, RESERVED_FUTURE = [
    'reserved for NCS compatibility', 'specified in RFC 4122',
    'reserved for Microsoft compatibility', 'reserved for future definition']


import sys
if sys.version_info > (3,):
    long = int  # Python 2 compatibility

cmp = lambda x, y: (x > y) - (x < y)


class UUID(object):
    """Instances of the UUID class represent UUIDs as specified in RFC 4122.
    UUID objects are immutable, hashable, and usable as dictionary keys.
    Converting a UUID to a string with str() yields something in the form
    '12345678-1234-1234-1234-123456789abc'.  The UUID constructor accepts
    four possible forms: a similar string of hexadecimal digits, or a
    string of 16 raw bytes as an argument named 'bytes', or a tuple of
    six integer fields (with 32-bit, 16-bit, 16-bit, 8-bit, 8-bit, and
    48-bit values respectively) as an argument named 'fields', or a single
    128-bit integer as an argument named 'int'.

    UUIDs have these read-only attributes:

        bytes       the UUID as a 16-byte string

        fields      a tuple of the six integer fields of the UUID,
                    which are also available as six individual attributes
                    and two derived attributes:

            time_low                the first 32 bits of the UUID
            time_mid                the next 16 bits of the UUID
            time_hi_version         the next 16 bits of the UUID
            clock_seq_hi_variant    the next 8 bits of the UUID
            clock_seq_low           the next 8 bits of the UUID
            node                    the last 48 bits of the UUID

            time                    the 60-bit timestamp
            clock_seq               the 14-bit sequence number

        hex         the UUID as a 32-character hexadecimal string

        int         the UUID as a 128-bit integer

        urn         the UUID as a URN as specified in RFC 4122

        variant     the UUID variant (one of the constants RESERVED_NCS,
                    RFC_4122, RESERVED_MICROSOFT, or RESERVED_FUTURE)

        version     the UUID version number (1 through 5, meaningful only
                    when the variant is RFC_4122)
    """

    def __init__(self, hex=None, bytes=None, fields=None, int=None,
                 version=None):
        r"""Create a UUID from either a string of 32 hexadecimal digits,
        a string of 16 bytes as the 'bytes' argument, a tuple of six
        integers (32-bit time_low, 16-bit time_mid, 16-bit time_hi_version,
        8-bit clock_seq_hi_variant, 8-bit clock_seq_low, 48-bit node) as
        the 'fields' argument, or a single 128-bit integer as the 'int'
        argument.  When a string of hex digits is given, curly braces,
        hyphens, and a URN prefix are all optional.  For example, these
        expressions all yield the same UUID:

        UUID('{12345678-1234-5678-1234-567812345678}')
        UUID('12345678123456781234567812345678')
        UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
        UUID(bytes='\x12\x34\x56\x78'*4)
        UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))
        UUID(int=0x12345678123456781234567812345678)

        Exactly one of 'hex', 'bytes', 'fields', or 'int' must be given.
        The 'version' argument is optional; if given, the resulting UUID
        will have its variant and version number set according to RFC 4122,
        overriding bits in the given 'hex', 'bytes', 'fields', or 'int'.
        """

        if [hex, bytes, fields, int].count(None) != 3:
            raise TypeError('need just one of hex, bytes, fields, or int')
        if hex is not None:
            hex = hex.replace('urn:', '').replace('uuid:', '')
            hex = hex.strip('{}').replace('-', '')
            if len(hex) != 32:
                raise ValueError('badly formed hexadecimal UUID string')
            int = long(hex, 16)
        if bytes is not None:
            if len(bytes) != 16:
                raise ValueError('bytes is not a 16-char string')
            int = long(('%02x' * 16) % tuple(map(ord, bytes)), 16)
        if fields is not None:
            if len(fields) != 6:
                raise ValueError('fields is not a 6-tuple')
            (time_low, time_mid, time_hi_version,
             clock_seq_hi_variant, clock_seq_low, node) = fields
            if not 0 <= time_low < long(1 << 32):
                raise ValueError('field 1 out of range (need a 32-bit value)')
            if not 0 <= time_mid < long(1 << 16):
                raise ValueError('field 2 out of range (need a 16-bit value)')
            if not 0 <= time_hi_version < long(1 << 16):
                raise ValueError('field 3 out of range (need a 16-bit value)')
            if not 0 <= clock_seq_hi_variant < long(1 << 8):
                raise ValueError('field 4 out of range (need an 8-bit value)')
            if not 0 <= clock_seq_low < long(1 << 8):
                raise ValueError('field 5 out of range (need an 8-bit value)')
            if not 0 <= node < long(1 << 48):
                raise ValueError('field 6 out of range (need a 48-bit value)')
            clock_seq = (clock_seq_hi_variant << long(8)) | clock_seq_low
            int = ((time_low << long(96)) | (time_mid << long(80)) |
                   (time_hi_version << long(64)) | (clock_seq << long(48)) | node)
        if int is not None:
            if not 0 <= int < 1 << long(128):
                raise ValueError('int is out of range (need a 128-bit value)')
        if version is not None:
            if not 1 <= version <= 5:
                raise ValueError('illegal version number')
            # Set the variant to RFC 4122.
            int &= ~(0xc000 << long(48))
            int |= 0x8000 << long(48)
            # Set the version number.
            int &= ~(0xf000 << long(64))
            int |= version << long(76)
        self.__dict__['int'] = int

    def __lt__(self, other):
        if isinstance(other, UUID):
            return self.int < other.int
        return NotImplemented

    def __hash__(self):
        return hash(self.int)

    def __int__(self):
        return self.int

    def __repr__(self):
        return 'UUID(%r)' % str(self)

    def __setattr__(self, name, value):
        raise TypeError('UUID objects are immutable')

    def __str__(self):
        hex = '%032x' % self.int
        return '%s-%s-%s-%s-%s' % (
            hex[:8], hex[8:12], hex[12:16], hex[16:20], hex[20:])

    def get_bytes(self):
        bytes = ''
        for shift in range(0, 128, 8):
            bytes = chr((self.int >> shift) & 0xff) + bytes
        return bytes

    bytes = property(get_bytes)

    def get_fields(self):
        return (self.time_low, self.time_mid, self.time_hi_version,
                self.clock_seq_hi_variant, self.clock_seq_low, self.node)

    fields = property(get_fields)

    def get_time_low(self):
        return self.int >> long(96)

    time_low = property(get_time_low)

    def get_time_mid(self):
        return (self.int >> long(80)) & 0xffff

    time_mid = property(get_time_mid)

    def get_time_hi_version(self):
        return (self.int >> long(64)) & 0xffff

    time_hi_version = property(get_time_hi_version)

    def get_clock_seq_hi_variant(self):
        return (self.int >> long(56)) & 0xff

    clock_seq_hi_variant = property(get_clock_seq_hi_variant)

    def get_clock_seq_low(self):
        return (self.int >> long(48)) & 0xff

    clock_seq_low = property(get_clock_seq_low)

    def get_time(self):
        return (((self.time_hi_version & 0x0fff) << long(48)) |
                (self.time_mid << long(32)) | self.time_low)

    time = property(get_time)

    def get_clock_seq(self):
        return (((self.clock_seq_hi_variant & long(0x3f)) << long(8)) |
                self.clock_seq_low)

    clock_seq = property(get_clock_seq)

    def get_node(self):
        return self.int & 0xffffffffffff

    node = property(get_node)

    def get_hex(self):
        return '%032x' % self.int

    hex = property(get_hex)

    def get_urn(self):
        return 'urn:uuid:' + str(self)

    urn = property(get_urn)

    def get_variant(self):
        if not self.int & (0x8000 << long(48)):
            return RESERVED_NCS
        elif not self.int & (0x4000 << long(48)):
            return RFC_4122
        elif not self.int & (0x2000 << long(48)):
            return RESERVED_MICROSOFT
        else:
            return RESERVED_FUTURE

    variant = property(get_variant)

    def get_version(self):
        # The version bits are only meaningful for RFC 4122 UUIDs.
        if self.variant == RFC_4122:
            return int((self.int >> long(76)) & 0xf)

    version = property(get_version)


def _ifconfig_getnode():
    """Get the hardware address on Unix by running ifconfig."""
    import os
    for d in ['', '/sbin/', '/usr/sbin']:
        try:
            pipe = os.popen(os.path.join(d, 'ifconfig'))
        except IOError:
            continue
        for line in pipe:
            words = line.lower().split()
            for i in range(len(words)):
                if words[i] in ['hwaddr', 'ether']:
                    return int(words[i + 1].replace(':', ''), 16)


def _ipconfig_getnode():
    """Get the hardware address on Windows by running ipconfig.exe."""
    import os
    import re
    dirs = ['', r'c:\windows\system32', r'c:\winnt\system32']
    try:
        import ctypes
        buffer = ctypes.create_string_buffer(300)
        ctypes.windll.kernel32.GetSystemDirectoryA(buffer, 300)
        dirs.insert(0, buffer.value.decode('mbcs'))
    except:
        pass
    for d in dirs:
        try:
            pipe = os.popen(os.path.join(d, 'ipconfig') + ' /all')
        except IOError:
            continue
        for line in pipe:
            value = line.split(':')[-1].strip().lower()
            if re.match('([0-9a-f][0-9a-f]-){5}[0-9a-f][0-9a-f]', value):
                return int(value.replace('-', ''), 16)


def _netbios_getnode():
    """Get the hardware address on Windows using NetBIOS calls.
    See http://support.microsoft.com/kb/118623 for details."""
    import win32wnet
    import netbios
    ncb = netbios.NCB()
    ncb.Command = netbios.NCBENUM
    ncb.Buffer = adapters = netbios.LANA_ENUM()
    adapters._pack()
    if win32wnet.Netbios(ncb) != 0:
        return
    adapters._unpack()
    for i in range(adapters.length):
        ncb.Reset()
        ncb.Command = netbios.NCBRESET
        ncb.Lana_num = ord(adapters.lana[i])
        if win32wnet.Netbios(ncb) != 0:
            continue
        ncb.Reset()
        ncb.Command = netbios.NCBASTAT
        ncb.Lana_num = ord(adapters.lana[i])
        ncb.Callname = '*'.ljust(16)
        ncb.Buffer = status = netbios.ADAPTER_STATUS()
        if win32wnet.Netbios(ncb) != 0:
            continue
        status._unpack()
        bytes = map(ord, status.adapter_address)
        return ((bytes[0] << long(40)) + (bytes[1] << long(32)) +
                (bytes[2] << long(24)) + (bytes[3] << long(16)) +
                (bytes[4] << long(8)) + bytes[5])

_uuid_generate_random = _uuid_generate_time = _UuidCreate = None


def _unixdll_getnode():
    """Get the hardware address on Unix using ctypes."""
    _uuid_generate_time(_buffer)
    return UUID(bytes=_buffer.raw).node


def _windll_getnode():
    """Get the hardware address on Windows using ctypes."""
    if _UuidCreate(_buffer) == 0:
        return UUID(bytes=_buffer.raw).node


def _random_getnode():
    """Get a random node ID, with eighth bit set as suggested by RFC 4122."""
    import random
    return random.randrange(0, 1 << long(48)) | long(0x010000000000)

_node = None


def getnode():
    """Get the hardware address as a 48-bit integer.  The first time this
    runs, it may launch a separate program, which could be quite slow.  If
    all attempts to obtain the hardware address fail, we choose a random
    48-bit number with its eighth bit set to 1 as recommended in RFC 4122."""

    global _node
    if _node is not None:
        return _node

    import sys
    if sys.platform == 'win32':
        getters = [_windll_getnode, _netbios_getnode, _ipconfig_getnode]
    else:
        getters = [_unixdll_getnode, _ifconfig_getnode]

    for getter in getters + [_random_getnode]:
        try:
            _node = getter()
        except:
            continue
        if _node is not None:
            return _node


def uuid1(node=None, clock_seq=None):
    """Generate a UUID from a host ID, sequence number, and the current time.
    If 'node' is not given, getnode() is used to obtain the hardware
    address.  If 'clock_seq' is given, it is used as the sequence number;
    otherwise a random 14-bit sequence number is chosen."""

    # When the system provides a version-1 UUID generator, use it (but don't
    # use UuidCreate here because its UUIDs don't conform to RFC 4122).
    if _uuid_generate_time and node is clock_seq is None:
        _uuid_generate_time(_buffer)
        return UUID(bytes=_buffer.raw)

    import time
    nanoseconds = int(time.time() * 1e9)
    # 0x01b21dd213814000 is the number of 100-ns intervals between the
    # UUID epoch 1582-10-15 00:00:00 and the Unix epoch 1970-01-01 00:00:00.
    timestamp = int(nanoseconds / 100) + long(0x01b21dd213814000)
    if clock_seq is None:
        import random
        clock_seq = random.randrange(1 << long(14))  # instead of stable storage
    time_low = timestamp & long(0xffffffff)
    time_mid = (timestamp >> long(32)) & long(0xffff)
    time_hi_version = (timestamp >> long(48)) & long(0x0fff)
    clock_seq_low = clock_seq & long(0xff)
    clock_seq_hi_variant = (clock_seq >> long(8)) & long(0x3f)
    if node is None:
        node = getnode()
    return UUID(fields=(time_low, time_mid, time_hi_version,
                        clock_seq_hi_variant, clock_seq_low, node), version=1)


def uuid3(namespace, name):
    """Generate a UUID from the MD5 hash of a namespace UUID and a name."""
    import md5
    my_hash = md5.md5(namespace.bytes + name).digest()
    return UUID(bytes=my_hash[:16], version=3)


def uuid4():
    """Generate a random UUID."""

    if _uuid_generate_random:
        _uuid_generate_random(_buffer)
        return UUID(bytes=_buffer.raw)

    # Otherwise, get randomness from urandom or the 'random' module.
    try:
        import os
        return UUID(bytes=os.urandom(16), version=4)
    except:
        import random
        bytes = [chr(random.randrange(256)) for i in range(16)]
        return UUID(bytes=bytes, version=4)


def uuid5(namespace, name):
    """Generate a UUID from the SHA-1 hash of a namespace UUID and a name."""
    import sha
    my_hash = sha.sha(namespace.bytes + name).digest()
    return UUID(bytes=my_hash[:16], version=5)

# The following standard UUIDs are for use with uuid3() or uuid5().

NAMESPACE_DNS = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_URL = UUID('6ba7b811-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_OID = UUID('6ba7b812-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_X500 = UUID('6ba7b814-9dad-11d1-80b4-00c04fd430c8')