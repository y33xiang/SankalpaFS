"""The Python implementation of the gRPC Sankalpa FS server."""

import sys
import sankalpa_fs_pb2
import os
import time
import tempfile

#TODO:
# version number as extended file attributes
# Multiple clients
# Exception handling

def _full_path(base_path, relative_path):
    if relative_path.startswith('/'):
        relative_path = relative_path[1:]
    return os.path.join(base_path, relative_path)

class SankalpaFSServicer(sankalpa_fs_pb2.BetaSankalpaFSServicer):
    """Provides methods that implement functionality of Sankalpa FS server."""

    def __init__(self, storage_dir):
        self.__base_dir = storage_dir

        self.__stream_packet_size = 64 * 1024  # TCP packet size
        self.__stream_packet_size -= 60  # maximum TCP header size
        self.__stream_packet_size -= 192  # maximum IPv4 header size
        self.__stream_packet_size -= 24  # Ethernet header size

    def get_mtime(self, Path, context):
        print '********** in get_mtime ************'
        print '********** %s' % self.__base_dir
        print '********** %s' % Path.path
        print '********** %s' % _full_path(self.__base_dir, Path.path)
        mt = os.stat(_full_path(self.__base_dir, Path.path)).st_mtime 
        print mt
        return sankalpa_fs_pb2.MTime(mtime=mt) 

    def get_file_contents(self, Path, context):
        with open(os.path.join(self.__base_dir, Path.path, 'rb')) as fo:
            while True:
                byte_stream = fo.read(self.__stream_packet_size)
                if byte_stream:
                    yield byte_stream
                else:
                    break

    def update_file(self, Content, context):
        file_name = None

        with tempfile.NamedTemporaryFile() as temp:
            counter = 0
            # TODO: try multiple for loops and slicing
            for cont in Content:
                if counter == 0:
                    file_name = cont
                    counter += 1
                    continue
                temp.write(Content.content)
            os.rename(tempfile.NamedTemporaryFile.name, os.path.join(self.__base_dir
                                                           ,file_name))

    def delete(self, Path, context):
        os.remove(os.path.join(self.__base_dir, Path.path))
        
def serve():
    storage_dir = sys.argv[1]
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    server = sankalpa_fs_pb2.beta_create_SankalpaFS_server(SankalpaFSServicer(sys.argv[1]))
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(24 * 60 * 60)
    except KeyboardInterrupt:
        server.stop()

if __name__ == '__main__':
    serve()