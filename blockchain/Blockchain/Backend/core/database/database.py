import os
import json


class BaseDB:
    def __init__(self):
        # Locate data directory relative to repository/project structure
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        data_dir = os.path.join(project_root, "data")
        if not os.path.exists(data_dir):
            cwd_data = os.path.abspath("data")
            if os.path.exists(cwd_data):
                data_dir = cwd_data
            else:
                os.makedirs(data_dir, exist_ok=True)
        self.basepath = data_dir
        self.filepath = os.path.join(self.basepath, self.filename)

    def read(self):
        if not os.path.exists(self.filepath):
            print(f"File {self.filepath} not available")
            return False

        with open(self.filepath, "r") as file:
            raw = file.readline()

        if len(raw) > 0:
            data = json.loads(raw)
        else:
            data = []
        return data

    def update(self, data):
        with open(self.filepath,'w+') as f:
            f.write(json.dumps(data))
        return True

    def write(self, item):
        data = self.read()
        if data:
            data = data + item
        else:
            data = item

        with open(self.filepath, "w+") as file:
            file.write(json.dumps(data))


class BlockchainDB(BaseDB):
    def __init__(self):
        self.filename = "blockchain"
        super().__init__()

    def lastBlock(self):
        data = self.read()

        if data:
            return data[-1]


class AccountDB(BaseDB):
    def __init__(self):
        self.filename = "account"
        super().__init__()


class NodeDB(BaseDB):
    def __init__(self):
        self.filename = "node"
        super().__init__()