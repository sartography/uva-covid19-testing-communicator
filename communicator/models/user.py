from communicator import ma


class User:
    def __init__(self, uid, display_name):
        self.uid = uid
        self.display_name = display_name


class UserSchema(ma.Schema):
    class Meta:
        fields = ["uid", "display_name"]
