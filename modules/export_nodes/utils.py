class ObjectTypes:
    MESH = 'MESH'
    ARMATURE = 'ARMATURE'
    NONE = 'NONE'


def object_filter(self, value):
    if self.filter_type == ObjectTypes.NONE:
        return True

    return value.type == self.filter_type


def object_filter_static(filter_type: str):
    def object_filter_temp(self, value):
        if filter_type == ObjectTypes.NONE:
            return True

        return value.type == filter_type
    return object_filter_temp
