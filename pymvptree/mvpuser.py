import pickle

from pymvptree.pymvptree import *


class Point:
    def __init__(self, id_, data, c_obj = None):
        if not isinstance(data, bytes):
            raise ValueError("data must be bytes")
        self._id = id_
        self._data = data
        if c_obj is None:
            self._c_obj = lib.mkpoint(
                pickle.dumps(self._id, protocol=0),
                self._data,
                len(self._data))
        else:
            self._c_obj = c_obj

    @classmethod
    def from_c_obj(cls, c_obj):
        if c_obj == ffi.NULL:
            raise ValueError("Invalid point NULL.")
        id_ = pickle.loads(ffi.string(lib.get_point_id(c_obj)))
        datalen = lib.get_point_datalen(c_obj)
        data = ffi.buffer(lib.get_point_data(c_obj), datalen)[:]
        return cls(id_, data, c_obj=c_obj)


class Tree:
    def __init__(self, c_obj = None):
        self.points = []
        if c_obj is None:
            self._c_obj = lib.newtree()
        else:
            self._c_obj = c_obj

    @classmethod
    def from_file(cls, filename):
        return cls(c_obj=lib.load(filename.encode("utf-8")))

    def to_file(self, filename):
        lib.save(filename.encode("utf-8"), self._c_obj)

    def add(self, point):
        if not isinstance(point, Point):
            raise ValueError("Must be a point.")
        self.points.append(point)
        lib.addpoint(self._c_obj, point._c_obj)

    def exact(self, data):
        p = Point(b'', data)
        nbresults = ffi.new("unsigned int *")
        error = ffi.new("MVPError *")
        res = lib.mvptree_retrieve(self._c_obj, p._c_obj, 1, 1, nbresults, error)
        if nbresults[0] > 0:
            return Point.from_c_obj(res[0])

    def search(self, data, radius, limit=65535):
        p = Point(b'', data)
        nbresults = ffi.new("unsigned int *")
        error = ffi.new("MVPError *")
        res = lib.mvptree_retrieve(self._c_obj,
                                   p._c_obj,
                                   limit,
                                   radius,
                                   nbresults,
                                   error)
        if error[0]:
            raise RuntimeError(ffi.string(lib.mvp_errstr(error[0])))
        for i in range(nbresults[0]):
            try:
                p = Point.from_c_obj(res[i])
            except ValueError:
                break
            else:
                yield p
