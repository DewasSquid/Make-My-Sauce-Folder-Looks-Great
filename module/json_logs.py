import json

class JsonLogs():
    def add(self, filename):
        """Will add the file to a json log. Containing every file that have already been renamed."""
        with open("logs.json", "r+") as f:
            data = json.load(f)
            data["already_marked"].append(filename)
            f.seek(0)
            json.dump(data, f, indent=4)
        
    def check(self, filename):
        """Return True if the file is already in the log. Return False otherwise."""
        with open("logs.json", "r") as f:
            data = json.load(f)
            
            return filename in data["already_marked"]