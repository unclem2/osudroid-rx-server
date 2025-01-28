import javaobj.v2
import javaobj.v2.transformers
from stream_unzip import stream_unzip
import javaobj
import struct
import io
from objects.replay_data.movementtype import MovementType
from objects.replay_data.cursordata import CursorData
from objects.replay_data.hitresult import HitResult
from objects.replay_data.replayobjectdata import ReplayObjectData


class Replay:
    def __init__(self):
        self.replay_file = None
        self.replay_obj = None
        self.map: str = None
        self.file_name: str = None
        self.md5: str = None
        self.unix_date: int = 0
        self.hit300k: int = 0
        self.hit300: int = 0
        self.hit100k: int = 0
        self.hit100: int = 0
        self.hit50: int = 0
        self.hit0: int = 0
        self.score: int = 0
        self.combo: int = 0
        self.username: str = None
        self.parsed_mods: list = []
        self.converted_mods: list = []
        self.__buffer_offset: int = 0
        self.cursor_data: list = []
        self.hit_result_data: list = []

    def __zipped_chunks(self, filename):
        with open(filename, "rb") as f:
            while chunk := f.read(65536):
                yield chunk



    def __read_byte(self, replay_data):
        replay_data.seek(self.__buffer_offset)
        self.__buffer_offset += 1
        return struct.unpack(">b", replay_data.read(1))[0]

    def __read_short(self, replay_data):
        replay_data.seek(self.__buffer_offset)
        self.__buffer_offset += 2
        return struct.unpack(">h", replay_data.read(2))[0]
    
    def __read_int(self, replay_data):
        replay_data.seek(self.__buffer_offset)
        self.__buffer_offset += 4
        return struct.unpack(">i", replay_data.read(4))[0]

    def __read_float(self, replay_data):
        replay_data.seek(self.__buffer_offset)
        self.__buffer_offset += 4
        return struct.unpack(">f", replay_data.read(4))[0]

    def __droid_replay_mods_to_std(self):
        mod_mapping = {
            "MOD_NOFAIL": "NF",
            "MOD_EASY": "EZ",
            "MOD_HIDDEN": "HD",
            "MOD_HARDROCK": "HR",
            "MOD_SUDDENDEATH": "SD",
            "MOD_DOUBLETIME": "DT",
            "MOD_RELAX": "RX",
            "MOD_HALFTIME": "HT",
            "MOD_NIGHTCORE": "NC",
            "MOD_FLASHLIGHT": "FL",
            "MOD_SCOREV2": "V2",
            "MOD_AUTOPILOT": "AP",
            "MOD_AUTO": "AT",
            "MOD_PRECISE": "PR",
            "MOD_REALLYEASY": "REZ",
            "MOD_SMALLCIRCLES": "SC",
            "MOD_PERFECT": "PF",
            "MOD_SUDDENDEATH": "SU",
        }

        for mod in self.parsed_mods:
            if mod in mod_mapping:
                self.converted_mods.append(mod_mapping[mod])
        return self.converted_mods

    def __parse_movement_data(self, replay_data):
        replay_data = io.BytesIO(replay_data)
        size = self.__read_int(replay_data)

        # copypasta begins here
        for i in range(size):
            move_size = self.__read_int(replay_data)
            time = []
            x = []
            y = []
            id = []
            for j in range(0, move_size):
                time.append(self.__read_int(replay_data))
                id.append(time[j] & 3)
                time[j] >>= 2
                if id[j] != MovementType.UP.value:
                    if self.version >= 5:
                        x.append(self.__read_float(replay_data))
                        y.append(self.__read_float(replay_data))
                    else:
                        x.append(self.__read_short(replay_data))
                        y.append(self.__read_short(replay_data))
                else:
                    x.append(-1)
                    y.append(-1)

            cursor_data = CursorData({
                "size": move_size,
                "time": time,
                "x": x,
                "y": y,
                "id": id
            }).__dict__

            self.cursor_data.append(cursor_data['occurrence_groups'])
            
    def __parse_hitresult_data(self, replay_data):
        replay_data = io.BytesIO(replay_data)

        hitobject_data_lenght = self.__read_int(replay_data)
        
        for i in range(hitobject_data_lenght):
            replay_object_data = ReplayObjectData(
                accuracy=0.0,
                tickset=[],
                result=HitResult.MISS
            )
            replay_object_data.accuracy = self.__read_short(replay_data)
            len = self.__read_byte(replay_data)
            
            if len > 0:
                bytes = []
                for j in range(len):
                    bytes.append(self.__read_byte(replay_data))
                for j in range(len * 8):
                    replay_object_data.tickset.append((bytes[len - round(j/8) - 1] & (1 << round(j % 8))) != 0)
                
            replay_object_data.result = HitResult(self.__read_byte(replay_data))
            self.hit_result_data.append(replay_object_data.__dict__)
                    
            

    def load(self, filename):
        self.replay_file = filename

        for file_name, file_size, unzipped_chunks in stream_unzip(
                self.__zipped_chunks(filename)):

            data_buffer = io.BytesIO()

            try:
                for chunk in unzipped_chunks:
                    data_buffer.write(chunk)
            except Exception as e:
                break

        self.replay_obj = javaobj.v2.loads(data_buffer.getvalue())

        for fields in self.replay_obj[0].__dict__['field_data'].values():
            for field, value in fields.items():
                if field.name == 'version':
                    self.version = value

        self.map = self.replay_obj[1].value
        self.file_name = self.replay_obj[2].value
        self.md5 = self.replay_obj[3].value

        if self.version >= 3:
            (self.unix_date, self.hit300k, self.hit300,
             self.hit100k, self.hit100, self.hit50,
             self.hit0, self.score, self.combo) = struct.unpack(">Qiiiiiiii", io.BytesIO(self.replay_obj[4].data).read(40))
            self.username = self.replay_obj[5].value

            for field in self.replay_obj[6].__dict__['field_data'].values():
                for field, value in field.items():
                    if field.name == "elements":
                        for element in value:
                            self.parsed_mods.append(element.value)
                        break

            self.__droid_replay_mods_to_std()

        if self.version >= 4:
            modifiers = self.replay_obj[7].value.split("|")
            for modifier in modifiers:
                if modifier.startswith("AR"):
                    self.force_ar = float(modifier.replace("AR", ""))
                if modifier.startswith("CS"):
                    self.force_cs = float(modifier.replace("CS", ""))
                if modifier.startswith("OD"):
                    self.force_od = float(modifier.replace("OD", ""))
                if modifier.startswith("HP"):
                    self.force_hp = float(modifier.replace("HP", ""))
                if modifier.startswith("x"):
                    self.speed_multiplier = float(
                        modifier.replace("x", "") or 1)
                if modifier.startswith("FLD"):
                    self.fl_delay = float(modifier.replace("FLD", "") or 0.12)

        buffer_index = 0
        if self.version <= 2:
            buffer_index = 4
        elif self.version == 3:
            buffer_index = 7
        elif self.version >= 4:
            buffer_index = 8

        replay_data = io.BytesIO()
        for i in range(buffer_index, len(self.replay_obj)):
            replay_data.write(self.replay_obj[i].data)

        self.__parse_movement_data(replay_data.getvalue())
        print(self.__buffer_offset)
        self.__parse_hitresult_data(replay_data.getvalue())

    def __str__(self):
        string = ""
        for key, value in self.__dict__.items():
            if key == "replay_obj" or key == "replay_file" or key == "cursor_data":
                continue

            string += f"{key}: {value} "
        return string
