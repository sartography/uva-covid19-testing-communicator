from communicator import ma


class User:
    def __init__(self, uid, display_name, is_admin):
        self.uid = uid
        self.display_name = display_name
        self.is_admin = is_admin


class UserSchema(ma.Schema):
    class Meta:
        fields = ["uid", "display_name", "is_admin"]
